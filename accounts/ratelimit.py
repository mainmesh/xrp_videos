"""Simple cache-based rate limiter for login / register / password reset.

Uses Django's cache framework so we don't add any new dependencies. Counters
are scoped by (action, ip) or (action, ip + username) so an attacker rotating
usernames still gets IP-throttled.
"""
from __future__ import annotations

from django.core.cache import cache
from django.utils import timezone


def _key(action: str, scope: str) -> str:
    return f"rl:{action}:{scope}"


def is_rate_limited(action: str, scope: str, limit: int, window_seconds: int) -> bool:
    """Return True if `scope` has exceeded `limit` requests in the rolling
    `window_seconds`. The first request that hits the limit is allowed; the
    *next* one within the window is rejected.
    """
    key = _key(action, scope)
    count = cache.get(key, 0)
    return count >= limit


def record_attempt(action: str, scope: str, window_seconds: int) -> int:
    """Increment the counter for `scope` and return the new count. The window
    is reset on each call so a busy attacker keeps hitting the limit until the
    earliest increment in the window expires.
    """
    key = _key(action, scope)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window_seconds)
        count = 1
    # Sliding window: bump expiry on each hit so an idle bucket eventually clears.
    cache.expire(key, window_seconds) if hasattr(cache, 'expire') else None
    return count


def client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def captcha_required(action: str, request, username: str | None = None) -> bool:
    """Captcha is required once failed attempts exceed the configured
    threshold *or* once the IP is already rate-limited."""
    ip_scope = f"ip:{client_ip(request)}"
    if is_rate_limited(action, ip_scope, limit=20, window_seconds=600):
        return True
    if username:
        un_scope = f"user:{username}"
        if is_rate_limited(f"{action}:user", un_scope, limit=5, window_seconds=900):
            return True
    return False


def make_math_captcha() -> dict:
    """Return a tiny math problem (sum of two small ints)."""
    from random import randint
    a, b = randint(2, 9), randint(2, 9)
    return {'a': a, 'b': b, 'question': f'What is {a} + {b}?'}


def now():
    return timezone.now()