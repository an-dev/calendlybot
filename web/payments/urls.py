from django.urls import path, re_path

from web.payments import views

urlpatterns = [
    path('cancel/', views.cancel, name='subscribe-cancel'),
    path('success/', views.success, name='subscribe-success'),
    re_path(r'^(?P<signed_session_id>[-:\w]+)/$', views.subscribe, name='subscribe-home'),
]
