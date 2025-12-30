from django.urls import path
from django.views.generic import TemplateView

app_name = 'clubs'

# Placeholder views - will be replaced in checkpoints 1.2-1.5
urlpatterns = [
    path('', TemplateView.as_view(template_name='clubs/club_list.html'), name='club_list'),
    path('new/', TemplateView.as_view(template_name='clubs/club_create.html'), name='club_create'),
]

