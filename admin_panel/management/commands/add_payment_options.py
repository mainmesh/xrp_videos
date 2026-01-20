from django.core.management.base import BaseCommand
from admin_panel.models import PaymentOption


class Command(BaseCommand):
    help = 'Add payment options for M-Pesa Kenya'

    def handle(self, *args, **options):
        # M-Pesa Kenya
        mpesa_ke, created = PaymentOption.objects.get_or_create(
            name='M-Pesa (Kenya)',
            defaults={
                'countries': 'KE',
                'currency': 'KES',
                'instructions': '''**Send money via M-Pesa to:**

📱 **Phone Number:** 0792167414
💵 **Amount:** Enter your desired deposit amount in KES

**Steps:**
1. Go to M-Pesa menu
2. Select "Send Money" (Lipa na M-Pesa)
3. Enter: **0792167414**
4. Enter amount in KES
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the M-Pesa deposit form to get credited automatically.

**Note:** KES 100 ≈ $1 USD (check current exchange rate)''',
                'active': True,
                'sort_order': 1
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created M-Pesa Kenya payment option'))
        else:
            # Update existing
            mpesa_ke.countries = 'KE'
            mpesa_ke.currency = 'KES'
            mpesa_ke.instructions = '''**Send money via M-Pesa to:**

📱 **Phone Number:** 0792167414
💵 **Amount:** Enter your desired deposit amount in KES

**Steps:**
1. Go to M-Pesa menu
2. Select "Send Money" (Lipa na M-Pesa)
3. Enter: **0792167414**
4. Enter amount in KES
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the M-Pesa deposit form to get credited automatically.

**Note:** KES 100 ≈ $1 USD (check current exchange rate)'''
            mpesa_ke.active = True
            mpesa_ke.sort_order = 1
            mpesa_ke.save()
            self.stdout.write(self.style.SUCCESS('✅ Updated M-Pesa Kenya payment option'))
        
        self.stdout.write(self.style.SUCCESS('Payment options configured successfully!'))
