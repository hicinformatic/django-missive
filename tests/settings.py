"""Django settings for testing django-missive."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Environment variables loaded from {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")


def _env(key: str, default: str = "") -> str:
    """Shortcut to fetch environment variables with defaults."""
    return os.getenv(key, default)


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
# Provider configuration (auto categorization)
# =============================================================================
# Simple list: each provider declares `supported_types` and is automatically categorized.
# No more duplication—Twilio is listed once instead of four times.

MISSIVE_PROVIDERS = [
    # Email providers
    "python_missive.providers.django_email.DjangoEmailProvider",
    "python_missive.providers.smtp.SMTPProvider",
    "python_missive.providers.sendgrid.SendGridProvider",
    "python_missive.providers.mailgun.MailgunProvider",
    "python_missive.providers.ses.SESProvider",
    "python_missive.providers.brevo.BrevoProvider",
    # SMS / Voice providers
    "python_missive.providers.twilio.TwilioProvider",
    "python_missive.providers.vonage.VonageProvider",
    "python_missive.providers.smspartner.SMSPartnerProvider",
    # Branded messaging providers
    "python_missive.providers.slack.SlackProvider",
    "python_missive.providers.teams.TeamsProvider",
    "python_missive.providers.telegram.TelegramProvider",
    "python_missive.providers.signal.SignalProvider",
    "python_missive.providers.messenger.MessengerProvider",
    # Postal / LRE providers
    "python_missive.providers.laposte.LaPosteProvider",
    "python_missive.providers.maileva.MailevaProvider",
    "python_missive.providers.ar24.AR24Provider",
    "python_missive.providers.certeurope.CerteuropeProvider",
    # Notifications / Push
    "python_missive.providers.fcm.FCMProvider",
    "python_missive.providers.apn.APNProvider",
    "python_missive.providers.notification.InAppNotificationProvider",
]

# =============================================================================
# Address verification backends configuration
# =============================================================================
# Ordered list: the first working backend is used by Missive helpers/admin tools.

MISSIVE_ADDRESS_BACKENDS = [
    {
        "class": "python_missive.address_backends.nominatim.NominatimAddressBackend",
        "config": {
            "NOMINATIM_USER_AGENT": _env(
                "NOMINATIM_USER_AGENT", "django-missive/1.0"
            ),
            "NOMINATIM_BASE_URL": _env(
                "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
            ),
        },
    },
    {
        "class": "python_missive.address_backends.photon.PhotonAddressBackend",
        "config": {
            "PHOTON_BASE_URL": _env(
                "PHOTON_BASE_URL", "https://photon.komoot.io"
            ),
        },
    },
    {
        "class": "python_missive.address_backends.google_maps.GoogleMapsAddressBackend",
        "config": {
            "GOOGLE_MAPS_API_KEY": _env("GOOGLE_MAPS_API_KEY", ""),
        },
    },
    {
        "class": "python_missive.address_backends.mapbox.MapboxAddressBackend",
        "config": {
            "MAPBOX_ACCESS_TOKEN": _env("MAPBOX_ACCESS_TOKEN", ""),
        },
    },
    {
        "class": "python_missive.address_backends.here.HereAddressBackend",
        "config": {
            "HERE_APP_ID": _env("HERE_APP_ID", ""),
            "HERE_APP_CODE": _env("HERE_APP_CODE", ""),
        },
    },
]

# Note: multi-type providers (Twilio, Brevo, SMSPartner) are automatically
# added to all supported categories. No need to repeat them!

# =============================================================================
# Configuration globale Missive
# =============================================================================

# Sandbox mode: if True, every send is executed in test mode (no real deliveries)
MISSIVE_SANDBOX = bool(os.getenv("MISSIVE_SANDBOX"))
MISSIVE_SANDBOX = True

# Base URL pour les webhooks (domaine accessible par les providers)
# Exemples :
#   - Production : "https://api.monapp.com"
#   - Development: "https://1234.ngrok.io" (ngrok tunnel)
#   - Local: "http://192.168.1.100:8000" (local network IP)
MISSIVE_WEBHOOK_BASE_URL = os.getenv(
    "MISSIVE_WEBHOOK_BASE_URL", "http://127.0.0.1:8000"
)

# =============================================================================
# API key configuration (loaded from environment variables)
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

# Messaging providers
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

# Default Django email configuration
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@example.com")
