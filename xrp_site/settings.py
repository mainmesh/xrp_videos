import os
from decouple import config, Csv
import dj_database_url

# Secret Key
SECRET_KEY = config('SECRET_KEY', default='dummy-key-change-this-in-production')

# Debug Mode
# Default to True for local development when env var is not set.
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed Hosts

# Add Vercel default host if running on Vercel
VERCEL_URL = os.environ.get('VERCEL_URL')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,xrp-videos.onrender.com', cast=Csv())
if VERCEL_URL:
    ALLOWED_HOSTS += [VERCEL_URL, '.vercel.app']

INSTALLED_APPS=['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','core','accounts.apps.AccountsConfig','videos','referrals','admin_panel.apps.AdminPanelConfig']

MIDDLEWARE=[
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF='xrp_site.urls'
TEMPLATES=[{
 'BACKEND':'django.template.backends.django.DjangoTemplates',
 'DIRS':['templates'],
 'APP_DIRS':True,
 'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.context_processors.unread_notifications']}
}]
WSGI_APPLICATION='xrp_site.wsgi.application'

# Database Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
        }
    }

# Static files configuration

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
WHITENOISE_MANIFEST_STRICT = False
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (uploaded by admin)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security Settings for Production
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Stripe settings (set via env vars in production)
STRIPE_API_KEY = config('STRIPE_API_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Login URLs
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='XRPPrime <noreply@xrpprime.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
