from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def upgrade(request):
    return TemplateResponse(request, 'web/upgrade.html')


@require_http_methods(["POST"])
def session_create(request):
    try:
        # Customer is only signing up for a subscription
        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url +
            "/success.html?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "/cancel.html",
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": plan_id}]},
        )
        return jsonify({'checkoutSessionId': checkout_session['id']})
    except Exception as e:
        return jsonify(error=str(e)), 403


    return TemplateResponse(request, 'web/upgrade.html', )


@require_http_methods(["GET"])
def upgrade(request):
    return TemplateResponse(request, 'web/upgrade.html')