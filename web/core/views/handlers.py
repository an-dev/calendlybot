import json
import logging

from django.core import signing
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import requires_subscription
from web.core.messages import SlackMarkdownEventCreatedMessage, SlackMarkdownEventCanceledMessage
from web.core.models import SlackUser
from web.core.services import SlackMessageService

logger = logging.getLogger(__name__)


def get_created_event_message_data(data):
    name = data['event']['assigned_to'][0]
    simple_text = f"Hi {name}, a new event has been scheduled."
    msg_object = {
        'name': name,
        'event_name': data['event_type']['name'],
        'event_start_time': data['event']['invitee_start_time_pretty'],
        'invitee_name': data['invitee']['name'],
        'invitee_email': data['invitee']['email'],
        'invitee_timezone': data['invitee']['timezone']
    }
    return simple_text, msg_object


def get_cancelled_event_message_data(data):
    name = data['event']['assigned_to'][0]
    simple_text = f"Hi {name}, the event below has been canceled."
    msg_object = {
        'name': name,
        'event_name': data['event_type']['name'],
        'event_start_time': data['event']['invitee_start_time_pretty'],
        'invitee_name': data['invitee']['name'],
        'invitee_email': data['invitee']['email'],
        'canceler_name': data['event']['canceler_name']
    }
    return simple_text, msg_object


@csrf_exempt
@requires_subscription
@require_http_methods(["POST"])
def handle(request, signed_value):
    try:
        workspace_slack_id, user_slack_id = signing.loads(signed_value)
        su = SlackUser.objects.get(slack_id=user_slack_id, workspace__slack_id=workspace_slack_id)

        data = json.loads(request.body)
        event_type = data.get('event')

        if event_type not in ['invitee.created', 'invitee.canceled']:
            logger.exception(
                "Something went wrong. Could not handle event type:\n{}".format(request.body))
            return HttpResponse(status=400)

        data = data['payload']
        if event_type == 'invitee.created':
            txt, message_values = get_created_event_message_data(data)
            msg = SlackMarkdownEventCreatedMessage(**message_values)

        if event_type == 'invitee.canceled':
            txt, message_values = get_cancelled_event_message_data(data)
            msg = SlackMarkdownEventCanceledMessage(**message_values)

        if event_type in ['invitee.created', 'invitee.canceled']:
            SlackMessageService(su.workspace.bot_token).send(
                su.slack_id,
                txt,
                msg.get_blocks(),
                msg.get_attachments()
            )
        return HttpResponse(status=200)
    except SlackUser.DoesNotExist:
        logger.exception("Could not find user")
    except Exception:
        logger.exception("Could not handle hook event")
        # # re-create webhook
        # calendly = Calendly(su.calendly_authtoken)
        # signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
        # response = calendly.create_webhook(f"{settings.SITE_URL}/handle/{signed_value}/")
        # if 'id' in response:
        #     Webhook.objects.create(user=su, calendly_id=response['id'])
        # else:
        #     logger.error("Could not recreate webhook {}".format(response))
    return HttpResponse(status=500)
