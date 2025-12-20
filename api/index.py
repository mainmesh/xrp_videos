import os
import sys
from django.core.wsgi import get_wsgi_application
from vercel_wsgi import handle_request

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

application = get_wsgi_application()

# Vercel entry point
def handler(request, context):
    return handle_request(application, request, context)
