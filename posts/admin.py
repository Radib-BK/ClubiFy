from django.contrib import admin
from .models import Post, Like, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'post_type', 'club', 'author', 'is_published', 'like_count', 'comment_count', 'created_at')
    list_filter = ('post_type', 'is_published', 'created_at', 'club')
    search_fields = ('title', 'body', 'author__username', 'club__name')
    raw_id_fields = ('club', 'author')
    readonly_fields = ('created_at', 'updated_at', 'like_count', 'comment_count')
    
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
        ('Engagement', {
            'fields': ('like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title')
    raw_id_fields = ('user', 'post')
    readonly_fields = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'body_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__title', 'body')
    raw_id_fields = ('user', 'post')
    readonly_fields = ('created_at', 'updated_at')
    
    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Comment'

