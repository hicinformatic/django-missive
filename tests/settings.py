"""
Django settings for testing django-missive
"""

import os
from pathlib import Path

# Charger les variables d'environnement depuis .env si disponible
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Variables d'environnement chargées depuis {env_path}")
except ImportError:
    print("⚠️ python-dotenv non installé. Installez-le avec: pip install python-dotenv")

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
# Configuration des providers (NOUVEAU FORMAT - auto-catégorisation)
# =============================================================================
# Liste simple : chaque provider déclare ses supported_types et est automatiquement catégorisé
# Plus de duplication ! Twilio n'est listé qu'une fois au lieu de 4 fois

MISSIVE_PROVIDERS = [
    # Providers Email
    "missive.providers.django_email.DjangoEmailProvider",
    "missive.providers.sendgrid.SendGridProvider",
    "missive.providers.mailgun.MailgunProvider",
    "missive.providers.ses.SESProvider",
    "missive.providers.brevo.BrevoProvider",  # Auto-catégorisé: EMAIL + SMS
    # Providers SMS/Voice (multi-types)
    "missive.providers.twilio.TwilioProvider",  # Auto-catégorisé: SMS + BRANDED + VOICE_CALL
    "missive.providers.vonage.VonageProvider",  # Auto-catégorisé: SMS + VOICE_CALL
    "missive.providers.smspartner.SMSPartnerProvider",  # Auto-catégorisé: SMS + EMAIL + VOICE_CALL
    # Providers Messageries de marque (BRANDED)
    "missive.providers.slack.SlackProvider",
    "missive.providers.teams.TeamsProvider",
    "missive.providers.telegram.TelegramProvider",
    "missive.providers.signal.SignalProvider",
    "missive.providers.messenger.MessengerProvider",
    # Providers Postal/LRE
    "missive.providers.laposte.LaPosteProvider",
    "missive.providers.ar24.AR24Provider",
    "missive.providers.certeurope.CerteuropeProvider",
    # Providers Notifications
    "missive.providers.fcm.FCMProvider",
    "missive.providers.apn.APNProvider",
    "missive.providers.notification.InAppNotificationProvider",
]

# Note: Les providers multi-types (Twilio, Brevo, SMSPartner) sont automatiquement
# ajoutés à chaque catégorie selon leurs supported_types. Plus besoin de les répéter !

# =============================================================================
# Configuration globale Missive
# =============================================================================

# Mode sandbox : si True, tous les envois sont en mode test (aucun envoi réel)
MISSIVE_SANDBOX = bool(os.getenv("MISSIVE_SANDBOX"))
MISSIVE_SANDBOX = True

# Base URL pour les webhooks (domaine accessible par les providers)
# Exemples :
#   - Production : "https://api.monapp.com"
#   - Développement : "https://1234.ngrok.io" (tunnel ngrok)
#   - Local : "http://192.168.1.100:8000" (IP locale sur réseau)
MISSIVE_WEBHOOK_BASE_URL = os.getenv(
    "MISSIVE_WEBHOOK_BASE_URL", "http://127.0.0.1:8000"
)

# =============================================================================
# Configuration des clés API (depuis variables d'environnement)
# =============================================================================

# Email providers
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

# SMS providers
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")
VONAGE_PHONE_NUMBER = os.getenv("VONAGE_PHONE_NUMBER")
SMSPARTNER_API_KEY = os.getenv("SMSPARTNER_API_KEY")
SMSPARTNER_SENDER = os.getenv("SMSPARTNER_SENDER", "DjangoMissive")

# Courrier & LRE providers
LAPOSTE_API_KEY = os.getenv("LAPOSTE_API_KEY")
AR24_API_TOKEN = os.getenv("AR24_API_TOKEN")
AR24_API_URL = os.getenv("AR24_API_URL", "https://api.ar24.fr")
AR24_SENDER_ID = os.getenv("AR24_SENDER_ID")
CERTEUROPE_API_KEY = os.getenv("CERTEUROPE_API_KEY")
CERTEUROPE_API_SECRET = os.getenv("CERTEUROPE_API_SECRET")
CERTEUROPE_API_URL = os.getenv("CERTEUROPE_API_URL")
CERTEUROPE_SENDER_EMAIL = os.getenv("CERTEUROPE_SENDER_EMAIL")

# Messageries providers
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SIGNAL_API_KEY = os.getenv("SIGNAL_API_KEY")
MESSENGER_PAGE_ACCESS_TOKEN = os.getenv("MESSENGER_PAGE_ACCESS_TOKEN")
MESSENGER_VERIFY_TOKEN = os.getenv("MESSENGER_VERIFY_TOKEN")

# Push notification providers
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
APN_CERTIFICATE_PATH = os.getenv("APN_CERTIFICATE_PATH")
APN_KEY_ID = os.getenv("APN_KEY_ID")
APN_TEAM_ID = os.getenv("APN_TEAM_ID")

# Providers professionnels
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
TEAMS_CLIENT_ID = os.getenv("TEAMS_CLIENT_ID")
TEAMS_CLIENT_SECRET = os.getenv("TEAMS_CLIENT_SECRET")
TEAMS_TENANT_ID = os.getenv("TEAMS_TENANT_ID")

# Configuration Email Django par défaut
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
