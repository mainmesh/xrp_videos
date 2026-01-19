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

    def credit(self, amount: float, reason: str = ""):
        self.balance = float(self.balance) + float(amount)
        self.save()

    def debit(self, amount: float, reason: str = "") -> bool:
        if float(self.balance) >= float(amount):
            self.balance = float(self.balance) - float(amount)
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user.username} - ${self.balance:.2f}"


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

