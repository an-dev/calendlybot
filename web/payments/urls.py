from django.urls import path

from web.payments import views

urlpatterns = [
    path('', views.upgrade, name='home'),
    path('session-create/', views.session_create, name='session-create'),
    path('cancel/', views.cancel, name='cancel'),
    path('success/', views.success, name='success'),
]
