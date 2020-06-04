from web.blog import views
from django.urls import path

urlpatterns = [
    path('', views.PostListView, name='home'),
    path('<slug:slug>/', views.PostDetailView, name='post_detail'),
]
