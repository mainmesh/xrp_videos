from django.core.management.base import BaseCommand
from admin_panel.models import Tier

class Command(BaseCommand):
    help = 'Fix tier names to Bronze, Silver, Gold'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Fixing Tier Names...")
        self.stdout.write("=" * 50)

        # Get all tiers sorted by price
        tiers = Tier.objects.all().order_by('price')
        self.stdout.write(f"\n📊 Found {tiers.count()} tiers:")
        for tier in tiers:
            self.stdout.write(f"  - {tier.name}: ${tier.price}")

        if tiers.count() >= 3:
            tier_names = ['Bronze', 'Silver', 'Gold']
            for i, tier in enumerate(tiers[:3]):
                old_name = tier.name
                tier.name = tier_names[i]
                tier.save()
                self.stdout.write(self.style.SUCCESS(f"\n✓ Renamed '{old_name}' → '{tier.name}'"))
            
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(self.style.SUCCESS("✅ Tier names fixed!"))
            self.stdout.write("\nCurrent Tiers:")
            for tier in Tier.objects.all().order_by('price'):
                self.stdout.write(f"  • {tier.name}: ${tier.price}")
        else:
            self.stdout.write(self.style.WARNING("\n⚠️  Not enough tiers found. Creating proper tiers..."))
            
            # Create proper tiers
            bronze, _ = Tier.objects.get_or_create(
                name='Bronze',
                defaults={'price': 0.0}
            )
            silver, _ = Tier.objects.get_or_create(
                name='Silver',
                defaults={'price': 50.0}
            )
            gold, _ = Tier.objects.get_or_create(
                name='Gold',
                defaults={'price': 100.0}
            )
            
            self.stdout.write(self.style.SUCCESS("✅ Created proper tiers:"))
            self.stdout.write("  • Bronze: $0")
            self.stdout.write("  • Silver: $50")
            self.stdout.write("  • Gold: $100")
