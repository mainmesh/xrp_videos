"""WSGI entrypoint with additional boot diagnostics for Vercel.

If Django fails during initialization, the stacktrace will be printed
and an optional /tmp/vercel_boot_error.log will be written.
"""
import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

try:
	from django.core.wsgi import get_wsgi_application
	application = get_wsgi_application()
except Exception as e:
	tb = traceback.format_exc()
	msg = f"[VERCEL_BOOT_ERROR] {e}\n{tb}"
	print(msg, file=sys.stdout)
	print(msg, file=sys.stderr)
	try:
		with open('/tmp/vercel_boot_error.log', 'w', encoding='utf-8') as f:
			f.write(msg)
	except Exception:
		pass
	raise

# Vercel compatibility: expose 'app' variable
app = application
app = application  # For Vercel Python runtime compatibility
