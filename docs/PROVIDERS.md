# Providers - Django Missive

Guide des providers disponibles et comment en ajouter.

## 📦 Providers disponibles

### Providers multi-types

| Provider | Types supportés | Fichier | Avantages |
|----------|----------------|---------|-----------|
| **SendinBlue/Brevo** | Email + SMS | `providers/sendinblue.py` | Un seul compte pour email + SMS |
| **La Poste** | Email AR + Postal | `providers/laposte.py` | Email recommandé électronique + courrier |
| **Twilio** | SMS + WhatsApp | `providers/twilio.py` | Leader mondial SMS/WhatsApp |

### Providers mono-type

| Provider | Type | Fichier | Usage |
|----------|------|---------|-------|
| **SendGrid** | Email | `providers/sendgrid.py` | Email transactionnel |
| **Mailgun** | Email | `providers/mailgun.py` | Email avec API simple |
| **Django Email** | Email | `providers/django_email.py` | SMTP natif Django (par défaut) |
| **SMSPartner** | SMS | `providers/smspartner.py` | SMS français |
| **In-App** | Notification | `providers/notification.py` | Notifications in-app |

## 🔧 Configuration

Dans `settings.py` :

```python
MISSIVE_CONFIG = {
    # Choisir le provider par type de missive
    'PROVIDERS': {
        'EMAIL': 'sendinblue',     # ou 'sendgrid', 'mailgun', 'django', 'laposte'
        'SMS': 'sendinblue',        # ou 'twilio', 'smspartner'
        'WHATSAPP': 'twilio',       # uniquement twilio pour l'instant
        'POSTAL': 'laposte',        # uniquement laposte pour l'instant
        'NOTIFICATION': 'inapp',    # notifications in-app
    },
    
    # Configuration SendinBlue (Email + SMS)
    'SENDINBLUE_API_KEY': os.getenv('SENDINBLUE_API_KEY'),
    'SENDINBLUE_SMS_SENDER': 'YourApp',
    
    # Configuration SendGrid (Email uniquement)
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    'SENDGRID_WEBHOOK_KEY': os.getenv('SENDGRID_WEBHOOK_KEY'),
    
    # Configuration Twilio (SMS + WhatsApp)
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    'TWILIO_PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
    'TWILIO_WHATSAPP_NUMBER': os.getenv('TWILIO_WHATSAPP_NUMBER'),
    
    # Configuration La Poste (Postal + Email AR)
    'LAPOSTE_API_KEY': os.getenv('LAPOSTE_API_KEY'),
    'LAPOSTE_SENDER_ADDRESS': {...},
    
    # Général
    'DEFAULT_FROM_EMAIL': 'noreply@example.com',
}
```

## 🎯 Exemples d'utilisation

### Utiliser SendinBlue pour tout (Email + SMS)

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'sendinblue',
        'SMS': 'sendinblue',  # Même provider !
    },
    'SENDINBLUE_API_KEY': os.getenv('SENDINBLUE_API_KEY'),
}
```

```python
from missive import MissiveBuilder, MissiveSender

# Email via SendinBlue
email = MissiveBuilder.create_email(
    source_object=order,
    sender=user,
    recipient_email='user@example.com',
    subject='Commande confirmée',
    body='...'
)
MissiveSender.send(email)  # → SendinBlueProvider.send_email()

# SMS via SendinBlue
sms = MissiveBuilder.create_sms(
    source_object=order,
    sender=user,
    recipient_phone='+33600000000',
    subject='RDV demain',
    body='...'
)
MissiveSender.send(sms)  # → SendinBlueProvider.send_sms()
```

### Mixer les providers

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'sendgrid',      # SendGrid pour les emails
        'SMS': 'twilio',          # Twilio pour les SMS
        'WHATSAPP': 'twilio',     # Twilio pour WhatsApp
        'POSTAL': 'laposte',      # La Poste pour le courrier
    },
}
```

### La Poste pour Email AR + Courrier

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'laposte',   # Email AR électronique
        'POSTAL': 'laposte',  # Courrier postal
    },
    'LAPOSTE_API_KEY': os.getenv('LAPOSTE_API_KEY'),
}
```

```python
# Email recommandé électronique
email_ar = MissiveBuilder.create_email(
    source_object=contract,
    sender=user,
    recipient_email='client@example.com',
    subject='Contrat à signer',
    body='...',
    is_registered=True  # Email AR
)
MissiveSender.send(email_ar)  # → LaPosteProvider.send_email()

# Courrier recommandé physique
letter = MissiveBuilder.from_object(
    source_object=contract,
    sender=user,
    missive_type=MissiveType.POSTAL,
    recipient_address='John Doe\n123 Rue Example\n75001 Paris',
    subject='Mise en demeure',
    body='...',
    is_registered=True,
    requires_signature=True
)
MissiveSender.send(letter)  # → LaPosteProvider.send_postal()
```

## 🛠️ Créer un nouveau provider

### Exemple : Provider qui supporte Email + SMS

Créer `missive/providers/myprovider.py` :

```python
from typing import Dict, Tuple, Optional
from .base import BaseProvider
from ..models import MissiveStatus

class MyProvider(BaseProvider):
    """Mon provider custom qui fait Email ET SMS"""
    
    name = "My Provider"
    supported_types = ['EMAIL', 'SMS']  # Multi-types
    
    # ===== ENVOI EMAIL =====
    def send_email(self) -> bool:
        """Envoie un email"""
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False
        
        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False
        
        try:
            # Votre logique d'envoi email ici
            api_key = self.config.get('MYPROVIDER_API_KEY')
            # ...
            
            external_id = "..."  # ID retourné par l'API
            
            self._update_status(MissiveStatus.SENT, provider=self.name, external_id=external_id)
            self._create_event('sent', 'Email envoyé')
            return True
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            return False
    
    # ===== ENVOI SMS =====
    def send_sms(self) -> bool:
        """Envoie un SMS"""
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False
        
        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False
        
        try:
            # Votre logique d'envoi SMS ici
            # ...
            
            self._update_status(MissiveStatus.SENT, provider=self.name)
            self._create_event('sent', 'SMS envoyé')
            return True
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            return False
    
    # ===== WEBHOOKS =====
    def validate_webhook_signature(self, payload: Dict, headers: Dict) -> Tuple[bool, str]:
        """Valide la signature du webhook"""
        # Votre logique de validation
        return True, ""
    
    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID de la missive"""
        return payload.get('reference_id')
    
    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement"""
        return payload.get('event', 'unknown')
```

### Ajouter le provider

1. **Dans `providers/__init__.py`** :

```python
from .myprovider import MyProvider

__all__ = [..., 'MyProvider']
```

2. **Dans `sender.py`**, ajouter dans le mapping :

```python
all_providers = {
    ...
    'myprovider': MyProvider,
}
```

3. **Configurer dans `settings.py`** :

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'myprovider',
        'SMS': 'myprovider',
    },
    'MYPROVIDER_API_KEY': os.getenv('MYPROVIDER_API_KEY'),
}
```

## 🌐 Webhooks

### Webhook unifié

Django Missive utilise **un seul endpoint** pour tous les webhooks :

```
/missive/webhook/{provider}/
```

Le provider est automatiquement détecté depuis l'URL.

### Ajouter un nouveau provider aux webhooks

1. Dans `providers/myprovider.py`, implémenter `handle_webhook()` :

```python
class MyProvider(BaseProvider):
    name = "My Provider"
    
    def handle_webhook(self, payload, headers):
        # Votre logique de traitement
        pass
```

2. Dans `views/webhooks.py`, ajouter au mapping :

```python
PROVIDER_CLASSES = {
    ...
    'myprovider': MyProvider,
}
```

C'est tout ! L'URL est automatique : `https://yourdomain.com/missive/webhook/myprovider/`

## 📊 Tableau récapitulatif

| Provider | Email | SMS | WhatsApp | Postal | Notification |
|----------|-------|-----|----------|--------|--------------|
| **SendinBlue** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **La Poste** | ✅ (AR) | ❌ | ❌ | ✅ | ❌ |
| **Twilio** | ❌ | ✅ | ✅ | ❌ | ❌ |
| SendGrid | ✅ | ❌ | ❌ | ❌ | ❌ |
| Mailgun | ✅ | ❌ | ❌ | ❌ | ❌ |
| SMSPartner | ❌ | ✅ | ❌ | ❌ | ❌ |
| Django Email | ✅ | ❌ | ❌ | ❌ | ❌ |
| In-App | ❌ | ❌ | ❌ | ❌ | ✅ |

## 🎯 Recommandations

### Startup / MVP
```python
'PROVIDERS': {
    'EMAIL': 'django',      # Gratuit, SMTP
    'SMS': 'twilio',         # Trial account
    'NOTIFICATION': 'inapp',
}
```

### Production économique
```python
'PROVIDERS': {
    'EMAIL': 'sendinblue',   # Bon rapport qualité/prix
    'SMS': 'sendinblue',     # Même compte
    'WHATSAPP': 'twilio',
    'POSTAL': 'laposte',
}
```

### Production enterprise
```python
'PROVIDERS': {
    'EMAIL': 'sendgrid',     # Très fiable, tracking avancé
    'SMS': 'twilio',         # Leader mondial
    'WHATSAPP': 'twilio',
    'POSTAL': 'laposte',
}
```

### France / Administrations
```python
'PROVIDERS': {
    'EMAIL': 'laposte',      # Email AR légal
    'POSTAL': 'laposte',     # Courrier recommandé
    'SMS': 'smspartner',     # Provider français
}
```

## 📝 Notes

- Un provider peut supporter plusieurs types (SendinBlue, La Poste, Twilio)
- La configuration se fait par type de missive, pas par provider
- Le système choisit automatiquement le bon provider selon le type
- Les webhooks sont gérés par le même provider (cohérence)

## 🔗 Documentation des APIs

- **SendGrid** : https://docs.sendgrid.com/
- **Mailgun** : https://documentation.mailgun.com/
- **SendinBlue** : https://developers.brevo.com/
- **Twilio** : https://www.twilio.com/docs
- **SMSPartner** : https://www.smspartner.fr/api/
- **La Poste** : https://developer.laposte.fr/

## 🚀 Tests

Chaque provider peut être testé individuellement :

```python
from missive.models import Missive, MissiveType
from missive.providers import SendinBlueProvider

missive = Missive.objects.create(...)

# Test direct du provider
provider = SendinBlueProvider(missive)

if provider.supports(MissiveType.EMAIL):
    success = provider.send_email()
    
if provider.supports(MissiveType.SMS):
    success = provider.send_sms()
```

