from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Split a string by the given argument"""
    if value:
        return value.split(arg)
    return []

@register.filter(name='mul')
def mul(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='divide')
def divide(value, arg):
    """Divide two numbers"""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter(name='youtube_embed')
def youtube_embed(url):
    """Convert any YouTube URL to embed format with proper parameters"""
    import re
    if not url:
        return url
    
    # Extract video ID from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        r'youtube-nocookie\.com\/embed\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # Use privacy-enhanced domain to avoid tracking issues and work better with ad blockers
            return f'https://www.youtube-nocookie.com/embed/{video_id}?autoplay=0&rel=0&modestbranding=1&playsinline=1'
    
    # Not a YouTube URL, return as is
    return url

@register.filter(name='youtube_id')
def youtube_id(url):
    """Extract YouTube video ID from any YouTube URL format"""
    import re
    if not url:
        return ''
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return ''

@register.filter(name='youtube_thumbnail')
def youtube_thumbnail(url, quality='maxresdefault'):
    """Get YouTube thumbnail URL. Quality options: maxresdefault, hqdefault, mqdefault, sddefault"""
    video_id = youtube_id(url)
    if video_id:
        return f'https://img.youtube.com/vi/{video_id}/{quality}.jpg'
    return ''


@register.filter(name='get_reward_for_tier')
def get_reward_for_tier(video, tier):
    """Get the reward amount for a specific tier for this video"""
    if not tier:
        return 0
    
    try:
        from videos.models import VideoTierPrice
        tier_price = VideoTierPrice.objects.filter(video=video, tier=tier).first()
        if tier_price:
            return tier_price.reward
    except Exception:
        pass
    
    # Fallback to video's default reward
    return video.reward if hasattr(video, 'reward') else 0


@register.simple_tag
def get_video_reward(video, user_tier=None):
    """Get the appropriate reward for a video based on user's tier"""
    if not user_tier:
        # Return the default reward or 0
        return video.reward if hasattr(video, 'reward') else 0
    
    try:
        from videos.models import VideoTierPrice
        # Get tier-specific reward
        tier_price = VideoTierPrice.objects.filter(video=video, tier=user_tier).first()
        if tier_price:
            return f"{tier_price.reward:.2f}"
        
        # If no specific tier price, return default
        return f"{video.reward:.2f}" if hasattr(video, 'reward') else "0.00"
    except Exception:
        return "0.00"
