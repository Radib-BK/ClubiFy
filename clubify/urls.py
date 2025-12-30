"""clubify URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    # Temporary: redirect home to clubs list (will be replaced in checkpoint 1.4)
    path('', RedirectView.as_view(url='/clubs/', permanent=False), name='home'),
    # Placeholder for clubs - will be implemented in checkpoint 1.2-1.5
    path('clubs/', include('clubs.urls')),
]
