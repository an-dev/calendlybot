import slack
from calendly import Calendly
from celery import shared_task
from django.conf import settings
from django.core import signing

from web.core.messages import STATIC_FREE_ACCT_MSG, STATIC_HELP_MSG, SlackHomeViewMessage, SlackHomeMessage
from web.core.models import Workspace, SlackUser, Webhook, Filter
from web.utils import remove_calendly_hooks, InvalidTokenError, count_active_hooks

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


class ConnectUserService:
    def run(self):
        try:
            # atm, we support just one authtoken per user.
            # Calling this service on the same user effectively overwrites
            calendly = Calendly(self.api_key)
            # check if there's an existing working hook for this user
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            active_hooks = count_active_hooks(calendly)
            if active_hooks > 1:
                logger.error(f'Trying to setup apikey on already setup account for {self.user_id}')
                return Result.from_failure("Your account is already setup to receive event notifications.")
            # elif active_hooks == 0:
            #     logger.warning(f'User {self.user_id} does not have a paid account')
            #     return Result.from_failure("Calenduck works only with Calendly Premium and Pro accounts.")
            else:
                su = SlackUser.objects.get(slack_id=self.user_id, workspace__slack_id=self.workspace_id)
                su.calendly_authtoken = self.api_key
                su.save()
                return Result.from_success()
        except InvalidTokenError:
            logger.warning(f'User {self.user_id} does not have a valid account')
            msg = STATIC_FREE_ACCT_MSG
        except Exception:
            logger.exception('Could not connect to calendly')
            msg = f"Could not connect to Calendly. {STATIC_HELP_MSG}"
        return Result.from_failure(msg)


class UpdateHomeMessageService:
    def __init__(self, user_id, workspace_id):
        self.user_id = user_id
        self.workspace_id = workspace_id

    def run(self, response_url):
        try:
            workspace = Workspace.objects.get(slack_id=self.workspace_id)
            su = SlackUser.objects.get(slack_id=self.user_id, workspace=workspace)
            SlackMessageService(workspace.bot_token).update_interaction(response_url, 'Calenduck settings updated.',
                                                                        SlackHomeMessage(su).get_blocks())
        except Exception:
            logger.exception('Could not update onboarding msg')
            return Result.from_failure('')


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


class DeleteWebhookService:
    def __init__(self, user_id):
        self.user_id = user_id

    def run(self):
        try:
            user = SlackUser.objects.get(slack_id=self.user_id)
            calendly = Calendly(user.calendly_authtoken)

            if count_active_hooks(calendly) > 0:
                if remove_calendly_hooks(calendly):
                    Webhook.objects.get(user=user).delete()
                else:
                    logger.warning(f'Could not delete webhooks for user {self.user_id}. Do this manually!')
            else:
                logger.info(f'No Webhook to delete')
            return Result.from_success()
        except Exception:
            msg = 'Could not delete Webhook'
            logger.exception(msg)
            return Result.from_failure(msg)


@shared_task(autoretry_for=(Exception,))
def delete_webhook(user_id):
    DeleteWebhookService(user_id).run()


class CreateWebhookService:
    def __init__(self, workspace_id, user_id, api_key):
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.api_key = api_key

    def run(self):
        try:
            delete_webhook.delay(self.user_id)
            # atm, we support just one authtoken per user.
            # Calling this service on the same user effectively overwrites
            calendly = Calendly(self.api_key)
            # check if there's an existing working hook for this user
            # this effectively means that if someone uses another's apiKey
            # if all its hooks are active they won't be able to setup
            active_hooks = count_active_hooks(calendly)
            if active_hooks > 1:
                logger.error(f'Trying to setup apikey on already setup account for {self.user_id}')
                result = Result.from_failure("Your account is already setup to receive event notifications.")
            # elif active_hooks == 0:
            #     logger.warning(f'User {self.user_id} does not have a paid account')
            #     return Result.from_failure("Calenduck works only with Calendly Premium and Pro accounts.")
            else:
                signed_value = signing.dumps((self.workspace_id, self.user_id))

                webhook_create_response = calendly.create_webhook(
                    f"{settings.SITE_URL}/handle/{signed_value}/")

                if 'id' not in webhook_create_response:
                    errors = ''
                    if 'message' in webhook_create_response:
                        errors = webhook_create_response.get('errors', webhook_create_response.get('message'))
                    logger.error(f'Could not setup Calendly webhook. {errors}')

                    if errors:
                        errors_detail = errors
                    else:
                        errors_detail = STATIC_HELP_MSG
                    result = Result.from_failure(f"Could not connect with Calendly API. {errors_detail}")
                else:
                    su = SlackUser.objects.get(slack_id=self.user_id, workspace__slack_id=self.workspace_id)
                    Webhook.objects.create(user=su, calendly_id=webhook_create_response['id'])
                    su.calendly_authtoken = self.api_key
                    su.save()

                    result = Result.from_success(
                        "Setup complete. You will now receive notifications on created and canceled events!")
        except InvalidTokenError:
            logger.warning(f'User {self.user_id} does not have a valid token')
            result = Result.from_failure("Calenduck works only with Calendly Premium and Pro accounts.")
        except Exception:
            logger.exception('Could not connect to calendly')
            result = Result.from_failure(f"Could not connect to Calendly. {STATIC_HELP_MSG}")
        return result


class DisconnectUserService:
    def __init__(self, user_id, workspace_id):
        self.user_id = user_id
        self.workspace_id = workspace_id

    def run(self):
        # check if active webtokens are present
        # delete them
        # delete the webhook object as well
        try:
            delete_webhook.delay(self.user_id)
            su = SlackUser.objects.get(slack_id=self.user_id, workspace__slack_id=self.workspace_id)
            su.calendly_authtoken = None
            su.calendly_email = None
            su.save()
            su.filters.all().delete()
            value = "Account successfully disconnected. Type `/duck start` to associate another Calendly account."
            return Result.from_success(value)
        except Exception:
            logger.exception('Could not disconnect account from calendly.')
            err = f"Could not disconnect account. {STATIC_HELP_MSG}"
        return Result.from_failure(err)


class CreateFiltersService:
    def __init__(self, user_id):
        self.user_id = user_id

    def run(self, selected_events):
        try:
            su = SlackUser.objects.get(slack_id=self.user_id)
            qs_filter = Filter.objects.filter(user=su)
            qs_filter.exclude(event_id__in=selected_events).delete()
            all_user_hooks = qs_filter.values_list('event_id', flat=True)

            for event_id in selected_events:
                if event_id not in all_user_hooks:
                    Filter.objects.create(event_id=event_id, user=su, destination_id=self.user_id)
            return Result.from_success()
        except Exception:
            logger.exception('Could not setup filters')
            return Result.from_failure('')


class SetDestinationService:
    def __init__(self, workspace_id):
        workspace = Workspace.objects.get(slack_id=workspace_id)
        self.client = slack.WebClient(token=workspace.bot_token)

    def run(self, user_id, event_id, destination_id):
        try:
            su = SlackUser.objects.get(slack_id=user_id)

            ffilter, _ = Filter.objects.get_or_create(user=su, event_id=event_id)
            ffilter.destination_id = destination_id
            ffilter.save()
            msg = "Setup complete. You will now receive notifications on created and canceled events!"
            if destination_id.startswith('C'):
                self.client.conversations_join(channel=destination_id)
            result = Result.from_success(msg)
        except Exception:
            logger.exception('Could not connect to calendly')
            result = Result.from_failure(f"Could not connect to Calendly. {STATIC_HELP_MSG}")
        return result
