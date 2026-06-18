from pathlib import Path
from datetime import timedelta
import os
from decouple import AutoConfig, Csv, RepositoryEnv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

config = AutoConfig(search_path=BASE_DIR)

SECRET_KEY = config('SECRET_KEY',
    default='django-insecure-change-this-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

# Railway / production hosts
_default_hosts = 'localhost,127.0.0.1,.up.railway.app,.railway.app' if not DEBUG else '*'
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=_default_hosts, cast=Csv())

RAILWAY_PUBLIC_DOMAIN = config('RAILWAY_PUBLIC_DOMAIN', default='')
if RAILWAY_PUBLIC_DOMAIN and RAILWAY_PUBLIC_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RAILWAY_PUBLIC_DOMAIN]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'cloudinary',
    'cloudinary_storage',
    'users',
    'jobs',
    'chat',
    'notifications',
    'admin_panel',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gigapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'gigapp.asgi.application'
WSGI_APPLICATION = 'gigapp.wsgi.application'


# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = config('DATABASE_URL',
    default=f'sqlite:///{BASE_DIR}/db.sqlite3')
_db_url = DATABASE_URL
DATABASES = {
    'default': dj_database_url.parse(
        _db_url,
        conn_max_age=600,
        ssl_require=(
            not DEBUG
            and ('postgres' in _db_url or 'postgresql' in _db_url)
        ),
    )
}

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:8080,http://127.0.0.1:8080',
    cast=Csv(),
)

# ── JWT ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# ── Cloudinary ────────────────────────────────────────────────────────────────
import cloudinary


def _load_cloudinary_storage():
    url = config('CLOUDINARY_URL', default='').strip()
    if url:
        cloudinary.config(secure=True)
        cloudinary.config_from_url(url)
        cfg = cloudinary.config()
        return {
            'CLOUD_NAME': cfg.cloud_name or '',
            'API_KEY': cfg.api_key or '',
            'API_SECRET': cfg.api_secret or '',
        }

    name = config('CLOUDINARY_CLOUD_NAME', default='')
    key = config('CLOUDINARY_API_KEY', default='')
    secret = config('CLOUDINARY_API_SECRET', default='')
    cloudinary.config(
        cloud_name=name,
        api_key=key,
        api_secret=secret,
        secure=True,
    )
    return {
        'CLOUD_NAME': name,
        'API_KEY': key,
        'API_SECRET': secret,
    }


CLOUDINARY_STORAGE = _load_cloudinary_storage()
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_CREDENTIALS = os.path.join(BASE_DIR, 'firebase-credentials.json')
FIREBASE_CREDENTIALS_JSON = config('FIREBASE_CREDENTIALS_JSON', default='')

# ── Channels / Redis ──────────────────────────────────────────────────────────
REDIS_URL = config('REDIS_URL', default='')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
    EMAIL_TIMEOUT = 15
    EMAIL_CONFIGURED = True
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@joblink.local'
    EMAIL_CONFIGURED = False

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:8080')

# ── SMS ───────────────────────────────────────────────────────────────────────
SMS_PROVIDER = config('SMS_PROVIDER', default='').lower()
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')
AFRICASTALKING_SENDER = config('AFRICASTALKING_SENDER', default='JobLink')
AFRICASTALKING_SANDBOX = config('AFRICASTALKING_SANDBOX', default=True, cast=bool)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_FROM_NUMBER = config('TWILIO_FROM_NUMBER', default='')

# ── MTN MoMo ──────────────────────────────────────────────────────────────────
MTN_MOMO_API_USER = config('MTN_MOMO_API_USER', default='')
MTN_MOMO_API_KEY = config('MTN_MOMO_API_KEY', default='')
MTN_MOMO_SUBSCRIPTION_KEY = config('MTN_MOMO_SUBSCRIPTION_KEY', default='')
MTN_MOMO_ENVIRONMENT = config('MTN_MOMO_ENVIRONMENT', default='sandbox')

# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if DEBUG:
    STATICFILES_STORAGE = (
        'whitenoise.storage.CompressedManifestStaticFilesStorage')
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'

# ── General ───────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kigali'
USE_I18N = True
USE_TZ = True

# ── CSRF & Cookies ────────────────────────────────────────────────────────────
_default_csrf = 'http://localhost:8080,http://127.0.0.1:8080'
if RAILWAY_PUBLIC_DOMAIN:
    _default_csrf = f'https://{RAILWAY_PUBLIC_DOMAIN},{_default_csrf}'
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS', default=_default_csrf, cast=Csv())
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config(
        'SECURE_SSL_REDIRECT', default=False, cast=bool)