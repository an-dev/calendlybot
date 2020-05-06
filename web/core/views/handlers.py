import json
import logging

from django.core import signing
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import requires_subscription, verify_request
from web.core.messages import SlackMarkdownEventCreatedMessage, SlackMarkdownEventCancelledMessage, STATIC_HELP_MSG
from web.core.models import Workspace, Webhook
from web.core.services import SlackMessageService
from web.core.views.commands import duck
from web.utils import COMMAND_LIST
from web.core.views import commands as slack_commands

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
        'invitee_timezone': data['invitee']['timezone'],
        'location': data['event']['location']
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
        workspace = Workspace.objects.get(slack_id=workspace_slack_id)

        data = json.loads(request.body)
        event = data.get('event')

        if event not in ['invitee.created', 'invitee.canceled']:
            logger.exception(
                "Something went wrong. Could not handle event type:\n{}".format(request.body))
            return HttpResponse(status=200)

        payload = data['payload']

        event_id = payload['event_type']['uuid']
        destination_id = Webhook.objects.get(user__slack_id=user_slack_id, event_id=event_id)

        if event == 'invitee.created':
            txt, message_values = get_created_event_message_data(data)
            msg = SlackMarkdownEventCreatedMessage(**message_values)
            logger.info(f'Received created event: {message_values}')
        else:
            txt, message_values = get_cancelled_event_message_data(data)
            msg = SlackMarkdownEventCancelledMessage(**message_values)
            logger.info(f'Received cancelled event: {message_values}')

        SlackMessageService(workspace.bot_token).send(
            destination_id,
            txt,
            msg.get_blocks(),
            msg.get_attachments()
        )
    except Exception:
        logger.exception("Could not handle hook event")
    return HttpResponse(status=200)


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def commands(request):
    try:
        command = request.POST['text'].split(' ')[0]
        if command in COMMAND_LIST:
            method_to_call = getattr(slack_commands, command)
            method_to_call(request)
        else:
            duck(request)
    except Exception:
        logger.exception(f"Error executing command: {request.POST}")
    return HttpResponse(status=200)
