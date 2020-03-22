import logging
from django.conf import settings

from calendly import Calendly
from django.core import signing
from django.http import HttpResponse

from web.core.models import Webhook
from web.core.services import SlackMessageService

from web.core.messages import STATIC_HELP_MSG

logger = logging.getLogger(__name__)

COMMAND_LIST = ['connect', 'upgrade', 'help']


def eligible_user(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'


def has_active_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.error('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


def setup_handle_destination(response_url, su, channel=None):
    slack_msg_service = SlackMessageService(su.workspace.bot_token)
    destination_id = channel if channel else su.slack_id
    try:
        calendly = Calendly(su.calendly_authtoken)
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
            Webhook.objects.create(user=su, calendly_id=webhook_create_response['id'], destination_id=destination_id)
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
