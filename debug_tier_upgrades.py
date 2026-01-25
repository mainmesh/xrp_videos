"""
Debug tier upgrade issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from videos.models import Tier

def debug_tiers():
    print("=" * 70)
    print("DEBUGGING TIER UPGRADE ISSUES")
    print("=" * 70)
    
    # Check all users
    users = User.objects.all()
    
    for user in users:
        try:
            profile = user.profile
            print(f"\n{'='*70}")
            print(f"User: {user.username}")
            print(f"Balance: ${profile.balance:.2f}")
            print(f"Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
            if profile.current_tier:
                print(f"Current Tier Price: ${profile.current_tier.price:.2f}")
            
            # Check all tiers
            tiers = Tier.objects.all().order_by('price')
            print(f"\nTier Upgrade Analysis:")
            for tier in tiers:
                can_afford = profile.balance >= tier.price
                
                if profile.current_tier:
                    already_has = profile.current_tier.price >= tier.price
                    if already_has:
                        status = f"❌ Already have {profile.current_tier.name} (${profile.current_tier.price}) >= {tier.name} (${tier.price})"
                    elif can_afford:
                        status = f"✅ CAN UPGRADE (have ${profile.balance:.2f} >= ${tier.price:.2f})"
                    else:
                        status = f"💰 Need ${tier.price - profile.balance:.2f} more"
                else:
                    if can_afford:
                        status = f"✅ CAN UPGRADE (have ${profile.balance:.2f} >= ${tier.price:.2f})"
                    else:
                        status = f"💰 Need ${tier.price - profile.balance:.2f} more"
                
                print(f"  {tier.name} (${tier.price:.2f}): {status}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n{'='*70}")

if __name__ == "__main__":
    debug_tiers()
