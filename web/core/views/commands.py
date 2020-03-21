from calendly import Calendly
from django.http import HttpResponse

from web.core.messages import SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage, \
    SlackMarkdownNotificationDestinationMessage, STATIC_HELP_MSG
from web.core.models import Workspace, SlackUser
from web.core.services import SlackMessageService
from web.payments.services import WorkspaceUpgradeService
import logging

from web.utils import has_active_hooks

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


def connect(request):
    user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
    workspace = Workspace.objects.get(slack_id=workspace_id)
    slack_msg_service = SlackMessageService(workspace.bot_token)
    try:
        su, created = SlackUser.objects.get_or_create(slack_id=user_id,
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
            su.calendly_authtoken = token
            su.calendly_email = response_from_echo['email']
            su.save()
            # ask user where they want to send the hook
            msg = SlackMarkdownNotificationDestinationMessage()
            slack_msg_service.send(su.slack_id, 'Where do you want me to send event notifications?', msg.get_blocks())
            return HttpResponse(status=200)
        else:
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            logger.error('Trying to setup Calendly token on already setup account', su.slack_id)
            slack_msg_service.send(su.slack_id,
                                   "Your account is already setup to receive event notifications. "
                                   "Please contact support if you're experiencing issues.")
    except IndexError:
        logger.warning('Missing calendly key')
        slack_msg_service.send(user_id,
                               f"Looks like you forgot the Calendly token. {STATIC_HELP_MSG}")
    except Exception:
        logger.exception('Could not connect to calendly')
        slack_msg_service.send(user_id,
                               f"Could not connect to Calendly. {STATIC_HELP_MSG}")
    return HttpResponse(status=200)
