from django.urls import path, include
from core.views import home, about, tiers, inbox, view_message, compose_message, chatbot
from accounts.views import stripe_webhook
from django.views.generic.base import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

urlpatterns = [
    path('admin/', include('admin_panel.urls')),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('tiers/', tiers, name='tiers'),
    # Messaging
    path('inbox/', inbox, name='inbox'),
    path('message/<int:message_id>/', view_message, name='view_message'),
    path('compose/', compose_message, name='compose_message'),
    # Chatbot
    path('api/chatbot/', chatbot, name='chatbot'),
    # Stripe webhook
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    # Django auth (login/logout/password management)
    path('accounts/', include('django.contrib.auth.urls')),
    # app-specific account urls (dashboard, register, etc.)
    path('accounts/', include('accounts.urls')),
    path('videos/', include('videos.urls')),
    path('referrals/', include('referrals.urls')),
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('images/favicon.ico'))),
]