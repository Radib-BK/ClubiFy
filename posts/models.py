from django.db import models
from django.contrib.auth.models import User
from clubs.models import Club


class PostType(models.TextChoices):
    BLOG = 'blog', 'Blog'
    NEWS = 'news', 'News'


class Post(models.Model):
    """
    Represents a blog post or news article within a club.
    - Blog: Any member can create
    - News: Only moderators and admins can create
    """
    title = models.CharField(max_length=200)
    body = models.TextField()
    post_type = models.CharField(
        max_length=10,
        choices=PostType.choices,
        default=PostType.BLOG
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    is_published = models.BooleanField(default=True)
    summary = models.TextField(blank=True, null=True, help_text='AI-generated summary of the post')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_post_type_display()}] {self.title}"

    @property
    def is_news(self):
        return self.post_type == PostType.NEWS

    @property
    def is_blog(self):
        return self.post_type == PostType.BLOG

