from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('clubs/<slug:slug>/posts/new/', views.create_post, name='create_post'),
]

