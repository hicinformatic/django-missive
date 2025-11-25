# Django Missive

🚀 Une bibliothèque Django complète pour gérer l'envoi de **missives multi-canaux** : emails, SMS, WhatsApp, courrier postal, et notifications in-app.

## ✨ Features

### Fonctionnalités principales

- 📧 **Multi-canaux** : 14 types supportés (Email, SMS, WhatsApp, Telegram, Signal, Messenger, RCS, Courrier postal, LRE, Appels vocaux, Notifications push, Slack, Teams)
- 🔌 **15+ providers intégrés** : SendGrid, Mailgun, Twilio, La Poste, Telegram, FCM, APN, Slack, Teams, etc.
- 📎 **Pièces jointes flexibles** : Fichiers locaux OU URLs externes (S3, Google Drive)
- 🔔 **Webhooks unifiés** : Un seul endpoint `/missive/webhook/{provider}/`
- 📊 **Tracking complet** : Historique, statuts, événements
- 🎯 **Modèle Recipient** : Centralisation des coordonnées (email, téléphone, adresse)
- 🔍 **Validation intégrée** : Tests de risque d'échec avant envoi
- 👨‍💼 **Admin Django complet** : Interface de gestion avec actions de validation
- 🔗 **GenericForeignKey** : Lien flexible avec vos modèles métier
- 📝 **Templates réutilisables** : Créez des templates de missives
- 📊 **Monitoring avancé** : Services, crédits, SLA et health check pour chaque provider
- 🔄 **Fallback automatique** : Bascule vers un provider de secours en cas de panne

### Architecture technique

- ✅ Compatible Django 3.2+ et Python 3.9+
- ✅ Structure modulaire par mixins (providers/base/)
- ✅ Tests unitaires complets (8/8 ✅)
- ✅ Documentation exhaustive (16 fichiers .md)
- ✅ CI/CD avec GitHub Actions
- ✅ Type hints et mypy
- ✅ Code formaté avec Black + isort

## Installation

### 🔧 Mode développement (projet local)

```bash
# Core uniquement (Django + validation)
pip install -r requirements.txt

# Développement (tests, linters)
pip install -r requirements-dev.txt

# Tous les providers
pip install -r requirements-all.txt
```

### 📦 Mode production (futur - après publication PyPI)

```bash
# Installation de base
pip install django-missive

# Avec providers spécifiques
pip install django-missive[email]        # Email (SendGrid, Mailgun, SES)
pip install django-missive[sms]          # SMS & Vocal (Twilio, Vonage)
pip install django-missive[messaging]    # Telegram, Signal, Messenger
pip install django-missive[push]         # Notifications push (FCM, APN)
pip install django-missive[professional] # Slack, Teams
pip install django-missive[postal]       # Courrier, LRE
pip install django-missive[all]          # Tous les providers
```

## Quick Start

1. Add `missive` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'missive',
]
```

2. Run migrations:

```bash
python manage.py migrate missive
```

3. Include the URLconf in your project `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('missive/', include('missive.urls')),  # Interface + Webhooks
]
```

This will create the following URLs:
- `/missive/` - Interface CRUD des missives
- `/missive/webhook/{provider}/` - Webhook unifié pour tous les providers

4. Configure providers and address backends in `settings.py`:

```python
# Providers automatically categorized by supported_types
MISSIVE_PROVIDERS = [
    # Email
    "python_missive.providers.django_email.DjangoEmailProvider",
    "python_missive.providers.smtp.SMTPProvider",
    "python_missive.providers.sendgrid.SendGridProvider",
    "python_missive.providers.mailgun.MailgunProvider",
    "python_missive.providers.ses.SESProvider",
    "python_missive.providers.brevo.BrevoProvider",
    # SMS / Voice
    "python_missive.providers.twilio.TwilioProvider",
    "python_missive.providers.vonage.VonageProvider",
    "python_missive.providers.smspartner.SMSPartnerProvider",
    # Branded / messaging
    "python_missive.providers.slack.SlackProvider",
    "python_missive.providers.teams.TeamsProvider",
    "python_missive.providers.telegram.TelegramProvider",
    "python_missive.providers.signal.SignalProvider",
    "python_missive.providers.messenger.MessengerProvider",
    # Postal / LRE
    "python_missive.providers.laposte.LaPosteProvider",
    "python_missive.providers.maileva.MailevaProvider",
    "python_missive.providers.ar24.AR24Provider",
    "python_missive.providers.certeurope.CerteuropeProvider",
    # Notifications / push
    "python_missive.providers.fcm.FCMProvider",
    "python_missive.providers.apn.APNProvider",
    "python_missive.providers.notification.InAppNotificationProvider",
]

# Address verification backends (first working backend is used)
MISSIVE_ADDRESS_BACKENDS = [
    {
        "class": "python_missive.address_backends.nominatim.NominatimAddressBackend",
        "config": {
            "NOMINATIM_USER_AGENT": os.getenv("NOMINATIM_USER_AGENT", "django-missive/1.0"),
            "NOMINATIM_BASE_URL": os.getenv(
                "NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org"
            ),
        },
    },
    {
        "class": "python_missive.address_backends.photon.PhotonAddressBackend",
        "config": {
            "PHOTON_BASE_URL": os.getenv("PHOTON_BASE_URL", "https://photon.komoot.io"),
        },
    },
    {
        "class": "python_missive.address_backends.google_maps.GoogleMapsAddressBackend",
        "config": {
            "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", ""),
        },
    },
    {
        "class": "python_missive.address_backends.mapbox.MapboxAddressBackend",
        "config": {
            "MAPBOX_ACCESS_TOKEN": os.getenv("MAPBOX_ACCESS_TOKEN", ""),
        },
    },
    {
        "class": "python_missive.address_backends.here.HereAddressBackend",
        "config": {
            "HERE_APP_ID": os.getenv("HERE_APP_ID", ""),
            "HERE_APP_CODE": os.getenv("HERE_APP_CODE", ""),
        },
    },
]
```

## 🚀 Usage rapide

### Envoyer un email

```python
from missive import MissiveBuilder, MissiveSender

# Créer
missive = MissiveBuilder.create_email(
    source_object=order,
    sender=request.user,
    recipient_email="client@example.com",
    subject="Commande confirmée",
    body="<p>Votre commande #123 est confirmée</p>",
    body_text="Votre commande #123 est confirmée",  # Version texte
)

# Envoyer
MissiveSender.send(missive)
```

### Utiliser le modèle Recipient

```python
from missive.models import Recipient, Missive

# Créer un destinataire avec toutes ses coordonnées
recipient = Recipient.objects.create(
    first_name="Jean",
    last_name="Dupont",
    company_name="ACME Corp",
    email="jean@acme.com",
    mobile="+33600000000",
    address_line1="123 Rue de la Paix",
    postal_code="75001",
    city="Paris",
    country="FR"
)

# Réutiliser pour plusieurs missives
email = Missive.objects.create(sender=user, recipient=recipient, ...)
sms = Missive.objects.create(sender=user, recipient=recipient, ...)
```

### Monitoring des providers

```python
from python_missive.providers import SendGridProvider, TwilioProvider

# Vérifier le statut et les crédits
provider = SendGridProvider()
status = provider.get_service_status()
print(f"Status: {status['status']}")
print(f"Services: {status['services']}")  # ['email', 'email_transactional', ...]
print(f"Credits: {status['credits']}")

# Health check complet
health = provider.health_check()
if not health['is_healthy']:
    print(f"⚠️ {health['summary']}")
    for issue in health['issues']:
        print(f"  - {issue}")

# Vérifier les crédits spécifiquement
credits = provider.check_credits()
if credits['needs_refill']:
    print(f"⚠️ Recharge nécessaire: {credits['remaining']} {credits['currency']}")
```

### Valider avant envoi

```python
from python_missive.providers import SendGridProvider

provider = SendGridProvider(missive)

# Analyser le risque d'échec
risk = provider.calculate_delivery_risk()

if risk['risk_score'] > 70:
    print(f"⚠️ Risque élevé : {risk['recommendations']}")
else:
    MissiveSender.send(missive)
```

## ⚙️ Configuration

Dans votre `settings.py`:

```python
# Django Missive Configuration
MISSIVE_CONFIG = {
    # Providers par type de missive
    'PROVIDERS': {
        'EMAIL': 'sendgrid',
        'SMS': 'twilio',
        'WHATSAPP': 'twilio',
        'POSTAL': 'laposte',
        'POSTAL_REGISTERED': 'laposte',
        'NOTIFICATION': 'inapp',
    },
    
    # SendGrid
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    
    # Twilio
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': '+33123456789',
    
    # La Poste
    'LAPOSTE_API_KEY': os.getenv('LAPOSTE_API_KEY'),
    
    # Général
    'DEFAULT_FROM_EMAIL': 'noreply@example.com',
}
```

## Usage

```python
# Example usage code here
```

## Development

### Quick Start

This project includes `dev.py` - a cross-platform development tool that works on **all operating systems**.

```bash
# Setup development environment
python dev.py install-dev

# Run tests
python dev.py test

# Format code
python dev.py format

# Build package
python dev.py build
```

**Linux/macOS users** can make it executable:
```bash
chmod +x dev.py
./dev.py install-dev
./dev.py test
```

### Available Commands

**Development:**
- `python dev.py venv` - Create virtual environment
- `python dev.py install` - Install in production mode
- `python dev.py install-dev` - Install in development mode

**Testing:**
- `python dev.py test` - Run tests with pytest
- `python dev.py test-verbose` - Run tests with verbose output
- `python dev.py coverage` - Run tests with coverage report

**Code Quality:**
- `python dev.py lint` - Run linters (flake8, mypy)
- `python dev.py format` - Format code (black, isort)
- `python dev.py check` - Run all checks (lint + format check)

**Building:**
- `python dev.py build` - Build wheel and source distribution
- `python dev.py clean` - Remove all build artifacts
- `python dev.py clean-test` - Remove test artifacts (htmlcov, .coverage, etc.)

**Publishing:**
- `python dev.py upload-test` - Upload to TestPyPI
- `python dev.py upload` - Upload to PyPI
- `python dev.py release` - Full release workflow

**Utilities:**
- `python dev.py show-version` - Show current version
- `python dev.py venv-clean` - Recreate virtual environment

Run `python dev.py help` to see all available commands.

### Django Development Server

Test the library with a Django development server:

```bash
# Run migrations and create superuser (admin/admin)
python dev.py migrate

# Start development server
python dev.py runserver
```

Access the admin interface at http://127.0.0.1:8000/admin/ (login: admin/admin)

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (Initial Release)

- Initial release
- Basic functionality

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/yourusername/django-missive/issues).

