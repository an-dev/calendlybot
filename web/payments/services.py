import slack
import stripe
from django.conf import settings
from django.core import signing

from web.utils import eligible_user


class WorkspaceUpgradeService:
    stripe.api_key = settings.STRIPE_SECRET_KEY

    def __init__(self, workspace):
        self.client = slack.WebClient(token=workspace.bot_token)
        self.workspace = workspace

    def run(self):
        response_users_list = self.client.users_list()
        user_count = self.workspace.user_count

        if user_count <= 8:
            plan_id = settings.STRIPE_PLAN_ID_SM
        elif 8 < user_count <= 20:
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
