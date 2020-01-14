import logging
import os

import slack
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

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


def send_message_to_users():
    client = slack.WebClient(token=os.environ["SLACK_USER_TOKEN"])
    response_users_list = client.users_list()
    for user in filter(lambda u: eligible_user(u), response_users_list['members']):
        client.chat_postMessage(
            channel=user['id'],
            text=f"Hello {user['real_name']}!")


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
        os.environ["SLACK_USER_TOKEN"] = response['access_token']
        send_message_to_users()

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
    import pdb; pdb.set_trace()
