import logging

import slack
from django.conf import settings

from calendly import Calendly
from django.core import signing
from django.http import HttpResponse

from web.core.models import Webhook
from web.core.services import SlackMessageService

from web.core.messages import STATIC_HELP_MSG
from web.utils.errors import InvalidTokenError

logger = logging.getLogger(__name__)

COMMAND_LIST = ['connect', 'disconnect', 'upgrade', 'help']


def eligible_user(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'


def get_user_count(workspace):
    client = slack.WebClient(token=workspace.bot_token)
    response_users_list = client.users_list()

    count = len([u for u in response_users_list['members'] if eligible_user(u)])
    workspace.user_count = count
    workspace.save()


def has_active_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    if hooks.get('type') == 'authentication_error':
        raise InvalidTokenError('')

    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.error('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


def has_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    if hooks.get('type') == 'authentication_error':
        raise InvalidTokenError('')

    return len(hooks['data'])


def remove_hooks(calendly_client):
    res = True
    hooks = calendly_client.list_webhooks()
    for hook in hooks['data']:
        response = calendly_client.remove_webhook(hook['id'])
        if response.get('success') in [False, None]:
            logger.error(f"Could not delete Calendly webhook for {hook['id']}")
            res = False
    return res


def setup_handle_destination(response_url, su, channel=None):
    slack_msg_service = SlackMessageService(su.workspace.bot_token)
    destination_id = channel if channel else su.slack_id
    try:
        calendly = Calendly(su.calendly_authtoken)

        if has_active_hooks(calendly):
            # check if there's an existing working hook for this user
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            logger.error(f'Trying to setup Calendly token on already setup account: {su.slack_id}')
            slack_msg_service.update_interaction(response_url,
                                                 "Your account is already setup to receive event notifications. "
                                                 "Please contact support if you're experiencing issues.")
        else:
            signed_value = signing.dumps((su.workspace.slack_id, destination_id))

            webhook_create_response = calendly.create_webhook(
                f"{settings.SITE_URL}/handle/{signed_value}/")

            if 'id' not in webhook_create_response:
                errors = {}
                if 'message' in webhook_create_response:
                    errors = webhook_create_response['errors']
                logger.error(f'Could not setup Calendly webhook. {errors}')
                slack_msg_service.update_interaction(
                    response_url,
                    text=f"Could not connect with Calendly API. {STATIC_HELP_MSG}")
            else:
                Webhook.objects.create(user=su, calendly_id=webhook_create_response['id'],
                                       destination_id=destination_id)
                if channel:
                    # join channel if not already there
                    slack_msg_service.client.conversations_join(channel=destination_id)
                slack_msg_service.update_interaction(
                    response_url,
                    text="Setup complete. You will now receive notifications on created and canceled events!")
    except Exception:
        logger.exception('Could not connect to calendly')
        slack_msg_service.update_interaction(
            response_url,
            text=f"Could not connect to Calendly. {STATIC_HELP_MSG}")
    return HttpResponse(status=200)
