import os, sys, pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','xrp_site.settings')
import django
django.setup()
from django.test import Client
from videos.models import Tier, Video
c=Client()
print('login', c.login(username='admin',password='admin123'))
Tier.objects.get_or_create(name='TestTier2', defaults={'price':5.0})
tier = Tier.objects.get(name='TestTier2')
post = {'title':'URL Test Video','duration':'10', f'tier_{tier.id}':'on', f'reward_{tier.id}':'0.25', 'url':'https://www.youtube.com/embed/dQw4w9WgXcQ', 'is_active':'on'}
resp = c.post('/admin/videos/', post, follow=True)
print('status', resp.status_code)
print(resp.content.decode()[:1000])
print('videos count', Video.objects.filter(title='URL Test Video').count())
