import slack
from calendly import Calendly

from web.core.messages import STATIC_START_MSG, STATIC_FREE_ACCT_MSG, STATIC_HELP_MSG, SlackHomeViewMessage
from web.core.models import Workspace, SlackUser, Webhook
from web.utils import has_hooks, remove_hooks, InvalidTokenError

from logging import getLogger

from web.utils.results import Result

logger = getLogger(__name__)


class SlackMessageService:
    def __init__(self, token):
        self.client = slack.WebClient(token=token)

    def send(self, channel, text, blocks=None, attachments=None):
        kwargs = {'channel': channel, 'text': text}
        if blocks:
            kwargs['blocks'] = blocks
        if attachments:
            kwargs['attachments'] = attachments
        return self.client.chat_postMessage(**kwargs)

    def update_interaction(self, response_url, text=None, blocks=None):
        kwargs = {"delete_original": True, "response_type": "in_channel"}
        if blocks:
            kwargs['blocks'] = blocks
        if text:
            kwargs['text'] = text
        return self.client.api_call(response_url, json=kwargs)


class DisconnectService:
    def __init__(self, user_id, workspace_id):
        self.user_id = user_id
        self.workspace_id = workspace_id

    def run(self):
        # check if active webtokens are present
        # delete them
        # delete the webhook object as well
        try:
            su = SlackUser.objects.get(slack_id=self.user_id, workspace__slack_id=self.workspace_id)
            calendly = Calendly(su.calendly_authtoken)
            if has_hooks(calendly) and remove_hooks(calendly):
                su.calendly_authtoken = None
                su.save()
                value = "Account successfully disconnected.\n" \
                        "Type `/duck connect your-calendly-token` to associate another Calendly account."
                Webhook.objects.filter(user=su).delete()
                return Result.from_success(value)
            else:
                logger.warning(f'Trying to delete non existent webhooks for user {self.user_id}')
                err = f"Doesn't seem like this account is connected. {STATIC_START_MSG}"
                return Result.from_failure(err)
        except InvalidTokenError:
            logger.warning(f'User {self.user_id} does not have a valid token')
            err = STATIC_FREE_ACCT_MSG
        except Exception:
            logger.exception('Could not disconnect account from calendly.')
            err = f"Could not disconnect account. {STATIC_HELP_MSG}"
        return Result.from_failure(err)


class UpdateHomeViewService:
    def __init__(self, user_id, workspace_id):
        self.user_id = user_id
        self.workspace_id = workspace_id

    def run(self):
        try:
            workspace = Workspace.objects.get(slack_id=self.workspace_id)
            su = SlackUser.objects.get(slack_id=self.user_id, workspace=workspace)
            client = slack.WebClient(token=workspace.bot_token)
            client.views_publish(user_id=self.user_id, view=SlackHomeViewMessage(su).get_view())
            return Result.from_success()
        except Exception:
            logger.exception('Could not update or create home view')
            return Result.from_failure('')


class OpenModalService:
    def __init__(self, workspace_id):
        self.workspace_id = workspace_id

    def run(self, trigger_id, blocks):
        try:
            workspace = Workspace.objects.get(slack_id=self.workspace_id)
            client = slack.WebClient(token=workspace.bot_token)
            client.views_open(trigger_id=trigger_id, view=blocks)
            return Result.from_success()
        except Exception:
            logger.exception('Could not update or create home view')
            return Result.from_failure('')
