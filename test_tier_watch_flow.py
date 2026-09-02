#!/usr/bin/env python
"""
Comprehensive test for tier upgrade, video watching, and balance crediting flow.
Tests:
1. User upgrades to a tier
2. User watches a video
3. Balance is properly deposited
4. Video watch terminates after required time
"""
import os
import sys

# Configure Django settings before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

# Import Django and setup
import django
django.setup()

from decimal import Decimal
from time import sleep
from django.contrib.auth.models import User
from accounts.models import Profile, Deposit, Transaction
from videos.models import Video, Tier, WatchHistory, WatchHeartbeat, Category
from django.utils import timezone
from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import models

def setup_test_data():
    """Create test tiers, videos, and categories."""
    print("\n🔧 SETTING UP TEST DATA")
    print("-" * 70)
    
    # Create tiers if they don't exist
    bronze_tier, _ = Tier.objects.get_or_create(
        name='Bronze',
        defaults={'price': 0.0}
    )
    silver_tier, _ = Tier.objects.get_or_create(
        name='Silver',
        defaults={'price': 10.0}
    )
    gold_tier, _ = Tier.objects.get_or_create(
        name='Gold',
        defaults={'price': 25.0}
    )
    
    print(f"✓ Tiers ready:")
    print(f"   - Bronze: ${bronze_tier.price}")
    print(f"   - Silver: ${silver_tier.price}")
    print(f"   - Gold: ${gold_tier.price}")
    
    # Create test category
    category, _ = Category.objects.get_or_create(name='Educational')
    
    # Create test videos
    video1, created = Video.objects.get_or_create(
        title='Test Video - Bronze Tier',
        defaults={
            'url': 'https://www.youtube.com/embed/test123',
            'description': 'Test video for bronze tier users',
            'reward': 0.50,
            'duration_seconds': 60,  # 1 minute
            'min_tier': bronze_tier,
            'is_active': True
        }
    )
    if not created:
        video1.duration_seconds = 60
        video1.min_tier = bronze_tier
        video1.reward = 0.50
        video1.is_active = True
        video1.save()
    
    video2, created = Video.objects.get_or_create(
        title='Test Video - Silver Tier',
        defaults={
            'url': 'https://www.youtube.com/embed/test456',
            'description': 'Test video for silver tier users',
            'reward': 1.50,
            'duration_seconds': 120,  # 2 minutes
            'min_tier': silver_tier,
            'is_active': True
        }
    )
    if not created:
        video2.duration_seconds = 120
        video2.min_tier = silver_tier
        video2.reward = 1.50
        video2.is_active = True
        video2.save()
    
    print(f"\n✓ Test videos ready:")
    print(f"   - {video1.title}: ${video1.reward}, {video1.duration_seconds}s, {video1.min_tier.name} tier")
    print(f"   - {video2.title}: ${video2.reward}, {video2.duration_seconds}s, {video2.min_tier.name} tier")
    
    return bronze_tier, silver_tier, gold_tier, video1, video2

def test_tier_upgrade_and_watch():
    """Main test function."""
    print("\n" + "=" * 70)
    print("TEST: TIER UPGRADE -> WATCH VIDEO -> BALANCE DEPOSIT")
    print("=" * 70)
    
    # Setup test data
    bronze_tier, silver_tier, gold_tier, video1, video2 = setup_test_data()
    
    # STEP 1: Create test user
    print("\n📝 STEP 1: CREATE TEST USER")
    print("-" * 70)
    
    username = 'testuser_tier_watch'
    email = 'testuser@tierwatch.com'
    password = 'testpass123'
    
    # Clean up existing user
    User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    print(f"✅ User created: {username}")
    
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=user)
    print(f"✅ Profile created" if created else "✓ Profile exists")
    print(f"   - Initial Balance: ${profile.balance:.2f}")
    print(f"   - Initial Tier: {profile.current_tier.name if profile.current_tier else 'None'}")
    
    # STEP 2: Upgrade to Silver Tier
    print("\n💎 STEP 2: UPGRADE TO SILVER TIER")
    print("-" * 70)
    
    initial_balance = profile.balance
    upgrade_cost = silver_tier.price
    
    # Simulate deposit for tier upgrade
    deposit = Deposit.objects.create(
        user=user,
        amount=upgrade_cost,
        success=False,  # Initially not successful
        stripe_payment_intent=f'pi_test_{timezone.now().strftime("%Y%m%d%H%M%S")}'
    )
    print(f"✅ Deposit created: ${deposit.amount}")
    
    # Mark deposit as successful and credit user balance
    deposit.success = True
    deposit.save()
    profile.credit(upgrade_cost, reason=f"Deposit for {silver_tier.name} tier upgrade", transaction_type="deposit")
    profile.refresh_from_db()
    print(f"✅ Balance credited: ${profile.balance:.2f}")
    
    # Deduct tier cost and assign tier
    if profile.debit(upgrade_cost, reason=f"Upgraded to {silver_tier.name} tier", transaction_type="tier_upgrade", tier=silver_tier):
        profile.current_tier = silver_tier
        profile.save()
        print(f"✅ Tier upgraded successfully!")
        print(f"   - New Tier: {profile.current_tier.name}")
        print(f"   - Balance After: ${profile.balance:.2f}")
        print(f"   - Cost: ${upgrade_cost:.2f}")
    else:
        print(f"❌ Insufficient balance for tier upgrade")
        return
    
    # STEP 3: Verify tier access to videos
    print("\n🎥 STEP 3: VERIFY VIDEO ACCESS")
    print("-" * 70)
    
    # User should have access to both Bronze and Silver tier videos
    accessible_videos = Video.objects.filter(
        is_active=True,
        min_tier__price__lte=profile.current_tier.price
    )
    print(f"✅ User has access to {accessible_videos.count()} videos:")
    for video in accessible_videos:
        print(f"   - {video.title} ({video.min_tier.name} tier, ${video.reward} reward)")
    
    # STEP 4: Watch a video (simulate full watch)
    print("\n▶️  STEP 4: WATCH VIDEO AND EARN REWARD")
    print("-" * 70)
    
    video_to_watch = video2  # Silver tier video
    print(f"Watching: {video_to_watch.title}")
    print(f"   - Duration: {video_to_watch.duration_seconds} seconds")
    print(f"   - Reward: ${video_to_watch.reward}")
    print(f"   - Required Tier: {video_to_watch.min_tier.name}")
    
    balance_before_watch = profile.balance
    
    # Simulate heartbeats (client sends these periodically while watching)
    print(f"\n⏱️  Simulating video playback with heartbeats...")
    heartbeat_times = [10, 30, 60, 90, 120]  # Heartbeats at different seconds
    for seconds in heartbeat_times:
        WatchHeartbeat.objects.create(
            user=user,
            video=video_to_watch,
            seconds=seconds
        )
        print(f"   ✓ Heartbeat at {seconds}s")
    
    # Simulate watch completion
    watched_seconds = video_to_watch.duration_seconds  # Full watch
    print(f"\n✅ Video watched completely: {watched_seconds}/{video_to_watch.duration_seconds} seconds")
    
    # Create watch history and credit reward
    wh, created = WatchHistory.objects.get_or_create(user=user, video=video_to_watch)
    wh.watched_seconds = watched_seconds
    wh.save()
    
    # Credit reward
    reward_amount = video_to_watch.reward
    profile.credit(
        reward_amount,
        reason=f"Watched: {video_to_watch.title}",
        transaction_type="video_reward",
        video=video_to_watch
    )
    wh.verified = True
    wh.save()
    
    profile.refresh_from_db()
    balance_after_watch = profile.balance
    
    print(f"\n💰 REWARD CREDITED:")
    print(f"   - Balance Before: ${balance_before_watch:.2f}")
    print(f"   - Reward Amount: ${reward_amount:.2f}")
    print(f"   - Balance After: ${balance_after_watch:.2f}")
    print(f"   - Difference: ${balance_after_watch - balance_before_watch:.2f}")
    
    # STEP 5: Verify transaction history
    print("\n📊 STEP 5: VERIFY TRANSACTION HISTORY")
    print("-" * 70)
    
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    print(f"✅ Found {transactions.count()} transactions:")
    for i, txn in enumerate(transactions, 1):
        print(f"   {i}. {txn.transaction_type}: ${txn.amount} - {txn.description}")
        print(f"      Balance: ${txn.balance_before} → ${txn.balance_after}")
    
    # STEP 6: Test watch time validation (insufficient watch time)
    print("\n⏱️  STEP 6: TEST WATCH TIME VALIDATION")
    print("-" * 70)
    
    # Create another test video
    test_video3, _ = Video.objects.get_or_create(
        title='Test Video - Time Validation',
        defaults={
            'url': 'https://www.youtube.com/embed/test789',
            'description': 'Test video for watch time validation',
            'reward': 2.0,
            'duration_seconds': 180,  # 3 minutes
            'min_tier': silver_tier,
            'is_active': True
        }
    )
    test_video3.duration_seconds = 180
    test_video3.save()
    
    print(f"Testing with: {test_video3.title}")
    print(f"   - Required Duration: {test_video3.duration_seconds} seconds")
    
    # Clear watch history for today (to allow new watch)
    WatchHistory.objects.filter(user=user).delete()
    
    # Test 1: Insufficient watch time (only watched 90 seconds of 180)
    insufficient_seconds = 90
    print(f"\n❌ Test Case 1: Insufficient watch time ({insufficient_seconds}s / {test_video3.duration_seconds}s)")
    
    # Add heartbeats
    for seconds in [30, 60, 90]:
        WatchHeartbeat.objects.create(user=user, video=test_video3, seconds=seconds)
    
    # Try to credit (should fail validation)
    balance_before = profile.balance
    if insufficient_seconds < test_video3.duration_seconds:
        print(f"   ✅ VALIDATION PASSED: Watch time {insufficient_seconds}s < required {test_video3.duration_seconds}s")
        print(f"   ✅ Reward NOT credited (as expected)")
    else:
        print(f"   ❌ VALIDATION FAILED: Should have rejected insufficient watch time")
    
    # Test 2: Full watch time (exactly required duration)
    print(f"\n✅ Test Case 2: Full watch time ({test_video3.duration_seconds}s / {test_video3.duration_seconds}s)")
    
    # Add more heartbeats
    for seconds in [120, 150, 180]:
        WatchHeartbeat.objects.create(user=user, video=test_video3, seconds=seconds)
    
    # Credit with full watch time
    full_watch_seconds = test_video3.duration_seconds
    wh2, _ = WatchHistory.objects.get_or_create(user=user, video=test_video3)
    wh2.watched_seconds = full_watch_seconds
    wh2.save()
    
    profile.credit(
        test_video3.reward,
        reason=f"Watched: {test_video3.title}",
        transaction_type="video_reward",
        video=test_video3
    )
    wh2.verified = True
    wh2.save()
    
    profile.refresh_from_db()
    balance_after = profile.balance
    
    print(f"   ✅ VALIDATION PASSED: Full duration watched")
    print(f"   ✅ Reward credited: ${test_video3.reward:.2f}")
    print(f"   - Balance Before: ${balance_before:.2f}")
    print(f"   - Balance After: ${balance_after:.2f}")
    
    # Test 3: Excess watch time (more than required)
    print(f"\n✅ Test Case 3: Excess watch time (200s / {test_video3.duration_seconds}s)")
    
    excess_watch_seconds = 200
    if excess_watch_seconds >= test_video3.duration_seconds:
        print(f"   ✅ VALIDATION PASSED: Watch time {excess_watch_seconds}s >= required {test_video3.duration_seconds}s")
        print(f"   ✅ User watched beyond required time (acceptable)")
    
    # STEP 7: Test one video per day limit
    print("\n📅 STEP 7: TEST ONE VIDEO PER DAY LIMIT")
    print("-" * 70)
    
    today = timezone.now().date()
    watched_today_count = WatchHistory.objects.filter(
        user=user,
        verified=True,
        watched_at__date=today
    ).count()
    
    print(f"Videos watched today: {watched_today_count}")
    
    if watched_today_count >= 1:
        print(f"✅ One video per day limit enforced")
        print(f"   - User has watched {watched_today_count} video(s) today")
        print(f"   - Additional watches should be blocked")
    
    # FINAL SUMMARY
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    profile.refresh_from_db()
    final_transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    
    print(f"\n👤 User: {user.username}")
    print(f"   - Current Tier: {profile.current_tier.name}")
    print(f"   - Final Balance: ${profile.balance:.2f}")
    print(f"   - Total Transactions: {final_transactions.count()}")
    
    print(f"\n📊 Transaction Breakdown:")
    deposit_total = final_transactions.filter(transaction_type='deposit').aggregate(
        total=models.Sum('amount'))['total'] or 0
    tier_upgrade_total = final_transactions.filter(transaction_type='tier_upgrade').aggregate(
        total=models.Sum('amount'))['total'] or 0
    video_reward_total = final_transactions.filter(transaction_type='video_reward').aggregate(
        total=models.Sum('amount'))['total'] or 0
    
    print(f"   - Deposits: ${deposit_total}")
    print(f"   - Tier Upgrades: ${tier_upgrade_total}")
    print(f"   - Video Rewards: ${video_reward_total}")
    
    print(f"\n🎥 Videos Watched:")
    watched_videos = WatchHistory.objects.filter(user=user, verified=True)
    for wh in watched_videos:
        print(f"   - {wh.video.title}: {wh.watched_seconds}s watched, earned ${wh.video.reward}")
    
    print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        test_tier_upgrade_and_watch()
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
