from django.core.management.base import BaseCommand
from videos.models import Tier


class Command(BaseCommand):
    help = 'Create default tiers (Bronze, Silver, Gold) if they do not exist'

    def handle(self, *args, **options):
        default_tiers = [
            {'name': 'Bronze', 'price': 0.0},
            {'name': 'Silver', 'price': 10.0},
            {'name': 'Gold', 'price': 25.0},
        ]

        created_count = 0
        for tier_data in default_tiers:
            tier, created = Tier.objects.get_or_create(
                name=tier_data['name'],
                defaults={'price': tier_data['price']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created tier: {tier.name} (${tier.price})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tier already exists: {tier.name} (${tier.price})')
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully created {created_count} tier(s)!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAll default tiers already exist.')
            )
