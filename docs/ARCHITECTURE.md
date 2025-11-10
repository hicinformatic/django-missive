# Architecture - Django Missive

Documentation de l'architecture de la bibliothèque.

## 📁 Structure du projet

```
django-missive/
├── missive/                      # Package principal
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 # Modèles Django principaux
│   ├── admin.py                  # Configuration Django Admin
│   ├── urls.py                   # URLs principales
│   ├── forms.py                  # Formulaires Django
│   ├── sender.py                 # Factory pour envoyer les missives
│   ├── helpers.py                # Helpers pour créer des missives
│   ├── attachment_helpers.py     # Helpers pour les pièces jointes
│   │
│   ├── backends/                 # Backends d'envoi par type
│   │   ├── __init__.py
│   │   ├── base.py               # Classe de base
│   │   ├── email.py              # SendGrid, Mailgun, Django Email
│   │   ├── sms.py                # Twilio, SMSPartner
│   │   ├── postal.py             # La Poste
│   │   ├── whatsapp.py           # WhatsApp via Twilio
│   │   └── notification.py       # Notifications in-app
│   │
│   ├── views/                    # Vues Django
│   │   ├── __init__.py
│   │   └── webhooks.py           # Endpoints pour recevoir les webhooks
│   │
│   ├── webhooks_models.py        # Modèles pour les webhooks
│   ├── webhooks_handlers.py      # Handlers pour traiter les webhooks
│   ├── webhooks_urls.py          # URLs des webhooks
│   │
│   ├── templates/                # Templates HTML
│   │   └── missive/
│   │       ├── base.html
│   │       ├── missive_list.html
│   │       ├── missive_detail.html
│   │       └── ...
│   │
│   └── migrations/               # Migrations Django
│
├── tests/                        # Tests et configuration de dev
│   ├── settings.py
│   ├── urls.py
│   ├── conftest.py
│   ├── test_models.py
│   └── test_views.py
│
├── dev.py                        # Outil CLI de développement
├── manage.py                     # Django management
├── pyproject.toml                # Configuration du package
├── README.md
├── USAGE.md
├── EXAMPLES.md
├── ARCHITECTURE.md               # Ce fichier
└── DEVELOPMENT.md
```

## 🏗️ Architecture des composants

### 1. Modèles de données

#### `models.py` - Modèles principaux
- **`Missive`** : Missive principale avec GenericForeignKey vers n'importe quel objet
- **`MissiveAttachment`** : Pièces jointes (fichier local ou URL externe) avec GenericForeignKey
- **`MissiveEvent`** : Historique et tracking des événements
- **`MissiveTemplate`** : Templates réutilisables

#### `webhooks_models.py` - Modèles webhooks
- **`MissiveWebhook`** : Stockage et traitement des webhooks reçus

### 2. Backends d'envoi (`backends/`)

Architecture extensible avec un backend par provider :

```python
BaseBackend
├── Email
│   ├── DjangoEmailBackend      # SMTP via Django
│   ├── SendGridBackend          # SendGrid API
│   └── MailgunBackend           # Mailgun API
├── SMS
│   ├── TwilioSMSBackend         # Twilio SMS
│   └── SMSPartnerBackend        # SMSPartner (FR)
├── WhatsApp
│   └── TwilioWhatsAppBackend    # WhatsApp via Twilio
├── Postal
│   └── LaPosteBackend           # La Poste API
└── Notification
    └── InAppNotificationBackend # Notifications in-app
```

**Ajouter un nouveau backend :**

```python
# missive/backends/email.py
from .base import BaseBackend
from ..models import MissiveStatus

class MyEmailBackend(BaseBackend):
    provider_name = "My Provider"
    
    def send(self) -> bool:
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False
        
        try:
            # Votre logique d'envoi ici
            # ...
            
            self._update_status(MissiveStatus.SENT, provider=self.provider_name)
            self._create_event('sent', 'Email envoyé')
            return True
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            return False
```

### 3. Sender (`sender.py`)

Le `MissiveSender` est une factory qui :
1. Détermine le backend approprié selon le type et la config
2. Instancie le backend
3. Envoie la missive

```python
# Utilisation simple
from missive.sender import MissiveSender

success = MissiveSender.send(missive)
```

### 4. Webhooks

#### Réception (`views/webhooks.py`)
- Vues Django pour recevoir les webhooks de chaque provider
- Parsing et validation
- Création d'un `MissiveWebhook`

#### Traitement (`webhooks_handlers.py`)
- Handlers spécifiques par provider
- Validation de signature
- Mise à jour de la missive
- Création d'événements

```
Webhook reçu → BaseWebhookView → MissiveWebhook créé
                                        ↓
                              WebhookHandler traite
                                        ↓
                              Missive mise à jour + MissiveEvent créé
```

### 5. Helpers

#### `helpers.py` - MissiveBuilder
Création facile de missives liées à des objets :

```python
MissiveBuilder.create_email(
    source_object=order,  # GenericForeignKey
    sender=user,
    recipient_email='user@example.com',
    subject='...',
    body='...'
)
```

#### Pièces jointes
Gestion directe via le modèle `MissiveAttachment` :

```python
from missive.models import MissiveAttachment

# Fichier local
MissiveAttachment.objects.create(content_object=order, file=uploaded_file, ...)

# URL externe (S3, etc.)
MissiveAttachment.objects.create(content_object=order, external_url='https://...', ...)
```

## 🔄 Flux de données

### Envoi d'une missive

```
1. Création
   Missive.objects.create(...) ou MissiveBuilder.create_email(...)
   
2. Envoi
   MissiveSender.send(missive)
   ↓
   Détermine le backend (email, sms, postal, etc.)
   ↓
   Backend.send()
   ↓
   API du provider (SendGrid, Twilio, etc.)
   ↓
   Mise à jour statut + création événement
   
3. Webhook (asynchrone)
   Provider → /webhooks/sendgrid/ → BaseWebhookView
   ↓
   MissiveWebhook créé
   ↓
   WebhookHandler traite
   ↓
   Missive mise à jour (DELIVERED, READ, etc.)
   ↓
   MissiveEvent créé
```

### Attachement de fichiers

```
1. Fichier attaché à un objet métier
   MissiveAttachment.objects.create(content_object=order, ...)
   ↓
   MissiveAttachment créé avec content_object=order
   
2. Création missive liée
   MissiveBuilder.create_email(source_object=order, ...)
   ↓
   Missive créée avec content_object=order
   
3. Tout est lié
   Order ← MissiveAttachment
   Order ← Missive
```

## 🔌 Points d'extension

### 1. Ajouter un nouveau backend

Créer une classe dans `backends/[type].py` :

```python
class MyBackend(BaseBackend):
    provider_name = "My Provider"
    
    def send(self) -> bool:
        # Implémenter la logique d'envoi
        pass
```

### 2. Ajouter un nouveau webhook handler

Dans `webhooks_handlers.py` :

```python
class MyProviderWebhookHandler(BaseWebhookHandler):
    provider = 'MY_PROVIDER'
    
    def validate_signature(self) -> bool:
        # Valider la signature
        pass
    
    def extract_missive_id(self) -> Optional[str]:
        # Extraire l'ID
        pass
```

### 3. Personnaliser le comportement

Via `settings.py` :

```python
MISSIVE_CONFIG = {
    # Choisir les backends
    'BACKENDS': {
        'EMAIL': 'sendgrid',     # ou 'mailgun', 'django'
        'SMS': 'twilio',          # ou 'smspartner'
    },
    
    # Configuration des providers
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    
    # Options
    'ENABLE_TRACKING': True,
    'AUTO_RETRY_FAILED': True,
    'MAX_RETRIES': 3,
}
```

## 🎯 Principes de conception

### 1. Extensibilité
- Architecture modulaire (backends, handlers)
- Facile d'ajouter de nouveaux providers
- GenericForeignKey pour flexibilité maximale

### 2. Traçabilité
- Tous les webhooks sont stockés
- Historique complet des événements
- Métadonnées JSON pour debugging

### 3. Fiabilité
- Validation de signature des webhooks
- Retry des webhooks échoués
- Gestion d'erreurs complète

### 4. Flexibilité
- Fichiers locaux ou externes (S3, etc.)
- Attachements liés à n'importe quel objet
- Templates réutilisables
- Configuration par settings

## 📊 Modèle de données

```
┌─────────────┐
│   Missive   │
├─────────────┤
│ content_type│──┐
│ object_id   │  │ GenericForeignKey vers n'importe quoi
│             │  │ (Order, Invoice, Participant, etc.)
│ type        │  │
│ status      │  │
│ recipient_* │  │
│ ...         │  │
└─────────────┘  │
       │         │
       │         │
       ├─────────┴──────────┬──────────────┐
       │                    │              │
       ↓                    ↓              ↓
┌──────────────┐    ┌─────────────┐  ┌──────────┐
│MissiveAttach │    │MissiveEvent │  │Webhook   │
│              │    │             │  │          │
│content_type  │    │event_type   │  │provider  │
│object_id     │    │metadata     │  │payload   │
│file/url      │    │...          │  │...       │
└──────────────┘    └─────────────┘  └──────────┘
```

## 🚀 Performance

### Traitement asynchrone recommandé

Pour la production, utiliser Celery :

```python
# missive/tasks.py
from celery import shared_task
from .webhooks_handlers import process_webhook
from .webhooks_models import MissiveWebhook

@shared_task
def process_webhook_task(webhook_id):
    webhook = MissiveWebhook.objects.get(id=webhook_id)
    return process_webhook(webhook)

# Dans views/webhooks.py
def process_async(self, webhook):
    from ..tasks import process_webhook_task
    process_webhook_task.delay(webhook.id)
```

## 📚 Documentation associée

- **README.md** : Introduction et quick start
- **USAGE.md** : Guide d'utilisation détaillé
- **EXAMPLES.md** : Exemples de code concrets
- **DEVELOPMENT.md** : Guide pour les contributeurs
- **ARCHITECTURE.md** : Ce fichier

## 🔐 Sécurité

1. **Validation de signature** : Tous les webhooks doivent être signés
2. **IP whitelisting** : Optionnel, vérifier l'IP source
3. **HTTPS only** : Toujours utiliser HTTPS en production
4. **Secrets** : Stocker les clés API dans des variables d'environnement

```python
# settings.py
MISSIVE_CONFIG = {
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),  # Jamais en dur !
}
```

