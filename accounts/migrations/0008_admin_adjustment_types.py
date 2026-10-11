from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_stripe_payment_intent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(choices=[('tier_upgrade', 'Tier Upgrade'), ('video_reward', 'Video Reward'), ('deposit', 'Deposit'), ('withdrawal', 'Withdrawal'), ('referral_bonus', 'Referral Bonus'), ('admin_credit', 'Admin Credit'), ('admin_debit', 'Admin Debit')], max_length=20),
        ),
    ]
