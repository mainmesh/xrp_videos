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
        
        # M-Pesa Tanzania
        mpesa_tz, created = PaymentOption.objects.get_or_create(
            name='M-Pesa (Tanzania)',
            defaults={
                'countries': 'TZ',
                'currency': 'TZS',
                'instructions': '''**Send money via M-Pesa to:**

📱 **Phone Number:** 0741029973
💵 **Amount:** Enter your desired deposit amount in TZS

**Steps:**
1. Go to M-Pesa menu
2. Select "Send Money" (Lipa na M-Pesa)
3. Enter: **0741029973**
4. Enter amount in TZS
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the M-Pesa deposit form to get credited automatically.

**Note:** TZS 2,300 ≈ $1 USD (check current exchange rate)''',
                'active': True,
                'sort_order': 2
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created M-Pesa Tanzania payment option'))
        else:
            # Update existing
            mpesa_tz.countries = 'TZ'
            mpesa_tz.currency = 'TZS'
            mpesa_tz.instructions = '''**Send money via M-Pesa to:**

📱 **Phone Number:** 0741029973
💵 **Amount:** Enter your desired deposit amount in TZS

**Steps:**
1. Go to M-Pesa menu
2. Select "Send Money" (Lipa na M-Pesa)
3. Enter: **0741029973**
4. Enter amount in TZS
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the M-Pesa deposit form to get credited automatically.

**Note:** TZS 2,300 ≈ $1 USD (check current exchange rate)'''
            mpesa_tz.active = True
            mpesa_tz.sort_order = 2
            mpesa_tz.save()
            self.stdout.write(self.style.SUCCESS('✅ Updated M-Pesa Tanzania payment option'))
        
        self.stdout.write(self.style.SUCCESS('Payment options configured successfully!'))
