from django.core.management.base import BaseCommand
from web.utils import mail


class Command(BaseCommand):

    def handle(self, *args, **options):
        mail.send_trial_end_email.delay()
