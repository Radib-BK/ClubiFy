"""
Role and permission helper functions for ClubiFy.
Use these to check user permissions in views and templates.
"""
from .models import Membership, MembershipRequest, RoleChoices, RequestStatus


def get_membership(user, club):
    """
    Get user's membership in a club.
    Returns None if user is not a member or not authenticated.
    """
    if not user.is_authenticated:
        return None
    return Membership.objects.filter(user=user, club=club).first()


def is_club_member(user, club):
    """Check if user is a member of the club (any role)."""
    return get_membership(user, club) is not None


def is_club_moderator(user, club):
    """Check if user is a moderator or admin of the club."""
    membership = get_membership(user, club)
    return membership and membership.role in [RoleChoices.ADMIN, RoleChoices.MODERATOR]


def is_club_admin(user, club):
    """Check if user is an admin of the club."""
    membership = get_membership(user, club)
    return membership and membership.role == RoleChoices.ADMIN


def get_user_role(user, club):
    """
    Get user's role in a club.
    Returns role string or None if not a member.
    """
    membership = get_membership(user, club)
    return membership.role if membership else None


def has_pending_request(user, club):
    """Check if user has a pending membership request."""
    if not user.is_authenticated:
        return False
    return MembershipRequest.objects.filter(
        user=user,
        club=club,
        status=RequestStatus.PENDING
    ).exists()


def can_create_post(user, club, post_type='blog'):
    """
    Check if user can create a specific type of post.
    - blog: any member
    - news: moderator or admin only
    """
    membership = get_membership(user, club)
    if not membership:
        return False
    
    if post_type == 'news':
        return membership.role in [RoleChoices.ADMIN, RoleChoices.MODERATOR]
    
    return True  # Any member can create blog posts

