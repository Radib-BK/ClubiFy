from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_type', 'club', 'author', 'is_published', 'created_at')
    list_filter = ('post_type', 'is_published', 'created_at', 'club')
    search_fields = ('title', 'body', 'author__username', 'club__name')
    raw_id_fields = ('club', 'author')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'body', 'post_type')
        }),
        ('Association', {
            'fields': ('club', 'author')
        }),
        ('Status', {
            'fields': ('is_published',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

