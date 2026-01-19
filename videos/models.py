from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Tier(models.Model):
    name = models.CharField(max_length=50)
    price = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.name} (${self.price})"


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Video(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField()
    thumbnail_url = models.URLField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    reward = models.FloatField(default=0.1)
    categories = models.ManyToManyField(Category, blank=True, related_name='videos')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='primary_videos', help_text="Primary category (deprecated - use categories)")
    min_tier = models.ForeignKey(Tier, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Minimum tier required to access this video")
    duration_seconds = models.IntegerField(default=0, help_text="Approx. duration in seconds")
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    
    @property
    def duration(self):
        """Alias for duration_seconds for template compatibility."""
        return self.duration_seconds

    @property
    def duration_minutes(self):
        """Duration rounded down to whole minutes for admin/display convenience."""
        try:
            return int(self.duration_seconds // 60)
        except Exception:
            return 0

    def __str__(self):
        return self.title


class VideoTierPrice(models.Model):
    """Tier-specific pricing and access for videos."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='tier_prices')
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    reward = models.FloatField(default=0.0, help_text="Reward amount for this tier")
    
    class Meta:
        unique_together = ('video', 'tier')
    
    def __str__(self):
        return f"{self.video.title} - {self.tier.name}: ${self.reward}"


class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_seconds = models.IntegerField(default=0)
    watched_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.video.title} @ {self.watched_at}"
