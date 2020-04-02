import slack
from calendly import Calendly
from django.http import HttpResponse

from web.core.messages import SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage, \
    SlackMarkdownNotificationDestinationMessage, STATIC_HELP_MSG, STATIC_START_MSG, STATIC_FREE_ACCT_MSG
from web.core.models import Workspace, SlackUser, Webhook
from web.core.services import SlackMessageService
from web.payments.services import WorkspaceUpgradeService
import logging

from web.utils import has_active_hooks, remove_hooks, has_hooks
from web.utils.errors import InvalidTokenError

logger = logging.getLogger(__name__)


def upgrade(request):
    try:
        user_id = request.POST['user_id']
        logger.info(f'User {user_id} is trying to upgrade')
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su = SlackUser.objects.get(slack_id=user_id, workspace=workspace)

        checkout_session_id = WorkspaceUpgradeService(workspace).run()

        msg = SlackMarkdownUpgradeLinkMessage(checkout_session_id)
        SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                      "Thanks for giving Calenduck a try!",
                                                      msg.get_blocks())
    except Workspace.DoesNotExist:
        logger.exception(f'Missing workspace: {request.POST}')
    except Exception:
        logger.exception('Could not upgrade to paid plan')
    return HttpResponse(status=200)


def help(request):
    try:
        user_id = request.POST['user_id']
        logger.info(f'User {user_id} is looking for help')
        workspace = Workspace.objects.get(slack_id=request.POST['team_id'])
        su = SlackUser.objects.get(slack_id=user_id, workspace=workspace)

        msg = SlackMarkdownHelpMessage()
        SlackMessageService(workspace.bot_token).send(su.slack_id,
                                                      "Here are some useful tips!",
                                                      msg.get_blocks(),
                                                      msg.get_attachments())
    except Workspace.DoesNotExist:
        logger.exception(f'Missing workspace: {request.POST}')
    except Exception:
        logger.exception('Could not deliver help command')
    return HttpResponse(status=200)


def connect(request):
    try:
        user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
        logger.info(f'User {user_id} is trying to connect to Calendly')
        workspace = Workspace.objects.get(slack_id=workspace_id)
        slack_msg_service = SlackMessageService(workspace.bot_token)
        su, new_user = SlackUser.objects.get_or_create(slack_id=user_id, workspace=workspace)
        if new_user:
            logger.info(f'User {user_id} is new!')
            client = slack.WebClient(token=workspace.bot_token)
            user_info = client.users_info(user=user_id)
            su.slack_name = user_info['user']['profile'].get('first_name', user_info['user']['profile']['real_name'])
            su.slack_email = user_info['user']['profile']['email']
            su.save()

        # atm, we support just one authtoken per user. Calling this command effectively overwrites
        token = request.POST['text'].split(' ')[1]
        logger.info(f'User {user_id} is using token {token}')
        calendly = Calendly(token)
        response_from_echo = calendly.echo()

        if 'email' not in response_from_echo:
            logger.info(f'User {user_id} does not have paid account')
            slack_msg_service.send(su.slack_id,
                                   "Could not find user in Calendly. Make sure the token is correct.")
            return HttpResponse(status=200)

        if has_active_hooks(calendly):
            # check if there's an existing working hook for this user
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            logger.error(f'Trying to setup Calendly token on already setup account: {user_id}')
            slack_msg_service.send(su.slack_id,
                                   "Your account is already setup to receive event notifications.\n"
                                   "Type `/duck disconnect` for a fresh install"
                                   " or contact support if you're experiencing issues.")
            return HttpResponse(status=200)

        su.calendly_authtoken = token
        su.calendly_email = response_from_echo['email']
        su.save()
        # ask user where they want to send the hook
        msg = SlackMarkdownNotificationDestinationMessage()
        slack_msg_service.send(su.slack_id, 'Where do you want me to send event notifications?', msg.get_blocks(),
                               msg.get_attachments())
    except IndexError:
        logger.warning('Missing calendly key')
        slack_msg_service.send(user_id,
                               f"Looks like you forgot to add a Calendly token. {STATIC_HELP_MSG}")
    except InvalidTokenError:
        logger.warning('User is not using pro or premium account')
        slack_msg_service.send(user_id, STATIC_FREE_ACCT_MSG)
    except Workspace.DoesNotExist:
        logger.exception(f'Missing workspace: {request.POST}')
    except Exception:
        logger.exception('Could not connect to calendly')
        slack_msg_service.send(user_id,
                               f"Could not connect to Calendly. {STATIC_HELP_MSG}")
    return HttpResponse(status=200)


def disconnect(request):
    try:
        user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
        logger.info(f'User {user_id} is trying to disconnect from Calendly')
        workspace = Workspace.objects.get(slack_id=workspace_id)
        slack_msg_service = SlackMessageService(workspace.bot_token)
        # check if active webtokens are present
        # delete them
        # delete the webhook object as well
        su = SlackUser.objects.get(slack_id=user_id)
        calendly = Calendly(su.calendly_authtoken)
        if has_hooks(calendly) and remove_hooks(calendly):
            Webhook.objects.filter(user=su).delete()
            su.calendly_authtoken = None
            su.save()
            slack_msg_service.send(user_id,
                                   "Account successfully disconnected.\n"
                                   "Type `/duck connect [calendly token]` to associate another Calendly account.")
        else:
            logger.warning(f'Trying to delete non existent webhooks for user {user_id}')
            slack_msg_service.send(user_id,
                                   f"Doesn't seem like this account is connected. {STATIC_START_MSG}")

        if Webhook.objects.filter(user__slack_id=user_id).exists():
            Webhook.objects.filter(user__slack_id=user_id).first().delete()
    except InvalidTokenError:
        logger.warning('User does not have a valid token')
        slack_msg_service.send(user_id, STATIC_FREE_ACCT_MSG)
    except Workspace.DoesNotExist:
        logger.exception(f'Missing workspace: {request.POST}')
    except Exception:
        logger.exception('Could not disconnect account from calendly.')
        slack_msg_service.send(user_id,
                               f"Could not disconnect account. {STATIC_HELP_MSG}")
    return HttpResponse(status=200)
