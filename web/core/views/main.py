import json
import logging
import os
import slack

from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import verify_request
from web.core.messages import STATIC_START_MSG
from web.core.modals import SlackDisconnectErrorModal, SlackConnectModal, \
    SlackConnectModalWithError, SlackDestinationErrorModal, SlackDestinationChannelModal
from web.core.models import SlackUser, Workspace
from web.core.services import SlackMessageService, DisconnectUserService, UpdateHomeViewService, OpenModalService, \
    ConnectUserService, SetDestinationService, UpdateHomeMessageService
from web.core.actions import *
from web.utils import get_user_count, mail

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
        trigger_id = data.get('trigger_id')
        user_id, workspace_id = data['user']['id'], data['user']['team_id']

        if data['type'] == 'block_actions':
            action = data['actions'][0]['action_id']
            logger.info(f"User {user_id} is interacting with {action}")

            response_url = data.get('response_url')

            if action == BTN_CONNECT:
                OpenModalService(workspace_id).run(trigger_id,
                                                   SlackConnectModal(private_metadata=response_url).get_view())
            if action == BTN_DISCONNECT:
                result = DisconnectUserService(user_id, workspace_id).run()
                UpdateHomeMessageService(user_id, workspace_id).run(response_url)
                UpdateHomeViewService(user_id, workspace_id).run()
                if result.failure:
                    OpenModalService(workspace_id).run(trigger_id, SlackDisconnectErrorModal().get_view())

            if action == BTN_HOOK_DEST:
                su = SlackUser.objects.get(slack_id=user_id, workspace__slack_id=workspace_id)
                OpenModalService(workspace_id).run(trigger_id,
                                                   SlackDestinationChannelModal(
                                                       su,
                                                       private_metadata=response_url).get_view()
                                                   )

            if action.startswith('hook_'):
                # get event id from action
                # call service and set destination
                # update og message
                import pdb; pdb.set_trace()

        if data['type'] == 'view_submission':
            block_data = dict(data['view']['state']['values'])

            if block_data.get('block_connect'):
                value = block_data['block_connect']['input_connect']['value']
                workspace = Workspace.objects.get(slack_id=workspace_id)
                result = ConnectUserService(user_id, workspace, value).run()
                if result.failure:
                    return HttpResponse(status=200,
                                        content=json.dumps(
                                            SlackConnectModalWithError('block_connect', result.error).get_view()),
                                        content_type='application/json')
                else:
                    if data['view'].get('private_metadata'):
                        UpdateHomeMessageService(user_id, workspace_id).run(data['view']['private_metadata'])
                    UpdateHomeViewService(user_id, workspace_id).run()

    except Exception:
        logger.exception("Could not parse interaction")
    return HttpResponse(status=200)
