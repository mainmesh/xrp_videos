import os
import sys
import pathlib
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from videos.models import Tier, Video

client = Client()

# Ensure admin exists
try:
    admin = User.objects.get(username='admin')
except User.DoesNotExist:
    print('admin user not found')
    sys.exit(1)

logged_in = client.login(username='admin', password='admin123')
print('logged_in=', logged_in)
if not logged_in:
    print('Failed to login as admin')
    sys.exit(1)

# Ensure at least one tier exists
tier, created = Tier.objects.get_or_create(name='TestTier', defaults={'price': 1.0})
print('tier id=', tier.id, 'created=', created)

# Create a tiny dummy video file
content = b"\x00\x00\x00dummyvideo"
uploaded = SimpleUploadedFile('test.mp4', content, content_type='video/mp4')

post_data = {
    'title': 'Automated Test Video',
    'duration': '5',
    # mark tier selected
    f'tier_{tier.id}': 'on',
    f'reward_{tier.id}': '0.50',
    'is_active': 'on'
}

files = {'video_file': uploaded}

response = client.post('/admin/videos/', post_data, files=files, follow=True)
print('POST status code:', response.status_code)

# Check if video created
created_videos = Video.objects.filter(title='Automated Test Video')
print('created_videos count=', created_videos.count())
for v in created_videos:
    print('Video:', v.id, v.title, v.url)

# Print any messages in response (rendered HTML) for debugging
content = response.content.decode('utf-8')[:2000]
print('Response snippet:', content)
