import json
import logging
import os

import slack
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import verify_request
from web.core.messages import SlackMarkdownNotificationDestinationChannelMessage, STATIC_START_MSG, STATIC_HELP_MSG
from web.core.models import SlackUser, Workspace
from web.core.services import SlackMessageService
from web.core.actions import *
from web.utils import eligible_user, setup_handle_destination

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
            su.manager = True
        su.save()
    return admin


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
        workspace.name = response['team'].get('name')
        workspace.save()

        user = create_users(workspace, response['authed_user']['id'])
        if user:
            client.token = workspace.bot_token
            if new:
                client.chat_postMessage(
                    channel=user.slack_id,
                    text=f"Hi {user.slack_name}, I'm Calenduck. {STATIC_START_MSG}")
            else:
                client.chat_postMessage(
                    channel=user.slack_id,
                    text=f"Welcome back {user.slack_name}. {STATIC_START_MSG}")

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
def interactions(request):
    try:
        data = json.loads(request.POST['payload'])
        action = data['actions'][0]['action_id']
        response_url = data['response_url']
        user_id, workspace_id = data['user']['id'], data['user']['team_id']
        su = SlackUser.objects.get(slack_id=user_id, workspace__slack_id=workspace_id)
        slack_msg_service = SlackMessageService(su.workspace.bot_token)

        if action == BTN_HOOK_DEST_SELF:
            return setup_handle_destination(response_url, su)
        elif action == BTN_HOOK_DEST_CHANNEL:
            msg = SlackMarkdownNotificationDestinationChannelMessage()
            slack_msg_service.update_interaction(
                response_url,
                blocks=msg.get_blocks()
            )
        elif action == SELECT_HOOK_DEST_CHANNEL:
            channel = data['actions'][0]['selected_channel']
            return setup_handle_destination(response_url, su, channel)
        else:
            if action == BTN_CANCEL:
                slack_msg_service.update_interaction(
                    response_url,
                    text="You can pick things up later by typing `/duck connect [calendly token]`.")
            else:
                slack_msg_service.send(su.slack_id, f"I don\'t think I understand. {STATIC_HELP_MSG}")
    except Exception:
        logger.exception("Could not parse interaction")
        slack_msg_service.update_interaction(
            response_url,
            text=f"Could not parse interaction. {STATIC_HELP_MSG}")
    return HttpResponse(status=200)
