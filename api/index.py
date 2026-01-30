# Vercel Python entrypoint for Django
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
app = get_wsgi_application()
