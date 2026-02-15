from django.db import models
from django.contrib.auth.models import User
from clubs.models import Club


class PostType(models.TextChoices):
    BLOG = "blog", "Blog"
    NEWS = "news", "News"


class Post(models.Model):
    """
    Represents a blog post or news article within a club.
    - Blog: Any member can create
    - News: Only moderators and admins can create
    """

    title = models.CharField(max_length=200)
    body = models.TextField()
    post_type = models.CharField(
        max_length=10, choices=PostType.choices, default=PostType.BLOG
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    is_published = models.BooleanField(default=True)
    summary = models.TextField(
        blank=True, null=True, help_text="AI-generated summary of the post"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_post_type_display()}] {self.title}"

    @property
    def is_news(self):
        return self.post_type == PostType.NEWS

    @property
    def is_blog(self):
        return self.post_type == PostType.BLOG

    @property
    def like_count(self):
        """Returns the total number of likes on this post."""
        return self.likes.count()

    @property
    def comment_count(self):
        """Returns the total number of comments on this post."""
        return self.comments.count()

    def is_liked_by(self, user):
        """Check if a specific user has liked this post."""
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class Like(models.Model):
    """
    Represents a like on a post.
    Each user can only like a post once.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"


class Comment(models.Model):
    """
    Represents a comment on a post.
    No nested comments - flat structure only.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} on {self.post.title}: {self.body[:50]}..."


class Bookmark(models.Model):
    """
    Represents a bookmark on a post.
    Each user can only bookmark a post once.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="post_bookmarks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["post", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.title}"
