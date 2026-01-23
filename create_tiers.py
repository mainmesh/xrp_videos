"""
Quick script to create default tiers in the database.
Run this after fixing database connection issues.

Usage:
    python create_tiers.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xrp_site.settings')
django.setup()

from videos.models import Tier

def create_default_tiers():
    """Create Bronze, Silver, and Gold tiers if they don't exist."""
    default_tiers = [
        {'name': 'Bronze', 'price': 0.0},
        {'name': 'Silver', 'price': 10.0},
        {'name': 'Gold', 'price': 25.0},
    ]

    print("Creating default tiers...")
    print("-" * 50)

    created_count = 0
    for tier_data in default_tiers:
        tier, created = Tier.objects.get_or_create(
            name=tier_data['name'],
            defaults={'price': tier_data['price']}
        )
        if created:
            created_count += 1
            print(f"✓ Created tier: {tier.name} (${tier.price})")
        else:
            print(f"⚠ Tier already exists: {tier.name} (${tier.price})")

    print("-" * 50)
    if created_count > 0:
        print(f"\n✓ Successfully created {created_count} tier(s)!")
    else:
        print("\n✓ All default tiers already exist.")

if __name__ == '__main__':
    try:
        create_default_tiers()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. Database is accessible")
        print("2. Migrations are run: python manage.py migrate")
        print("3. Required packages are installed: pip install -r requirements.txt")
