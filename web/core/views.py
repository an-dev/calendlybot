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

from web.core.message import SlackMarkdownEventCreatedMessage, SlackMarkdownEventCanceledMessage
from web.core.models import SlackUser, Webhook, Workspace

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def index(request):
    return TemplateResponse(request, 'web/index.html',
                            {'oauth_scope': oauth_scope, 'client_id': client_id})


def eligible_user(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'


def send_message_to_users(workspace, new_workspace):
    client = slack.WebClient(token=workspace.bot_token)
    response_users_list = client.users_list()

    for user in filter(lambda u: eligible_user(u), response_users_list['members']):
        su, _ = SlackUser.objects.get_or_create(slack_id=user['id'], workspace=workspace)
        su.name = user['real_name']
        su.save()
        if new_workspace:
            client.chat_postMessage(
                channel=su.slack_id,
                text=f"Hello {user['real_name']}. I'm CalendlyBot. Type `/connect` to start!")


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
@require_http_methods(["POST"])
def connect(request):
    try:
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su, _ = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                workspace=workspace)
        client = slack.WebClient(token=su.workspace.bot_token)
        calendly = Calendly(request.POST['text'])
        response = calendly.echo()
        if not response.get('email'):
            client.chat_postMessage(
                channel=su.slack_id,
                text="Could not find user in Calendly. Make sure the APIKey is correct.")
            return HttpResponse(status=200)
        su.calendly_email = response['email']
        su.calendly_authtoken = request.POST['text']
        su.save()
        signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
        response = calendly.create_webhook(f"{settings.SITE_URL}/handle/{signed_value}/")
        if not response['id']:
            client.chat_postMessage(
                channel=su.slack_id,
                text="Could not connect with Calendly API. Please retry.")
            return HttpResponse(status=200)
        Webhook.objects.create(user=su, calendly_id=response['id'])
        client.chat_postMessage(
            channel=su.slack_id,
            text="Setup complete. You will now receive notifications on created and canceled events!")
    except Exception:
        logger.exception("Could not complete request")
    return HttpResponse(status=200)


@csrf_exempt
@require_http_methods(["POST"])
def handle(request, signed_value):
    try:
        workspace_slack_id, user_slack_id = signing.loads(signed_value)
        su = SlackUser.objects.get(slack_id=user_slack_id, workspace__slack_id=workspace_slack_id)
        client = slack.WebClient(token=su.workspace.bot_token)

        data = request.POST
        event_type = data.get('event')

        if event_type not in ['invitee.created', 'invitee.canceled']:
            logger.exception("Something went wrong. Could not handle event type.", request.POST)
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
            txt = f"Hi {name}. A new event has been scheduled."
            msg = SlackMarkdownEventCreatedMessage(**message_values)

        if event_type == 'invitee.canceled':
            message_values = {
                'name': name,
                'event_name': data['event_type']['name'],
                'invitee_name': data['invitee']['name'],
                'invitee_email': data['invitee']['email'],
                'canceler_name': data['event']['canceler_name']
            }
            txt = f"Hi {name}. The event below has been canceled."
            msg = SlackMarkdownEventCanceledMessage(**message_values)

        if event_type in ['invitee.created', 'invitee.canceled']:
            client.chat_postMessage(
                channel=su.slack_id,
                txt=txt,
                blocks=msg.get_blocks(),
                attachments=msg.get_attachments()
            )
        return HttpResponse(status=200)
    except Exception:
        logger.exception("Could not handle hook event")
        return HttpResponse(status=500)
