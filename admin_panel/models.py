from django.db import models


class SiteSettings(models.Model):
    """Site-wide settings."""
    # Maintenance
    maintenance_mode = models.BooleanField(default=False, help_text="Enable to put site in maintenance mode")
    maintenance_message = models.TextField(default="We're currently performing maintenance. Please check back soon!", help_text="Message shown during maintenance")
    
    # Platform Info
    site_name = models.CharField(max_length=100, default="xrpvideos")
    contact_email = models.EmailField(default="admin@xrpvideos.com")
    
    # Withdrawal Settings
    min_withdrawal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00, help_text="Minimum amount users can withdraw")
    min_referrals_for_withdrawal = models.IntegerField(default=7, help_text="Minimum referrals required to withdraw")
    withdrawal_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Withdrawal fee percentage (0-100)")
    
    # Referral Settings
    referral_bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Referral commission percentage")
    
    # Video Rewards
    default_video_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0.50, help_text="Default reward for watching videos")
    
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

