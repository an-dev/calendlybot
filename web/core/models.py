from django.contrib.auth.models import AbstractUser
from django.db import models

# workspace
#     bot_token
#
# user
#     slack_id
#     slack_email
#     calendly_email
#     workspace
#
# webhooks
#     slack_user
#     authtoken
#     calendly_hook_id


class Workspace(models.Model):
    slack_id = models.CharField(max_length=16)
    bot_token = models.CharField(max_length=64)


class User(AbstractUser):
    slack_id = models.CharField(max_length=16, unique=True)
    slack_email = models.EmailField(blank=True, null=True)
    calendly_email = models.EmailField(unique=True, null=True)
    workspace = models.ForeignKey('Workspace', related_name='workspaces', on_delete=models.CASCADE)
