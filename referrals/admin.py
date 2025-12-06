from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import ReferralLink, ReferralBonus


@admin.register(ReferralLink)
class ReferralLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "code_display", "usage_count", "total_earnings")
    search_fields = ("user__username", "user__email", "code")
    readonly_fields = ("code",)
    ordering = ("-user__profile__referrals_count",)
    
    def code_display(self, obj):
        return format_html(
            '<code style="background: #f8f9fa; padding: 4px 8px; border: 1px solid #dee2e6; border-radius: 4px; font-family: monospace; font-weight: bold;">{}</code>',
            obj.code
        )
    code_display.short_description = "Referral Code"
    code_display.admin_order_field = "code"
    
    def usage_count(self, obj):
        count = obj.user.profile.referrals_count
        color = "#28a745" if count >= 10 else "#ffc107" if count >= 5 else "#6c757d"
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">{} referrals</span>',
            color, count
        )
    usage_count.short_description = "Total Referrals"
    
    def total_earnings(self, obj):
        total = ReferralBonus.objects.filter(from_user=obj.user).aggregate(total=models.Sum('amount'))['total'] or 0
        return format_html('<span style="font-weight: bold; color: #28a745;">${:.2f}</span>', total)
    total_earnings.short_description = "Total Earnings"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "user__profile")


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "amount_display", "created_at")
    list_filter = ("created_at",)
    search_fields = ("from_user__username", "to_user__username", "from_user__email", "to_user__email")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #28a745;">${:.2f}</span>', obj.amount)
    amount_display.short_description = "Bonus Amount"
    amount_display.admin_order_field = "amount"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("from_user", "to_user")


# Add missing import for models
from django.db import models
