import slack
from calendly import Calendly

from web.core.messages import STATIC_START_MSG, STATIC_FREE_ACCT_MSG, STATIC_HELP_MSG, SlackHomeViewMessage
from web.core.models import Workspace, SlackUser, Webhook
from web.utils import has_calendly_hooks, remove_calendly_hooks, InvalidTokenError, has_active_hooks

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

            if not has_calendly_hooks(calendly):
                logger.warning(f'Deleting non existent webhooks for user {self.user_id}')
            else:
                if remove_calendly_hooks(calendly):
                    Webhook.objects.filter(user=su).delete()
                else:
                    logger.warning(f'Could not delete webhooks for user {self.user_id}. Do this manually!')
            su.calendly_authtoken = None
            su.calendly_email = None
            su.save()
            value = "Account successfully disconnected. Type `/duck start` to associate another Calendly account."
            return Result.from_success(value)
        except InvalidTokenError:
            logger.warning(f'User {self.user_id} does not have a valid token')
            return Result.from_success(STATIC_FREE_ACCT_MSG)
        except Exception:
            logger.exception('Could not disconnect account from calendly.')
            err = f"Could not disconnect account. {STATIC_HELP_MSG}"
        return Result.from_failure(err)


class ConnectService:
    def __init__(self, user_id, workspace, api_key):
        self.user_id = user_id
        self.workspace = workspace
        self.api_key = api_key

    def run(self):
        try:
            su, new_user = SlackUser.objects.get_or_create(slack_id=self.user_id, workspace=self.workspace)
            if new_user:
                logger.info(f'New user from existing workspace: {self.user_id}')
                client = slack.WebClient(token=self.workspace.bot_token)
                user_info = client.users_info(user=self.user_id)['user']['profile']
                su.slack_name = user_info.get('first_name', user_info['real_name'])
                su.slack_email = user_info['email']
                su.save()

            # atm, we support just one authtoken per user.
            # Calling this service on the same user effectively overwrites
            calendly = Calendly(self.api_key)
            response_from_echo = calendly.echo()

            if 'email' not in response_from_echo:
                logger.warning(f'Could not find user for api key {self.api_key}')
                return Result.from_failure("Could not find user in Calendly. Make sure the token is correct.")

            # check if there's an existing working hook for this user
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            if has_active_hooks(calendly):
                logger.error(f'Trying to setup apikey on already setup account for {self.user_id}')
                return Result.from_failure("Your account is already setup to receive event notifications.")

            su.calendly_authtoken = self.api_key
            su.calendly_email = response_from_echo['email']
            su.save()
            return Result.from_success()
        except InvalidTokenError:
            logger.warning(f'User {self.user_id} does not have paid account')
            msg = STATIC_FREE_ACCT_MSG
        except Exception:
            logger.exception('Could not connect to calendly')
            msg = f"Could not connect to Calendly. {STATIC_HELP_MSG}"
        return Result.from_failure(msg)


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
        workspace = Workspace.objects.get(slack_id=workspace_id)
        self.client = slack.WebClient(token=workspace.bot_token)

    def run(self, trigger_id, view, push=False):
        try:
            if push:
                self.client.views_push(trigger_id=trigger_id, view=view)
            else:
                self.client.views_open(trigger_id=trigger_id, view=view)
            return Result.from_success()
        except Exception:
            logger.exception('Could not update or create home view')
            return Result.from_failure('')
