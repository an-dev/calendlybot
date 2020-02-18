from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('cp/', admin.site.urls),
    path('', include('web.core.urls')),
    path('subscribe/', include('web.payments.urls'), name='subscribe'),
]
