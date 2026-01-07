"""clubify URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from clubs.views import ClubListView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', ClubListView.as_view(), name='home'),
    path('clubs/', include('clubs.urls')),
    path('', include('memberships.urls')),
    path('', include('posts.urls')),
]
