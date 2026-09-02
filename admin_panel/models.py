from django.db import models
from django.contrib.auth.models import User


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


class AdminRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    STANDARD_ADMIN = 'admin', 'Standard Admin'
    STAFF = 'staff', 'Staff (read-only)'


class AdminPermission(models.Model):
    """Granular permission flag. A user gains permissions either from their
    role's default set or from explicit rows in AdminProfile.permissions."""
    key = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=200)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key


class AdminProfile(models.Model):
    """Per-admin user metadata. Created automatically the first time a user is
    promoted into any non-default admin role (data migration in 0002)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.STAFF)
    permissions = models.ManyToManyField(AdminPermission, blank=True, related_name='admins')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class AuditLog(models.Model):
    """Append-only audit log for sensitive actions performed in the admin
    panel. `before`/`after` are stored as JSON to allow diff rendering later."""
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        who = self.actor.username if self.actor else 'system'
        return f"AuditLog({who} {self.action} {self.target_type}#{self.target_id})"

