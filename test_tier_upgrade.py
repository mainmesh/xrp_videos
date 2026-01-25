"""
Test script to check tier upgrade functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from videos.models import Tier

def test_tier_upgrade():
    print("=" * 50)
    print("Testing Tier Upgrade Functionality")
    print("=" * 50)
    
    # Check if tiers exist
    tiers = Tier.objects.all().order_by('price')
    print(f"\nFound {tiers.count()} tiers:")
    for tier in tiers:
        print(f"  - {tier.name}: ${tier.price}")
    
    # Check users and their profiles
    users = User.objects.all()[:5]  # Check first 5 users
    print(f"\nChecking users:")
    for user in users:
        try:
            profile = user.profile
            print(f"\n  User: {user.username}")
            print(f"  Balance: ${profile.balance:.2f}")
            print(f"  Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
            
            # Check upgrade eligibility for each tier
            for tier in tiers:
                can_upgrade = True
                reason = ""
                
                if profile.current_tier and profile.current_tier.price >= tier.price:
                    can_upgrade = False
                    reason = f"Already have {profile.current_tier.name} or higher"
                elif profile.balance < tier.price:
                    can_upgrade = False
                    reason = f"Insufficient balance (need ${tier.price:.2f}, have ${profile.balance:.2f})"
                else:
                    reason = "✓ Can upgrade!"
                
                print(f"    {tier.name}: {reason}")
                
        except Profile.DoesNotExist:
            print(f"  User: {user.username} - NO PROFILE!")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_tier_upgrade()
