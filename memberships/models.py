from django.db import models
from django.contrib.auth.models import User
from clubs.models import Club


class RoleChoices(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    MODERATOR = 'moderator', 'Moderator'
    MEMBER = 'member', 'Member'


class RequestStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class Membership(models.Model):
    """
    Represents a user's membership in a club with a specific role.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'club']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.club.name} ({self.role})"

    @property
    def is_admin(self):
        return self.role == RoleChoices.ADMIN

    @property
    def is_moderator(self):
        return self.role in [RoleChoices.ADMIN, RoleChoices.MODERATOR]


class MembershipRequest(models.Model):
    """
    Represents a pending request to join a club.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='membership_requests'
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='membership_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests'
    )

    class Meta:
        # Allow multiple requests over time (user can re-request after rejection)
        # Note: unique_together removed to allow re-requests after rejection
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.user.username} -> {self.club.name} ({self.status})"

    @property
    def is_pending(self):
        return self.status == RequestStatus.PENDING

