#!/usr/bin/env python
"""
Test video watching and earning flow
"""
import os
import django

# Force SQLite for local testing
os.environ['DATABASE_URL'] = ''
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from videos.models import Video, WatchHistory, VideoTierPrice
from django.utils import timezone

print("=" * 70)
print("VIDEO WATCHING & EARNING TEST")
print("=" * 70)

# Get the test user
try:
    user = User.objects.get(username='newuser')
    profile = user.profile
    print(f"\n✓ Found test user: {user.username}")
    print(f"  - Current Tier: {profile.current_tier.name if profile.current_tier else 'Free'}")
    print(f"  - Current Balance: ${profile.balance}")
except User.DoesNotExist:
    print("❌ Test user 'newuser' not found. Please run test_complete_user_flow.py first")
    exit(1)

# Get available videos
available_videos = Video.objects.filter(
    is_active=True,
    min_tier__price__lte=profile.current_tier.price if profile.current_tier else 0
).order_by('-created_at')

print(f"\n✓ Available videos: {available_videos.count()}")

# Watch first video
if available_videos.count() > 0:
    video = available_videos.first()
    print(f"\n📹 WATCHING VIDEO: {video.title}")
    print(f"   - Duration: {video.duration_minutes} minutes")
    print(f"   - Min Tier: {video.min_tier.name if video.min_tier else 'Free'}")
    
    # Get reward for user's tier
    tier_price = VideoTierPrice.objects.filter(
        video=video,
        tier=profile.current_tier
    ).first()
    
    if tier_price:
        reward_amount = tier_price.reward
        print(f"   - Reward for {profile.current_tier.name}: ${reward_amount}")
        
        # Check if already watched
        already_watched = WatchHistory.objects.filter(
            user=user,
            video=video
        ).exists()
        
        if already_watched:
            print(f"\n⚠️  You've already watched this video!")
            watch_count = WatchHistory.objects.filter(user=user, video=video).count()
            print(f"   - Watch count: {watch_count}")
        else:
            # Create watch history
            balance_before = profile.balance
            
            watch = WatchHistory.objects.create(
                user=user,
                video=video,
                watched_at=timezone.now()
            )
            
            # Credit reward to user
            profile.balance = float(profile.balance) + float(reward_amount)
            profile.save()
            
            print(f"\n✅ VIDEO WATCHED & REWARDED!")
            print(f"   - Balance Before: ${balance_before}")
            print(f"   - Reward Earned: ${reward_amount}")
            print(f"   - Balance After: ${profile.balance}")
            print(f"   - Watch ID: {watch.id}")
    else:
        print(f"\n⚠️  No tier pricing found for {profile.current_tier.name}")
else:
    print("\n⚠️  No videos available")

# Summary of user's watch history
print(f"\n" + "=" * 70)
print("USER WATCH HISTORY")
print("=" * 70)

watch_history = WatchHistory.objects.filter(user=user).order_by('-watched_at')
print(f"\nTotal videos watched: {watch_history.count()}")

for watch in watch_history:
    tier_price = VideoTierPrice.objects.filter(
        video=watch.video,
        tier=profile.current_tier
    ).first()
    reward = tier_price.reward if tier_price else 0
    
    print(f"\n📹 {watch.video.title}")
    print(f"   - Watched: {watch.watched_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - Duration: {watch.video.duration_minutes} minutes")
    print(f"   - Earned: ${reward}")

# Final balance
profile.refresh_from_db()
print(f"\n" + "=" * 70)
print(f"💰 FINAL BALANCE: ${profile.balance}")
print(f"🎯 CURRENT TIER: {profile.current_tier.name if profile.current_tier else 'Free'}")
print("=" * 70)

print(f"\n✅ Test complete! Login at http://127.0.0.1:8000/accounts/login/")
print(f"   Username: newuser")
print(f"   Password: newuser123")
