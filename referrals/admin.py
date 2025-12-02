from django.contrib import admin
from .models import ReferralLink, ReferralBonus


@admin.register(ReferralLink)
class ReferralLinkAdmin(admin.ModelAdmin):
    list_display = ("user", "code")


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "amount", "created_at")
