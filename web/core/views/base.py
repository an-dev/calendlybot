import json
import logging
import os

import slack
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import verify_request
from web.core.models import SlackUser, Workspace
from web.utils import eligible_user

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
def get_destinations():
    import pdb; pdb.set_trace()
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def interactions(request):
    import pdb;
    pdb.set_trace()
    import json
    data = json.loads(request.POST['payload'])
    # switch data['action'] and call correct method accordingly
    return HttpResponse(status=200)
