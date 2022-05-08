import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone
from web.core.models import SlackUser
from web.payments.services import WorkspaceUpgradeService

logger = logging.getLogger(__name__)


class SendEmail:
    def __init__(self, to_email):
        self.to_email = to_email

    def subject(self):
        return ""

    def template_slug(self):
        return ""

    def run(self):
        body = loader.render_to_string(f'emails/{self.template_slug()}.txt')
        html = loader.render_to_string(f'emails/{self.template_slug()}.html')

        logger.info(f"Sending {self.template_slug()} email to {self.to_email}")

        return send_mail(
            subject=self.subject(),
            message=body,
            from_email=settings.FROM_EMAIL,
            recipient_list=[self.to_email],
            html_message=html,
        )


class SendUpgradeEmail(SendEmail):
    def run(self, workspace):
        checkout_session_id = WorkspaceUpgradeService(workspace).run()
        body = loader.render_to_string(f'emails/{self.template_slug()}.txt')
        html = loader.render_to_string(
            f'emails/{self.template_slug()}.html',
            context={'subscribe_link': f'{settings.SITE_URL}/subscribe/{checkout_session_id}/'})

        logger.info(f"Sending {self.template_slug()} email to {self.to_email}")

        return send_mail(
            subject=self.subject(),
            message=body,
            from_email=settings.FROM_EMAIL,
            recipient_list=[self.to_email],
            html_message=html,
        )


class SendWelcomeEmail(SendEmail):
    def subject(self):
        return "Welcome to Calenduck!"

    def template_slug(self):
        return "welcome"


class SendTrialEndEmail(SendUpgradeEmail):
    def subject(self):
        return "Calenduck trial ending soon!"

    def template_slug(self):
        return "trial-end"


class SendAbandonedUpgradeEmail(SendUpgradeEmail):
    def subject(self):
        return "Still thinking about it?"

    def template_slug(self):
        return "abandoned-upgrade"


def send_welcome_email(user_id):
    try:
        email = SlackUser.objects.get(slack_id=user_id).slack_email
        SendWelcomeEmail(email).run()
    except Exception:
        logger.exception("Could not send welcome email")


def send_trial_end_email():
    try:
        slack_users = SlackUser.objects \
            .filter(workspace__trial_end=timezone.now().date() + timedelta(days=3),
                    workspace__subscription__isnull=True)
        [SendTrialEndEmail(su.slack_email).run(su.workspace) for su in slack_users]
    except Exception:
        logger.exception("Could not send trial end email")


def send_abandoned_upgrade_email(user_id):
    try:
        su = SlackUser.objects.get(workspace__subscription__isnull=True, slack_id=user_id)
        SendAbandonedUpgradeEmail(su.slack_email).run(su.workspace)
    except Exception:
        logger.exception("Could not send upgrade abandoned email")
