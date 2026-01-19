from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('clubs/<slug:slug>/posts/new/', views.create_post, name='create_post'),
    path('clubs/<slug:slug>/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('clubs/<slug:slug>/posts/<int:post_id>/summarize/', views.summarize_post, name='summarize_post'),
    path('clubs/<slug:slug>/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('clubs/<slug:slug>/posts/<int:post_id>/like/', views.toggle_like, name='toggle_like'),
    path('clubs/<slug:slug>/posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('clubs/<slug:slug>/posts/<int:post_id>/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('clubs/<slug:slug>/news/', views.news_list, name='news_list'),
    path('clubs/<slug:slug>/blogs/', views.blog_list, name='blog_list'),
]
