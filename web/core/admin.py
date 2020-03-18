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

    list_display = ('slack_id', 'trial_end', 'subscription', tot_users)


class WebhooksInline(admin.StackedInline):
    extra = 2
    model = Webhook


class SlackUserAdmin(admin.ModelAdmin):
    inlines = (WebhooksInline,)
    readonly_fields = ('workspace',)

    list_display = ('slack_email', 'calendly_authtoken', 'workspace', 'is_installer')


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(SlackUser, SlackUserAdmin)
