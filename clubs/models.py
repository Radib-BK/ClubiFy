import random
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Light pastel colors for club cards
PASTEL_COLORS = [
    '#FFE5E5',  # Light Pink
    '#E5F0FF',  # Light Blue
    '#E5FFE5',  # Light Green
    '#FFF5E5',  # Light Orange
    '#F5E5FF',  # Light Purple
    '#E5FFFF',  # Light Cyan
    '#FFFFE5',  # Light Yellow
    '#FFE5F5',  # Light Magenta
    '#E5FFF0',  # Light Mint
    '#FFF0E5',  # Light Peach
    '#E5F5FF',  # Light Sky
]
PASTEL_COLOR_CHOICES = [(color, color) for color in PASTEL_COLORS]


class Club(models.Model):
    """
    Represents a club that users can create and join.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField()
    color = models.CharField(max_length=7, blank=True, help_text="Card background color (auto-generated)")
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_clubs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

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
        return reverse('clubs:club_detail', kwargs={'slug': self.slug})

