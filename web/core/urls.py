from django.urls import path, re_path

from web.core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('install/', views.install, name='install'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('auth/', views.auth, name='auth'),
    path('commands/', views.commands, name='commands'),
    path('interactions/', views.interactions, name='interactions'),
    path('destinations/', views.get_destinations, name='destinations'),
    re_path(r'^handle/(?P<signed_value>[-:\w]+)/$', views.handle, name='handle'),
]

core_map_paths = ('index', 'faq', 'privacy')
