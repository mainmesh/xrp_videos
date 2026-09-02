"""Audit log helper. Call `audit(...)` from views / services when performing
sensitive actions. Safe to call from request handlers; failures are swallowed
so they never break the user-visible flow.
"""
from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from .models import AuditLog


def _client_ip(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None


def audit(
    action: str,
    *,
    request: HttpRequest | None = None,
    actor=None,
    target_type: str = '',
    target_id: str = '',
    description: str = '',
    before: Any = None,
    after: Any = None,
) -> AuditLog | None:
    """Append an audit log entry. Never raises."""
    try:
        entry = AuditLog.objects.create(
            actor=actor if (actor and getattr(actor, 'is_authenticated', False)) else None,
            action=action[:64],
            target_type=target_type[:64],
            target_id=str(target_id)[:64] if target_id else '',
            description=description[:255],
            before=before,
            after=after,
            ip_address=_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '') if request else '')[:255],
        )
        return entry
    except Exception:
        # Never break the user-visible flow because audit failed.
        return None


def diff(before: dict | None, after: dict | None) -> dict:
    """Produce a minimal {field: [old, new]} diff for two JSON-able dicts."""
    before = before or {}
    after = after or {}
    keys = set(before.keys()) | set(after.keys())
    return {
        k: [before.get(k), after.get(k)]
        for k in sorted(keys)
        if before.get(k) != after.get(k)
    }