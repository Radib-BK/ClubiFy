from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from clubs.models import Club
from .models import Membership, MembershipRequest, RoleChoices, RequestStatus
from .helpers import get_membership
from .decorators import club_member_required, club_admin_required


@login_required
def request_membership(request, slug):
    """Handle membership request for a club."""
    club = get_object_or_404(Club, slug=slug)
    user = request.user

    # Check if already a member
    if Membership.objects.filter(user=user, club=club).exists():
        messages.info(request, f"You are already a member of {club.name}.")
        return redirect("clubs:club_detail", slug=slug)

    # Check if there's already a PENDING request (only block pending, not rejected)
    pending_request = MembershipRequest.objects.filter(
        user=user, club=club, status=RequestStatus.PENDING
    ).first()

    if pending_request:
        messages.info(request, f"Your request to join {club.name} is already pending.")
        return redirect("clubs:club_detail", slug=slug)

    # Create new membership request (allows re-requesting after rejection)
    MembershipRequest.objects.create(user=user, club=club)
    messages.success(request, f"Your request to join {club.name} has been submitted!")

    return redirect("clubs:club_detail", slug=slug)


@club_member_required
def member_list(request, slug):
    """Display list of club members - only visible to members."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_membership(request.user, club)
    members = (
        Membership.objects.filter(club=club)
        .select_related("user")
        .order_by("role", "-joined_at")
    )

    return render(
        request,
        "memberships/member_list.html",
        {
            "club": club,
            "members": members,
            "membership": membership,
            "is_admin": membership and membership.is_admin,
        },
    )


@club_admin_required
def request_list(request, slug):
    """Display pending membership requests - only visible to admin."""
    club = get_object_or_404(Club, slug=slug)

    pending_requests = (
        MembershipRequest.objects.filter(club=club, status=RequestStatus.PENDING)
        .select_related("user")
        .order_by("-requested_at")
    )

    return render(
        request,
        "memberships/request_list.html",
        {
            "club": club,
            "pending_requests": pending_requests,
        },
    )


@club_admin_required
def approve_request(request, slug, request_id):
    """Approve a membership request - admin only."""
    club = get_object_or_404(Club, slug=slug)

    membership_request = get_object_or_404(
        MembershipRequest, id=request_id, club=club, status=RequestStatus.PENDING
    )

    # Update request status
    membership_request.status = RequestStatus.APPROVED
    membership_request.reviewed_at = timezone.now()
    membership_request.reviewed_by = request.user
    membership_request.save()

    # Create membership
    Membership.objects.create(
        user=membership_request.user, club=club, role=RoleChoices.MEMBER
    )

    messages.success(
        request, f"{membership_request.user.username} has been approved as a member!"
    )
    return redirect("memberships:request_list", slug=slug)


@club_admin_required
def reject_request(request, slug, request_id):
    """Reject a membership request - admin only."""
    club = get_object_or_404(Club, slug=slug)

    membership_request = get_object_or_404(
        MembershipRequest, id=request_id, club=club, status=RequestStatus.PENDING
    )

    # Update request status
    membership_request.status = RequestStatus.REJECTED
    membership_request.reviewed_at = timezone.now()
    membership_request.reviewed_by = request.user
    membership_request.save()

    messages.info(
        request, f"{membership_request.user.username}'s request has been rejected."
    )
    return redirect("memberships:request_list", slug=slug)


@club_admin_required
def promote_to_moderator(request, slug, membership_id):
    """Promote a member to moderator - admin only."""
    club = get_object_or_404(Club, slug=slug)

    membership = get_object_or_404(Membership, id=membership_id, club=club)

    # Can't promote yourself or another admin
    if membership.role == RoleChoices.ADMIN:
        messages.error(request, "Cannot change admin role.")
        return redirect("memberships:member_list", slug=slug)

    if membership.role == RoleChoices.MODERATOR:
        messages.info(request, f"{membership.user.username} is already a moderator.")
        return redirect("memberships:member_list", slug=slug)

    membership.role = RoleChoices.MODERATOR
    membership.save()

    messages.success(
        request, f"{membership.user.username} has been promoted to Moderator!"
    )
    return redirect("memberships:member_list", slug=slug)


@club_admin_required
def demote_to_member(request, slug, membership_id):
    """Demote a moderator back to member - admin only."""
    club = get_object_or_404(Club, slug=slug)

    membership = get_object_or_404(Membership, id=membership_id, club=club)

    # Can't demote an admin
    if membership.role == RoleChoices.ADMIN:
        messages.error(request, "Cannot demote an admin.")
        return redirect("memberships:member_list", slug=slug)

    if membership.role == RoleChoices.MEMBER:
        messages.info(request, f"{membership.user.username} is already a member.")
        return redirect("memberships:member_list", slug=slug)

    membership.role = RoleChoices.MEMBER
    membership.save()

    messages.success(request, f"{membership.user.username} has been demoted to Member.")
    return redirect("memberships:member_list", slug=slug)


@club_admin_required
def remove_member(request, slug, membership_id):
    """Remove a member from the club - admin only."""
    club = get_object_or_404(Club, slug=slug)

    membership = get_object_or_404(Membership, id=membership_id, club=club)

    # Can't remove yourself
    if membership.user == request.user:
        messages.error(request, "You cannot remove yourself from the club.")
        return redirect("memberships:member_list", slug=slug)

    # Can't remove other admins (must have at least one admin)
    if membership.role == RoleChoices.ADMIN:
        messages.error(
            request, "Cannot remove an admin. Promote another member to admin first."
        )
        return redirect("memberships:member_list", slug=slug)

    username = membership.user.username
    membership.delete()

    messages.success(request, f"{username} has been removed from the club.")
    return redirect("memberships:member_list", slug=slug)
