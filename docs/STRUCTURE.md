# Structure finale - Django Missive

## 📁 Organisation du code

```
django-missive/
├── missive/                          # Package principal
│   ├── __init__.py                   # Exports lazy (évite imports circulaires)
│   ├── apps.py                       # Config Django app
│   ├── admin.py                      # TOUS les admins
│   ├── urls.py                       # URLs principales
│   ├── forms.py                      # Formulaires
│   ├── sender.py                     # Factory pour envoyer (dispatch vers providers)
│   ├── helpers.py                    # MissiveBuilder
│   ├── utils.py                      # Utilitaires
│   │
│   ├── models/                       # 📦 MODÈLES (organisés par fichier)
│   │   ├── __init__.py               # Exports tous les modèles
│   │   ├── choices.py                # Enums (MissiveType, MissiveStatus, etc.)
│   │   ├── recipient.py              # Modèle Recipient
│   │   ├── missive.py                # Modèle Missive (principal)
│   │   ├── attachment.py             # Modèle MissiveAttachment
│   │   ├── event.py                  # Modèle MissiveEvent
│   │   └── template.py               # Modèle MissiveTemplate
│   │
│   ├── providers/                    # 🎯 UN FICHIER PAR PROVIDER
│   │   ├── __init__.py
│   │   ├── base/                     # 📦 BaseProvider modulaire (mixins)
│   │   │   ├── __init__.py           # BaseProvider (combine tous les mixins)
│   │   │   ├── common.py             # Fonctions communes (config, status, events)
│   │   │   ├── email.py              # BaseEmailMixin (validation, spam, SMTP)
│   │   │   ├── sms.py                # BaseSMSMixin (validation phone, segments)
│   │   │   ├── whatsapp.py           # BaseWhatsAppMixin (formatage, média)
│   │   │   ├── postal.py             # BasePostalMixin (adresse, coût, impression)
│   │   │   └── notification.py       # BaseNotificationMixin (formatage, prefs)
│   │   ├── sendgrid.py               # SendGrid (email)
│   │   ├── mailgun.py                # Mailgun (email)
│   │   ├── django_email.py           # Django SMTP (email)
│   │   ├── twilio.py                 # Twilio (SMS + WhatsApp)
│   │   ├── smspartner.py             # SMSPartner (SMS français)
│   │   ├── laposte.py                # La Poste (courrier postal)
│   │   ├── sendinblue.py             # SendinBlue (email + SMS)
│   │   └── notification.py           # In-app notifications
│   │
│   ├── views/                        # Vues Django
│   │   ├── __init__.py
│   │   ├── missive_views.py          # CRUD des missives
│   │   └── webhooks.py               # Endpoints webhooks
│   │
│   ├── templates/                    # Templates HTML
│   └── migrations/                   # Migrations Django
│
├── tests/                            # Tests et config dev
├── dev.py                            # CLI de développement
├── manage.py                         # Django management
├── pyproject.toml                    # Configuration package
└── docs/
    ├── README.md
    ├── USAGE.md
    ├── EXAMPLES.md
    ├── DEVELOPMENT.md
    ├── ARCHITECTURE.md
    └── STRUCTURE.md                  # Ce fichier
```

## 🎯 Modèles (models/)

Les modèles sont organisés dans un dossier pour une meilleure lisibilité :

### Fichiers de modèles

- **`choices.py`** - Tous les enums (`MissiveType`, `MissiveStatus`, `MissivePriority`, `RecipientType`)
- **`recipient.py`** - Modèle `Recipient` avec coordonnées complètes (nom, email, téléphone, adresse postale)
- **`missive.py`** - Modèle principal `Missive` avec GenericForeignKey
- **`attachment.py`** - `MissiveAttachment` pour pièces jointes (fichier local OU URL) avec GenericForeignKey
- **`event.py`** - `MissiveEvent` pour l'historique/tracking
- **`template.py`** - `MissiveTemplate` pour les templates réutilisables
- **`__init__.py`** - Exporte tous les modèles

### Import unifié

Tous les modèles restent accessibles de la même façon :

```python
from missive.models import Missive, Recipient, MissiveAttachment, MissiveEvent, MissiveTemplate
from missive.models import MissiveType, MissiveStatus, MissivePriority, RecipientType
```

## 🔌 Providers (providers/)

### Architecture modulaire par mixins

Le `BaseProvider` est organisé en **mixins** par type de missive :

```
providers/base/
├── common.py       # BaseProviderCommon (config, status, events)
├── email.py        # BaseEmailMixin (validation email, spam, SMTP)
├── sms.py          # BaseSMSMixin (validation phone, segments, coût)
├── whatsapp.py     # BaseWhatsAppMixin (formatage, média)
├── postal.py       # BasePostalMixin (validation adresse, coût postal)
└── notification.py # BaseNotificationMixin (formatage, préférences)
```

**BaseProvider** = composition de tous les mixins via héritage multiple.

### Provider concret exemple

```python
# providers/sendgrid.py
from .base import BaseProvider

class SendGridProvider(BaseProvider):
    name = "SendGrid"
    supported_types = [MissiveType.EMAIL]
    
    def send_email(self) -> bool:
        """Implémentation SendGrid"""
        # Hérite automatiquement de BaseEmailMixin :
        # - validate_email()
        # - test_smtp_server()
        # - add_attachment_email()
        # - calculate_spam_score()
        
        email = self.missive.get_recipient_email()
        validation = self.validate_email(email)  # ← du mixin
        
        # ... logique d'envoi SendGrid
        return True
    
    def handle_webhook(self, payload, headers):
        """Traite les webhooks SendGrid"""
        # ... logique de traitement
        pass
```

### Providers disponibles :

| Provider | Type | Fichier |
|----------|------|---------|
| SendGrid | Email | `providers/sendgrid.py` |
| Mailgun | Email | `providers/mailgun.py` |
| Django Email | Email | `providers/django_email.py` |
| Twilio | SMS + WhatsApp | `providers/twilio.py` |
| SMSPartner | SMS | `providers/smspartner.py` |
| SendinBlue | Email + SMS | `providers/sendinblue.py` |
| La Poste | Postal + Email AR | `providers/laposte.py` |
| In-App | Notification | `providers/notification.py` |

### Ajouter un nouveau provider :

1. Créer `providers/mon_provider.py`
2. Hériter de `BaseProvider`
3. Définir `supported_types`
4. Implémenter les méthodes `send_*()` selon les types supportés
5. Implémenter `handle_webhook()`
6. L'ajouter dans `sender.py` et `views/webhooks.py`

**Avantage des mixins** : Vous héritez automatiquement de toutes les méthodes utiles !

```python
from .base import BaseProvider

class MonProvider(BaseProvider):
    name = "MonProvider"
    supported_types = [MissiveType.EMAIL, MissiveType.SMS]
    
    def send_email(self) -> bool:
        # Utilise automatiquement :
        # - self.validate_email()
        # - self.test_smtp_server()
        # - self.add_attachment_email()
        # - self.calculate_spam_score()
        pass
    
    def send_sms(self) -> bool:
        # Utilise automatiquement :
        # - self.validate_phone_number()
        # - self.calculate_sms_segments()
        # - self.format_phone_international()
        pass
```

## 📨 Flux d'envoi

```
1. Créer la missive
   MissiveBuilder.create_email(source_object=order, ...)
   
2. Envoyer
   MissiveSender.send(missive)
   ↓
   Détermine le provider (sendgrid, twilio, etc.)
   ↓
   Provider.send()
   ↓
   API externe
   ↓
   Statut = SENT + MissiveEvent créé
```

## 🔔 Flux des webhooks

```
Provider → POST /missive/webhook/{provider}/
          ↓
      WebhookView (vue unifiée)
          ↓
      Détecte le provider depuis l'URL
          ↓
      Provider.handle_webhook(payload, headers)
          ↓
      1. Valide signature
      2. Trouve la missive (via external_id)
      3. Met à jour le statut
      4. Crée un MissiveEvent (avec le provider)
          ↓
      Retourne (success, error, missive)
```

## 🔗 URLs

### URLs (`urls.py`)

**Interface CRUD :**
```python
/missive/              # Liste
/missive/123/          # Détail
/missive/create/       # Créer
/missive/123/update/   # Modifier
/missive/123/delete/   # Supprimer
```

**Webhook unifié :**
```python
/missive/webhook/{provider}/   # Un seul endpoint pour tous les providers
                                # Ex: /missive/webhook/sendgrid/
                                #     /missive/webhook/twilio/
                                #     /missive/webhook/laposte/
/missive/webhook/test/         # Test (dev only)
```

## ⚙️ Configuration (`settings.py`)

```python
MISSIVE_CONFIG = {
    # Choix des providers par type
    'PROVIDERS': {
        'EMAIL': 'sendgrid',     # ou 'mailgun', 'django'
        'SMS': 'twilio',         # ou 'smspartner'
        'WHATSAPP': 'twilio',
        'POSTAL': 'laposte',
        'NOTIFICATION': 'inapp',
    },
    
    # Configuration SendGrid
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    'SENDGRID_WEBHOOK_KEY': os.getenv('SENDGRID_WEBHOOK_KEY'),
    
    # Configuration Twilio
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
    'TWILIO_WHATSAPP_NUMBER': os.getenv('TWILIO_WHATSAPP_NUMBER'),
    
    # Configuration Mailgun
    'MAILGUN_API_KEY': os.getenv('MAILGUN_API_KEY'),
    'MAILGUN_DOMAIN': os.getenv('MAILGUN_DOMAIN'),
    
    # Configuration SMSPartner
    'SMSPARTNER_API_KEY': os.getenv('SMSPARTNER_API_KEY'),
    'SMSPARTNER_SENDER': 'YourApp',
    
    # Configuration La Poste
    'LAPOSTE_API_KEY': os.getenv('LAPOSTE_API_KEY'),
    'LAPOSTE_SENDER_ADDRESS': {...},
    
    # Général
    'DEFAULT_FROM_EMAIL': 'noreply@example.com',
}
```

## 🎓 Utilisation simple

### Envoyer une missive

```python
from missive import MissiveBuilder, MissiveSender, MissiveType

# Créer
missive = MissiveBuilder.create_email(
    source_object=order,
    sender=user,
    recipient_email='user@example.com',
    subject='Commande confirmée',
    body='...'
)

# Envoyer
MissiveSender.send(missive)
```

### Attacher un fichier

```python
from missive.models import MissiveAttachment

# Fichier local
attachment = MissiveAttachment.objects.create(
    missive=missive,  # ou content_object=order
    file=uploaded_file,
    filename="facture.pdf"
)

# URL externe (S3, etc.)
attachment = MissiveAttachment.objects.create(
    content_object=order,
    external_url="https://s3.amazonaws.com/bucket/file.pdf",
    filename="rapport.pdf"
)
```

### Configurer les webhooks

```python
# Dans urls.py de votre projet
urlpatterns = [
    path('missive/', include('missive.urls')),  # Tout est inclus
]

# Configurer dans vos providers :
# SendGrid webhook URL:   https://yourdomain.com/missive/webhook/sendgrid/
# Twilio webhook URL:     https://yourdomain.com/missive/webhook/twilio/
# Mailgun webhook URL:    https://yourdomain.com/missive/webhook/mailgun/
# La Poste webhook URL:   https://yourdomain.com/missive/webhook/laposte/
# SendinBlue webhook URL: https://yourdomain.com/missive/webhook/sendinblue/
```

## 🚀 Lancer le serveur de dev

```bash
python3 dev.py install-dev
python3 dev.py migrate
python3 dev.py runserver
```

Accès: http://127.0.0.1:8000/admin/ (admin/admin)

## 📚 Avantages de cette architecture

✅ **Modulaire** : BaseProvider = composition de mixins par type  
✅ **Simple** : Un provider = un fichier  
✅ **Cohérent** : Envoi + Webhooks au même endroit  
✅ **Extensible** : Facile d'ajouter un provider  
✅ **Organisé** : Modèles séparés par fichier (meilleure lisibilité)  
✅ **Réutilisable** : Méthodes utiles héritées automatiquement  
✅ **Pas de surcoût** : Pas de modèle Webhook inutile  
✅ **Traçable** : MissiveEvent suffit pour l'historique  
✅ **Flexible** : GenericForeignKey partout  
✅ **Fichiers externes** : Support S3, Google Drive, etc.  
✅ **Destinataires centralisés** : Modèle Recipient réutilisable  
✅ **Validation intégrée** : Tests de risque d'échec dans l'admin  

## 📖 Documentation complète

- **README.md** - Introduction
- **USAGE.md** - Guide utilisateur
- **EXAMPLES.md** - Exemples de code
- **DEVELOPMENT.md** - Guide développeur
- **ARCHITECTURE.md** - Architecture technique
- **STRUCTURE.md** - Ce fichier

