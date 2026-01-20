import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from admin_panel.models import Tier

print("🔧 Fixing Tier Names...")
print("=" * 50)

# Get all tiers sorted by price
tiers = Tier.objects.all().order_by('price')
print(f"\n📊 Found {tiers.count()} tiers:")
for tier in tiers:
    print(f"  - {tier.name}: ${tier.price}")

if tiers.count() >= 3:
    tier_names = ['Bronze', 'Silver', 'Gold']
    for i, tier in enumerate(tiers[:3]):
        old_name = tier.name
        tier.name = tier_names[i]
        tier.save()
        print(f"\n✓ Renamed '{old_name}' → '{tier.name}'")
    
    print("\n" + "=" * 50)
    print("✅ Tier names fixed!")
    print("\nCurrent Tiers:")
    for tier in Tier.objects.all().order_by('price'):
        print(f"  • {tier.name}: ${tier.price}")
else:
    print("\n⚠️  Not enough tiers found. Creating proper tiers...")
    
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
    
    print("✅ Created proper tiers:")
    print(f"  • Bronze: $0")
    print(f"  • Silver: $50")
    print(f"  • Gold: $100")
