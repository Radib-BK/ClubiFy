from django.contrib import admin
from django.utils.html import format_html
from .models import Club


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "color_preview", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description", "created_by__username")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "color_preview_large")

    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        (
            "Appearance",
            {
                "fields": ("color", "color_preview_large", "logo"),
            },
        ),
        (
            "Metadata",
            {"fields": ("created_by", "created_at"), "classes": ("collapse",)},
        ),
    )

    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; border: 1px solid #ccc;"></div>',
                obj.color,
            )
        return "-"

    color_preview.short_description = "Color"

    def color_preview_large(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 100px; height: 50px; background-color: {}; border-radius: 8px; border: 1px solid #ccc;"></div>',
                obj.color,
            )
        return "-"

    color_preview_large.short_description = "Color Preview"
