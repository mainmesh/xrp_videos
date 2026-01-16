import os,sys,pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','xrp_site.settings')
import django
django.setup()
from videos.models import Video
qs = Video.objects.filter(title='Debug Upload')
print('count', qs.count())
for v in qs:
    print(v.id, v.title, v.url, v.min_tier)
