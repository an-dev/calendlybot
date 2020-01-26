from django.urls import path

from web.payments import views

urlpatterns = [
    # path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path('upgrade/', views.upgrade, name='upgrade'),
    path('session-create/', views.session_create, name='session-create'),
]
