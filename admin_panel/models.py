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


class PaymentOption(models.Model):
    """Payment methods where users can send money.

    - `name`: Display name (e.g., 'Bank Transfer', 'M-Pesa', 'Bitcoin').
    - `countries`: optional comma-separated list of ISO country codes this option applies to. Blank means global.
    - `currency`: optional currency code for this option.
    - `instructions`: free-form instructions or account details shown to the user.
    - `active`: whether the option should be shown.
    - `sort_order`: ordering when displayed.
    """
    name = models.CharField(max_length=100)
    countries = models.CharField(max_length=200, blank=True, help_text="Comma-separated ISO country codes (e.g. US,GB,KE). Blank = all countries")
    currency = models.CharField(max_length=10, blank=True)
    instructions = models.TextField(blank=True, help_text="Payment instructions or account details")
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=100)

    class Meta:
        ordering = ["sort_order", "name"]

    def countries_list(self):
        if not self.countries:
            return []
        return [c.strip().upper() for c in self.countries.split(",") if c.strip()]

    def matches_country(self, country_code: str | None) -> bool:
        if not self.active:
            return False
        if not self.countries:
            return True
        if not country_code:
            return False
        country_code = country_code.strip().upper()
        return country_code in self.countries_list()

    def __str__(self):
        return f"{self.name} ({'Global' if not self.countries else self.countries})"

