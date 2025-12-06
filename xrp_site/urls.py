from django.urls import path, include
from core.views import home, about, tiers
from accounts.views import stripe_webhook
from django.contrib import admin

# Import custom admin configuration
from . import admin as custom_admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-panel/', include('admin_panel.urls')),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('tiers/', tiers, name='tiers'),
    # Stripe webhook
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    # Django auth (login/logout/password management)
    path('accounts/', include('django.contrib.auth.urls')),
    # app-specific account urls (dashboard, register, etc.)
    path('accounts/', include('accounts.urls')),
    path('videos/', include('videos.urls')),
    path('referrals/', include('referrals.urls')),
]