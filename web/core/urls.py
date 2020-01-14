from django.urls import path

from web.core import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('connect/', views.connect, name='connect'),
]
