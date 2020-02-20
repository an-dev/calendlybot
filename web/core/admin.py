# Register your models here.
from django.contrib import admin

from web.core.models import SlackUser, Subscription, Workspace, Webhook


class SubscriptionInline(admin.StackedInline):
    model = Subscription


class WorkspaceAdmin(admin.ModelAdmin):
    inlines = (SubscriptionInline,)


class WebhooksInline(admin.StackedInline):
    extra = 2
    model = Webhook


class SlackUserAdmin(admin.ModelAdmin):
    inlines = (WebhooksInline,)
    readonly_fields = ('workspace',)


admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(SlackUser, SlackUserAdmin)
