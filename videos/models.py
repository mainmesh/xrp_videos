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
    # Optional uploaded file stored in MEDIA_ROOT (prefer this for admin uploads)
    file = models.FileField(upload_to='videos/uploads/', blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, default='')
    countries = models.CharField(max_length=200, blank=True, default='', help_text="Comma-separated ISO country codes where this video is available. Blank = global")
    description = models.TextField(blank=True, default='')
    reward = models.FloatField(default=0.1)
    # Atomic reward model: per-video $ amount. Falls back to legacy `reward` (float)
    # when this is zero so existing rows continue to work without data migration.
    reward_amount = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Reward credited on completion. Falls back to `reward` if 0.",
    )
    categories = models.ManyToManyField(Category, blank=True, related_name='videos')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='primary_videos', help_text="Primary category (deprecated - use categories)")
    min_tier = models.ForeignKey(Tier, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Minimum tier required to access this video")
    duration_seconds = models.IntegerField(default=30, help_text="Watch duration in seconds required to earn the reward.")
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def effective_reward(self) -> float:
        """Resolve the per-completion reward. Uses `reward_amount` if set,
        otherwise the float `reward` field for backward compatibility."""
        try:
            if self.reward_amount and self.reward_amount > 0:
                return float(self.reward_amount)
        except Exception:
            pass
        return float(self.reward or 0)
    
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

    def countries_list(self):
        if not self.countries:
            return []
        return [c.strip().upper() for c in self.countries.split(',') if c.strip()]

    def matches_country(self, country_code: str | None) -> bool:
        """Return True if the video is available for the given country code (ISO), or globally when countries is blank."""
        if not self.countries:
            return True
        if not country_code:
            return False
        return country_code.strip().upper() in self.countries_list()

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


class WatchHeartbeat(models.Model):
    """Periodic heartbeat records from the client while watching a video."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Heartbeat {self.user.username} {self.video.title} @ {self.seconds}s"


class VideoWatch(models.Model):
    """One watch-session per (user, video, client). Acts as the authoritative
    idempotency record used by `videos.complete_watch` to ensure each video is
    credited at most once per session. The `client_id` is generated by the
    browser tab on `start` so a user opening multiple tabs cannot earn twice.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_watches')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watches')
    client_id = models.CharField(max_length=64, help_text="Per-tab UUID from the client.")
    started_at = models.DateTimeField(default=timezone.now)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    credited = models.BooleanField(default=False)
    credited_at = models.DateTimeField(null=True, blank=True)
    amount_credited = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'video'], name='videos_videowatch_unique_user_video'),
        ]
        indexes = [
            models.Index(fields=['user', 'credited']),
            models.Index(fields=['video', 'credited']),
        ]

    def elapsed_seconds(self) -> int:
        from django.utils import timezone as tz
        end = self.credited_at or self.last_heartbeat_at or tz.now()
        return int((end - self.started_at).total_seconds())

    def __str__(self):
        state = 'credited' if self.credited else 'pending'
        return f"VideoWatch({self.user.username} - {self.video.title}) [{state}]"


class WatchCompletionAttempt(models.Model):
    """Append-only audit trail for completion attempts. Records every POST to
    the complete endpoint (successful or rejected) so we can spot fraud and
    debug support tickets without polluting the VideoWatch table."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completion_attempts')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='completion_attempts')
    client_id = models.CharField(max_length=64)
    elapsed_seconds = models.IntegerField(default=0)
    accepted = models.BooleanField(default=False)
    reason = models.CharField(max_length=64, default='', help_text="e.g. credited, duplicate, too_soon, no_session")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['video', 'accepted']),
        ]

    def __str__(self):
        flag = 'OK' if self.accepted else 'X'
        return f"CompletionAttempt({flag} {self.user.username} - {self.video.title})"
