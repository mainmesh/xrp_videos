from django.db import models
from django.contrib.auth.models import User


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
    reward = models.FloatField(default=0.1)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    min_tier = models.ForeignKey(Tier, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Minimum tier required to access this video")
    duration_seconds = models.IntegerField(default=0, help_text="Approx. duration in seconds")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_seconds = models.IntegerField(default=0)
    watched_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.video.title} @ {self.watched_at}"
