from django.contrib.auth.models import User
from django.db import migrations

from admin_panel.permissions import PERMISSIONS


def seed(apps, schema_editor):
    AdminPermission = apps.get_model('admin_panel', 'AdminPermission')
    AdminProfile = apps.get_model('admin_panel', 'AdminProfile')
    for key, label in PERMISSIONS.items():
        AdminPermission.objects.update_or_create(key=key, defaults={'label': label})
    for u in User.objects.all():
        if u.is_superuser:
            role = 'super_admin'
        elif u.is_staff:
            role = 'admin'
        else:
            continue
        AdminProfile.objects.update_or_create(user_id=u.id, defaults={'role': role})


def unseed(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('admin_panel', '0004_adminpermission_adminprofile_auditlog'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]