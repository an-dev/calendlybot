import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def upgrade(request):
    return TemplateResponse(request, 'web/upgrade.html')


@csrf_exempt
@require_http_methods(["POST"])
def session_create(request):
    try:
        # Customer is only signing up for a subscription
        stripe.api_key = settings.STRIPE_SECRET_KEY
        checkout_session = stripe.checkout.Session.create(
            success_url=settings.SITE_URL + "/success/?session_id={CHECKOUT_SESSION_ID}/",
            cancel_url=f"{settings.SITE_URL}/cancel/",
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": settings.STRIPE_PLAN_ID}]},
        )
        return HttpResponse(json.dumps({'checkoutSessionId': checkout_session['id']}), status=200)
    except Exception:
        logger.exception('Could not create checkout session')
        return HttpResponse(
            json.dumps({'error': 'Could not create session for payment. Retry later or contact support'}), status=403)


@require_http_methods(["GET"])
def cancel(request):
    return TemplateResponse(request, 'web/upgrade.html')


@require_http_methods(["GET"])
def success(request):
    import pdb; pdb.set_trace()
    return TemplateResponse(request, 'web/upgrade.html')
