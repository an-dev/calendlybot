from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.core.urls')),
    path('upgrade/', include('web.payments.urls'), name='upgrade'),
]
