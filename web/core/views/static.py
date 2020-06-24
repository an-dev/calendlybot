import os

from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

client_id = os.environ["SLACK_CLIENT_ID"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]


@require_http_methods(["GET"])
def index(request):
    return render(request, 'web/index.html')


@require_http_methods(["GET"])
def install(request):
    return redirect(
        f"https://slack.com/oauth/v2/authorize?scope={oauth_scope}&client_id={client_id}")


@require_http_methods(["GET"])
def faq(request):
    return TemplateResponse(request, 'web/faq.html')


@require_http_methods(["GET"])
def privacy(request):
    return TemplateResponse(request, 'web/privacy.html')


@require_http_methods(["GET"])
def terms(request):
    return TemplateResponse(request, 'web/terms.html')


@require_http_methods(["GET"])
def pricing(request):
    return TemplateResponse(request, 'web/pricing.html')
