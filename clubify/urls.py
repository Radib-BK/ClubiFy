"""clubify URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', RedirectView.as_view(url='/clubs/', permanent=False), name='home'),
    path('clubs/', include('clubs.urls')),
    path('', include('memberships.urls')),
    path('', include('posts.urls')),
]
