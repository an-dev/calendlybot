from calendly import Calendly
from django.core import signing
from django.conf import settings
from django.http import HttpResponse

from web.core.messages import SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage, \
    SlackMarkdownNotificationDestinationMessage
from web.core.models import Workspace, SlackUser, Webhook
from web.core.services import SlackMessageService
from web.payments.services import WorkspaceUpgradeService
import logging

logger = logging.getLogger(__name__)


def upgrade(request):
    workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
    su = SlackUser.objects.get(slack_id=request.POST['user_id'], workspace=workspace)

    checkout_session_id = WorkspaceUpgradeService(workspace).run()

    msg = SlackMarkdownUpgradeLinkMessage(checkout_session_id)
    SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                  "Thanks for giving Calenduck a try!",
                                                  msg.get_blocks())
    return HttpResponse(status=200)


def help(request):
    workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
    su = SlackUser.objects.get(slack_id=request.POST['user_id'], workspace=workspace)

    msg = SlackMarkdownHelpMessage()
    SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                  "Here are some useful tips!",
                                                  msg.get_blocks(),
                                                  msg.get_attachments())
    return HttpResponse(status=200)


def has_active_hooks(calendly_client):
    hooks = calendly_client.list_webhooks()
    active_hooks = len([h for h in hooks['data'] if h['attributes']['state'] == 'active'])
    if active_hooks > 1:
        logger.warning('There should be 1 active hook per user. Please check this.')
    return active_hooks > 0


def connect(request):
    workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
    slack_msg_service = SlackMessageService(workspace.bot_token)
    try:
        su, created = SlackUser.objects.get_or_create(slack_id=request.POST['user_id'],
                                                      workspace=workspace)

        # atm, we support just one authtoken per user. Calling this command effectively overwrites
        token = request.POST['text'].split(' ')[1]
        calendly = Calendly(token)
        response_from_echo = calendly.echo()
        if 'email' not in response_from_echo:
            logger.info(f'User {su.slack_email} does not have paid account')
            slack_msg_service.send(su.slack_id,
                                   "Could not find user in Calendly. Make sure the token is correct.")
            return HttpResponse(status=200)

        # check if there's an existing working hook for this user
        if not has_active_hooks(calendly):
            # ask user where they want to send the hook
            su.calendly_authtoken = token
            su.calendly_email = response_from_echo['email']
            su.save()
            return init_handle_destination(slack_msg_service, su)

        else:
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            slack_msg_service.send(su.slack_id,
                                   "Your account is already setup to receive event notifications. "
                                   "Please contact support if you're experiencing issues.")
    except IndexError:
        logger.warning('Missing calendly key')
        slack_msg_service.send(su.slack_id,
                               "Looks like you forgot the Calendly token. Try typing `/duck help` if you're lost.")
    except Exception:
        logger.exception('Could not connect to calendly')
        slack_msg_service.send(request.POST['user_id'],
                               "Could not connect to Calendly. Try again or contact us for help.")
    return HttpResponse(status=200)


def init_handle_destination(slack_msg_service, su):
    msg = SlackMarkdownNotificationDestinationMessage()
    slack_msg_service.send(su.slack_id, 'Where do you want me to send event notifications?', msg.get_blocks())
    return HttpResponse(status=200)


def setup_handle_destination(response_url, su, channel=None):
    slack_msg_service = SlackMessageService(su.workspace.bot_token)
    try:
        calendly = Calendly(su.calendly_authtoken)
        if channel:
            signed_value = signing.dumps((su.workspace.slack_id, channel))
        else:
            signed_value = signing.dumps((su.workspace.slack_id, su.slack_id))
        response_from_webhook_create = calendly.create_webhook(
            f"{settings.SITE_URL}/handle/{signed_value}/")
        if 'id' not in response_from_webhook_create:
            msg = 'Please retry'
            errors = {}
            if 'message' in response_from_webhook_create:
                msg, errors = response_from_webhook_create['message'], response_from_webhook_create['errors']
            logger.error(f'Could not setup Calendly webhook. {msg} {errors}')
            slack_msg_service.update_interaction(
                response_url,
                text=f"Could not connect with Calendly API. {msg}.")
            return HttpResponse(status=200)
        Webhook.objects.create(user=su, calendly_id=response_from_webhook_create['id'])
        slack_msg_service.update_interaction(
            response_url,
            text="Setup complete. You will now receive notifications on created and canceled events!")
    except Exception:
        logger.exception('Could not connect to calendly')
        slack_msg_service.update_interaction(
            response_url,
            text="Could not connect to Calendly. Try again or contact us for help.")
    return HttpResponse(status=200)
