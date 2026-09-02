from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.FloatField(default=0)
    referred_by = models.ForeignKey(User, null=True, blank=True, related_name='referred_users', on_delete=models.SET_NULL)
    referrals_count = models.IntegerField(default=0)
    current_tier = models.ForeignKey('videos.Tier', null=True, blank=True, on_delete=models.SET_NULL, help_text="Current tier the user has access to")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    accepted_terms_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_in = models.BooleanField(default=False)
    failed_login_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    def credit(self, amount: float, reason: str = "", transaction_type: str = "deposit", video=None):
        from decimal import Decimal
        balance_before = Decimal(str(self.balance))
        self.balance = float(self.balance) + float(amount)
        self.save()
        
        # Log transaction
        Transaction.objects.create(
            user=self.user,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            balance_before=balance_before,
            balance_after=Decimal(str(self.balance)),
            description=reason or f"{transaction_type.replace('_', ' ').title()}",
            video=video
        )

    def debit(self, amount: float, reason: str = "", transaction_type: str = "withdrawal", tier=None) -> bool:
        from decimal import Decimal
        if float(self.balance) >= float(amount):
            balance_before = Decimal(str(self.balance))
            self.balance = float(self.balance) - float(amount)
            self.save()
            
            # Log transaction
            Transaction.objects.create(
                user=self.user,
                transaction_type=transaction_type,
                amount=Decimal(str(amount)),
                balance_before=balance_before,
                balance_after=Decimal(str(self.balance)),
                description=reason or f"{transaction_type.replace('_', ' ').title()}",
                tier=tier
            )
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - ${self.balance:.2f}"


class EmailVerification(models.Model):
    """One-time token sent by email to confirm a user's email address on signup
    or when the user changes their email. The token expires in 24 hours."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verifications')
    token = models.CharField(max_length=64, unique=True)
    new_email = models.EmailField(blank=True, help_text="Filled when verifying an email change.")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        from django.utils import timezone
        return self.used_at is None and timezone.now() < self.expires_at

    def __str__(self):
        return f"EmailVerification(user={self.user.username}, used={'{bool(self.used_at)}'})"


class LoginAttempt(models.Model):
    """Tracks login attempts (success/failure) and timestamps, used for rate-limit
    inspection and showing the user 'last login' info."""

    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['username', 'created_at'])]

    def __str__(self):
        return f"LoginAttempt({self.username}, success={self.success}, ip={self.ip_address})"


class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_payment_intent = models.CharField(max_length=200, null=True, blank=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        return f"Deposit {self.amount} for {self.user.username}"


class WithdrawalRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    approved_by = models.ForeignKey(User, null=True, blank=True, related_name='approved_withdrawals', on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)

    def approve(self, approver: User):
        if self.status != "pending":
            return
        # Debit user's profile balance
        try:
            profile = self.user.profile
            if profile.debit(self.amount, reason="withdrawal"):
                self.status = "approved"
                self.approved_by = approver
                self.approved_at = timezone.now()
                self.save()
                # Placeholder for email notification
        except Profile.DoesNotExist:
            pass

    def __str__(self):
        return f"Withdrawal {self.amount} by {self.user.username} - {self.status}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # Also create referral link
        import uuid
        from referrals.models import ReferralLink
        code = str(uuid.uuid4())[:8].upper()
        ReferralLink.objects.create(user=instance, code=code)


class PaymentAttempt(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    country = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True)
    payment_option = models.ForeignKey('admin_panel.PaymentOption', null=True, blank=True, on_delete=models.SET_NULL)
    raw_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verifier_note = models.TextField(blank=True)

    def mark_verified(self, verifier_note="Verified automatically"):
        if self.status == 'verified':
            return
        self.status = 'verified'
        from django.utils import timezone
        self.verified_at = timezone.now()
        self.verifier_note = verifier_note
        self.save()
        # credit user's profile
        try:
            self.user.profile.credit(float(self.amount), reason="deposit_mpesa")
        except Exception:
            pass

    def mark_rejected(self, note="Rejected"):
        self.status = 'rejected'
        self.verifier_note = note
        self.save()

    def __str__(self):
        return f"PaymentAttempt {self.amount} {self.user.username} - {self.status}"


class Transaction(models.Model):
    """Track all financial transactions for audit trail"""
    TRANSACTION_TYPES = (
        ("tier_upgrade", "Tier Upgrade"),
        ("video_reward", "Video Reward"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("referral_bonus", "Referral Bonus"),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional references
    tier = models.ForeignKey('videos.Tier', null=True, blank=True, on_delete=models.SET_NULL)
    video = models.ForeignKey('videos.Video', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ${self.amount} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

