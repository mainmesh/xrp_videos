from django.contrib import admin
from .models import Tier, Category, Video, WatchHistory


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ("name", "price")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "min_tier", "reward", "is_active")
    list_filter = ("category", "min_tier", "is_active")


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "watched_seconds", "verified", "watched_at")
