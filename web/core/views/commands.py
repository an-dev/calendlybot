from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone

from web.core.messages import SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage, SlackHomeMessage
from web.core.models import Workspace, SlackUser
from web.core.services import SlackMessageService
from web.payments.services import WorkspaceUpgradeService
from web.payments.views import check_abandoned_upgrade
import logging


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
        # get workspace id + current timestamp
        # if user doesn't upgrade in 1/2 days
        # send email
        tomorrow = timezone.now() + timedelta(days=1)
        check_abandoned_upgrade.apply_async((user_id, workspace.slack_id), eta=tomorrow)
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


def duck(request):
    user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
    workspace = Workspace.objects.get(slack_id=workspace_id)
    logger.info(f'User {user_id} is interacting with main command')
    slack_msg_service = SlackMessageService(workspace.bot_token)
    su, new_user = SlackUser.objects.get_or_create(slack_id=user_id, workspace=workspace)
    if new_user:
        logger.info(f'New user from existing workspace: {user_id}')
        user_info = slack_msg_service.client.users_info(user=user_id)['user']['profile']
        su.slack_name = user_info.get('first_name', user_info['real_name'])
        su.slack_email = user_info['email']
        su.save()

    msg = SlackHomeMessage(su)
    slack_msg_service.send(user_id, "Hello Andy! Manage Calenduck's settings and notification preferences below",
                           msg.get_blocks())
    return HttpResponse(status=200)


# def reset(request):
#     user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
#     logger.info(f'User {user_id} is trying to disconnect from Calendly')
#     result = DisconnectUserService(user_id, workspace_id).run()
#     if result.success:
#         UpdateHomeViewService(user_id, workspace_id).run()
#         msg = result.value
#     else:
#         msg = result.error
#     workspace = Workspace.objects.get(slack_id=workspace_id)
#     SlackMessageService(workspace.bot_token).send(user_id, msg)
#     return HttpResponse(status=200)
