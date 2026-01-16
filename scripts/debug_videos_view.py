import os, sys, pathlib, traceback
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
import django
django.setup()
from django.test import RequestFactory
from django.contrib.auth.models import User
from videos.models import Tier
from django.core.files.uploadedfile import SimpleUploadedFile
import admin_panel.views as vviews

factory = RequestFactory()
user = User.objects.get(username='admin')

# ensure tier
tier, _ = Tier.objects.get_or_create(name='DebugTier', defaults={'price':1.0})

# create request
content = b"\x00\x00dummy"
file = SimpleUploadedFile('test.mp4', content, content_type='video/mp4')
post = {
    'title': 'Debug Upload',
    'duration': '3',
    f'tier_{tier.id}': 'on',
    f'reward_{tier.id}': '0.5',
    'is_active': 'on'
}
req = factory.post('/admin/videos/', data=post, FILES={'video_file': file})
req.user = user
# Attach messages storage (RequestFactory doesn't apply middleware)
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.fallback import FallbackStorage
# Attach a session and messages storage (RequestFactory doesn't apply middleware)
req.session = SessionStore()
req._messages = FallbackStorage(req)

try:
    resp = vviews.videos_list(req)
    print('Response status:', resp.status_code)
    print(resp.content[:1000])
except Exception as e:
    print('Exception during view call:')
    traceback.print_exc()
