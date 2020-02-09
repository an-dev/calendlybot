from django.urls import path, re_path

from web.core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('auth/', views.auth, name='auth'),
    path('connect/', views.connect, name='connect'),
    path('upgrade/', views.upgrade, name='upgrade'),
    path('help/', views.support, name='support'),
    re_path(r'^handle/(?P<signed_value>[-:\w]+)/$', views.handle, name='handle'),
]
