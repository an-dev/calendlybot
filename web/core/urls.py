from django.urls import path, re_path

from web.core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('connect/', views.connect, name='connect'),
    re_path(r'^handle/(?P<signed_value>[-:\w]+)/$', views.handle, name='handle'),
]
