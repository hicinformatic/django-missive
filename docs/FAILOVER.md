# 🔄 Système de Fallback et Failover

Ce document explique le système de **fallback automatique** des providers dans django-missive.

## 🎯 Vue d'ensemble

Lorsqu'un provider est en panne ou échoue, django-missive peut automatiquement basculer sur un provider de secours. Cela garantit une haute disponibilité pour vos envois.

### Avantages

- ✅ **Haute disponibilité** : Si un provider est down, un autre prend le relais
- ✅ **Résilience** : Pas de perte de messages en cas de panne
- ✅ **Optimisation des coûts** : Utiliser des providers moins chers en priorité
- ✅ **Flexibilité** : Configurer différents ordres de priorité par type de missive
- ✅ **Health check intégré** : Détection automatique des providers indisponibles

## 📝 Configuration

### Configuration de base

Dans votre `settings.py` :

```python
# Nouveau système de configuration avec fallback
MISSIVE_PROVIDERS = {
    # Emails : SendGrid en priorité, puis Mailgun, puis SMTP Django
    'EMAIL': [
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.mailgun.MailgunProvider',
        'missive.providers.django_email.DjangoEmailProvider',  # Fallback ultime
    ],
    
    # SMS : Twilio puis SMSPartner
    'SMS': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    
    # WhatsApp : Twilio uniquement
    'WHATSAPP': [
        'missive.providers.twilio.TwilioProvider',
    ],
    
    # Postal : La Poste uniquement
    'POSTAL': [
        'missive.providers.laposte.LaPosteProvider',
    ],
    
    # Notifications : In-app uniquement
    'NOTIFICATION': [
        'missive.providers.notification.InAppNotificationProvider',
    ],
}
```

### Configuration simple (sans fallback)

Si vous ne voulez qu'un seul provider par type :

```python
MISSIVE_PROVIDERS = {
    'EMAIL': 'missive.providers.sendgrid.SendGridProvider',  # String simple
    'SMS': 'missive.providers.twilio.TwilioProvider',
}
```

Sera automatiquement converti en liste.

### Ancienne configuration (deprecated)

L'ancienne configuration est toujours supportée mais génère un warning :

```python
MISSIVE_CONFIG = {
    'PROVIDERS': {
        'EMAIL': 'missive.providers.sendgrid.SendGridProvider',
        # ...
    }
}
```

⚠️ **Migration recommandée** vers `MISSIVE_PROVIDERS` pour bénéficier du fallback.

## 🚀 Utilisation

### Envoi standard avec fallback

```python
from missive.models import Missive
from missive.sender import MissiveSender

missive = Missive.objects.create(
    sender=request.user,
    missive_type="EMAIL",
    recipient_email="user@example.com",
    subject="Test",
    body="<p>Hello</p>",
)

# Envoi avec fallback automatique
try:
    success = MissiveSender.send(missive)
    print("✅ Envoyé avec succès")
except RuntimeError as e:
    print(f"❌ Tous les providers ont échoué: {e}")
```

### Désactiver le fallback

```python
# Utiliser UNIQUEMENT le premier provider, sans essayer les suivants
try:
    success = MissiveSender.send(missive, enable_fallback=False)
except RuntimeError as e:
    print(f"❌ Le provider principal a échoué: {e}")
```

### Désactiver le health check

```python
# Ne pas vérifier la santé du provider avant l'envoi (plus rapide mais moins sûr)
success = MissiveSender.send(missive, skip_health_check=True)
```

### Provider explicite (pas de fallback)

```python
# Si vous spécifiez un provider sur la missive, pas de fallback
missive = Missive.objects.create(
    sender=request.user,
    missive_type="EMAIL",
    provider="missive.providers.mailgun.MailgunProvider",  # Forcer Mailgun
    recipient_email="user@example.com",
    subject="Test",
    body="<p>Hello</p>",
)

MissiveSender.send(missive)  # Utilisera UNIQUEMENT Mailgun
```

## 🔍 Processus de fallback

### Étapes

Lorsque vous appelez `MissiveSender.send(missive)` :

1. **Récupération de la liste des providers** :
   - Si `missive.provider` est défini → utilise CE provider uniquement (pas de fallback)
   - Sinon, charge la liste depuis `MISSIVE_PROVIDERS[missive.missive_type]`
   - Fallback sur les providers par défaut si non configuré

2. **Pour chaque provider dans l'ordre** :
   - **Health check** (si `skip_health_check=False`) :
     - Appelle `provider.health_check()`
     - Si `is_healthy=False` → skip ce provider et essaie le suivant
   - **Tentative d'envoi** :
     - Instancie le provider
     - Appelle `provider.send()`
     - Si succès → termine et met à jour `missive.provider`
     - Si échec → essaie le suivant (si `enable_fallback=True`)

3. **Résultat** :
   - Si au moins un provider a réussi → retourne `True`
   - Si tous ont échoué → lève `RuntimeError` avec détails des tentatives

### Exemple de logs

```
INFO: Missive 123: Tentative d'envoi avec 3 provider(s) disponible(s)
INFO: Missive 123: Tentative 1/3 avec SendGridProvider
WARNING: Missive 123: SendGridProvider n'est pas healthy, skip
INFO: Missive 123: Tentative 2/3 avec MailgunProvider
INFO: Missive 123: ✅ Envoyé avec succès via MailgunProvider (tentative 2/3)
```

## ⚙️ Scénarios d'usage

### Scénario 1 : Optimisation des coûts

Utiliser un provider gratuit/moins cher en priorité, puis un payant :

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.django_email.DjangoEmailProvider',  # SMTP gratuit
        'missive.providers.sendgrid.SendGridProvider',         # Payant si SMTP fail
    ],
}
```

### Scénario 2 : Haute disponibilité

Plusieurs providers payants en redondance :

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.mailgun.MailgunProvider',
        'missive.providers.sendinblue.SendinBlueProvider',
    ],
}
```

### Scénario 3 : Géographie

Providers différents selon la région :

```python
# settings_eu.py
MISSIVE_PROVIDERS = {
    'SMS': [
        'missive.providers.smspartner.SMSPartnerProvider',  # Provider français
        'missive.providers.twilio.TwilioProvider',          # Fallback international
    ],
}

# settings_us.py
MISSIVE_PROVIDERS = {
    'SMS': [
        'missive.providers.twilio.TwilioProvider',          # Provider US
    ],
}
```

### Scénario 4 : Migration progressive

Migrer d'un provider à un autre :

```python
# Phase 1 : Ancien provider en priorité, nouveau en test
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.sendgrid.SendGridProvider',  # Ancien
        'missive.providers.mailgun.MailgunProvider',    # Nouveau (fallback)
    ],
}

# Phase 2 : Nouveau provider en priorité
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.mailgun.MailgunProvider',    # Nouveau
        'missive.providers.sendgrid.SendGridProvider',  # Ancien (fallback)
    ],
}

# Phase 3 : Nouveau provider uniquement
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.mailgun.MailgunProvider',
    ],
}
```

## 🏥 Health Check

Le health check est automatiquement effectué avant chaque tentative d'envoi.

### Qu'est-ce qui est vérifié ?

- **Statut opérationnel** : Le service est-il up ?
- **Crédits** : Reste-t-il des crédits/quota ?
- **Rate limits** : Le rate limit est-il atteint ?

### Exemple de health check

```python
from missive.providers.sendgrid import SendGridProvider

provider = SendGridProvider()
health = provider.health_check()

# {
#     'is_healthy': False,
#     'status': 'critical',
#     'summary': 'SendGrid : Problèmes critiques - 2 issue(s) ⚠️',
#     'issues': [
#         'Service indisponible',
#         'Crédits faibles: 10 emails'
#     ],
#     'recommendations': [
#         'Recharger le compte provider'
#     ]
# }
```

### Désactiver le health check

Si le health check est trop lent ou cause des faux positifs :

```python
# Globalement dans settings.py
MISSIVE_CONFIG = {
    'SKIP_HEALTH_CHECK': True,
}

# Ou par appel
MissiveSender.send(missive, skip_health_check=True)
```

## 📊 Monitoring

### Logger les tentatives

django-missive log automatiquement tous les essais :

```python
import logging

# Dans settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'missive_failover.log',
        },
    },
    'loggers': {
        'missive.sender': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

### Créer un MissiveAttempt model (optionnel)

Pour tracer toutes les tentatives en base :

```python
class MissiveAttempt(models.Model):
    """Traçabilité des tentatives d'envoi."""
    missive = models.ForeignKey(Missive, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255)
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=50)  # success, failed, skipped
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Alertes

Configurer des alertes si tous les providers échouent :

```python
from django.core.mail import mail_admins

try:
    MissiveSender.send(missive)
except RuntimeError as e:
    # Alerter les admins
    mail_admins(
        subject=f"CRITIQUE: Échec d'envoi missive {missive.id}",
        message=str(e),
        fail_silently=True,
    )
    
    # Ou intégration Sentry
    import sentry_sdk
    sentry_sdk.capture_exception(e)
```

## 🧪 Tests

### Tester le fallback

```python
from unittest.mock import patch, MagicMock
from django.test import TestCase
from missive.models import Missive
from missive.sender import MissiveSender

class FailoverTestCase(TestCase):
    def test_fallback_to_second_provider(self):
        """Test que le fallback fonctionne si le premier provider échoue."""
        missive = Missive.objects.create(
            sender=self.user,
            missive_type="EMAIL",
            recipient_email="test@example.com",
        )
        
        # Mock : Premier provider échoue, deuxième réussit
        with patch('missive.providers.sendgrid.SendGridProvider.send', return_value=False):
            with patch('missive.providers.mailgun.MailgunProvider.send', return_value=True):
                success = MissiveSender.send(missive)
                
                self.assertTrue(success)
                # Vérifier que c'est Mailgun qui a été utilisé
                self.assertIn('mailgun', missive.provider.lower())
    
    def test_all_providers_fail(self):
        """Test que RuntimeError est levée si tous échouent."""
        missive = Missive.objects.create(
            sender=self.user,
            missive_type="EMAIL",
            recipient_email="test@example.com",
        )
        
        # Mock : Tous les providers échouent
        with patch('missive.providers.sendgrid.SendGridProvider.send', return_value=False):
            with patch('missive.providers.mailgun.MailgunProvider.send', return_value=False):
                with self.assertRaises(RuntimeError):
                    MissiveSender.send(missive)
```

## 🎓 Bonnes pratiques

### 1. Toujours avoir un fallback local

Avoir au moins Django Email SMTP comme dernier recours :

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.django_email.DjangoEmailProvider',  # Toujours OK
    ],
}
```

### 2. Surveiller les coûts

Si le fallback utilise un provider plus cher, mettre des alertes :

```python
# Après l'envoi
if 'expensive_provider' in missive.provider:
    send_alert("Fallback sur provider coûteux!")
```

### 3. Tester régulièrement

Lancer des tests périodiques pour vérifier que le fallback fonctionne :

```python
# Management command
python manage.py test_failover
```

### 4. Éviter les boucles infinies

Ne pas configurer de fallback circulaire :

```python
# ❌ MAUVAIS
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'custom.Provider1',  # Fallback sur Provider2
        'custom.Provider2',  # Fallback sur Provider1 ⚠️
    ],
}
```

### 5. Documenter les priorités

Expliquer pourquoi tel provider est prioritaire :

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        # SendGrid : Meilleur taux de délivrabilité
        'missive.providers.sendgrid.SendGridProvider',
        
        # Mailgun : Moins cher, mais moins fiable
        'missive.providers.mailgun.MailgunProvider',
        
        # SMTP : Gratuit, dernier recours
        'missive.providers.django_email.DjangoEmailProvider',
    ],
}
```

## 🔧 Paramètres avancés

### Configuration globale

```python
MISSIVE_CONFIG = {
    # Désactiver le health check globalement (performance)
    'SKIP_HEALTH_CHECK': False,
    
    # Timeout pour le health check (secondes)
    'HEALTH_CHECK_TIMEOUT': 5,
    
    # Nombre maximum de tentatives de fallback
    'MAX_FALLBACK_ATTEMPTS': 3,
    
    # Délai entre les tentatives (secondes)
    'FALLBACK_RETRY_DELAY': 1,
}
```

### Provider personnalisé avec fallback

```python
class MyCustomProvider(BaseProvider):
    name = "CustomProvider"
    
    def send_email(self) -> bool:
        try:
            # Tentative d'envoi
            return self._send_via_api()
        except APIError:
            # Fallback interne au provider
            return self._send_via_smtp()
```

## 📚 Références

- [MONITORING.md](MONITORING.md) : Monitoring et health check
- [ARCHITECTURE.md](ARCHITECTURE.md) : Architecture des providers
- [README.md](../README.md) : Documentation générale

---

**Documentation django-missive** | [Retour à l'index](../README.md)

