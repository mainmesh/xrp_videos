from django.core.management.base import BaseCommand
from admin_panel.models import PaymentOption


class Command(BaseCommand):
    help = 'Add payment options for M-Pesa Till and Crypto wallets'

    def handle(self, *args, **options):
        # M-Pesa Till Kenya
        till_ke, created = PaymentOption.objects.get_or_create(
            name='M-Pesa Till (Kenya)',
            defaults={
                'payment_type': 'mpesa_till',
                'countries': 'KE',
                'currency': 'KES',
                'till_number': '1563070',
                'instructions': '''**Pay via M-Pesa Till Number:**

🏪 **Till Number:** 1563070
💵 **Amount:** Enter your desired deposit amount in KES

**Steps:**
1. Go to M-Pesa menu on your phone
2. Select "Lipa na M-Pesa" → "Buy Goods and Services"
3. Enter Till Number: **1563070**
4. Enter amount in KES
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the deposit form to get credited automatically.

**Note:** KES 100 ≈ $1 USD (check current exchange rate)''',
                'active': True,
                'sort_order': 1
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Created M-Pesa Till Kenya payment option'))
        else:
            till_ke.payment_type = 'mpesa_till'
            till_ke.countries = 'KE'
            till_ke.currency = 'KES'
            till_ke.till_number = '1563070'
            till_ke.instructions = '''**Pay via M-Pesa Till Number:**

🏪 **Till Number:** 1563070
💵 **Amount:** Enter your desired deposit amount in KES

**Steps:**
1. Go to M-Pesa menu on your phone
2. Select "Lipa na M-Pesa" → "Buy Goods and Services"
3. Enter Till Number: **1563070**
4. Enter amount in KES
5. Enter your PIN and confirm
6. You will receive a confirmation SMS

**After Payment:**
Copy the M-Pesa confirmation message and submit it via the deposit form to get credited automatically.

**Note:** KES 100 ≈ $1 USD (check current exchange rate)'''
            till_ke.active = True
            till_ke.sort_order = 1
            till_ke.save()
            self.stdout.write(self.style.SUCCESS('Updated M-Pesa Till Kenya payment option'))

        # Crypto wallets
        crypto_options = [
            {
                'name': 'Solana (SOL)',
                'payment_type': 'crypto_wallet',
                'crypto_network': 'SOL',
                'wallet_address': '',
                'currency': 'SOL',
                'instructions': 'Send SOL to the wallet address below. Network: Solana. Transaction confirmations take ~1 minute.',
                'sort_order': 10,
            },
            {
                'name': 'Bitcoin (BTC)',
                'payment_type': 'crypto_wallet',
                'crypto_network': 'BTC',
                'wallet_address': '',
                'currency': 'BTC',
                'instructions': 'Send BTC to the wallet address below. Network: Bitcoin. Transaction confirmations take ~10-60 minutes.',
                'sort_order': 11,
            },
            {
                'name': 'Ethereum (ETH)',
                'payment_type': 'crypto_wallet',
                'crypto_network': 'ETH',
                'wallet_address': '',
                'currency': 'ETH',
                'instructions': 'Send ETH to the wallet address below. Network: Ethereum. Transaction confirmations take ~1-5 minutes.',
                'sort_order': 12,
            },
        ]

        for opt in crypto_options:
            obj, created = PaymentOption.objects.get_or_create(
                name=opt['name'],
                defaults={
                    'payment_type': opt['payment_type'],
                    'crypto_network': opt['crypto_network'],
                    'wallet_address': opt['wallet_address'],
                    'currency': opt['currency'],
                    'instructions': opt['instructions'],
                    'active': True,
                    'sort_order': opt['sort_order'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created {opt["name"]} payment option'))
            else:
                obj.payment_type = opt['payment_type']
                obj.crypto_network = opt['crypto_network']
                obj.wallet_address = opt['wallet_address']
                obj.currency = opt['currency']
                obj.instructions = opt['instructions']
                obj.active = True
                obj.sort_order = opt['sort_order']
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Updated {opt["name"]} payment option'))

        self.stdout.write(self.style.SUCCESS('Payment options configured successfully!'))
