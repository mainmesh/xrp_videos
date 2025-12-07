from django.db import models


class SiteSettings(models.Model):
    """Site-wide settings."""
    maintenance_mode = models.BooleanField(default=False, help_text="Enable to put site in maintenance mode")
    maintenance_message = models.TextField(default="We're currently performing maintenance. Please check back soon!", help_text="Message shown during maintenance")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return "Site Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings singleton."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

