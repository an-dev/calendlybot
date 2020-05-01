import json
import logging
import os
import slack

from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import verify_request
from web.core.messages import SlackMarkdownNotificationDestinationChannelMessage, STATIC_START_MSG, STATIC_HELP_MSG, \
    SlackHomeViewMessage
from web.core.models import SlackUser, Workspace
from web.core.services import SlackMessageService, DisconnectService, UpdateHomeViewService, OpenModalService
from web.core.actions import *
from web.utils import setup_handle_destination, get_user_count, mail

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]

logger = logging.getLogger(__name__)


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
        token = response['access_token']
        user_id = response['authed_user']['id']
        team_id = response['team']['id']
        logger.info(f"Authed user is {response['authed_user']}")

        # Save the bot token to an environmental variable or to your data store
        # for later use
        # response doesn't have a bot object
        workspace, new_workspace = Workspace.objects.get_or_create(slack_id=team_id)
        workspace.bot_token = token
        workspace.name = response['team'].get('name')
        workspace.save()

        get_user_count.delay(response['team']['id'])

        client = slack.WebClient(token=token)
        user_info = client.users_info(user=user_id)
        su, new_user = SlackUser.objects.get_or_create(slack_id=user_id, workspace=workspace)
        su.slack_name = user_info['user']['profile'].get('first_name', user_info['user']['profile']['real_name'])
        su.slack_email = user_info['user']['profile']['email']
        su.save()

        if su and new_user:
            client.token = workspace.bot_token
            if new_user:
                client.chat_postMessage(
                    channel=su.slack_id,
                    text=f"Hi {su.slack_name}, I'm Calenduck. {STATIC_START_MSG}")
                mail.send_welcome_email.delay(user_id)
            else:
                client.chat_postMessage(
                    channel=su.slack_id,
                    text=f"Welcome back {su.slack_name}. {STATIC_START_MSG}")

        # Don't forget to let the user know that auth has succeeded!
        msg = "Auth complete!"

        UpdateHomeViewService(user_id, team_id)

    except Exception:
        logger.exception(f"Could not complete auth setup: {request.GET}")
        msg = "Uh oh. Could not setup auth."
        error = True
    return TemplateResponse(request, 'web/auth.html', {'msg': msg, 'error': error})


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def interactions(request):
    try:
        data = json.loads(request.POST['payload'])
        container_type = data['container']['type']
        action = data['actions'][0]['action_id']
        user_id, workspace_id = data['user']['id'], data['user']['team_id']
        su = SlackUser.objects.get(slack_id=user_id, workspace__slack_id=workspace_id)
        slack_msg_service = SlackMessageService(su.workspace.bot_token)

        logger.info(f"User {user_id} is interacting with {action}")

        if container_type == 'message_attachment':
            try:
                response_url = data['response_url']
                if action == BTN_HOOK_DEST_SELF:
                    return setup_handle_destination(response_url, su)
                elif action == BTN_HOOK_DEST_CHANNEL:
                    msg = SlackMarkdownNotificationDestinationChannelMessage()
                    slack_msg_service.update_interaction(
                        response_url,
                        blocks=msg.get_blocks()
                    )
                elif action == SELECT_HOOK_DEST_CHANNEL:
                    channel = data['actions'][0]['selected_conversation']
                    logger.info(f"{channel} channel selected")
                    return setup_handle_destination(response_url, su, channel)
                else:
                    if action == BTN_CANCEL:
                        slack_msg_service.update_interaction(
                            response_url,
                            text="You can pick things up later by typing `/duck connect your-calendly-token`.")
                    else:
                        slack_msg_service.send(su.slack_id, f"I don\'t think I understand. {STATIC_HELP_MSG}")
            except Exception as e:
                slack_msg_service.update_interaction(
                    response_url,
                    text=f"Could not parse interaction. {STATIC_HELP_MSG}")
                raise e
        else:
            trigger_id = data['trigger_id']
            if action == BTN_CONNECT:
                import pdb;
                pdb.set_trace()

            if action == BTN_DISCONNECT:
                import pdb;
                pdb.set_trace()
                # result = DisconnectService(user_id, workspace_id).run()
                # if result.success:
                #     UpdateHomeViewService(user_id, workspace_id)
                # else:
                    # display dialog/modal?
                    # msg = result.error
                    # add message from the error to the msg to display in the modal
                test_msg = {
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Notification settings",
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Cancel",
                    },
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Could not disconnect Calendly account. Please try again or contact support."
                            }
                        }
                    ]
                }
                OpenModalService(workspace_id).run(trigger_id, test_msg)
    except Exception:
        logger.exception("Could not parse interaction")
    return HttpResponse(status=200)
