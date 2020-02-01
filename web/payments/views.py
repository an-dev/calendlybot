import logging

import stripe
from django.conf import settings
from django.core import signing
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from web.core.models import Subscription

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def subscribe(request, signed_session_id):
    session_id = signing.loads(signed_session_id, settings.CALENDLY_BOT_SUBSCRIBE_HASH)
    return TemplateResponse(request,
                            'web/subscribe.html',
                            context={'stripeCheckoutId': session_id,
                                     'stripePublishableKey': settings.STRIPE_PUBLIC_KEY})


@require_http_methods(["GET"])
def cancel(request):
    return TemplateResponse(request, 'web/cancel.html')


def switch_plan(plan_id):
    if plan_id == settings.STRIPE_PLAN_ID_SM:
        plan_label = Subscription.PLANS.small
    elif plan_id == settings.STRIPE_PLAN_ID_MD:
        plan_label = Subscription.PLANS.medium
    elif plan_id == settings.STRIPE_PLAN_ID_LG:
        plan_label = Subscription.PLANS.large
    else:
        plan_label = None
    return plan_label


@require_http_methods(["GET"])
def success(request):
    context = {}
    try:
        if 'session_id' in request.GET:
            session_id = request.GET['session_id']
            stripe.api_key = settings.STRIPE_SECRET_KEY
            data = stripe.checkout.Session.retrieve(session_id)
            workspace_id = data.client_reference_id
            if Subscription.objects.filter(workspace_id=workspace_id).exists():
                raise ValueError(f'Workspace {workspace_id} already has subsctiption.')

            Subscription.objects.create(workspace_id=workspace_id,
                                        plan=switch_plan(data.display_items[0].plan.id))
    except ValueError:
        context = {
            'msg': "Looks like you've already paid for Calenduck. Go ahead and use our product in your slack workspace!"}
    except Exception:
        logger.exception('Could not create subscription')

    return TemplateResponse(request, 'web/success.html', context)
