from django.http import HttpResponse

from web.core.messages import SlackMarkdownUpgradeLinkMessage, SlackMarkdownHelpMessage
from web.core.models import Workspace, SlackUser
from web.core.services import SlackMessageService, DisconnectService, ConnectService, UpdateHomeViewService
from web.payments.services import WorkspaceUpgradeService
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
    user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
    import pdb; pdb.set_trace()
    result = ConnectService(user_id, workspace_id, None).run()
    if result.success:
        msg = result.value
    else:
        msg = result.error
    workspace = Workspace.objects.get(slack_id=workspace_id)
    SlackMessageService(workspace.bot_token).send(user_id, msg)
    return HttpResponse(status=200)


def disconnect(request):
    user_id, workspace_id = request.POST['user_id'], request.POST['team_id']
    logger.info(f'User {user_id} is trying to disconnect from Calendly')
    result = DisconnectService(user_id, workspace_id).run()
    if result.success:
        UpdateHomeViewService(user_id, workspace_id).run()
        msg = result.value
    else:
        msg = result.error
    workspace = Workspace.objects.get(slack_id=workspace_id)
    SlackMessageService(workspace.bot_token).send(user_id, msg)
    return HttpResponse(status=200)
