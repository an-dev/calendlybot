import slack
import stripe
from django.conf import settings
from django.core import signing


class WorkspaceUpgradeService:
    stripe.api_key = settings.STRIPE_SECRET_KEY

    def __init__(self, workspace):
        self.client = slack.WebClient(token=workspace.bot_token)
        self.workspace = workspace

    def run(self):
        user_count = self.workspace.slackusers.count()

        if user_count <= 5:
            plan_id = settings.STRIPE_PLAN_ID_MD
        else:
            plan_id = settings.STRIPE_PLAN_ID_LG

        checkout_session = stripe.checkout.Session.create(
            success_url=settings.SITE_URL + "/subscribe/success/?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=f"{settings.SITE_URL}/subscribe/cancel/",
            payment_method_types=["card"],
            subscription_data={"items": [{"plan": plan_id}]},
            client_reference_id=self.workspace.id,
            billing_address_collection='auto',
        )
        return signing.dumps(checkout_session['id'], settings.CALENDLY_BOT_SUBSCRIBE_HASH)
