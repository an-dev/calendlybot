import hashlib
import hmac
import logging
import os
import time
import functools

from django.http import HttpResponse

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
