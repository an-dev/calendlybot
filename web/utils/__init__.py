import logging

import slack
from celery import shared_task
from slack.errors import SlackApiError

from web.core.models import Workspace, SlackUser
from web.utils.errors import InvalidTokenError

logger = logging.getLogger(__name__)

COMMAND_LIST = ['reset', 'upgrade', 'help']


def user_eligible(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'


def user_connected(user: SlackUser):
    return user.calendly_email and user.calendly_authtoken


@shared_task(autoretry_for=(SlackApiError,))
def get_user_count(workspace_slack_id):
    try:
        workspace = Workspace.objects.get(slack_id=workspace_slack_id)
        client = slack.WebClient(token=workspace.bot_token)
        response_users_list = client.users_list()

        count = len([u for u in response_users_list['members'] if user_eligible(u)])
        workspace.user_count = count
        workspace.save()
    except Exception:
        logger.exception('Could not get workspace size')


def has_active_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    if hooks.get('type') == 'authentication_error':
        raise InvalidTokenError()

    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.error('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


def has_calendly_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    if hooks.get('type') == 'authentication_error':
        raise InvalidTokenError()

    return len(hooks['data'])


def remove_calendly_hooks(calendly_client):
    res = True
    hooks = calendly_client.list_webhooks()
    for hook in hooks['data']:
        response = calendly_client.remove_webhook(hook['id'])
        if not response.get('success'):
            logger.error(f"Could not delete Calendly webhook for {hook['id']}")
            res = False
    return res
