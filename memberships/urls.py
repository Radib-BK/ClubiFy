from django.urls import path
from . import views

app_name = "memberships"

urlpatterns = [
    path(
        "clubs/<slug:slug>/join/", views.request_membership, name="request_membership"
    ),
    path("clubs/<slug:slug>/members/", views.member_list, name="member_list"),
    path("clubs/<slug:slug>/requests/", views.request_list, name="request_list"),
    path(
        "clubs/<slug:slug>/requests/<int:request_id>/approve/",
        views.approve_request,
        name="approve_request",
    ),
    path(
        "clubs/<slug:slug>/requests/<int:request_id>/reject/",
        views.reject_request,
        name="reject_request",
    ),
    path(
        "clubs/<slug:slug>/members/<int:membership_id>/promote/",
        views.promote_to_moderator,
        name="promote_to_moderator",
    ),
    path(
        "clubs/<slug:slug>/members/<int:membership_id>/demote/",
        views.demote_to_member,
        name="demote_to_member",
    ),
    path(
        "clubs/<slug:slug>/members/<int:membership_id>/remove/",
        views.remove_member,
        name="remove_member",
    ),
]
