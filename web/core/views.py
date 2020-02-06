import json
import logging
import os

import slack
from calendly import Calendly
from django.conf import settings
from django.core import signing
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import requires_subscription, verify_request
from web.core.messages import SlackMarkdownEventCanceledMessage, SlackMarkdownEventCreatedMessage, \
    SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage
from web.core.models import SlackUser, Webhook, Workspace
from web.core.services import SlackMessageService
from web.payments.services import WorkspaceUpgradeService
from web.utils import eligible_user

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def index(request):
    return TemplateResponse(request, 'web/index.html',
                            {'oauth_scope': oauth_scope, 'client_id': client_id})


def send_message_to_users(workspace, new_workspace):
    client = slack.WebClient(token=workspace.bot_token)
    response_users_list = client.users_list()

    for user in filter(lambda u: eligible_user(u), response_users_list['members']):
        su, _ = SlackUser.objects.get_or_create(slack_id=user['id'], workspace=workspace)
        su.slack_name = user['real_name']
        su.save()
        if new_workspace:
            client.chat_postMessage(
                channel=su.slack_id,
                text=f"Hello {user['real_name']}. I'm Calenduck. Type `/connect` to start!")


def has_active_hooks(calendly):
    hooks = calendly.list_webhooks()
    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.warning('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


@require_http_methods(["GET"])
def auth(request):
    try:
        # Retrieve the auth code from the request params
        auth_code = request.GET['code']

        # An empty string is a valid token for this request
        client = slack.WebClient(token="")

        # Request the auth tokens from Slack
        response = client.oauth_v2_access(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )

        # Save the bot token to an environmental variable or to your data store
        # for later use
        # response doesn't have a bot object
        workspace, new = Workspace.objects.get_or_create(slack_id=response['team']['id'])
        workspace.bot_token = response['access_token']
        workspace.save()

        send_message_to_users(workspace, new)

        # Don't forget to let the user know that auth has succeeded!
        msg = "Auth complete!"
    except Exception:
        logger.exception("Could not complete auth setup")
        msg = "Uh oh. Could not setup auth. Please retry."
    return TemplateResponse(request, 'web/auth.html',
                            {'msg': msg})


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def connect(request):
    try:
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su, created = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                      workspace=workspace)

        # atm, we support just one authtoken per user. Calling this command effectively overwrites
        calendly = Calendly(request.POST['text'])
        response_from_echo = calendly.echo()
        slack_msg_service = SlackMessageService(su.workspace.bot_token)
        if 'email' not in response_from_echo:
            slack_msg_service.send(su.slack_id,
                                   "Could not find user in Calendly. Make sure the APIKey is correct.")
            return HttpResponse(status=200)

        # check if there's an existing working hook for this user
        if not has_active_hooks(calendly):
            signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
            response_from_webhook_create = calendly.create_webhook(
                f"{settings.SITE_URL}/handle/{signed_value}/")
            if 'id' not in response_from_webhook_create:
                msg = 'Please retry'
                if 'message' in response_from_webhook_create:
                    msg = response_from_webhook_create['message']
                slack_msg_service.send(su.slack_id,
                                       f"Could not connect with Calendly API. {msg}.")
                return HttpResponse(status=200)
            Webhook.objects.create(user=su, calendly_id=response_from_webhook_create['id'])
            su.calendly_authtoken = request.POST['text']
            su.calendly_email = response_from_echo['email']
            su.save()
            slack_msg_service.send(su.slack_id,
                                   "Setup complete. You will now receive notifications on created and canceled events!")
        else:
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            slack_msg_service.send(su.slack_id,
                                   "The account is already setup to receive event notifications. Please contact support if you're experiencing issues.")
    except Exception:
        logger.exception("Could not complete connect request")
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def upgrade(request):
    try:
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su = SlackUser.objects.get(slack_id=request.POST['user_id'], workspace=workspace)

        checkout_session_id = WorkspaceUpgradeService(workspace).run()

        msg = SlackMarkdownUpgradeLinkMessage(checkout_session_id)
        SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                      "Thanks for giving Calenduck a try!",
                                                      msg.get_blocks())
    except Exception:
        logger.exception("Could not complete upgrade request")
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def upgrade(request):
    try:
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su = SlackUser.objects.get(slack_id=request.POST['user_id'], workspace=workspace)

        msg = SlackMarkdownHelpMessage()
        SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                      "Here are some useful tips!",
                                                      msg.get_blocks(),
                                                      msg.get_attachments())
    except Exception:
        logger.exception("Could not complete help request")
    return HttpResponse(status=200)


@csrf_exempt
@requires_subscription
@require_http_methods(["POST"])
def handle(request, signed_value):
    try:
        workspace_slack_id, user_slack_id = signing.loads(signed_value)
        su = SlackUser.objects.get(slack_id=user_slack_id, workspace__slack_id=workspace_slack_id)

        data = json.loads(request.body)
        event_type = data.get('event')

        if event_type not in ['invitee.created', 'invitee.canceled']:
            logger.exception(
                "Something went wrong. Could not handle event type:\n{}".format(request.body))
            return HttpResponse(status=400)

        data = data['payload']
        name = data['event']['assigned_to'][0]
        if event_type == 'invitee.created':
            message_values = {
                'name': name,
                'event_name': data['event_type']['name'],
                'event_start_time': data['event']['invitee_start_time_pretty'],
                'invitee_name': data['invitee']['name'],
                'invitee_email': data['invitee']['email'],
                'invitee_timezone': data['invitee']['timezone']
            }
            txt = f"Hi {name}, a new event has been scheduled."
            msg = SlackMarkdownEventCreatedMessage(**message_values)

        if event_type == 'invitee.canceled':
            message_values = {
                'name': name,
                'event_name': data['event_type']['name'],
                'event_start_time': data['event']['invitee_start_time_pretty'],
                'invitee_name': data['invitee']['name'],
                'invitee_email': data['invitee']['email'],
                'canceler_name': data['event']['canceler_name']
            }
            txt = f"Hi {name}, the event below has been canceled."
            msg = SlackMarkdownEventCanceledMessage(**message_values)

        if event_type in ['invitee.created', 'invitee.canceled']:
            SlackMessageService(su.workspace.bot_token).send(
                su.slack_id,
                txt,
                msg.get_blocks(),
                msg.get_attachments()
            )
        return HttpResponse(status=200)
    except SlackUser.DoesNotExist:
        logger.exception("Could not find user")
    except Exception:
        logger.exception("Could not handle hook event")
        # # re-create webhook
        # calendly = Calendly(su.calendly_authtoken)
        # signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
        # response = calendly.create_webhook(f"{settings.SITE_URL}/handle/{signed_value}/")
        # if 'id' in response:
        #     Webhook.objects.create(user=su, calendly_id=response['id'])
        # else:
        #     logger.error("Could not recreate webhook {}".format(response))
    return HttpResponse(status=500)
