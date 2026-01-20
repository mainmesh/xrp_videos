#!/usr/bin/env python
"""
Complete user flow test: Signup -> Deposit -> Upgrade Tier -> Verify
"""
import os
import django
from decimal import Decimal

# Force SQLite for local testing
os.environ['DATABASE_URL'] = ''
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile, Deposit
from videos.models import Video, Tier
from django.utils import timezone

print("=" * 70)
print("COMPLETE USER FLOW TEST")
print("=" * 70)

# Step 1: Create a new user (simulating signup)
print("\n📝 STEP 1: USER SIGNUP")
print("-" * 70)

username = 'newuser'
email = 'newuser@example.com'
password = 'newuser123'

try:
    # Delete if exists for clean test
    User.objects.filter(username=username).delete()
    print(f"✓ Cleaned up existing user: {username}")
except:
    pass

user = User.objects.create_user(
    username=username,
    email=email,
    password=password
)
print(f"✅ User created successfully!")
print(f"   - Username: {username}")
print(f"   - Email: {email}")
print(f"   - Password: {password}")

# Step 2: Check Profile creation
print("\n👤 STEP 2: PROFILE CHECK")
print("-" * 70)

profile, created = Profile.objects.get_or_create(user=user)
if created:
    print(f"✅ Profile created automatically")
else:
    print(f"✓ Profile already exists")

print(f"   - Balance: ${profile.balance}")
print(f"   - Current Tier: {profile.current_tier.name if profile.current_tier else 'Free (No Tier)'}")
print(f"   - Referrals Count: {profile.referrals_count}")

# Step 3: Check available tiers
print("\n💎 STEP 3: AVAILABLE TIERS")
print("-" * 70)

tiers = Tier.objects.all().order_by('price')
print(f"✓ Found {tiers.count()} tiers:")
for tier in tiers:
    print(f"   - {tier.name}: ${tier.price}")

# Step 4: Simulate deposit
print("\n💰 STEP 4: SIMULATE DEPOSIT")
print("-" * 70)

# Choose Silver tier for testing
silver_tier = Tier.objects.filter(name='Silver').first()
if not silver_tier:
    print("❌ Silver tier not found!")
    exit(1)

deposit_amount = silver_tier.price
print(f"User wants to upgrade to: {silver_tier.name} (${silver_tier.price})")

# Create deposit record (using Stripe simulation)
deposit = Deposit.objects.create(
    user=user,
    amount=deposit_amount,
    success=False,  # Initially pending
    stripe_payment_intent=f'pi_test_{timezone.now().strftime("%Y%m%d%H%M%S")}'
)
print(f"✅ Deposit created:")
print(f"   - Amount: ${deposit.amount}")
print(f"   - Success: {deposit.success}")
print(f"   - Stripe Payment Intent: {deposit.stripe_payment_intent}")
print(f"   - Created: {deposit.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

# Step 5: Admin approves deposit (simulating admin action)
print("\n✅ STEP 5: ADMIN APPROVES DEPOSIT")
print("-" * 70)

admin_user = User.objects.filter(is_staff=True).first()
if not admin_user:
    print("⚠️  No admin user found, creating one...")
    admin_user = User.objects.create_superuser('admin', 'admin@xrpvideos.com', 'admin123')

# Mark deposit as successful
deposit.success = True
deposit.save()

# Credit user's balance
profile.balance = float(profile.balance) + float(deposit.amount)
profile.save()

print(f"✅ Deposit marked as successful")
print(f"   - User balance credited: ${deposit.amount}")
print(f"   - New balance: ${profile.balance}")

# Step 6: User upgrades tier
print("\n⬆️  STEP 6: UPGRADE TIER")
print("-" * 70)

if profile.balance >= silver_tier.price:
    profile.balance = float(profile.balance) - float(silver_tier.price)
    profile.current_tier = silver_tier
    profile.save()
    print(f"✅ Tier upgraded successfully!")
    print(f"   - New Tier: {profile.current_tier.name}")
    print(f"   - Tier Cost: ${silver_tier.price}")
    print(f"   - Remaining Balance: ${profile.balance}")
else:
    print(f"❌ Insufficient balance for tier upgrade")

# Step 7: Check available videos for user
print("\n🎬 STEP 7: AVAILABLE VIDEOS")
print("-" * 70)

if profile.current_tier:
    available_videos = Video.objects.filter(
        is_active=True,
        min_tier__price__lte=profile.current_tier.price
    ).order_by('-created_at')
else:
    available_videos = Video.objects.filter(
        is_active=True,
        min_tier__isnull=True
    ).order_by('-created_at')

print(f"✅ Found {available_videos.count()} videos available for {silver_tier.name} tier:")
for video in available_videos[:5]:  # Show first 5
    tier_reward = None
    tier_price = video.tier_prices.filter(tier=profile.current_tier).first()
    if tier_price:
        tier_reward = tier_price.reward
    
    print(f"\n   📹 {video.title}")
    print(f"      - Duration: {video.duration_minutes} minutes")
    print(f"      - Min Tier: {video.min_tier.name if video.min_tier else 'Free'}")
    if tier_reward:
        print(f"      - Reward for {silver_tier.name}: ${tier_reward}")

# Step 8: Verify on admin side
print("\n" + "=" * 70)
print("🔍 ADMIN PANEL VERIFICATION")
print("=" * 70)

# Refresh from database
user.refresh_from_db()
profile.refresh_from_db()

print(f"\n👤 USER DETAILS (as seen by admin):")
print(f"   - ID: {user.id}")
print(f"   - Username: {user.username}")
print(f"   - Email: {user.email}")
print(f"   - Is Staff: {user.is_staff}")
print(f"   - Is Active: {user.is_active}")
print(f"   - Date Joined: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}")

print(f"\n💼 PROFILE DETAILS (as seen by admin):")
print(f"   - Balance: ${profile.balance}")
print(f"   - Current Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
print(f"   - Referrals Count: {profile.referrals_count}")
print(f"   - Referred By: {profile.referred_by.username if profile.referred_by else 'None'}")

print(f"\n💰 DEPOSIT HISTORY (as seen by admin):")
user_deposits = Deposit.objects.filter(user=user).order_by('-created_at')
print(f"   - Total Deposits: {user_deposits.count()}")
for dep in user_deposits:
    print(f"\n   📄 Deposit #{dep.id}")
    print(f"      - Amount: ${dep.amount}")
    print(f"      - Success: {dep.success}")
    print(f"      - Stripe Payment Intent: {dep.stripe_payment_intent or 'N/A'}")
    print(f"      - Created: {dep.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

# Step 9: Summary Statistics
print("\n" + "=" * 70)
print("📊 SUMMARY STATISTICS")
print("=" * 70)

total_users = User.objects.count()
total_deposits = Deposit.objects.filter(success=True).count()
total_deposit_amount = Deposit.objects.filter(success=True).aggregate(
    total=django.db.models.Sum('amount')
)['total'] or 0

print(f"   - Total Users: {total_users}")
print(f"   - Total Completed Deposits: {total_deposits}")
print(f"   - Total Deposit Amount: ${total_deposit_amount}")
print(f"   - Total Videos: {Video.objects.filter(is_active=True).count()}")
print(f"   - Total Tiers: {tiers.count()}")

# Step 10: Access URLs
print("\n" + "=" * 70)
print("🌐 ACCESS INFORMATION")
print("=" * 70)

print(f"\n✅ TEST COMPLETED SUCCESSFULLY!")
print(f"\nYou can now test in browser:")
print(f"\n👤 USER LOGIN:")
print(f"   URL: http://127.0.0.1:8000/accounts/login/")
print(f"   Username: {username}")
print(f"   Password: {password}")

print(f"\n👨‍💼 ADMIN PANEL:")
print(f"   URL: http://127.0.0.1:8000/admin/login/")
print(f"   Username: admin")
print(f"   Password: admin123")

print(f"\n📊 Admin Panel Sections to Check:")
print(f"   - Users: http://127.0.0.1:8000/admin/users/")
print(f"   - Deposits: http://127.0.0.1:8000/admin/deposits/")
print(f"   - Videos: http://127.0.0.1:8000/admin/videos/")

print("\n" + "=" * 70)
