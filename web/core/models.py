import logging
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from model_utils import Choices
from model_utils.models import TimeStampedModel

logger = logging.getLogger(__name__)


def set_trial_end():
    return timezone.now().date() + timedelta(days=settings.TRIAL_DAYS)


class Workspace(TimeStampedModel):
    slack_id = models.CharField(unique=True, max_length=16)
    bot_token = models.CharField(max_length=64)
    trial_end = models.DateField(default=set_trial_end)
    name = models.CharField(max_length=128, null=True, blank=True)
    user_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "{} ({})".format(self.name, self.slack_id)


class SlackUser(TimeStampedModel):
    slack_id = models.CharField(max_length=16)
    slack_name = models.CharField(max_length=64, blank=True, null=True)
    slack_email = models.EmailField(null=True)
    calendly_email = models.EmailField(unique=True, null=True, blank=True)
    calendly_authtoken = models.CharField(max_length=64, null=True, blank=True)
    workspace = models.ForeignKey('Workspace', related_name='slackusers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('slack_id', 'workspace')

    def __str__(self):
        return "{} ({})".format(self.slack_email, self.slack_id)


class Webhook(TimeStampedModel):
    user = models.ForeignKey('SlackUser', related_name='webhooks', null=True, on_delete=models.SET_NULL)
    calendly_id = models.PositiveIntegerField()
    destination_id = models.CharField(max_length=32, null=True, blank=True)

    def __str__(self):
        return "{}".format(self.calendly_id)


class Subscription(TimeStampedModel):

    PLANS = Choices(
        ("small", "Standard"),
        ("medium", "Business"),
        ("large", "Enterprise")
    )

    workspace = models.OneToOneField('Workspace', related_name='subscription', on_delete=models.CASCADE)
    plan = models.CharField(max_length=16, choices=PLANS)

    def __str__(self):
        return "{} plan for workspace {}".format(self.plan, self.workspace.slack_id)
