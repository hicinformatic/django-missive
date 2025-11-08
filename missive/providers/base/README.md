# Base Provider - Architecture Modulaire

Le provider de base est organisé en **mixins** pour une séparation claire des responsabilités par type de missive.

## 📁 Structure

```
base/
├── __init__.py         # BaseProvider (combine tous les mixins)
├── common.py           # BaseProviderCommon (fonctions communes)
├── email.py            # BaseEmailMixin (email)
├── sms.py              # BaseSMSMixin (SMS)
├── whatsapp.py         # BaseWhatsAppMixin (WhatsApp)
├── postal.py           # BasePostalMixin (courrier postal)
├── notification.py     # BaseNotificationMixin (notifications in-app)
└── README.md           # Ce fichier
```

## 🎯 Philosophie

Au lieu d'un énorme fichier `base.py` de 700+ lignes, nous avons :

✅ **1 fichier par type de missive** (email, SMS, postal, etc.)  
✅ **Fonctionnalités spécifiques** isolées dans leur mixin  
✅ **Composition** via héritage multiple  
✅ **Réutilisabilité** - Les providers n'héritent que de ce dont ils ont besoin  

## 📦 Fichiers détaillés

### `common.py` - BaseProviderCommon

**Responsabilité** : Fonctionnalités communes à tous les providers.

**Méthodes** :
- `__init__()` - Initialisation
- `supports(missive_type)` - Vérifie si type supporté
- `_get_config()` - Récupère la config Django
- `_update_status()` - Met à jour le statut de la missive
- `_create_event()` - Crée un événement de tracking
- `get_status_from_event()` - Mapping événement → statut

**Exemple** :
```python
class MyProvider(BaseProviderCommon):
    name = "MyProvider"
    supported_types = [MissiveType.EMAIL]
    
    # Hérite automatiquement de toutes les méthodes communes
```

### `email.py` - BaseEmailMixin

**Responsabilité** : Tout ce qui concerne les emails.

**Méthodes** :
- `send_email()` - Template pour envoi (à override)
- `validate_email(email)` - Validation syntaxique et domaine
- `_calculate_email_risk_score()` - Score de risque email
- `test_smtp_server(domain)` - Test de serveur SMTP
- `add_attachment_email(attachment)` - Prépare pièce jointe
- `calculate_spam_score(subject, body)` - Score de spam

**Exemple** :
```python
# Validation d'un email
validation = provider.validate_email("user@example.com")
# → {'is_valid': True, 'risk_score': 15, ...}

# Test du serveur SMTP
smtp_test = provider.test_smtp_server("example.com")
# → {'is_reachable': True, 'mx_records': [...], ...}
```

### `sms.py` - BaseSMSMixin

**Responsabilité** : Tout ce qui concerne les SMS.

**Méthodes** :
- `send_sms()` - Template pour envoi (à override)
- `validate_phone_number(phone, country)` - Validation téléphone
- `calculate_sms_segments(message)` - Calcul segments et coût
- `format_phone_international(phone, country)` - Formatage international

**Exemple** :
```python
# Validation téléphone
validation = provider.validate_phone_number("+33612345678")
# → {'is_valid': True, 'is_mobile': True, 'carrier': 'Orange', ...}

# Calcul du coût
segments = provider.calculate_sms_segments("Message de 200 caractères...")
# → {'segments': 2, 'cost': 0.10, 'encoding': 'GSM-7'}
```

### `whatsapp.py` - BaseWhatsAppMixin

**Responsabilité** : Tout ce qui concerne WhatsApp.

**Méthodes** :
- `send_whatsapp()` - Template pour envoi (à override)
- `validate_whatsapp_number(phone)` - Vérifie si numéro sur WhatsApp
- `format_whatsapp_message(body, body_text)` - Formatage WhatsApp (bold, italic)
- `add_attachment_whatsapp(attachment)` - Prépare média (image, vidéo, doc)

**Exemple** :
```python
# Formatage du message
formatted = provider.format_whatsapp_message(
    "<b>Important</b>: RDV demain"
)
# → "*Important*: RDV demain"

# Vérification des limites de fichier
media = provider.add_attachment_whatsapp(attachment)
# → {'media_type': 'image', 'max_size': 5242880, ...}
```

### `postal.py` - BasePostalMixin

**Responsabilité** : Tout ce qui concerne le courrier postal.

**Méthodes** :
- `send_postal()` - Template pour envoi (à override)
- `validate_postal_address(address)` - Validation adresse
- `calculate_postal_cost(weight, registered, international)` - Calcul coût
- `prepare_postal_attachments(attachments)` - Prépare pièces jointes pour impression

**Exemple** :
```python
# Validation adresse
validation = provider.validate_postal_address(address_multiline)
# → {'is_valid': True, 'is_complete': True, ...}

# Calcul coût
cost = provider.calculate_postal_cost(
    weight_grams=50,
    is_registered=True,
    international=False
)
# → {'cost': 5.79, 'format': 'recommandé', 'delivery_days': 2}
```

### `notification.py` - BaseNotificationMixin

**Responsabilité** : Tout ce qui concerne les notifications in-app.

**Méthodes** :
- `send_notification()` - Template pour envoi (à override)
- `format_notification_data()` - Formate pour frontend (titre, icône, URL)
- `check_user_notification_preferences(user)` - Vérifie préférences user

**Exemple** :
```python
# Formatage pour frontend
data = provider.format_notification_data()
# → {'title': '...', 'body': '...', 'icon': '🔔', 'url': '/orders/123/'}

# Vérification préférences
prefs = provider.check_user_notification_preferences(user)
# → {'accepts_notifications': True, 'quiet_hours': False, ...}
```

## 🔄 Composition du BaseProvider

Le `BaseProvider` final combine **tous les mixins** :

```python
class BaseProvider(
    BaseProviderCommon,      # Fonctions communes
    BaseEmailMixin,          # Méthodes email
    BaseSMSMixin,            # Méthodes SMS
    BaseWhatsAppMixin,       # Méthodes WhatsApp
    BasePostalMixin,         # Méthodes postal
    BaseNotificationMixin,   # Méthodes notification
):
    """
    Provider complet avec toutes les fonctionnalités.
    """
    pass
```

**Avantages** :
- Tous les providers concrets héritent automatiquement de **toutes** les fonctionnalités
- Chaque provider peut override uniquement ce qu'il souhaite
- Code mieux organisé et plus facile à maintenir

## 🎓 Utilisation dans les providers concrets

### Provider simple (1 seul type)

```python
# providers/sendgrid.py
from .base import BaseProvider

class SendGridProvider(BaseProvider):
    name = "SendGrid"
    supported_types = [MissiveType.EMAIL]
    
    def send_email(self) -> bool:
        """Implémentation SendGrid spécifique"""
        # Hérite automatiquement de :
        # - validate_email()
        # - test_smtp_server()
        # - add_attachment_email()
        # - calculate_spam_score()
        # etc.
        
        email = self.missive.get_recipient_email()
        # ... logique d'envoi SendGrid
        return True
```

### Provider multi-types

```python
# providers/twilio.py
from .base import BaseProvider

class TwilioProvider(BaseProvider):
    name = "Twilio"
    supported_types = [MissiveType.SMS, MissiveType.WHATSAPP]
    
    def send_sms(self) -> bool:
        """Implémentation Twilio SMS"""
        # Hérite de BaseSMSMixin :
        # - validate_phone_number()
        # - calculate_sms_segments()
        # - format_phone_international()
        
        phone = self.missive.get_recipient_phone()
        formatted = self.format_phone_international(phone)
        # ... logique d'envoi Twilio
        return True
    
    def send_whatsapp(self) -> bool:
        """Implémentation Twilio WhatsApp"""
        # Hérite de BaseWhatsAppMixin :
        # - validate_whatsapp_number()
        # - format_whatsapp_message()
        # - add_attachment_whatsapp()
        
        phone = self.missive.get_recipient_phone()
        message = self.format_whatsapp_message(
            self.missive.body,
            self.missive.body_text
        )
        # ... logique d'envoi Twilio WhatsApp
        return True
```

## 🔧 Override de méthodes

Les providers peuvent override les méthodes des mixins :

```python
class LaPosteProvider(BaseProvider):
    name = "La Poste"
    supported_types = [MissiveType.POSTAL, MissiveType.EMAIL]
    
    def calculate_postal_cost(self, weight_grams, is_registered, international):
        """Override avec tarifs La Poste spécifiques"""
        # Logique personnalisée pour La Poste
        # Tarifs mis à jour, options Colissimo, etc.
        return super().calculate_postal_cost(...)
    
    def validate_postal_address(self, address):
        """Override avec validation via API La Poste"""
        # Utiliser l'API La Poste pour valider l'adresse
        # https://datanova.laposte.fr/datasets/laposte-hexasmal
        result = super().validate_postal_address(address)
        # ... enrichir avec données La Poste
        return result
```

## 📊 Statistiques de la refactorisation

**Avant** : 1 fichier monolithique
- `base.py` - **691 lignes**

**Maintenant** : 7 fichiers modulaires
```
base/
├── __init__.py         # 278 lignes - BaseProvider complet
├── common.py           # 139 lignes - Fonctions communes
├── email.py            # 262 lignes - Email (validation, spam, SMTP)
├── sms.py              # 202 lignes - SMS (validation, segments, coût)
├── whatsapp.py         # 134 lignes - WhatsApp (formatage, média)
├── postal.py           # 162 lignes - Postal (adresse, coût, impression)
└── notification.py     # 109 lignes - Notification (formatage, prefs)

Total: ~1286 lignes (mieux organisées !)
```

## ✨ Avantages

✅ **Séparation des responsabilités** - Chaque fichier = 1 type de missive  
✅ **Lisibilité** - Plus facile de trouver une fonctionnalité  
✅ **Maintenabilité** - Modifications isolées par type  
✅ **Testabilité** - Tests unitaires par mixin  
✅ **Extensibilité** - Facile d'ajouter un nouveau type  
✅ **Réutilisabilité** - Les mixins peuvent être utilisés indépendamment  
✅ **Documentation** - Chaque fichier bien documenté  

## 🚀 Fonctionnalités par type

| Type | Mixin | Fonctionnalités clés |
|------|-------|---------------------|
| **Email** | `BaseEmailMixin` | Validation email, MX records, spam score, SMTP test |
| **SMS** | `BaseSMSMixin` | Validation phone, segments, coût, formatage international |
| **WhatsApp** | `BaseWhatsAppMixin` | Validation WhatsApp, formatage markdown, limites média |
| **Postal** | `BasePostalMixin` | Validation adresse, calcul coût, préparation impression |
| **Notification** | `BaseNotificationMixin` | Formatage data, préférences user, icônes |
| **Commun** | `BaseProviderCommon` | Config, status, events, webhooks |

## 💡 Bonnes pratiques

### 1. Un provider = uniquement les méthodes send_*

```python
class MyEmailProvider(BaseProvider):
    supported_types = [MissiveType.EMAIL]
    
    # Implémenter UNIQUEMENT l'envoi
    def send_email(self) -> bool:
        # Utiliser les méthodes héritées
        email = self.missive.get_recipient_email()
        validation = self.validate_email(email)  # ← du mixin
        
        if validation['risk_score'] > 70:
            return False
        
        # Logique d'envoi spécifique
        ...
```

### 2. Override seulement si nécessaire

```python
class CustomSMSProvider(BaseProvider):
    supported_types = [MissiveType.SMS]
    
    # Override si logique différente
    def calculate_sms_segments(self, message):
        # Logique personnalisée
        result = super().calculate_sms_segments(message)
        result['custom_field'] = '...'
        return result
```

### 3. Utiliser les TODO comme guide

Chaque mixin contient des `# TODO:` avec des exemples d'implémentation :

```python
# TODO: Vérifier les enregistrements MX
# try:
#     import dns.resolver
#     mx_records = dns.resolver.resolve(domain, 'MX')
#     details['mx_records'] = [str(r.exchange) for r in mx_records]
# except:
#     warnings.append("Aucun enregistrement MX trouvé")
```

Décommentez et adaptez selon vos besoins !

## 🔍 Exemple complet : Provider multi-types

```python
from .base import BaseProvider
from ..models import MissiveType

class SuperProvider(BaseProvider):
    """Provider qui supporte email ET SMS"""
    
    name = "SuperProvider"
    supported_types = [MissiveType.EMAIL, MissiveType.SMS]
    
    def send_email(self) -> bool:
        """Envoi email"""
        # Utilise BaseEmailMixin
        email = self.missive.get_recipient_email()
        validation = self.validate_email(email)
        spam = self.calculate_spam_score(
            self.missive.subject,
            self.missive.body
        )
        
        if spam['spam_score'] > 50:
            return False
        
        # ... envoi via API
        return True
    
    def send_sms(self) -> bool:
        """Envoi SMS"""
        # Utilise BaseSMSMixin
        phone = self.missive.get_recipient_phone()
        validation = self.validate_phone_number(phone)
        segments = self.calculate_sms_segments(self.missive.body_text)
        
        if segments['segments'] > 3:
            # Message trop long
            return False
        
        # ... envoi via API
        return True
    
    def handle_webhook(self, payload, headers):
        """Gestion des webhooks"""
        # Utilise BaseProviderCommon
        valid, error = self.validate_webhook_signature(payload, headers)
        if not valid:
            return False, error, None
        
        # ... traitement
        return True, "", missive
```

## 📚 Documentation associée

- **VALIDATION.md** - Guide complet sur la validation et les risques
- **ADMIN_ACTIONS.md** - Actions admin utilisant ces méthodes
- **PROVIDERS.md** - Liste de tous les providers
- **ARCHITECTURE.md** - Architecture globale de la bibliothèque

## 🎯 Points clés

1. **BaseProvider = composition de 6 mixins**
2. **Chaque mixin = 1 responsabilité claire**
3. **Héritage multiple** pour combiner les fonctionnalités
4. **Override optionnel** pour personnalisation
5. **TODO bien documentés** pour implémentations futures
6. **Rétrocompatibilité totale** - Les providers existants fonctionnent sans changement

