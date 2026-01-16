import os
import sys
import pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
import django
django.setup()
from django.test import Client
from django.contrib.auth.models import User

c = Client()
path = '/accounts/profile/'
print('GET as anonymous ->')
resp = c.get(path)
print('status:', resp.status_code)
if hasattr(resp, 'redirect_chain'):
	print('redirect chain:', resp.redirect_chain)
print('content snippet:', (resp.content.decode('utf-8')[:1000] if resp.content else '<empty>'))

# Try as admin
print('\nLogging in as admin...')
logged = c.login(username='admin', password='admin123')
print('login ok:', logged)
resp2 = c.get(path)
print('GET as admin -> status:', resp2.status_code)
if hasattr(resp2, 'redirect_chain'):
	print('redirect chain:', resp2.redirect_chain)
print('content snippet:', (resp2.content.decode('utf-8')[:1000] if resp2.content else '<empty>'))
