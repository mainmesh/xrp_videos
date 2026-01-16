import os
import sys
import pathlib
# Ensure project root is on sys.path so `xrp_site` module can be imported
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()
from django.contrib.auth.models import User
supers = [(u.username, u.email, u.is_staff, u.is_superuser) for u in User.objects.filter(is_superuser=True)]
print(supers)
