# Sélection des Providers - Django Missive

Guide pour choisir et changer les providers.

## 🎯 Ordre de priorité

Django Missive choisit le provider selon cet ordre :

1. **`Missive.provider`** (au niveau de la missive) 🥇
2. **`MISSIVE_CONFIG['PROVIDERS'][type]`** (configuration globale) 🥈
3. **Provider par défaut** selon le type 🥉

## 📝 Exemples

### 1. Configuration globale (recommandé)

Dans `settings.py` :

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'sendgrid',      # Tous les emails via SendGrid
        'SMS': 'twilio',          # Tous les SMS via Twilio
        'WHATSAPP': 'twilio',
        'POSTAL': 'laposte',
    },
}
```

```python
# Utilisation
missive = MissiveBuilder.create_email(
    sender=user,
    recipient_email='user@example.com',
    subject='Test',
    body='...'
)

MissiveSender.send(missive)  # → Utilise SendGrid (config globale)
```

### 2. Spécifier le provider par missive

Pour **forcer un provider spécifique** sur une missive :

```python
# Email important via SendGrid (meilleure délivrabilité)
missive_important = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient_email='vip@example.com',
    subject='Contrat important',
    body='...',
    provider='sendgrid',  # ← Force SendGrid pour cette missive
    priority=MissivePriority.HIGH
)

# Email marketing via Mailgun (moins cher)
missive_marketing = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient_email='client@example.com',
    subject='Newsletter',
    body='...',
    provider='mailgun',  # ← Force Mailgun pour cette missive
    priority=MissivePriority.NORMAL
)

MissiveSender.send(missive_important)  # → SendGrid
MissiveSender.send(missive_marketing)  # → Mailgun
```

### 3. Mixer les providers selon le contexte

```python
from missive import MissiveBuilder, MissiveSender

def send_order_confirmation(order):
    """Email via SendinBlue (moins cher pour le transactionnel)"""
    missive = MissiveBuilder.create_email(
        source_object=order,
        sender=order.user,
        recipient_email=order.email,
        subject=f'Commande #{order.id}',
        body='...',
        provider='sendinblue'  # Provider spécifique
    )
    MissiveSender.send(missive)

def send_legal_notice(user, address):
    """Courrier recommandé + Email AR via La Poste (légal)"""
    # Courrier postal
    postal = MissiveBuilder.from_object(
        source_object=user,
        sender=system_user,
        missive_type=MissiveType.POSTAL,
        recipient_address=address,
        subject='Mise en demeure',
        body='...',
        is_registered=True,
        provider='laposte'  # La Poste pour le légal
    )
    
    # Email AR (même provider)
    email_ar = MissiveBuilder.create_email(
        source_object=user,
        sender=system_user,
        recipient_email=user.email,
        subject='Mise en demeure (Email AR)',
        body='...',
        is_registered=True,
        provider='laposte'  # La Poste Email AR
    )
    
    MissiveSender.send(postal)
    MissiveSender.send(email_ar)
```

### 4. Changer de provider dynamiquement

```python
# Créer avec un provider
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient_email='user@example.com',
    subject='Test',
    body='...',
    provider='sendgrid'
)

# Le premier envoi échoue
if not MissiveSender.send(missive):
    # Changer de provider et réessayer
    missive.provider = 'mailgun'
    missive.status = MissiveStatus.PENDING  # Remettre en pending
    missive.save()
    
    MissiveSender.send(missive)  # Réessaye avec Mailgun
```

## 📊 Traçabilité avec MissiveEvent

Chaque événement enregistre le provider utilisé :

```python
# Après l'envoi, consulter l'historique
for event in missive.events.all():
    print(f"{event.created_at}: {event.event_type} via {event.provider}")

# Exemple de sortie:
# 2025-11-07 21:30:00: sent via SendGrid
# 2025-11-07 21:30:15: delivered via SendGrid
# 2025-11-07 21:35:42: opened via SendGrid
```

### Statistiques par provider

```python
from missive.models import MissiveEvent
from django.db.models import Count

# Nombre d'événements par provider
stats = MissiveEvent.objects.values('provider').annotate(
    count=Count('id')
).order_by('-count')

for stat in stats:
    print(f"{stat['provider']}: {stat['count']} événements")
```

## 🔄 Cas d'usage avancés

### A/B Testing de providers

```python
import random

def send_with_ab_test(user, subject, body):
    """Teste SendGrid vs Mailgun"""
    provider = random.choice(['sendgrid', 'mailgun'])
    
    missive = Missive.objects.create(
        sender=user,
        missive_type=MissiveType.EMAIL,
        recipient_email=user.email,
        subject=subject,
        body=body,
        provider=provider,  # A/B test
        metadata={'ab_test': 'email_provider'}
    )
    
    return MissiveSender.send(missive)
```

### Failover automatique

```python
def send_with_failover(missive, providers_list):
    """Essaie plusieurs providers jusqu'à succès"""
    for provider in providers_list:
        missive.provider = provider
        missive.save()
        
        if MissiveSender.send(missive):
            return True
        
        # Reset pour réessayer
        missive.status = MissiveStatus.PENDING
        missive.error_message = ''
    
    return False

# Usage
missive = Missive.objects.create(...)
success = send_with_failover(missive, ['sendgrid', 'mailgun', 'django'])
```

### Provider selon le pays

```python
def get_provider_for_country(country_code):
    """Choisit le provider selon le pays"""
    if country_code == 'FR':
        return 'smspartner'  # Provider français
    else:
        return 'twilio'  # International

# Usage
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.SMS,
    recipient_phone=phone,
    subject='Code',
    body='...',
    provider=get_provider_for_country(user.country)
)
```

## 🎨 Interface admin

Dans l'admin Django, vous pouvez :

1. **Créer une missive** et choisir le provider dans le formulaire
2. **Modifier le provider** avant l'envoi
3. **Voir le provider utilisé** dans la liste
4. **Filtrer par provider** dans les événements
5. **Voir l'historique** : quel provider a généré chaque événement

## 📋 Liste des providers disponibles

| Code | Provider | Types |
|------|----------|-------|
| `sendgrid` | SendGrid | Email |
| `mailgun` | Mailgun | Email |
| `sendinblue` / `brevo` | SendinBlue | Email + SMS |
| `django` | Django SMTP | Email |
| `twilio` | Twilio | SMS + WhatsApp |
| `smspartner` | SMSPartner | SMS |
| `laposte` | La Poste | Postal + Email AR |
| `inapp` | In-App | Notification |

## ⚠️ Validation

Le système vérifie automatiquement que le provider supporte le type de missive :

```python
# Ceci échouera car SendGrid ne supporte pas les SMS
missive = Missive.objects.create(
    missive_type=MissiveType.SMS,
    provider='sendgrid',  # ❌ SendGrid ne fait pas de SMS
    ...
)

MissiveSender.send(missive)  # → Échec avec message d'erreur
```

## 💡 Bonnes pratiques

1. **Config globale par défaut** : Définir dans `MISSIVE_CONFIG`
2. **Override au cas par cas** : Utiliser `missive.provider` seulement quand nécessaire
3. **Traçabilité** : Consulter `missive.events.all()` pour l'historique
4. **Metadata** : Stocker le contexte dans `missive.metadata`

```python
missive = Missive.objects.create(
    ...,
    provider='sendgrid',
    metadata={
        'campaign': 'black_friday',
        'segment': 'vip_customers',
        'ab_test_variant': 'A'
    }
)
```

