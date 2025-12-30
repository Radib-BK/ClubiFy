from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from clubs.models import Club
from .models import Membership, MembershipRequest, RoleChoices, RequestStatus


def get_user_membership(user, club):
    """Helper to get user's membership in a club."""
    if not user.is_authenticated:
        return None
    return Membership.objects.filter(user=user, club=club).first()


def is_club_admin(user, club):
    """Check if user is admin of the club."""
    membership = get_user_membership(user, club)
    return membership and membership.is_admin


@login_required
def request_membership(request, slug):
    """Handle membership request for a club."""
    club = get_object_or_404(Club, slug=slug)
    user = request.user

    # Check if already a member
    if Membership.objects.filter(user=user, club=club).exists():
        messages.info(request, f'You are already a member of {club.name}.')
        return redirect('clubs:club_detail', slug=slug)

    # Check if request already exists
    existing_request = MembershipRequest.objects.filter(user=user, club=club).first()
    
    if existing_request:
        if existing_request.status == RequestStatus.PENDING:
            messages.info(request, f'Your request to join {club.name} is already pending.')
        elif existing_request.status == RequestStatus.REJECTED:
            messages.warning(request, f'Your previous request to join {club.name} was rejected.')
        return redirect('clubs:club_detail', slug=slug)

    # Create new membership request
    MembershipRequest.objects.create(user=user, club=club)
    messages.success(request, f'Your request to join {club.name} has been submitted!')
    
    return redirect('clubs:club_detail', slug=slug)


@login_required
def member_list(request, slug):
    """Display list of club members - only visible to members."""
    club = get_object_or_404(Club, slug=slug)
    membership = get_user_membership(request.user, club)
    
    if not membership:
        messages.error(request, 'You must be a member to view the member list.')
        return redirect('clubs:club_detail', slug=slug)
    
    members = Membership.objects.filter(club=club).select_related('user').order_by('role', '-joined_at')
    
    return render(request, 'memberships/member_list.html', {
        'club': club,
        'members': members,
        'membership': membership,
    })


@login_required
def request_list(request, slug):
    """Display pending membership requests - only visible to admin."""
    club = get_object_or_404(Club, slug=slug)
    
    if not is_club_admin(request.user, club):
        messages.error(request, 'Only club admins can view membership requests.')
        return redirect('clubs:club_detail', slug=slug)
    
    pending_requests = MembershipRequest.objects.filter(
        club=club, 
        status=RequestStatus.PENDING
    ).select_related('user').order_by('-requested_at')
    
    return render(request, 'memberships/request_list.html', {
        'club': club,
        'pending_requests': pending_requests,
    })


@login_required
def approve_request(request, slug, request_id):
    """Approve a membership request - admin only."""
    club = get_object_or_404(Club, slug=slug)
    
    if not is_club_admin(request.user, club):
        messages.error(request, 'Only club admins can approve requests.')
        return redirect('clubs:club_detail', slug=slug)
    
    membership_request = get_object_or_404(
        MembershipRequest, 
        id=request_id, 
        club=club, 
        status=RequestStatus.PENDING
    )
    
    # Update request status
    membership_request.status = RequestStatus.APPROVED
    membership_request.reviewed_at = timezone.now()
    membership_request.reviewed_by = request.user
    membership_request.save()
    
    # Create membership
    Membership.objects.create(
        user=membership_request.user,
        club=club,
        role=RoleChoices.MEMBER
    )
    
    messages.success(request, f'{membership_request.user.username} has been approved as a member!')
    return redirect('memberships:request_list', slug=slug)


@login_required
def reject_request(request, slug, request_id):
    """Reject a membership request - admin only."""
    club = get_object_or_404(Club, slug=slug)
    
    if not is_club_admin(request.user, club):
        messages.error(request, 'Only club admins can reject requests.')
        return redirect('clubs:club_detail', slug=slug)
    
    membership_request = get_object_or_404(
        MembershipRequest, 
        id=request_id, 
        club=club, 
        status=RequestStatus.PENDING
    )
    
    # Update request status
    membership_request.status = RequestStatus.REJECTED
    membership_request.reviewed_at = timezone.now()
    membership_request.reviewed_by = request.user
    membership_request.save()
    
    messages.info(request, f'{membership_request.user.username}\'s request has been rejected.')
    return redirect('memberships:request_list', slug=slug)

