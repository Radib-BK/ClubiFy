"""
Mixins for class-based views requiring club role checks.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from clubs.models import Club
from .helpers import is_club_member, is_club_moderator, is_club_admin, get_membership


class ClubMixin:
    """Base mixin that provides club and membership context."""

    def get_club(self):
        """Get the club from URL slug."""
        if not hasattr(self, "_club"):
            self._club = get_object_or_404(Club, slug=self.kwargs.get("slug"))
        return self._club

    def get_membership(self):
        """Get current user's membership in the club."""
        if not hasattr(self, "_membership"):
            self._membership = get_membership(self.request.user, self.get_club())
        return self._membership

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["club"] = self.get_club()
        context["membership"] = self.get_membership()
        return context


class ClubMemberRequiredMixin(LoginRequiredMixin, ClubMixin):
    """Mixin that requires the user to be a club member."""

    def dispatch(self, request, *args, **kwargs):
        # First check login
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Then check membership
        if not is_club_member(request.user, self.get_club()):
            messages.error(request, "You must be a member of this club.")
            return redirect("clubs:club_detail", slug=self.kwargs.get("slug"))

        return super().dispatch(request, *args, **kwargs)


class ClubModeratorRequiredMixin(LoginRequiredMixin, ClubMixin):
    """Mixin that requires the user to be a club moderator or admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not is_club_moderator(request.user, self.get_club()):
            messages.error(request, "You must be a moderator or admin.")
            return redirect("clubs:club_detail", slug=self.kwargs.get("slug"))

        return super().dispatch(request, *args, **kwargs)


class ClubAdminRequiredMixin(LoginRequiredMixin, ClubMixin):
    """Mixin that requires the user to be a club admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not is_club_admin(request.user, self.get_club()):
            messages.error(request, "You must be an admin.")
            return redirect("clubs:club_detail", slug=self.kwargs.get("slug"))

        return super().dispatch(request, *args, **kwargs)
