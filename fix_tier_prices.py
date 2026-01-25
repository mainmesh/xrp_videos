"""
Update tier prices: Bronze=Free, Silver=$50, Gold=$100
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
    
    # Get tiers
    bronze = Tier.objects.filter(name='Bronze').first()
    silver = Tier.objects.filter(name='Silver').first()
    gold = Tier.objects.filter(name='Gold').first()
    
    print(f"\nCurrent prices:")
    if bronze:
        print(f"  Bronze: ${bronze.price}")
    if silver:
        print(f"  Silver: ${silver.price}")
    if gold:
        print(f"  Gold: ${gold.price}")
    
    print(f"\nUpdating to new prices...")
    
    if bronze:
        bronze.price = 0.00
        bronze.save()
        print(f"  ✓ Bronze: $0.00 (Free)")
    
    if silver:
        silver.price = 50.00
        silver.save()
        print(f"  ✓ Silver: $50.00")
    
    if gold:
        gold.price = 100.00
        gold.save()
        print(f"  ✓ Gold: $100.00")
    
    print("\n" + "=" * 50)
    print("✅ Tier prices updated successfully!")
    print("=" * 50)

if __name__ == "__main__":
    update_tier_prices()
