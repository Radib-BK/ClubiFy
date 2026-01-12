from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.ClubListView.as_view(), name='club_list'),
    path('new/', views.ClubCreateView.as_view(), name='club_create'),
    path('<slug:slug>/edit/', views.ClubUpdateView.as_view(), name='club_edit'),
    path('<slug:slug>/', views.ClubDetailView.as_view(), name='club_detail'),
]
