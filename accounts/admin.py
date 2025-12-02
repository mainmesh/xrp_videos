from django.contrib import admin
from .models import Profile, Deposit, WithdrawalRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "referred_by", "referrals_count")


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "created_at", "success")


@admin.register(WithdrawalRequest)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at", "approved_by")
    actions = ["approve_withdrawals"]

    def approve_withdrawals(self, request, queryset):
        for w in queryset.filter(status="pending"):
            w.approve(request.user)
        self.message_user(request, "Selected withdrawals processed (approved where possible).")
    approve_withdrawals.short_description = "Approve selected withdrawals"
