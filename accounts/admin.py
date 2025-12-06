from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Profile, Deposit, WithdrawalRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "balance_display", "referred_by", "referrals_count", "current_tier", "member_since")
    list_filter = ("current_tier",)
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("balance", "referrals_count")
    ordering = ("-balance",)
    
    def balance_display(self, obj):
        color = "green" if obj.balance > 0 else "gray"
        return format_html('<span style="color: {}; font-weight: bold;">${:.2f}</span>', color, obj.balance)
    balance_display.short_description = "Balance"
    balance_display.admin_order_field = "balance"
    
    def member_since(self, obj):
        return obj.user.date_joined.strftime("%b %d, %Y")
    member_since.short_description = "Member Since"
    member_since.admin_order_field = "user__date_joined"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "referred_by", "current_tier")


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_display", "created_at", "success_badge", "stripe_payment_intent")
    list_filter = ("success", "created_at")
    search_fields = ("user__username", "user__email", "stripe_payment_intent")
    readonly_fields = ("created_at", "stripe_payment_intent")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold;">${:.2f}</span>', obj.amount)
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"
    
    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">✓ SUCCESS</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">✗ FAILED</span>')
    success_badge.short_description = "Status"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user")


@admin.register(WithdrawalRequest)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_display", "status_badge", "created_at", "approved_by", "approved_at")
    list_filter = ("status", "created_at", "approved_at")
    search_fields = ("user__username", "user__email", "approved_by__username")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["approve_withdrawals", "reject_withdrawals"]
    
    def amount_display(self, obj):
        return format_html('<span style="font-weight: bold;">${:.2f}</span>', obj.amount)
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"
    
    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "approved": "#28a745",
            "rejected": "#dc3545"
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.status
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def approve_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status="pending"):
            w.approve(request.user)
            count += 1
        self.message_user(request, f"{count} withdrawal(s) approved successfully.", level="success")
    approve_withdrawals.short_description = "✓ Approve selected withdrawals"
    
    def reject_withdrawals(self, request, queryset):
        count = queryset.filter(status="pending").update(status="rejected")
        self.message_user(request, f"{count} withdrawal(s) rejected.", level="warning")
    reject_withdrawals.short_description = "✗ Reject selected withdrawals"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("user", "approved_by")
