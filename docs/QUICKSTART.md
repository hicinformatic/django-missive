# Démarrage rapide - Django Missive 🚀

Guide ultra-rapide pour commencer avec Django Missive.

## ⚡ Installation en 3 commandes

```bash
# 1. Setup
python3 dev.py install-dev

# 2. Migrations
python3 dev.py migrate

# 3. Lancer le serveur
python3 dev.py runserver
```

**Accès admin** : http://127.0.0.1:8000/admin/ (admin/admin)

## 📦 Utilisation basique

### 1. Envoyer un email

```python
from missive import MissiveBuilder, MissiveSender, MissiveType

# Créer + envoyer
missive = MissiveBuilder.create_email(
    source_object=order,  # Optionnel : lier à un objet
    sender=request.user,
    recipient_email='user@example.com',
    subject='Commande confirmée',
    body='Votre commande #123 est confirmée !'
)

MissiveSender.send(missive)
```

### 2. Envoyer un SMS

```python
missive = MissiveBuilder.create_sms(
    source_object=appointment,
    sender=system_user,
    recipient_phone='+33600000000',
    subject='Rappel RDV',
    body='RDV demain à 14h'
)

MissiveSender.send(missive)
```

### 3. Attacher un fichier

```python
from missive.models import MissiveAttachment

# Fichier local
attachment = MissiveAttachment.objects.create(
    content_object=order,
    file=request.FILES['document'],
    filename="facture.pdf",
    description="Facture de commande"
)

# URL externe (S3, etc.)
attachment = MissiveAttachment.objects.create(
    content_object=invoice,
    external_url="https://s3.amazonaws.com/bucket/invoice.pdf",
    filename="facture_123.pdf"
)
```

## 🔧 Configuration minimale

Dans votre `settings.py` :

```python
INSTALLED_APPS = [
    ...
    'missive',
]

# Configuration (optionnel, valeurs par défaut)
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'django',  # ou 'sendgrid', 'mailgun'
        'SMS': 'twilio',     # ou 'smspartner'
    }
}

# Email Django (par défaut)
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

Dans votre `urls.py` :

```python
urlpatterns = [
    path('missive/', include('missive.urls')),  # Tout est inclus
]
```

Cela crée les URLs suivantes :
- `/missive/` - Interface CRUD
- `/missive/webhook/{provider}/` - Webhook unifié (sendgrid, twilio, laposte, etc.)

## 📋 Types de missives supportés

| Type | Provider par défaut | Champs requis |
|------|---------------------|---------------|
| 📧 Email | Django SMTP | `recipient_email` |
| 📱 SMS | Twilio | `recipient_phone` |
| 💬 WhatsApp | Twilio | `recipient_phone` |
| 📮 Postal | La Poste | `recipient_address` |
| 🔔 Notification | In-app | `recipient_user` |

## 🔌 Providers disponibles

### Email
- `django` - SMTP via Django (par défaut)
- `sendgrid` - SendGrid API
- `mailgun` - Mailgun API

### SMS
- `twilio` - Twilio API (par défaut)
- `smspartner` - SMSPartner (FR)

### WhatsApp
- `twilio` - Twilio WhatsApp Business

### Postal
- `laposte` - La Poste API

## 🎯 Commandes dev.py

```bash
python3 dev.py help           # Aide
python3 dev.py runserver      # Serveur dev
python3 dev.py migrate        # Migrations
python3 dev.py test           # Tests
python3 dev.py clean-test     # Nettoyer fichiers de test
python3 dev.py format         # Formater le code
python3 dev.py build          # Builder le package
```

## 🌐 Configuration Webhooks

Un seul endpoint unifié pour tous les providers :

```
SendGrid:     https://yourdomain.com/missive/webhook/sendgrid/
Mailgun:      https://yourdomain.com/missive/webhook/mailgun/
Twilio:       https://yourdomain.com/missive/webhook/twilio/
SMSPartner:   https://yourdomain.com/missive/webhook/smspartner/
La Poste:     https://yourdomain.com/missive/webhook/laposte/
SendinBlue:   https://yourdomain.com/missive/webhook/sendinblue/
```

## 📚 Documentation complète

- **USAGE.md** - Guide d'utilisation complet
- **EXAMPLES.md** - Exemples de code
- **STRUCTURE.md** - Organisation du code
- **DEVELOPMENT.md** - Guide développeur
- **ARCHITECTURE.md** - Architecture technique

## 🎁 Fonctionnalités principales

✅ **Multi-canaux** : Email, SMS, WhatsApp, Postal, Notifications  
✅ **Recommandé** : Support courrier/email recommandé avec AR  
✅ **Flexible** : GenericForeignKey pour lier à n'importe quel modèle  
✅ **Fichiers** : Local OU externe (S3, etc.)  
✅ **Tracking** : Historique complet des événements  
✅ **Webhooks** : Support automatique des callbacks providers  
✅ **Templates** : Templates réutilisables avec variables  
✅ **Envoi programmé** : Scheduler l'envoi  
✅ **Stats** : Statistiques par objet/type/status  

## 🚀 Prêt à publier

```bash
python3 dev.py build          # Builder
python3 dev.py upload-test    # Test sur TestPyPI
python3 dev.py upload         # Publier sur PyPI
```

Ensuite : `pip install django-missive`

