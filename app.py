import logging
import os
import slack
from flask import Flask, request

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/auth", methods=["GET"])
def pre_install():
    return f'<a href="https://slack.com/oauth/authorize?scope={oauth_scope}&client_id={client_id}">Add to Slack</a>'


@app.route("/post-auth", methods=["GET"])
def post_install():
    try:
        # Retrieve the auth code from the request params
        auth_code = request.args['code']

        # An empty string is a valid token for this request
        client = slack.WebClient(token="")

        # Request the auth tokens from Slack
        response = client.oauth_access(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )

        # Save the bot token to an environmental variable or to your data store
        # for later use
        os.environ["SLACK_USER_TOKEN"] = response['access_token']
        send_message_to_users()

        # Don't forget to let the user know that auth has succeeded!
        return "Auth complete!"
    except Exception:
        logger.exception("Could not complete auth setup")
        return "Uh oh. Could not setup Auth. Please retry."


def eligible_user(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'


def send_message_to_users():
    client = slack.WebClient(token=os.environ["SLACK_USER_TOKEN"])
    response_users_list = client.users_list()
    for user in filter(lambda u: eligible_user(u), response_users_list['members']):
        client.chat_postMessage(
            channel=user['id'],
            text=f"Hello {user['real_name']}!")


if __name__ == '__main__':
    app.run(debug=True)
