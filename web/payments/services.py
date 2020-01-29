import stripe
from django.conf import settings


class StripeSessionService:
    def __init__(self):
        self.stripe = settings.STRIPE_SECRET_KEY

    def create(self, workspace_id):

        checkout_session = self.stripe.checkout.Session.create(
            success_url=settings.SITE_URL + "/upgrade/success/?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=f"{settings.SITE_URL}/upgrade/cancel/",
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": plan_id}]},
        )
        return self.client.chat_postMessage(**kwargs)
