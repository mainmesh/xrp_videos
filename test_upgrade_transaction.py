"""
Test tier upgrade with actual transaction
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from videos.models import Tier

def test_upgrade_transaction():
    print("=" * 50)
    print("Testing Tier Upgrade Transaction")
    print("=" * 50)
    
    # Get a user with no tier but has balance
    user = User.objects.get(username='mark')
    profile = user.profile
    
    print(f"\nBefore upgrade:")
    print(f"  Balance: ${profile.balance:.2f}")
    print(f"  Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
    
    # Give user some balance
    profile.credit(10.0, "Test funds")
    print(f"\nAfter adding $10:")
    print(f"  Balance: ${profile.balance:.2f}")
    
    # Get the TestTier (costs $1.00)
    tier = Tier.objects.get(name='TestTier')
    
    # Attempt upgrade
    print(f"\nAttempting to upgrade to {tier.name} (${tier.price})...")
    
    # Check conditions
    if profile.current_tier and profile.current_tier.price >= tier.price:
        print("  ❌ Already have this tier or higher")
    elif profile.balance < tier.price:
        print(f"  ❌ Insufficient balance (need ${tier.price:.2f}, have ${profile.balance:.2f})")
    else:
        # Perform upgrade
        if profile.debit(tier.price, reason=f"Upgrade to {tier.name}"):
            profile.current_tier = tier
            profile.save()
            print("  ✅ Upgrade successful!")
        else:
            print("  ❌ Debit failed")
    
    print(f"\nAfter upgrade:")
    print(f"  Balance: ${profile.balance:.2f}")
    print(f"  Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_upgrade_transaction()
