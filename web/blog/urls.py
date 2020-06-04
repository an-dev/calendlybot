from web.blog import views
from django.urls import path

urlpatterns = [
    path('', views.PostListView, name='blog'),
    path('<slug:slug>/', views.PostDetailView, name='blog_post'),
]
