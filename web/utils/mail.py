import logging
from datetime import timedelta
from smtplib import SMTPServerDisconnected

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils import timezone

from web.core.models import Workspace, SlackUser

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


class SendWelcomeEmail(SendEmail):
    def subject(self):
        return "Welcome to Calenduck!"

    def template_slug(self):
        return "welcome"


class SendTrialEndEmail(SendEmail):
    def subject(self):
        return "Calenduck trial ending soon!"

    def template_slug(self):
        return "trial-end"


@shared_task(autoretry_for=(ValueError, SMTPServerDisconnected))
def send_welcome_email(user_id):
    from web.core.models import SlackUser

    try:
        email = SlackUser.objects.get(slack_id=user_id).slack_email
        SendWelcomeEmail(email).run()
    except Exception:
        logger.exception("Could not send welcome email")


def send_trial_end_email():
    try:
        emails = SlackUser.objects\
            .filter(workspace__trial_end=timezone.now().date() + timedelta(days=3))\
            .values_list('slack_email', flat=True)
        [SendTrialEndEmail(email).run() for email in emails]
    except Exception:
        logger.exception("Could not send trial email")
