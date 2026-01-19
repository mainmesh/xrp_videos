from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Video, WatchHistory, Tier
from .models import WatchHeartbeat
from accounts.models import Profile
from referrals.models import ReferralBonus
from django.db import transaction
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required


def video_list(request):
    """List videos the user has access to based on their tier."""
    videos = Video.objects.filter(is_active=True)
    
    # If logged in, filter by tier access
    user_tier = None
    if request.user.is_authenticated:
        try:
            user_tier = request.user.profile.current_tier
        except (AttributeError, Profile.DoesNotExist):
            user_tier = None
        
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

    # Geo-filter: try to infer country from headers set by CDNs or proxies
    def _infer_country(req):
        headers = [
            'HTTP_CF_IPCOUNTRY',
            'HTTP_X_COUNTRY',
            'HTTP_GEOIP_COUNTRY_CODE',
            'GEOIP_COUNTRY_CODE',
            'HTTP_X_APPENGINE_COUNTRY',
        ]
        for h in headers:
            val = req.META.get(h)
            if val:
                return val.strip().upper()
        # fallback to user profile if available
        try:
            if req.user.is_authenticated:
                prof = getattr(req.user, 'profile', None)
                if prof is not None and hasattr(prof, 'country'):
                    return (prof.country or '').strip().upper()
        except Exception:
            pass
        return None

    country = _infer_country(request)
    # if country inferred, filter videos by availability
    if country:
        videos = [v for v in videos if v.matches_country(country)]

    # Available filter: show only unwatched videos for logged in users
    show_available = request.GET.get('available') == '1'
    if show_available and request.user.is_authenticated:
        watched_vid_ids = WatchHistory.objects.filter(user=request.user, verified=True).values_list('video_id', flat=True)
        videos = [v for v in videos if v.id not in set(watched_vid_ids)]
    
    context = {
        "videos": videos,
        "user_tier": user_tier,
        "all_tiers": Tier.objects.all().order_by('price')
    }
    return render(request, "videos/list.html", context)


def video_detail(request, pk):
    """Show video detail, checking tier access."""
    video = get_object_or_404(Video, pk=pk)
    
    # Check tier access
    has_access = False
    user_tier = None
    
    if video.min_tier is None:
        # Free video, everyone can access
        has_access = True
    elif request.user.is_authenticated:
        try:
            user_tier = request.user.profile.current_tier
        except (AttributeError, Profile.DoesNotExist):
            user_tier = None
        
        if user_tier and user_tier.price >= video.min_tier.price:
            has_access = True
    
    context = {
        "video": video,
        "has_access": has_access,
        "required_tier": video.min_tier,
        "user_tier": user_tier
    }
    return render(request, "videos/detail.html", context)



@login_required
@require_http_methods(["POST"])
@transaction.atomic
def heartbeat(request):
    """Receive periodic heartbeats from the client while watching.
    Expects JSON: {"seconds": <int>, "video_id": <int>}.
    Records a WatchHeartbeat row for the user/video.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = {}

    seconds = int(payload.get('seconds', 0) or 0)
    video_id = payload.get('video_id')
    if not video_id:
        return JsonResponse({"error": "missing_video_id"}, status=400)

    try:
        video = Video.objects.get(pk=int(video_id))
    except Exception:
        return JsonResponse({"error": "invalid_video"}, status=400)

    # create heartbeat record (do not fail client on DB errors)
    try:
        WatchHeartbeat.objects.create(user=request.user, video=video, seconds=seconds)
    except Exception:
        return JsonResponse({"status": "error"}, status=500)

    return JsonResponse({"status": "ok"})



@staff_member_required
def video_upload(request):
    """Simple staff-only uploader: accepts a file upload or a URL and creates a Video.
    This is intentionally permissive so you can add videos quickly.
    """
    if request.method == 'POST':
        title = request.POST.get('title') or 'Untitled'
        file_obj = request.FILES.get('file')
        url = (request.POST.get('url') or '').strip()
        duration_minutes = request.POST.get('duration_minutes')

        if not file_obj and not url:
            return render(request, 'videos/upload.html', { 'error': 'Provide a file or a URL', 'title': title, 'url': url })

        video = Video(title=title)

        # Save uploaded file to MEDIA via default storage
        if file_obj:
            save_path = f'videos/uploads/{file_obj.name}'
            try:
                path = default_storage.save(save_path, ContentFile(file_obj.read()))
                media_url = (settings.MEDIA_URL.rstrip('/') + '/' + path).replace('\\', '/')
                video.url = media_url
            except Exception:
                video.url = ''

        # Normalize common YouTube URLs to embed form
        if not video.url and url:
            normalized = url
            try:
                if 'youtube.com/watch' in url and 'embed' not in url:
                    import re
                    m = re.search(r'v=([^&]+)', url)
                    if m:
                        vid = m.group(1)
                        normalized = f'https://www.youtube.com/embed/{vid}'
                elif 'youtu.be/' in url:
                    vid = url.rstrip('/').split('/')[-1]
                    normalized = f'https://www.youtube.com/embed/{vid}'
            except Exception:
                normalized = url
            video.url = normalized

        # Duration (minutes) -> seconds
        if duration_minutes:
            try:
                video.duration_seconds = int(float(duration_minutes) * 60)
            except Exception:
                pass

        # Try to save the video record
        video.created_by = request.user
        video.save()

        return redirect('videos:detail', pk=video.pk)

    return render(request, 'videos/upload.html')


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def watch_complete(request, pk):
    """Called by frontend when a user finishes watching a video.
    Credits reward and referral bonus if applicable.
    Prevents double-crediting by checking WatchHistory.verified flag.
    Validates that user watched minimum duration (80% of video).
    """
    video = get_object_or_404(Video, pk=pk)
    
    # Get watched seconds from POST data
    watched_seconds = int(request.POST.get('watched_seconds', 0))
    
    # Validate minimum watch duration (80% of video duration)
    min_watch_seconds = int(video.duration_seconds * 0.8)
    if watched_seconds < min_watch_seconds:
        return JsonResponse({
            "error": "insufficient_watch_time",
            "message": f"Please watch at least {min_watch_seconds} seconds (80% of video)",
            "required": min_watch_seconds,
            "watched": watched_seconds
        }, status=400)

    # Require at least 3 heartbeats recorded for this user/video in recent session
    recent_heartbeats = WatchHeartbeat.objects.filter(user=request.user, video=video).order_by('-created_at')[:10]
    if recent_heartbeats.count() < 3:
        return JsonResponse({"error": "insufficient_heartbeats", "message": "Playback not validated by server heartbeats."}, status=400)
    
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
    wh.watched_seconds = watched_seconds  # Use actual watched time from client
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
