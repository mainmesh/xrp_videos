"""Vercel Python entrypoint for Django.

Vercel's Python runtime requires a top-level `app` (ASGI/Flask) or
`application` (Django WSGI) variable. We expose Django's WSGI callable as
`application` and let boot errors propagate (they get logged by Vercel).

The legacy file also wrapped init in try/except, which left `app` undefined
when boot failed and made Vercel error with: "Could not find a top-level
'app', 'application', or 'handler' in api/index.py". This is the fix.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

# Top-level `application` is required by Vercel for Django.
application = get_wsgi_application()

# Backwards-compat alias for any code/imports still expecting `app`.
app = application