from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('clubs/<slug:slug>/join/', views.request_membership, name='request_membership'),
    path('clubs/<slug:slug>/members/', views.member_list, name='member_list'),
    path('clubs/<slug:slug>/requests/', views.request_list, name='request_list'),
]
