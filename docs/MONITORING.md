# 📊 Monitoring des Providers

Ce document explique le système de monitoring et de gestion des crédits/statuts des providers.

## 🎯 Vue d'ensemble

Chaque provider peut maintenant exposer :
- **Services disponibles** : Liste granulaire des fonctionnalités offertes
- **Statut opérationnel** : operational, degraded, down, unknown
- **Crédits/Quotas** : Montant restant, type (argent, emails, SMS, illimité)
- **Rate limits** : Limitations de débit par seconde/minute/heure/jour
- **SLA** : Uptime %, temps de réponse, taux de succès
- **Health check** : Vérification automatique de la santé du provider

## 🔧 Services disponibles

### Déclaration

Chaque provider déclare sa liste de services :

```python
class SendGridProvider(BaseProvider):
    name = "SendGrid"
    supported_types = ["EMAIL"]
    services = ["email", "email_transactional", "email_marketing"]
```

### Exemples de services par provider

#### SendGrid
```python
services = ["email", "email_transactional", "email_marketing"]
```

#### Brevo/SendinBlue (Multi-canal)
```python
services = [
    "email",
    "email_transactional",
    "email_marketing",
    "sms",
    "contacts",
    "automation",
]
```

#### La Poste (Services spécialisés)
```python
services = [
    "postal",              # Courrier simple
    "postal_registered",   # Recommandé R1
    "postal_signature",    # Recommandé R2/R3 avec signature
    "email_ar",            # Email avec AR électronique
    "colissimo",           # Colis (future extension)
]
```

#### Twilio (Communication)
```python
services = ["sms", "whatsapp", "voice", "verify"]
```

#### SMSPartner
```python
services = ["sms", "sms_low_cost", "sms_premium"]
```

### Vérification d'un service

```python
provider = SendGridProvider()
if provider.has_service("email_marketing"):
    # Utiliser la fonctionnalité
    pass
```

## 📈 Monitoring du statut

### Méthode `get_service_status()`

Chaque provider implémente cette méthode pour retourner son statut :

```python
def get_service_status(self) -> Dict[str, Any]:
    """
    Récupère le statut complet du provider.
    
    Returns:
        Dict contenant :
        - status (str): 'operational', 'degraded', 'down', 'unknown'
        - is_available (bool): Provider disponible
        - services (List[str]): Liste des services offerts
        - credits (Dict): Informations sur les crédits
        - rate_limits (Dict): Limites de débit
        - sla (Dict): SLA et performances
        - last_check (datetime): Date du dernier check
        - warnings (List[str]): Avertissements
        - details (Dict): Détails spécifiques au provider
    """
```

### Exemples d'utilisation

#### Vérifier le statut complet

```python
from missive.providers.sendgrid import SendGridProvider

provider = SendGridProvider()
status = provider.get_service_status()

print(f"Status: {status['status']}")
print(f"Available: {status['is_available']}")
print(f"Services: {', '.join(status['services'])}")
print(f"Warnings: {status['warnings']}")
```

#### Vérifier spécifiquement les crédits

```python
provider = SMSPartnerProvider()
credits = provider.check_credits()

if credits['needs_refill']:
    print(f"⚠️ Recharge nécessaire!")
    print(f"Solde: {credits['remaining']} {credits['currency']}")
    print(f"URL: {credits['refill_url']}")
```

#### Vérifier les rate limits

```python
provider = TwilioProvider()
limits = provider.check_rate_limits()

if limits['is_throttled']:
    print(f"⚠️ Rate limit atteint, attendre...")
    time.sleep(60)
```

#### Health check complet

```python
provider = SendinBlueProvider()
health = provider.health_check()

if not health['is_healthy']:
    print(f"❌ {health['summary']}")
    for issue in health['issues']:
        print(f"  - {issue}")
    for rec in health['recommendations']:
        print(f"  ➤ {rec}")
else:
    print(f"✅ {health['summary']}")
```

## 💰 Types de crédits

### Money (Prépaiement)

Providers comme **Twilio**, **SMSPartner**, **La Poste** :

```json
{
  "type": "money",
  "remaining": 42.50,
  "currency": "EUR",
  "limit": null,
  "percentage": null
}
```

### Quota d'emails

Providers comme **SendGrid** :

```json
{
  "type": "emails",
  "remaining": 8500,
  "currency": "emails",
  "limit": 10000,
  "percentage": 85.0
}
```

### Mixed (Email + SMS)

Providers comme **Brevo/SendinBlue** :

```json
{
  "type": "mixed",
  "email": {
    "remaining": 5000,
    "limit": 10000,
    "type": "emails_per_day"
  },
  "sms": {
    "remaining": 250,
    "currency": "sms_units"
  }
}
```

### Unlimited

Providers locaux comme **Django Email**, **In-App Notification** :

```json
{
  "type": "unlimited",
  "remaining": null,
  "currency": "",
  "limit": null,
  "percentage": null
}
```

## 📊 SLA et métriques

### Méthode `get_sla_metrics()`

```python
provider = SendGridProvider()
sla = provider.get_sla_metrics()

print(f"Uptime: {sla['uptime_percentage']}%")
print(f"Target: {sla['uptime_target']}%")
print(f"Meets SLA: {sla['meets_sla']}")
print(f"Success rate: {sla['success_rate']}%")
```

### Exemples de SLA par provider

| Provider | Uptime Target | Response Time | Notes |
|----------|---------------|---------------|-------|
| SendGrid | 99.99% | ~100ms | Enterprise grade |
| Twilio | 99.95% | ~150ms | Telecom standard |
| Brevo | 99.95% | ~120ms | Marketing automation |
| Mailgun | 99.99% | ~80ms | High performance |
| La Poste | 99.9% | ~300ms | Service public |
| SMSPartner | 99.9% | ~200ms | Provider français |

## 🚨 Alertes et monitoring

### Surveiller les crédits

```python
def monitor_all_providers():
    """Surveille tous les providers et envoie des alertes."""
    from missive.providers import (
        SendGridProvider,
        SMSPartnerProvider,
        TwilioProvider,
    )
    
    providers = [
        SendGridProvider(),
        SMSPartnerProvider(),
        TwilioProvider(),
    ]
    
    for provider in providers:
        health = provider.health_check()
        
        if health['status'] == 'critical':
            send_alert(f"🚨 {provider.name}: CRITIQUE", health)
        elif health['status'] == 'warning':
            send_warning(f"⚠️ {provider.name}: Attention", health)
```

### Tâche Celery périodique

```python
from celery import shared_task

@shared_task
def check_providers_health():
    """Tâche Celery pour vérifier la santé des providers."""
    from missive.providers.sendgrid import SendGridProvider
    from missive.providers.twilio import TwilioProvider
    
    for ProviderClass in [SendGridProvider, TwilioProvider]:
        provider = ProviderClass()
        health = provider.health_check()
        
        # Stocker en DB ou Redis
        cache.set(
            f'provider_health_{provider.name}',
            health,
            timeout=300  # 5 minutes
        )
        
        # Alerter si problème
        if not health['is_healthy']:
            notify_admins(provider.name, health)
```

### Dashboard Django Admin

Créer une vue custom dans l'admin :

```python
from django.contrib import admin
from django.shortcuts import render

@admin.site.register_view('providers-status', 'Statut des Providers')
def providers_status_view(request):
    """Vue admin pour le statut des providers."""
    from missive.providers import ALL_PROVIDERS
    
    statuses = []
    for ProviderClass in ALL_PROVIDERS:
        provider = ProviderClass()
        status = provider.get_service_status()
        health = provider.health_check()
        
        statuses.append({
            'provider': provider,
            'status': status,
            'health': health,
        })
    
    return render(request, 'admin/providers_status.html', {
        'statuses': statuses,
    })
```

## 🔍 Implémentation par provider

### Template de code commenté

Chaque provider a un template commenté à décommenter et adapter :

```python
def get_service_status(self) -> Dict:
    # TODO: Implémenter l'appel à l'API du provider
    # import requests
    #
    # try:
    #     api_key = self.config.get("PROVIDER_API_KEY")
    #     response = requests.get(
    #         "https://api.provider.com/account",
    #         headers={"Authorization": f"Bearer {api_key}"},
    #         timeout=5
    #     )
    #
    #     if response.status_code == 200:
    #         data = response.json()
    #         # Extraire les données...
    #         return {...}
    # except Exception as e:
    #     return {"status": "unknown", "warnings": [str(e)]}
    
    # Version par défaut
    return {
        "status": "unknown",
        "warnings": ["API non implémentée - décommenter le code"],
        # ...
    }
```

## 📚 Références

### Documentation des APIs providers

- **SendGrid**: https://docs.sendgrid.com/api-reference/stats/retrieve-email-statistics
- **Twilio**: https://www.twilio.com/docs/usage/api/usage-record
- **Brevo**: https://developers.brevo.com/reference/getaccount-1
- **Mailgun**: https://documentation.mailgun.com/en/latest/api-stats.html
- **SMSPartner**: https://www.smspartner.fr/api-sms/documentation-api/
- **La Poste**: https://developer.laposte.fr/products

### Status Pages

- **SendGrid**: https://status.sendgrid.com/
- **Twilio**: https://status.twilio.com/
- **Brevo**: https://status.brevo.com/
- **Mailgun**: https://status.mailgun.com/

## 🎓 Bonnes pratiques

1. **Cache les résultats** : Les appels aux APIs sont lents, utilisez Redis/Memcached
2. **Timeout courts** : 5 secondes max pour ne pas bloquer l'application
3. **Gestion d'erreurs** : Toujours retourner un statut "unknown" en cas d'erreur
4. **Alertes proactives** : Surveiller avant d'arriver à 0 crédit
5. **Fallback providers** : Si un provider est down, basculer automatiquement
6. **Logs structurés** : Logger tous les checks pour debugging
7. **Métriques** : Intégrer avec Prometheus/Grafana pour monitoring
8. **Documentation** : Maintenir à jour les seuils d'alerte et SLA

## 🔧 Configuration

Dans `settings.py` :

```python
MISSIVE_CONFIG = {
    # ...
    
    # Seuils d'alerte (%)
    'CREDIT_WARNING_THRESHOLD': 10,
    'CREDIT_CRITICAL_THRESHOLD': 5,
    
    # Fréquence de vérification (secondes)
    'HEALTH_CHECK_INTERVAL': 300,  # 5 minutes
    
    # Notifications
    'ALERT_EMAIL': 'admin@example.com',
    'ALERT_SLACK_WEBHOOK': 'https://hooks.slack.com/...',
}
```

## 🚀 Exemple d'intégration complète

```python
from django.core.management.base import BaseCommand
from missive.providers.sendgrid import SendGridProvider
from missive.providers.twilio import TwilioProvider
import json

class Command(BaseCommand):
    help = 'Check all providers status'

    def handle(self, *args, **options):
        providers = [SendGridProvider(), TwilioProvider()]
        
        for provider in providers:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Provider: {provider.name}")
            self.stdout.write(f"{'='*60}")
            
            # Status complet
            status = provider.get_service_status()
            self.stdout.write(f"Status: {status['status']}")
            self.stdout.write(f"Services: {', '.join(status['services'])}")
            
            # Crédits
            credits = provider.check_credits()
            self.stdout.write(f"\nCrédits:")
            self.stdout.write(f"  Type: {credits['type']}")
            self.stdout.write(f"  Remaining: {credits['remaining']} {credits['currency']}")
            if credits['needs_refill']:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠️ Recharge nécessaire!"
                ))
            
            # Health check
            health = provider.health_check()
            if health['is_healthy']:
                self.stdout.write(self.style.SUCCESS(f"\n✅ {health['summary']}"))
            else:
                self.stdout.write(self.style.ERROR(f"\n❌ {health['summary']}"))
                for issue in health['issues']:
                    self.stdout.write(f"  - {issue}")
```

Utilisation :

```bash
python manage.py check_providers_status
```

---

**Documentation django-missive** | [Retour à l'index](README.md)

