from django.db import models


class Workspace(models.Model):
    slack_id = models.CharField(max_length=16)
    bot_token = models.CharField(max_length=64)

    def __str__(self):
        return "Slack Workspace {}".format(self.slack_id)


class SlackUser(models.Model):
    slack_id = models.CharField(max_length=16, unique=True)
    slack_name = models.CharField(max_length=64, blank=True, null=True)
    calendly_email = models.EmailField(unique=True, null=True)
    calendly_authtoken = models.CharField(max_length=64, unique=True, null=True)
    workspace = models.ForeignKey('Workspace', related_name='slackusers', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('slack_id', 'workspace')

    def __str__(self):
        return "Slack User {}".format(self.slack_id)


class Webhook(models.Model):
    user = models.ForeignKey('SlackUser', related_name='webhooks', on_delete=models.CASCADE)
    calendly_id = models.PositiveIntegerField()

    def __str__(self):
        return "Calendly Hook {}".format(self.calendly_id)
