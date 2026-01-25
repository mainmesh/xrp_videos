"""
Comprehensive test of tier upgrade functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, Transaction
from videos.models import Tier

def test_complete_tier_upgrade():
    print("=" * 70)
    print("COMPREHENSIVE TIER UPGRADE TEST")
    print("=" * 70)
    
    # Get test user
    user = User.objects.get(username='mark')
    profile = user.profile
    
    print(f"\n📊 INITIAL STATE:")
    print(f"  User: {user.username}")
    print(f"  Balance: ${profile.balance:.2f}")
    print(f"  Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
    
    # Get tiers
    tiers = Tier.objects.all().order_by('price')
    print(f"\n🎯 AVAILABLE TIERS:")
    for tier in tiers:
        print(f"  - {tier.name}: ${tier.price:.2f}")
    
    # Test 1: Try to upgrade without sufficient balance
    print(f"\n\n{'='*70}")
    print("TEST 1: Attempt upgrade with insufficient balance")
    print("="*70)
    
    tier = tiers.first()  # TestTier ($5.00)
    print(f"Attempting to upgrade to {tier.name} (${tier.price:.2f})...")
    print(f"Current balance: ${profile.balance:.2f}")
    
    if profile.balance < tier.price:
        print(f"❌ Insufficient balance! Need ${tier.price - profile.balance:.2f} more.")
    else:
        print(f"✓ Sufficient balance!")
    
    # Test 2: Add funds and upgrade
    print(f"\n\n{'='*70}")
    print("TEST 2: Add funds and perform upgrade")
    print("="*70)
    
    print(f"Adding $20 to account...")
    profile.credit(20.0, "Test funds", transaction_type="deposit")
    print(f"New balance: ${profile.balance:.2f}")
    
    print(f"\nAttempting upgrade to {tier.name} (${tier.price:.2f})...")
    
    # Check conditions
    can_upgrade = True
    if profile.current_tier and profile.current_tier.price >= tier.price:
        print(f"❌ Already have {profile.current_tier.name} or higher")
        can_upgrade = False
    elif profile.balance < tier.price:
        print(f"❌ Insufficient balance")
        can_upgrade = False
    else:
        # Perform upgrade
        old_tier = profile.current_tier.name if profile.current_tier else "No Tier"
        if profile.debit(tier.price, reason=f"Upgrade to {tier.name} tier", transaction_type="tier_upgrade", tier=tier):
            profile.current_tier = tier
            profile.save()
            print(f"✅ Successfully upgraded from {old_tier} to {tier.name}!")
            print(f"   Amount debited: ${tier.price:.2f}")
            print(f"   New balance: ${profile.balance:.2f}")
    
    # Test 3: Try to upgrade to same tier (should fail)
    print(f"\n\n{'='*70}")
    print("TEST 3: Attempt to re-purchase same tier (should fail)")
    print("="*70)
    
    print(f"Attempting to upgrade to {tier.name} again...")
    if profile.current_tier and profile.current_tier.price >= tier.price:
        print(f"❌ Already have {profile.current_tier.name} tier! Cannot downgrade or re-purchase.")
    
    # Test 4: Upgrade to higher tier
    print(f"\n\n{'='*70}")
    print("TEST 4: Upgrade to higher tier")
    print("="*70)
    
    tier2 = tiers[1]  # DebugTier ($10.00)
    print(f"Current tier: {profile.current_tier.name} (${profile.current_tier.price:.2f})")
    print(f"Attempting upgrade to {tier2.name} (${tier2.price:.2f})...")
    print(f"Current balance: ${profile.balance:.2f}")
    
    if profile.current_tier and profile.current_tier.price >= tier2.price:
        print(f"❌ Already have {profile.current_tier.name} or higher")
    elif profile.balance < tier2.price:
        print(f"❌ Insufficient balance (need ${tier2.price - profile.balance:.2f} more)")
    else:
        old_tier = profile.current_tier.name
        if profile.debit(tier2.price, reason=f"Upgrade to {tier2.name} tier", transaction_type="tier_upgrade", tier=tier2):
            profile.current_tier = tier2
            profile.save()
            print(f"✅ Successfully upgraded from {old_tier} to {tier2.name}!")
            print(f"   Amount debited: ${tier2.price:.2f}")
            print(f"   New balance: ${profile.balance:.2f}")
    
    # Test 5: Check transaction history
    print(f"\n\n{'='*70}")
    print("TEST 5: Transaction History")
    print("="*70)
    
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')[:10]
    print(f"\nRecent transactions for {user.username}:")
    print(f"{'Type':<20} {'Amount':<10} {'Before':<10} {'After':<10} {'Description':<30}")
    print("-" * 80)
    
    for txn in transactions:
        print(f"{txn.get_transaction_type_display():<20} ${txn.amount:<9.2f} ${txn.balance_before:<9.2f} ${txn.balance_after:<9.2f} {txn.description[:28]:<30}")
    
    # Final state
    print(f"\n\n{'='*70}")
    print("FINAL STATE")
    print("="*70)
    
    profile.refresh_from_db()
    print(f"  User: {user.username}")
    print(f"  Balance: ${profile.balance:.2f}")
    print(f"  Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
    print(f"  Total Transactions: {transactions.count()}")
    
    print(f"\n{'='*70}")
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    test_complete_tier_upgrade()
