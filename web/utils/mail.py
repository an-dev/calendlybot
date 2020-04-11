import logging
from smtplib import SMTPServerDisconnected

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader

logger = logging.getLogger(__name__)


class SendEmail:
    def __init__(self, to_email):
        self.to_email = to_email

    def subject(self):
        return ""

    def run(self):
        body = loader.render_to_string('emails/welcome.txt')
        html = loader.render_to_string('emails/welcome.html')

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


@shared_task(autoretry_for=(ValueError, SMTPServerDisconnected))
def send_welcome_email(user_id):
    from web.core.models import SlackUser

    try:
        email = SlackUser.objects.get(slack_id=user_id).slack_email
        SendWelcomeEmail(email).run()
    except Exception:
        logger.exception("Could not send email")
