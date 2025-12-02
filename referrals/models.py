from django.db import models
from django.contrib.auth.models import User


class ReferralLink(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.user.username} -> {self.code}"


class ReferralBonus(models.Model):
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bonuses_received')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bonuses_given')
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.amount} from {self.from_user.username} to {self.to_user.username}"
# placeholder