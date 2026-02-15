import random
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Light pastel colors for club cards (slightly darker for better visibility)
PASTEL_COLORS = [
    "#FFD4D4",  # Light Pink
    "#D4E5FF",  # Light Blue
    "#D4FFD4",  # Light Green
    "#FFE8D4",  # Light Orange
    "#E8D4FF",  # Light Purple
    "#D4FFFF",  # Light Cyan
    "#FFFFD4",  # Light Yellow
    "#FFD4E8",  # Light Magenta
    "#D4FFE8",  # Light Mint
    "#FFE5D4",  # Light Peach
    "#D4E8FF",  # Light Sky
]
PASTEL_COLOR_CHOICES = [(color, color) for color in PASTEL_COLORS]


class Club(models.Model):
    """
    Represents a club that users can create and join.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField()
    color = models.CharField(
        max_length=7, blank=True, help_text="Card background color (auto-generated)"
    )
    logo = models.FileField(upload_to="club_logos/", blank=True, null=True)
    banner = models.FileField(
        upload_to="club_banners/",
        blank=True,
        null=True,
        help_text="Optional banner image for the club",
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_clubs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Club.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1

        # Auto-generate random pastel color if not set
        if not self.color:
            self.color = random.choice(PASTEL_COLORS)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("clubs:club_detail", kwargs={"slug": self.slug})
