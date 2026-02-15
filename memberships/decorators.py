"""
View decorators for role-based access control.
Use these to protect views that require specific club roles.
"""

from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from clubs.models import Club
from .helpers import is_club_member, is_club_moderator, is_club_admin


def club_member_required(view_func):
    """
    Decorator that requires the user to be a member of the club.
    Expects 'slug' in URL kwargs.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, slug, *args, **kwargs):
        club = get_object_or_404(Club, slug=slug)

        if not is_club_member(request.user, club):
            messages.error(
                request, "You must be a member of this club to access this page."
            )
            return redirect("clubs:club_detail", slug=slug)

        return view_func(request, slug, *args, **kwargs)

    return wrapper


def club_moderator_required(view_func):
    """
    Decorator that requires the user to be a moderator or admin of the club.
    Expects 'slug' in URL kwargs.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, slug, *args, **kwargs):
        club = get_object_or_404(Club, slug=slug)

        if not is_club_moderator(request.user, club):
            messages.error(
                request, "You must be a moderator or admin to access this page."
            )
            return redirect("clubs:club_detail", slug=slug)

        return view_func(request, slug, *args, **kwargs)

    return wrapper


def club_admin_required(view_func):
    """
    Decorator that requires the user to be an admin of the club.
    Expects 'slug' in URL kwargs.
    """

    @wraps(view_func)
    @login_required
    def wrapper(request, slug, *args, **kwargs):
        club = get_object_or_404(Club, slug=slug)

        if not is_club_admin(request.user, club):
            messages.error(request, "You must be an admin to access this page.")
            return redirect("clubs:club_detail", slug=slug)

        return view_func(request, slug, *args, **kwargs)

    return wrapper
