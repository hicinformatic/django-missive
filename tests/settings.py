"""
Django settings for testing django-missive
"""

import os
from pathlib import Path

# Charger les variables d'environnement depuis .env si disponible
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Variables d'environnement chargées depuis {env_path}")
except ImportError:
    print("⚠️ python-dotenv non installé. Installez-le avec: pip install python-dotenv")
    pass

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-django-missive")

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "missive",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",  # Use a file for development, memory for tests
    }
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# Configuration des providers avec failover
# =============================================================================
MISSIVE_PROVIDERS = {
    # Email
    'EMAIL': [
        'missive.providers.django_email.DjangoEmailProvider',
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.mailgun.MailgunProvider',
        'missive.providers.ses.SESProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    
    # SMS et évolutions
    'SMS': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.vonage.VonageProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    'RCS': [
        'missive.providers.twilio.TwilioProvider',
    ],
    
    # Messageries instantanées
    'WHATSAPP': [
        'missive.providers.twilio.TwilioProvider',
    ],
    'TELEGRAM': [
        'missive.providers.telegram.TelegramProvider',
    ],
    'SIGNAL': [
        'missive.providers.signal.SignalProvider',
    ],
    'MESSENGER': [
        'missive.providers.messenger.MessengerProvider',
    ],
    
    # Courrier
    'POSTAL': [
        'missive.providers.laposte.LaPosteProvider',
    ],
    'LRE': [
        'missive.providers.ar24.AR24Provider',
        'missive.providers.certeurope.CerteuropeProvider',
    ],
    
    # Vocal
    'VOICE_CALL': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.vonage.VonageProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    
    # Notifications
    'NOTIFICATION': [
        'missive.providers.notification.InAppNotificationProvider',
    ],
    'PUSH_NOTIFICATION': [
        'missive.providers.fcm.FCMProvider',
        'missive.providers.apn.APNProvider',
    ],
    
    # Messageries professionnelles
    'SLACK': [
        'missive.providers.slack.SlackProvider',
    ],
    'TEAMS': [
        'missive.providers.teams.TeamsProvider',
    ],
}

# =============================================================================
# Configuration des clés API (depuis variables d'environnement)
# =============================================================================

# Email providers
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

# SMS providers
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
VONAGE_PHONE_NUMBER = os.getenv('VONAGE_PHONE_NUMBER')
SMSPARTNER_API_KEY = os.getenv('SMSPARTNER_API_KEY')
SMSPARTNER_SENDER = os.getenv('SMSPARTNER_SENDER', 'DjangoMissive')

# Courrier & LRE providers
LAPOSTE_API_KEY = os.getenv('LAPOSTE_API_KEY')
AR24_API_TOKEN = os.getenv('AR24_API_TOKEN')
AR24_API_URL = os.getenv('AR24_API_URL', 'https://api.ar24.fr')
AR24_SENDER_ID = os.getenv('AR24_SENDER_ID')
CERTEUROPE_API_KEY = os.getenv('CERTEUROPE_API_KEY')
CERTEUROPE_API_SECRET = os.getenv('CERTEUROPE_API_SECRET')
CERTEUROPE_API_URL = os.getenv('CERTEUROPE_API_URL')
CERTEUROPE_SENDER_EMAIL = os.getenv('CERTEUROPE_SENDER_EMAIL')

# Messageries providers
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SIGNAL_API_KEY = os.getenv('SIGNAL_API_KEY')
MESSENGER_PAGE_ACCESS_TOKEN = os.getenv('MESSENGER_PAGE_ACCESS_TOKEN')
MESSENGER_VERIFY_TOKEN = os.getenv('MESSENGER_VERIFY_TOKEN')

# Push notification providers
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY')
APN_CERTIFICATE_PATH = os.getenv('APN_CERTIFICATE_PATH')
APN_KEY_ID = os.getenv('APN_KEY_ID')
APN_TEAM_ID = os.getenv('APN_TEAM_ID')

# Providers professionnels
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
TEAMS_CLIENT_ID = os.getenv('TEAMS_CLIENT_ID')
TEAMS_CLIENT_SECRET = os.getenv('TEAMS_CLIENT_SECRET')
TEAMS_TENANT_ID = os.getenv('TEAMS_TENANT_ID')

# Configuration Email Django par défaut
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# Configuration globale pour les providers (legacy, peut être déprécié)
MISSIVE_CONFIG = {
    'SENDGRID_API_KEY': SENDGRID_API_KEY,
    'MAILGUN_API_KEY': MAILGUN_API_KEY,
    'TWILIO_ACCOUNT_SID': TWILIO_ACCOUNT_SID,
    'SMSPARTNER_API_KEY': SMSPARTNER_API_KEY,
    'LAPOSTE_API_KEY': LAPOSTE_API_KEY,
    'AR24_API_TOKEN': AR24_API_TOKEN,
    'CERTEUROPE_API_KEY': CERTEUROPE_API_KEY,
}

