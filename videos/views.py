from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Video, WatchHistory, Tier
from accounts.models import Profile
from referrals.models import ReferralBonus
from django.db import transaction


def video_list(request):
    """List videos the user has access to based on their tier."""
    videos = Video.objects.filter(is_active=True)
    
    # If logged in, filter by tier access
    if request.user.is_authenticated:
        user_tier = request.user.profile.current_tier
        if user_tier:
            # Show videos that don't require a tier OR require this tier or lower
            videos = videos.filter(
                Q(min_tier__isnull=True) |  # Free videos
                Q(min_tier=user_tier) |     # This exact tier
                Q(min_tier__price__lte=user_tier.price)  # Lower priced tiers
            )
        else:
            # Only free videos
            videos = videos.filter(min_tier__isnull=True)
    else:
        # Anonymous users only see free videos
        videos = videos.filter(min_tier__isnull=True)
    
    context = {
        "videos": videos,
        "user_tier": request.user.profile.current_tier if request.user.is_authenticated else None,
        "all_tiers": Tier.objects.all().order_by('price')
    }
    return render(request, "videos/list.html", context)


def video_detail(request, pk):
    """Show video detail, checking tier access."""
    video = get_object_or_404(Video, pk=pk)
    
    # Check tier access
    has_access = False
    if video.min_tier is None:
        # Free video, everyone can access
        has_access = True
    elif request.user.is_authenticated:
        user_tier = request.user.profile.current_tier
        if user_tier and user_tier.price >= video.min_tier.price:
            has_access = True
    
    context = {
        "video": video,
        "has_access": has_access,
        "required_tier": video.min_tier,
        "user_tier": request.user.profile.current_tier if request.user.is_authenticated else None
    }
    return render(request, "videos/detail.html", context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def watch_complete(request, pk):
    """Called by frontend when a user finishes watching a video.
    Credits reward and referral bonus if applicable.
    Prevents double-crediting by checking WatchHistory.verified flag.
    """
    video = get_object_or_404(Video, pk=pk)
    
    # Check tier access
    user_tier = request.user.profile.current_tier
    if video.min_tier:
        if not user_tier or user_tier.price < video.min_tier.price:
            return JsonResponse({"error": "insufficient_tier"}, status=403)
    
    # Check if already verified (prevent double-crediting)
    existing_wh = WatchHistory.objects.filter(user=request.user, video=video, verified=True).first()
    if existing_wh:
        return JsonResponse({"error": "already_credited"}, status=400)

    # Determine reward amount: prefer tier-specific reward if configured
    reward_to_credit = float(video.reward or 0)
    try:
        user_tier = request.user.profile.current_tier
        if user_tier:
            # try exact tier first
            vtp = video.tier_prices.filter(tier=user_tier).first()
            if not vtp:
                # try the highest tier price that the user qualifies for (tier price <= user tier price)
                vtp = video.tier_prices.filter(tier__price__lte=user_tier.price).select_related('tier').order_by('-tier__price').first()
            if vtp:
                reward_to_credit = float(vtp.reward)
    except Exception:
        # fallback to video.reward if any errors
        reward_to_credit = float(video.reward or 0)

    # Create or update watch history (mark verified only after successful credit)
    wh, created = WatchHistory.objects.get_or_create(user=request.user, video=video)
    wh.watched_seconds = video.duration_seconds
    wh.save()

    # Credit user profile
    try:
        profile = request.user.profile
        profile.credit(reward_to_credit, reason=f"watch:{video.id}")
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Credit referral bonus (10% to referrer) if applicable
    try:
        referred_by = request.user.profile.referred_by
        if referred_by:
            bonus_amount = round(reward_to_credit * 0.10, 4)
            ReferralBonus.objects.create(to_user=referred_by, from_user=request.user, amount=bonus_amount)
            # credit referrer's profile
            try:
                ref_profile = referred_by.profile
                ref_profile.credit(bonus_amount, reason=f"referral:{request.user.id}")
            except Exception:
                pass
    except Exception:
        pass

    # mark watch as verified after successful crediting
    wh.verified = True
    wh.save()

    return JsonResponse({"status": "credited", "reward": reward_to_credit})
