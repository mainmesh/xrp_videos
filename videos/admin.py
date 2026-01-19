from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import Tier, Category, Video, WatchHistory


class VideoAdminForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(required=False, min_value=0, label="Duration (minutes)")

    class Meta:
        model = Video
        fields = ["title", "url", "category", "min_tier", "reward", "duration_minutes", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize duration_minutes from duration_seconds
        if self.instance and getattr(self.instance, 'duration_seconds', None) is not None:
            self.fields['duration_minutes'].initial = int(self.instance.duration_seconds // 60)

    def clean_url(self):
        url = self.cleaned_data.get('url', '').strip()
        # If user pasted a YouTube watch URL, convert to embed URL
        try:
            if 'youtube.com/watch' in url and 'v=' in url:
                # extract v param
                import urllib.parse as _up
                parsed = _up.urlparse(url)
                qs = _up.parse_qs(parsed.query)
                vid = qs.get('v', [None])[0]
                if vid:
                    return f'https://www.youtube.com/embed/{vid}'
            if 'youtu.be/' in url:
                # youtu.be/VIDEO
                parts = url.split('/')
                vid = parts[-1]
                if vid:
                    # strip query params
                    vid = vid.split('?')[0]
                    return f'https://www.youtube.com/embed/{vid}'
        except Exception:
            pass
        # Attempt to set a YouTube embed URL and populate thumbnail when possible
        try:
            if 'youtube.com/watch' in url and 'v=' in url:
                import urllib.parse as _up
                parsed = _up.urlparse(url)
                qs = _up.parse_qs(parsed.query)
                vid = qs.get('v', [None])[0]
                if vid:
                    return f'https://www.youtube.com/embed/{vid}'
            if 'youtu.be/' in url:
                parts = url.split('/')
                vid = parts[-1]
                if vid:
                    vid = vid.split('?')[0]
                    return f'https://www.youtube.com/embed/{vid}'
        except Exception:
            pass
        return url

    def clean(self):
        cleaned = super().clean()
        minutes = cleaned.get('duration_minutes')
        if minutes is None:
            cleaned['duration_seconds'] = 0
        else:
            cleaned['duration_seconds'] = int(minutes) * 60
        return cleaned

    def save(self, commit=True):
        # Ensure duration_seconds is set on instance before saving
        inst = super().save(commit=False)
        minutes = self.cleaned_data.get('duration_minutes')
        inst.duration_seconds = int(minutes or 0) * 60
        # Auto-fill YouTube thumbnail if possible and thumbnail_url is empty
        try:
            if 'youtube.com/embed/' in inst.url and not inst.thumbnail_url:
                vid = inst.url.split('youtube.com/embed/')[-1].split('?')[0]
                inst.thumbnail_url = f'https://img.youtube.com/vi/{vid}/maxresdefault.jpg'
        except Exception:
            pass
        if commit:
            inst.save()
            self.save_m2m()
        return inst


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
    form = VideoAdminForm
    list_display = ("title", "category", "min_tier", "reward_display", "watch_count", "is_active_badge", "created_by")
    list_filter = ("category", "min_tier", "is_active", "created_by")
    search_fields = ("title", "url")
    readonly_fields = ("created_by",)
    ordering = ("title",)
    actions = ["activate_videos", "deactivate_videos"]
    
    fieldsets = (
        ("Video Information", {
            "fields": ("title", "url", "category")
        }),
        ("Earning Settings", {
            "fields": ("min_tier", "reward", "duration_minutes")
        }),
        ("Status", {
            "fields": ("is_active", "created_by")
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

    def save_model(self, request, obj, form, change):
        # Set created_by if not present
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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
