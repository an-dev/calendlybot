import functools
import hashlib
import hmac
import logging
import os
import time

from django.core import signing
from django.http import HttpResponse
from django.utils import timezone
from slack.errors import SlackApiError
from web.core.messages import SlackMarkdownUpgradePromptMessage
from web.core.models import Workspace
from web.core.services import SlackMessageService
from web.utils import disable_webhook

slack_signing_secret = os.environ['SLACK_SIGNING_SECRET']

logger = logging.getLogger(__name__)


def verify_request(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            request_body = request.body
            timestamp = request.headers['X-Slack-Request-Timestamp']
            if abs(time.time() - float(timestamp)) > 60 * 5:
                # The request timestamp is more than five minutes from local time.
                # It could be a replay attack, so let's ignore it.
                raise ValueError('Request is older than five minutes from locale')

            sig_basestring = f"v0:{timestamp}:{request_body.decode('utf-8')}".encode('utf-8')

            my_signature = 'v0={}'.format(hmac.new(
                bytes(slack_signing_secret, 'utf-8'),
                sig_basestring,
                hashlib.sha256
            ).hexdigest())
            slack_signature = request.headers['X-Slack-Signature']
            if hmac.compare_digest(my_signature, slack_signature):
                return func(request, *args, **kwargs)
            else:
                raise ValueError('Signatures are different')
        except Exception:
            logger.exception("Could not verify request comes from slack")
            return HttpResponse(status=400)

    return wrapper


def requires_subscription(func):
    @functools.wraps(func)
    def wrapper(request, signed_value, *args, **kwargs):
        try:
            # if workspace does not have subscription
            # check if vaild trial
            workspace_slack_id, user_slack_id = signing.loads(signed_value)
            workspace = Workspace.objects.get(slack_id=workspace_slack_id)
            if timezone.now().date() > workspace.trial_end and not hasattr(workspace, 'subscription'):
                logger.info(f"User {user_slack_id} needs to upgrade")
                msg = SlackMarkdownUpgradePromptMessage()
                SlackMessageService(workspace.bot_token).send(
                    user_slack_id,
                    "Could not display event details",
                    msg.get_blocks()
                )
                return HttpResponse(status=200)
            else:
                return func(request, signed_value, *args, **kwargs)
        except Workspace.DoesNotExist:
            logger.exception(f"Workspace {workspace_slack_id} does not exist for user {user_slack_id}")
        except SlackApiError as sae:
            logger.warning(f"Slack error: {sae}")
            if sae.response['error'] == 'account_inactive':
                disable_webhook(user_slack_id)
        except Exception:
            logger.exception("Could not verify if view needs subscription")
        return HttpResponse(status=400)

    return wrapper
