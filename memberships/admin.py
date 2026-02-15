from django.contrib import admin
from .models import Membership, MembershipRequest


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "role", "joined_at")
    list_filter = ("role", "joined_at", "club")
    search_fields = ("user__username", "club__name")
    raw_id_fields = ("user", "club")


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "status", "requested_at", "reviewed_by")
    list_filter = ("status", "requested_at", "club")
    search_fields = ("user__username", "club__name")
    raw_id_fields = ("user", "club", "reviewed_by")
    readonly_fields = ("requested_at",)
