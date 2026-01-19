from django.contrib import admin
from .models import SiteSettings, PaymentOption


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "maintenance_mode", "updated_at")


@admin.register(PaymentOption)
class PaymentOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "countries", "active", "sort_order")
    list_filter = ("active",)
    search_fields = ("name", "countries", "currency")
    ordering = ("sort_order", "name")
