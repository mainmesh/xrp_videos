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
        r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # Add parameters to enable autoplay, controls, and allow embedding
            return f'https://www.youtube.com/embed/{video_id}?enablejsapi=1&origin=https://xrp-videos.vercel.app&widget_referrer=https://xrp-videos.vercel.app'
    
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
