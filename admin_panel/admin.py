from django.contrib import admin
from .models import SiteSettings, PaymentOption


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "maintenance_mode", "updated_at")


@admin.register(PaymentOption)
class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "payment_type", "till_number", "crypto_network", "wallet_address", "currency", "countries", "active", "sort_order")
    list_filter = ("payment_type", "active", "crypto_network")
    search_fields = ("name", "countries", "currency", "till_number", "wallet_address")
    ordering = ("sort_order", "name")
    fieldsets = (
        ("General", {
            "fields": ("name", "payment_type", "active", "sort_order")
        }),
        ("M-Pesa Till", {
            "fields": ("till_number",),
            "classes": ("collapse",),
        }),
        ("Crypto Wallet", {
            "fields": ("crypto_network", "wallet_address"),
            "classes": ("collapse",),
        }),
        ("Display", {
            "fields": ("countries", "currency", "instructions"),
        }),
    )
