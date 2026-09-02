from django.urls import path, include
from core.views import home, about, tiers, chatbot
from accounts.views import stripe_webhook
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('admin/', include('admin_panel.urls')),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('tiers/', tiers, name='tiers'),
    # Chatbot
    path('api/chatbot/', chatbot, name='chatbot'),
    # Stripe webhook
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    # App-specific account URLs first so our custom login/logout win.
    path('accounts/', include('accounts.urls')),
    # Django contrib auth URLs for the remaining defaults (password_change etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    path('videos/', include('videos.urls')),
    path('referrals/', include('referrals.urls')),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('images/favicon.ico'))),
]