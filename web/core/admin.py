# Register your models here.
from django.contrib import admin

from web.core.models import SlackUser, Subscription, Workspace, Webhook, Filter


class SubscriptionInline(admin.StackedInline):
    model = Subscription


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = (SubscriptionInline,)
    fields = ('name', 'slack_id', 'bot_token', 'user_count', 'trial_end', 'created', 'modified')
    readonly_fields = ('slack_id', 'bot_token', 'user_count', 'created', 'modified')

    list_display = ('name', 'slack_id', 'trial_end', 'subscription', 'user_count', 'created')


class WebhooksInline(admin.StackedInline):
    extra = 2
    model = Webhook


class FiltersInline(admin.StackedInline):
    model = Filter
    extra = 2


class SlackUserAdmin(admin.ModelAdmin):
    inlines = (WebhooksInline, FiltersInline)
    fields = (
        'slack_id', 'slack_name', 'slack_email', 'calendly_email', 'calendly_authtoken', 'created',
        'modified', 'workspace')
    readonly_fields = ('slack_id', 'slack_name', 'slack_email', 'created', 'modified')
    raw_id_fields = ('workspace',)
    list_display = ('slack_email', 'slack_id', 'calendly_authtoken', 'workspace', 'created')


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(SlackUser, SlackUserAdmin)
