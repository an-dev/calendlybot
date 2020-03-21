import json
import logging

from django.core import signing
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from web.core.decorators import requires_subscription, verify_request
from web.core.messages import SlackMarkdownEventCreatedMessage, SlackMarkdownEventCanceledMessage
from web.core.models import SlackUser, Workspace
from web.core.services import SlackMessageService
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
        workspace_slack_id, destination_slack_id = signing.loads(signed_value)
        workspace = Workspace.object.get(slack_id=workspace_slack_id)

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
            SlackMessageService(workspace.bot_token).send(
                destination_slack_id,
                txt,
                msg.get_blocks(),
                msg.get_attachments()
            )
        return HttpResponse(status=200)
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


@csrf_exempt
@verify_request
@require_http_methods(["POST"])
def commands(request):
    try:
        command = request.POST['text'].split(' ')[0]
        if command not in COMMAND_LIST:
            workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
            su, created = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                          workspace=workspace)
            slack_msg_service = SlackMessageService(workspace.bot_token)
            slack_msg_service.send(su.slack_id,
                                   "Could not find command. Try typing `/duck help` if you're lost.")
            return HttpResponse(status=200)
        method_to_call = getattr(slack_commands, command)
        return method_to_call(request)
    except Exception:
        logger.exception("Error executing command")
        return HttpResponse(status=200)
