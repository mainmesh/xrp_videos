from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import Tier, Category, Video, WatchHistory


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ("name", "price_display", "user_count")
    search_fields = ("name",)
    ordering = ("price",)
    
    def price_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #28a745;">${:.2f}</span>', obj.price)
    price_display.short_description = "Price"
    price_display.admin_order_field = "price"
    
    def user_count(self, obj):
        count = obj.profile_set.count()
        return format_html('<span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{} users</span>', count)
    user_count.short_description = "Active Users"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "video_count")
    search_fields = ("name",)
    
    def video_count(self, obj):
        count = obj.video_set.count()
        return format_html('<span style="background: #6f42c1; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{} videos</span>', count)
    video_count.short_description = "Videos"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "min_tier", "reward_display", "watch_count", "is_active_badge", "created_at")
    list_filter = ("category", "min_tier", "is_active", "created_at")
    search_fields = ("title", "description", "youtube_video_id")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["activate_videos", "deactivate_videos"]
    
    fieldsets = (
        ("Video Information", {
            "fields": ("title", "description", "youtube_video_id", "category")
        }),
        ("Earning Settings", {
            "fields": ("min_tier", "reward", "duration_seconds")
        }),
        ("Status", {
            "fields": ("is_active", "created_at")
        }),
    )
    
    def reward_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #28a745;">${:.4f}</span>', obj.reward)
    reward_display.short_description = "Reward"
    reward_display.admin_order_field = "reward"
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">✓ ACTIVE</span>')
        return format_html('<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">✗ INACTIVE</span>')
    is_active_badge.short_description = "Status"
    
    def watch_count(self, obj):
        count = obj.watchhistory_set.filter(verified=True).count()
        return format_html('<span style="background: #17a2b8; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{} views</span>', count)
    watch_count.short_description = "Verified Views"
    
    def activate_videos(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} video(s) activated.", level="success")
    activate_videos.short_description = "✓ Activate selected videos"
    
    def deactivate_videos(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} video(s) deactivated.", level="warning")
    deactivate_videos.short_description = "✗ Deactivate selected videos"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("category", "min_tier")


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "watched_seconds", "duration_display", "verified_badge", "watched_at")
    list_filter = ("verified", "watched_at", "video__category")
    search_fields = ("user__username", "user__email", "video__title")
    readonly_fields = ("watched_at",)
    date_hierarchy = "watched_at"
    ordering = ("-watched_at",)
    actions = ["verify_watches"]
    
    def duration_display(self, obj):
        percentage = (obj.watched_seconds / obj.video.duration_seconds * 100) if obj.video.duration_seconds > 0 else 0
        color = "#28a745" if percentage >= 80 else "#ffc107" if percentage >= 50 else "#dc3545"
        return format_html(
            '<div style="background: #e9ecef; border-radius: 10px; overflow: hidden; width: 100px;">'
            '<div style="background: {}; width: {:.0f}%; padding: 2px 5px; font-size: 10px; color: white; font-weight: bold; text-align: center;">{:.0f}%</div>'
            '</div>',
            color, percentage, percentage
        )
    duration_display.short_description = "Progress"
    
    def verified_badge(self, obj):
        if obj.verified:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">✓ VERIFIED</span>')
        return format_html('<span style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">⏳ PENDING</span>')
    verified_badge.short_description = "Status"
    
    def verify_watches(self, request, queryset):
        count = queryset.filter(verified=False).update(verified=True)
        self.message_user(request, f"{count} watch(es) verified.", level="success")
    verify_watches.short_description = "✓ Verify selected watches"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "video", "video__category")
