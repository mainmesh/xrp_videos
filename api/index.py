"""Vercel Python entrypoint for Django with boot-time diagnostics.

This wrapper prints any import/initialization exceptions to stdout/stderr
and writes a small log file to /tmp/vercel_boot_error.log so runtime errors
are easier to inspect in Vercel logs.
"""
import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

try:
	from django.core.wsgi import get_wsgi_application
	app = get_wsgi_application()
except Exception as e:
	tb = traceback.format_exc()
	msg = f"[VERCEL_BOOT_ERROR] {e}\n{tb}"
	# Print to stdout/stderr so Vercel captures it
	print(msg, file=sys.stdout)
	print(msg, file=sys.stderr)
	# Try to persist to /tmp for easier retrieval (read-only on some platforms)
	try:
		with open('/tmp/vercel_boot_error.log', 'w', encoding='utf-8') as f:
			f.write(msg)
	except Exception:
		pass
	# Re-raise so the process fails visibly
	raise
