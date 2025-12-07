from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Creates or resets admin superuser with username=admin and password=admin123'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin123'
        email = 'admin@xrpvideos.com'
        
        try:
            # Try to get existing admin user
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Admin user "{username}" password reset successfully!'))
        except User.DoesNotExist:
            # Create new admin user
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Admin user "{username}" created successfully!'))
        
        self.stdout.write(self.style.SUCCESS(f'  Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'  Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'  Staff: {user.is_staff}'))
        self.stdout.write(self.style.SUCCESS(f'  Superuser: {user.is_superuser}'))
