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

from web.core.decorators import verify_request
from web.core.messages import SlackMarkdownNotificationDestinationMessage
from web.core.models import SlackUser, Webhook, Workspace
from web.core.services import SlackMessageService
from web.utils import eligible_user, COMMAND_LIST

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]

logger = logging.getLogger(__name__)


def create_users(workspace, admin_id):
    client = slack.WebClient(token=workspace.bot_token)
    response_users_list = client.users_list()
    admin = None

    for user in filter(lambda u: eligible_user(u), response_users_list['members']):
        su, _ = SlackUser.objects.get_or_create(slack_id=user['id'], workspace=workspace)
        su.slack_name = user['profile'].get('first_name', user['profile']['real_name'])
        su.slack_email = user['profile']['email']
        if user['id'] == admin_id:
            admin = su
            su.is_installer = True
        su.save()
    return admin


def has_active_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.warning('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


@require_http_methods(["GET"])
def auth(request):
    error = False
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

        user = create_users(workspace, response['authed_user']['id'])
        if user:
            client.token = workspace.bot_token
            if new:
                client.chat_postMessage(
                    channel=user.slack_id,
                    text=f"Hi {user.slack_name}. I'm Calenduck. Type `/duck connect` to start!")
            else:
                client.chat_postMessage(
                    channel=user.slack_id,
                    text=f"Welcome back {user.slack_name}. Type `/duck connect` to start!")

        # Don't forget to let the user know that auth has succeeded!
        msg = "Auth complete!"
    except Exception:
        logger.exception("Could not complete auth setup")
        msg = "Uh oh. Could not setup auth."
        error = True
    return TemplateResponse(request, 'web/auth.html', {'msg': msg, 'error': error})


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def commands(request):
    try:
        command = request.POST['text'].split(' ')[0]
        if command not in COMMAND_LIST:
            workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
            su, created = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                          workspace=workspace)
            slack_msg_service = SlackMessageService(workspace.bot_token)
            slack_msg_service.send(su.slack_id,
                                   "Could not find command. Try typing `/duck help` if you're lost.")
            return HttpResponse(status=200)
        return globals()[command](request)
    except Exception:
        logger.exception("Error executing command")
        return HttpResponse(status=200)


def connect(request):
    workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
    su, created = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                  workspace=workspace)

    # atm, we support just one authtoken per user. Calling this command effectively overwrites
    token = request.POST['text'].split(' ')[1]
    calendly = Calendly(token)
    response_from_echo = calendly.echo()
    slack_msg_service = SlackMessageService(su.workspace.bot_token)
    if 'email' not in response_from_echo:
        logger.info(f'User {su.slack_email} does not have paid account')
        slack_msg_service.send(su.slack_id,
                               "Could not find user in Calendly. Make sure the token is correct.")
        return HttpResponse(status=200)

    # check if there's an existing working hook for this user
    if not has_active_hooks(calendly):

        # ask user where they want to send the hook

        signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
        response_from_webhook_create = calendly.create_webhook(
            f"{settings.SITE_URL}/handle/{signed_value}/")
        if 'id' not in response_from_webhook_create:
            msg = 'Please retry'
            if 'message' in response_from_webhook_create:
                msg = response_from_webhook_create['message']
            logger.warning(f'Could not setup Calendly webhook.', msg)
            slack_msg_service.send(su.slack_id,
                                   f"Could not connect with Calendly API. {msg}.")
            return HttpResponse(status=200)
        Webhook.objects.create(user=su, calendly_id=response_from_webhook_create['id'])
        su.calendly_authtoken = token
        su.calendly_email = response_from_echo['email']
        su.save()
        slack_msg_service.send(su.slack_id,
                               "Setup complete. You will now receive notifications on created and canceled events!")
    else:
        # this effectively means that if someone uses another's apiKey
        # if all its hooks are active they won't be able to setup
        slack_msg_service.send(su.slack_id,
                               "Your account is already setup to receive event notifications. "
                               "Please contact support if you're experiencing issues.")
    return HttpResponse(status=200)


def setup_handle_destination(slack_msg_service, su):
    msg = SlackMarkdownNotificationDestinationMessage()
    slack_msg_service.send(su.slack_id, msg)
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def get_destinations():
    import pdb; pdb.set_trace()
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def interactions():
    import pdb;
    pdb.set_trace()
    return HttpResponse(status=200)
