# Register your models here.
from django.contrib import admin

from web.core.models import SlackUser, Subscription, Workspace, Webhook


class SubscriptionInline(admin.StackedInline):
    model = Subscription


def tot_users(obj):
    return obj.slackusers.count()


tot_users.short_description = 'Total users'


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = (SubscriptionInline,)
    fields = ('name', 'slack_id', 'bot_token', 'trial_end', 'created', 'modified')
    readonly_fields = ('name', 'slack_id', 'bot_token', 'created', 'modified')

    list_display = ('name', 'slack_id', 'trial_end', 'subscription', tot_users, 'created')


class WebhooksInline(admin.StackedInline):
    extra = 2
    model = Webhook


class SlackUserAdmin(admin.ModelAdmin):
    inlines = (WebhooksInline,)
    fields = (
        'slack_id', 'slack_name', 'slack_email', 'manager', 'calendly_email', 'calendly_authtoken', 'created',
        'modified', 'workspace')
    readonly_fields = ('slack_id', 'slack_name', 'slack_email', 'created', 'modified')
    raw_id_fields = ('workspace',)
    list_display = ('slack_email', 'calendly_authtoken', 'workspace', 'manager', 'created')


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(SlackUser, SlackUserAdmin)
