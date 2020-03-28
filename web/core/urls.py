from django.urls import path, re_path

from web.core.views import base, static, handlers

urlpatterns = [
    path('', static.index, name='index'),
    path('install/', static.install, name='install'),
    path('faq/', static.faq, name='faq'),
    path('privacy/', static.privacy, name='privacy'),
    path('auth/', base.auth, name='auth'),
    path('commands/', handlers.commands, name='commands'),
    path('interactions/', base.interactions, name='interactions'),
    re_path(r'^handle/(?P<signed_value>[-:\w]+)/$', handlers.handle, name='handle'),
]

core_map_paths = ('index', 'faq', 'privacy')
