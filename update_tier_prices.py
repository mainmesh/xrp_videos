"""
Update tier prices to create proper hierarchy
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from videos.models import Tier

def update_tier_prices():
    print("=" * 50)
    print("Updating Tier Prices")
    print("=" * 50)
    
    # Get all tiers
    tiers = Tier.objects.all().order_by('id')
    
    if tiers.count() == 0:
        print("\nNo tiers found. Creating default tiers...")
        Tier.objects.create(name="Bronze", price=5.00)
        Tier.objects.create(name="Silver", price=10.00)
        Tier.objects.create(name="Gold", price=25.00)
        Tier.objects.create(name="Platinum", price=50.00)
        print("✓ Created 4 default tiers")
        return
    
    print(f"\nFound {tiers.count()} existing tiers:")
    for tier in tiers:
        print(f"  - {tier.name}: ${tier.price}")
    
    # Update prices to create hierarchy
    tier_updates = {
        'TestTier': 5.00,
        'DebugTier': 10.00,
        'TestTier2': 25.00,
        'Bronze': 5.00,
        'Silver': 10.00,
        'Gold': 25.00,
        'Platinum': 50.00,
    }
    
    print("\nUpdating tier prices...")
    for tier in tiers:
        if tier.name in tier_updates:
            old_price = tier.price
            tier.price = tier_updates[tier.name]
            tier.save()
            print(f"  ✓ {tier.name}: ${old_price} → ${tier.price}")
        else:
            print(f"  - {tier.name}: ${tier.price} (no change)")
    
    print("\n" + "=" * 50)
    print("Tier hierarchy updated successfully!")
    print("=" * 50)

if __name__ == "__main__":
    update_tier_prices()
