from django.db import models
from django.utils.text import slugify
# from django.contrib.auth.models import User
from django.conf import settings


class Artwork(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),                   # Artist saved but not submitted
        ("submitted", "Submitted for Review"),# Artist sent to admin
        ("approved", "Approved"),             # Admin accepted — visible in marketplace
        ("rejected", "Rejected"),             # Admin denied listing
        ("sold", "Sold"),                     # Buyer purchased
        ("archived", "Archived"),             # Removed from display
    ]

    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='artworks')

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    
    category = models.CharField(max_length=100, blank=True, null=True)  # e.g., Painting, Drawing, Sculpture
    medium = models.CharField(max_length=100, blank=True, null=True)    # e.g., Oil, Acrylic, Digital
    
    width_cm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    depth_cm = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    creation_year = models.PositiveIntegerField(blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)

    main_image = models.ImageField(upload_to="artworks/images/")
    additional_images = models.JSONField(blank=True, null=True)  # store image URLs from media storage
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    admin_comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.artist.id}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.artist.username}"
