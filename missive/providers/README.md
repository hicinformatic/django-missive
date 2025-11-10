# 📦 Providers Django-Missive

Guide d'installation et configuration des providers de communication.

## 📋 Table des matières

- [Installation](#installation)
- [Providers Email](#providers-email)
- [Providers SMS & Vocal](#providers-sms--vocal)
- [Messageries instantanées](#messageries-instantanées)
- [Notifications Push](#notifications-push)
- [Messageries professionnelles](#messageries-professionnelles)
- [Courrier](#courrier)

## 🚀 Installation

### 🔧 Développement local (actuellement)

```bash
# Core uniquement (Django + validation)
pip install -r ../../requirements.txt

# Développement (tests, linters)
pip install -r ../../requirements-dev.txt

# Tous les providers
pip install -r ../../requirements-all.txt
```

### 📦 Production (après publication PyPI)

Quand le package sera publié sur PyPI, vous pourrez installer par catégorie :

```bash
# Installation de base
pip install django-missive

# Avec providers spécifiques
pip install django-missive[email]        # Email
pip install django-missive[sms]          # SMS & Vocal
pip install django-missive[messaging]    # Telegram, Signal, Messenger
pip install django-missive[push]         # FCM, APN
pip install django-missive[professional] # Slack, Teams
pip install django-missive[postal]       # Courrier, LRE
pip install django-missive[all]          # Tous les providers
```

---

## 📧 Providers Email

### Django Email (inclus par défaut)
- **Provider**: `django_email`
- **Configuration**: Utilise `settings.EMAIL_*` de Django
- **Dépendances**: Aucune
- **Usage**: Email basique via SMTP configuré dans Django

### SendGrid
- **Provider**: `sendgrid`
- **Installation**: `pip install sendgrid>=6.11`
- **Configuration**:
```python
SENDGRID_API_KEY = "SG.xxxx"
```

### Mailgun
- **Provider**: `mailgun`
- **Installation**: `pip install mailgun>=0.1.1`
- **Configuration**:
```python
MAILGUN_API_KEY = "key-xxxx"
MAILGUN_DOMAIN = "mg.example.com"
```

### Amazon SES
- **Provider**: `ses`
- **Installation**: `pip install boto3>=1.28`
- **Configuration**:
```python
AWS_ACCESS_KEY_ID = "xxxx"
AWS_SECRET_ACCESS_KEY = "xxxx"
AWS_REGION_NAME = "eu-west-1"
```

---

## 📱 Providers SMS & Vocal

### Twilio (SMS, WhatsApp, Vocal)
- **Providers**: `twilio`
- **Installation**: `pip install twilio>=8.10`
- **Configuration**:
```python
TWILIO_ACCOUNT_SID = "ACxxxx"
TWILIO_AUTH_TOKEN = "xxxx"
TWILIO_PHONE_NUMBER = "+33600000000"  # Numéro expéditeur
TWILIO_WHATSAPP_NUMBER = "whatsapp:+33600000000"  # Pour WhatsApp
```
- **Destinataire**: Nécessite `mobile` pour SMS/WhatsApp

### Vonage (ex-Nexmo)
- **Provider**: `vonage`
- **Installation**: `pip install vonage>=3.11`
- **Configuration**:
```python
VONAGE_API_KEY = "xxxx"
VONAGE_API_SECRET = "xxxx"
VONAGE_PHONE_NUMBER = "+33600000000"
```

### RCS (Rich Communication Services)
- **Provider**: `twilio` (via Twilio Conversations)
- **Installation**: Même que Twilio
- **Note**: Évolution du SMS avec rich media

---

## 💬 Messageries instantanées

### Telegram
- **Provider**: `telegram`
- **Installation**: `pip install python-telegram-bot>=20.7`
- **Configuration**:
```python
TELEGRAM_BOT_TOKEN = "1234567890:ABCxxxx"
```
- **Destinataire**: Nécessite `metadata.telegram_chat_id`
- **Documentation**: https://core.telegram.org/bots/api

### Signal
- **Provider**: `signal`
- **Installation**: Service externe signal-cli-rest-api requis
- **Configuration**:
```python
SIGNAL_CLI_REST_API_URL = "http://localhost:8080"
SIGNAL_SENDER_NUMBER = "+33600000000"
```
- **Destinataire**: Nécessite `mobile`
- **Documentation**: https://github.com/bbernhard/signal-cli-rest-api

### Facebook Messenger
- **Provider**: `messenger`
- **Installation**: `pip install requests>=2.31`
- **Configuration**:
```python
MESSENGER_PAGE_ACCESS_TOKEN = "xxxx"
MESSENGER_APP_SECRET = "xxxx"
```
- **Destinataire**: Nécessite `metadata.messenger_psid`
- **Documentation**: https://developers.facebook.com/docs/messenger-platform

---

## 🔔 Notifications Push

### Firebase Cloud Messaging (Android/iOS)
- **Provider**: `fcm`
- **Installation**: `pip install firebase-admin>=6.3`
- **Configuration**:
```python
FCM_SERVICE_ACCOUNT_JSON = "/path/to/serviceAccountKey.json"
# ou
FCM_SERVER_KEY = "xxxx"  # Legacy (deprecated)
```
- **Destinataire**: Nécessite `metadata.fcm_device_token`
- **Documentation**: https://firebase.google.com/docs/cloud-messaging

### Apple Push Notification (iOS)
- **Provider**: `apn`
- **Installation**: `pip install aioapns>=3.1`
- **Configuration**:
```python
APN_CERTIFICATE_PATH = "/path/to/cert.pem"
APN_KEY_ID = "xxxx"
APN_TEAM_ID = "xxxx"
APN_BUNDLE_ID = "com.example.app"
APN_USE_SANDBOX = False  # True pour dev
```
- **Destinataire**: Nécessite `metadata.apn_device_token`
- **Documentation**: https://developer.apple.com/documentation/usernotifications

---

## 🏢 Messageries professionnelles

### Slack
- **Provider**: `slack`
- **Installation**: `pip install slack-sdk>=3.26`
- **Configuration**:
```python
SLACK_BOT_TOKEN = "xoxb-xxxx"
SLACK_SIGNING_SECRET = "xxxx"
```
- **Destinataire**: Nécessite `metadata.slack_user_id` ou `metadata.slack_channel_id`
- **Documentation**: https://api.slack.com/messaging/sending

### Microsoft Teams
- **Provider**: `teams`
- **Installation**: `pip install msgraph-core>=1.0 msal>=1.25`
- **Configuration**:
```python
TEAMS_CLIENT_ID = "xxxx"
TEAMS_CLIENT_SECRET = "xxxx"
TEAMS_TENANT_ID = "xxxx"
```
- **Destinataire**: Nécessite `metadata.teams_user_id` ou `metadata.teams_channel_id`
- **Documentation**: https://learn.microsoft.com/en-us/graph/api/chat-post-messages

---

## 📮 Courrier

### La Poste
- **Provider**: `laposte`
- **Installation**: `pip install requests>=2.31 reportlab>=4.0`
- **Configuration**:
```python
LAPOSTE_API_KEY = "xxxx"
LAPOSTE_CONTRACT_NUMBER = "xxxx"
```
- **Destinataire**: Nécessite adresse complète (`address_line1`, `postal_code`, `city`, `country`)

### LRE (Lettre Recommandée Électronique)
- **Provider**: `lre`
- **Installation**: `pip install requests>=2.31 reportlab>=4.0`
- **Configuration**:
```python
LRE_SERVICE = "ar24"  # ou "certeurope"
LRE_API_KEY = "xxxx"
LRE_API_SECRET = "xxxx"
```
- **Destinataire**: Nécessite `email` + adresse complète (recommandé)
- **Services compatibles**: AR24, Certeurope

---

## 🔧 Configuration des providers dans settings.py

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.django_email.DjangoEmailProvider',
        'missive.providers.sendgrid.SendGridProvider',  # Failover
    ],
    'SMS': [
        'missive.providers.twilio.TwilioProvider',
    ],
    'TELEGRAM': [
        'missive.providers.telegram.TelegramProvider',
    ],
    # ... autres types ...
}
```

---

## 📝 Métadonnées requises par destinataire

Certains providers nécessitent des informations stockées dans `Recipient.metadata` (JSONField) :

```python
recipient.metadata = {
    # Telegram
    'telegram_chat_id': '123456789',
    
    # Messenger
    'messenger_psid': 'xxxx',
    
    # Push notifications
    'fcm_device_token': 'xxxx',
    'apn_device_token': 'xxxx',
    
    # Pro
    'slack_user_id': 'U01234567',
    'slack_channel_id': 'C01234567',
    'teams_user_id': 'xxxx-xxxx-xxxx',
}
```

---

## 🎯 Commandes de génération

```bash
# Générer des destinataires d'exemple
python manage.py generate_recipients

# Générer des missives d'exemple
python manage.py generate_missives

# Nettoyer les doublons
python manage.py clean_duplicates
```

---

## 📊 Matrice de compatibilité

| Type | Email | Mobile | Adresse | Metadata |
|------|-------|--------|---------|----------|
| EMAIL | ✅ | - | - | - |
| SMS | - | ✅ | - | - |
| RCS | - | ✅ | - | - |
| WHATSAPP | - | ✅ | - | - |
| TELEGRAM | - | - | - | ✅ chat_id |
| SIGNAL | - | ✅ | - | - |
| MESSENGER | - | - | - | ✅ psid |
| POSTAL | - | - | ✅ | - |
| LRE | ✅ | - | ✅ (recommandé) | - |
| VOICE_CALL | - | ✅ | - | - |
| NOTIFICATION | - | - | - | - |
| PUSH | - | - | - | ✅ device_token |
| SLACK | - | - | - | ✅ user_id |
| TEAMS | - | - | - | ✅ user_id |

---

## 🔐 Bonnes pratiques

1. **Secrets** : Stockez les API keys dans des variables d'environnement
2. **Failover** : Configurez plusieurs providers par type pour la redondance
3. **Validation** : Utilisez les actions de validation dans l'admin avant envoi
4. **Metadata** : Validez que les metadata sont présents avant d'envoyer
5. **Tests** : Testez d'abord avec les modes sandbox/test des providers

---

## 🚧 Providers en simulation

Les nouveaux providers sont actuellement en **mode simulation** (méthode `send()` ne fait pas d'appel réel).

Pour activer un provider :
1. Installer les dépendances
2. Configurer les credentials dans `settings.py`
3. Implémenter la méthode `send()` dans le fichier provider
4. Tester en mode sandbox
5. Passer en production

---

## 💡 Support

- Documentation complète : [README.md](../../README.md)
- Issues : GitHub Issues
- Provider manquant ? Créez un nouveau fichier dans `missive/providers/` en héritant de `BaseProvider`

