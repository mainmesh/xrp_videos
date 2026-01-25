"""
Rename tiers to proper names: Bronze, Silver, Gold, Platinum
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from videos.models import Tier

def rename_tiers():
    print("=" * 50)
    print("Renaming Tiers to Professional Names")
    print("=" * 50)
    
    # Get existing tiers ordered by price
    tiers = Tier.objects.all().order_by('price')
    
    print(f"\nCurrent tiers:")
    for tier in tiers:
        print(f"  - {tier.name}: ${tier.price}")
    
    # Rename mapping based on order
    new_names = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    
    print(f"\nRenaming tiers...")
    for i, tier in enumerate(tiers):
        if i < len(new_names):
            old_name = tier.name
            tier.name = new_names[i]
            tier.save()
            print(f"  ✓ {old_name} → {tier.name} (${tier.price})")
    
    print(f"\n" + "=" * 50)
    print("Updated tiers:")
    for tier in Tier.objects.all().order_by('price'):
        print(f"  - {tier.name}: ${tier.price}")
    
    print("=" * 50)
    print("✅ Tier names updated successfully!")
    print("=" * 50)

if __name__ == "__main__":
    rename_tiers()
