from django.urls import path

from web.core import views

urlpatterns = [
    path('auth/$', views.auth, name='auth'),
    path('post-auth/$', views.post_auth, name='post-auth'),
]
