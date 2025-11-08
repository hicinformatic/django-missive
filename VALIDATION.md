# Validation et Tests de Risque d'Échec

Django Missive inclut des fonctionnalités de validation et d'évaluation du risque d'échec de délivrance pour améliorer le taux de succès de vos envois.

## 🎯 Fonctionnalités

Chaque provider hérite de méthodes de validation permettant de :
- Valider les adresses email (syntaxe, MX records, domaines jetables)
- Valider les numéros de téléphone (format, type de ligne, opérateur)
- Tester la disponibilité des services
- Calculer un score de risque global

## 📧 Validation d'emails

### Méthode `validate_email()`

```python
from missive.providers import SendGridProvider

provider = SendGridProvider()
result = provider.validate_email("user@example.com")

print(result)
# {
#     'is_valid': True,
#     'is_deliverable': True,
#     'risk_score': 15,
#     'warnings': [],
#     'details': {
#         'domain': 'example.com',
#         'mx_records': ['mail.example.com']
#     }
# }
```

### Ce qui est vérifié

✅ **Syntaxe** - Format de l'email (regex)  
✅ **Domaine** - Extraction et validation du domaine  
🔜 **MX Records** - Vérification DNS (à implémenter avec `dnspython`)  
🔜 **Domaines jetables** - Détection de tempmail, guerrillamail, etc.  
🔜 **Blacklists** - Vérification dans les listes de spam  

### Implémentation complète (optionnelle)

Pour activer toutes les validations, installez les dépendances :

```bash
pip install dnspython
```

Puis décommentez le code dans `providers/base.py` :

```python
def validate_email(self, email: str) -> Dict[str, Any]:
    # ...
    
    # Vérifier les enregistrements MX
    try:
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        details['mx_records'] = [str(r.exchange) for r in mx_records]
        if not mx_records:
            warnings.append("Aucun enregistrement MX trouvé")
    except Exception:
        warnings.append("Impossible de vérifier les MX records")
```

## 📱 Validation de numéros de téléphone

### Méthode `validate_phone_number()`

```python
from missive.providers import TwilioProvider

provider = TwilioProvider()
result = provider.validate_phone_number("+33612345678")

print(result)
# {
#     'is_valid': True,
#     'is_mobile': True,
#     'formatted': '+33612345678',
#     'carrier': 'Orange',
#     'line_type': 'mobile',
#     'risk_score': 0,
#     'warnings': []
# }
```

### Ce qui est vérifié

✅ **Format** - Nettoyage et validation basique  
✅ **Format international** - Détection du préfixe +  
🔜 **Type de ligne** - Mobile vs Fixe vs VoIP (nécessite `phonenumbers`)  
🔜 **Opérateur** - Détection de l'opérateur  
🔜 **Pays** - Validation selon le pays  

### Implémentation complète (optionnelle)

Pour activer toutes les validations, installez :

```bash
pip install phonenumbers
```

Puis décommentez le code dans `providers/base.py` :

```python
def validate_phone_number(self, phone: str, country_code: str = "FR") -> Dict[str, Any]:
    # ...
    
    import phonenumbers
    try:
        parsed = phonenumbers.parse(phone, country_code)
        is_valid = phonenumbers.is_valid_number(parsed)
        formatted = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
        number_type = phonenumbers.number_type(parsed)
        is_mobile = number_type == phonenumbers.PhoneNumberType.MOBILE
        
        # Opérateur
        from phonenumbers import carrier
        carrier_name = carrier.name_for_number(parsed, 'fr')
        
    except Exception as e:
        is_valid = False
        warnings.append(str(e))
```

## 🔍 Test de serveur SMTP

### Méthode `test_smtp_server()`

```python
provider = SendGridProvider()
result = provider.test_smtp_server("example.com")

print(result)
# {
#     'is_reachable': True,
#     'mx_records': ['mail.example.com', 'mail2.example.com'],
#     'supports_tls': True,
#     'smtp_banner': '220 mail.example.com ESMTP',
#     'response_time_ms': 245,
#     'warnings': []
# }
```

### Implémentation (à décommenter)

```python
import dns.resolver
import smtplib
from time import time

try:
    # Résolution MX
    mx_records = dns.resolver.resolve(domain, 'MX')
    mx_host = str(mx_records[0].exchange)
    
    # Test de connexion
    start = time()
    server = smtplib.SMTP(mx_host, timeout=10)
    response_time = int((time() - start) * 1000)
    
    # Test TLS
    supports_tls = hasattr(server, 'starttls')
    banner = server.ehlo_resp.decode() if server.ehlo_resp else ""
    
    server.quit()
    
    return {
        'is_reachable': True,
        'mx_records': [str(r.exchange) for r in mx_records],
        'supports_tls': supports_tls,
        'smtp_banner': banner,
        'response_time_ms': response_time,
        'warnings': []
    }
except Exception as e:
    return {
        'is_reachable': False,
        'warnings': [str(e)]
    }
```

## ⚡ Vérification de disponibilité du service

### Méthode `check_service_availability()`

Chaque provider peut implémenter sa propre vérification :

```python
from missive.providers import SendGridProvider

provider = SendGridProvider()
result = provider.check_service_availability()

print(result)
# {
#     'is_available': True,
#     'response_time_ms': 123,
#     'quota_remaining': 5000,
#     'status': 'operational',
#     'last_check': datetime(...),
#     'warnings': []
# }
```

### Exemple d'implémentation pour SendGrid

Dans `providers/sendgrid.py` :

```python
def check_service_availability(self) -> Dict[str, Any]:
    """Vérifie le quota et la disponibilité de SendGrid"""
    import requests
    from time import time
    
    try:
        start = time()
        response = requests.get(
            'https://api.sendgrid.com/v3/user/credits',
            headers={'Authorization': f'Bearer {self.config["api_key"]}'},
            timeout=5
        )
        response_time = int((time() - start) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'is_available': True,
                'response_time_ms': response_time,
                'quota_remaining': data.get('total', 0),
                'status': 'operational',
                'last_check': timezone.now(),
                'warnings': []
            }
    except Exception as e:
        return {
            'is_available': False,
            'warnings': [str(e)]
        }
```

## 📊 Calcul du risque global

### Méthode `calculate_delivery_risk()`

Combine tous les facteurs pour un score global :

```python
from missive import MissiveBuilder, MissiveSender
from missive.providers import SendGridProvider

# Créer une missive
missive = MissiveBuilder.create_email(
    source_object=order,
    sender=user,
    recipient_email="user@tempmail.com",
    subject="Commande",
    body="<p>Merci pour votre commande</p>",
    body_text="Merci pour votre commande"
)

# Analyser le risque avant envoi
provider = SendGridProvider(missive)
risk = provider.calculate_delivery_risk()

print(f"Score de risque: {risk['risk_score']}")
print(f"Niveau: {risk['risk_level']}")
print(f"Recommandations: {risk['recommendations']}")

if risk['should_send']:
    MissiveSender.send(missive)
else:
    print(f"⚠️ Envoi déconseillé (risque {risk['risk_score']}%)")
    # Notifier l'admin, demander confirmation, etc.
```

### Résultat

```python
{
    'risk_score': 85,                    # Score global 0-100
    'risk_level': 'critical',            # low/medium/high/critical
    'should_send': False,                # Recommandation
    'factors': {
        'email_validation': {
            'is_valid': True,
            'is_deliverable': False,
            'risk_score': 80,
            'warnings': ['Domaine jetable détecté']
        },
        'service_availability': {
            'is_available': True,
            'quota_remaining': 1000
        }
    },
    'recommendations': [
        'Domaine jetable détecté',
        'Utiliser une adresse email valide'
    ]
}
```

## 🎯 Facteurs de risque

### Poids des facteurs

| Facteur | Poids | Description |
|---------|-------|-------------|
| **Validation destinataire** | 60% | Email/phone valide et délivrable |
| **Disponibilité service** | 20% | API accessible, quota disponible |
| **Historique** | 10% | Échecs précédents avec ce destinataire |
| **Contenu** | 10% | Spam score, mots blacklistés |

### Niveaux de risque

| Score | Niveau | Action recommandée |
|-------|--------|-------------------|
| 0-24 | **Low** 🟢 | Envoi sûr |
| 25-49 | **Medium** 🟡 | Envoi avec surveillance |
| 50-74 | **High** 🟠 | Vérification recommandée |
| 75-100 | **Critical** 🔴 | Envoi déconseillé |

## 🚀 Utilisation avancée

### Validation avant création

```python
from missive.providers import SendGridProvider

provider = SendGridProvider()

# Valider AVANT de créer la missive
email_check = provider.validate_email(user_email)
if email_check['risk_score'] > 50:
    print(f"⚠️ Email suspect: {email_check['warnings']}")
    # Demander à l'utilisateur de vérifier son email
else:
    # Créer et envoyer la missive
    missive = MissiveBuilder.create_email(...)
    MissiveSender.send(missive)
```

### Validation en masse

```python
from missive.models import Recipient
from missive.providers import SendGridProvider

provider = SendGridProvider()

# Valider tous les destinataires
for recipient in Recipient.objects.filter(is_active=True):
    if recipient.email:
        check = provider.validate_email(recipient.email)
        if check['risk_score'] > 70:
            print(f"❌ {recipient.email}: {check['warnings']}")
            recipient.is_active = False
            recipient.notes = f"Email invalide: {', '.join(check['warnings'])}"
            recipient.save()
```

### Monitoring des services

```python
from missive.providers import get_all_providers

# Vérifier tous les providers
for provider_class in get_all_providers():
    provider = provider_class()
    status = provider.check_service_availability()
    
    print(f"{provider.name}: {status['status']}")
    if not status['is_available']:
        # Envoyer une alerte admin
        send_alert(f"Provider {provider.name} indisponible!")
```

## 📦 Dépendances optionnelles

Pour activer toutes les fonctionnalités de validation :

```bash
pip install dnspython phonenumbers
```

Ajoutez dans `pyproject.toml` :

```toml
[project.optional-dependencies]
validation = [
    "dnspython>=2.4.0",
    "phonenumbers>=8.13.0",
]
```

Installation :

```bash
pip install django-missive[validation]
```

## 🔧 Configuration

Dans `settings.py` :

```python
MISSIVE_CONFIG = {
    # Seuil de risque pour envoi automatique
    'RISK_THRESHOLD': 70,  # 0-100, défaut: 70
    
    # Activer validation automatique avant envoi
    'AUTO_VALIDATE': True,  # défaut: False
    
    # Bloquer l'envoi si risque trop élevé
    'BLOCK_HIGH_RISK': True,  # défaut: False
    
    # Domaines jetables à bloquer
    'BLOCKED_DOMAINS': [
        'tempmail.com',
        'guerrillamail.com',
        '10minutemail.com',
    ],
}
```

## 🛠️ Implémentation personnalisée

Vous pouvez override les méthodes de validation dans vos providers :

```python
from missive.providers import SendGridProvider

class CustomSendGridProvider(SendGridProvider):
    """Provider SendGrid avec validation personnalisée"""
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validation personnalisée avec vos propres règles"""
        result = super().validate_email(email)
        
        # Ajouter vos propres validations
        domain = email.split('@')[1]
        
        # Bloquer certains domaines spécifiques
        if domain in ['competitor.com', 'spam.com']:
            result['risk_score'] = 100
            result['warnings'].append("Domaine bloqué")
            result['is_deliverable'] = False
        
        # Vérifier votre propre liste de bounces
        from myapp.models import EmailBounce
        if EmailBounce.objects.filter(email=email).exists():
            result['risk_score'] = min(result['risk_score'] + 50, 100)
            result['warnings'].append("Email en bounce précédemment")
        
        return result
```

## 📈 Exemples d'utilisation

### 1. Validation avant envoi de campagne

```python
from missive.providers import SendGridProvider

provider = SendGridProvider()
emails_to_send = ['user1@example.com', 'user2@tempmail.com', 'user3@company.com']

safe_emails = []
risky_emails = []

for email in emails_to_send:
    validation = provider.validate_email(email)
    if validation['risk_score'] < 50:
        safe_emails.append(email)
    else:
        risky_emails.append((email, validation['warnings']))

print(f"✅ Emails sûrs: {len(safe_emails)}")
print(f"⚠️ Emails risqués: {len(risky_emails)}")
```

### 2. Test de serveur mail avant configuration

```python
from missive.providers import SendGridProvider

provider = SendGridProvider()

# Tester le serveur mail d'un nouveau client
domain = "newclient.com"
smtp_test = provider.test_smtp_server(domain)

if smtp_test['is_reachable']:
    print(f"✅ Serveur SMTP opérationnel")
    print(f"   MX: {smtp_test['mx_records']}")
    print(f"   TLS: {smtp_test['supports_tls']}")
    print(f"   Temps de réponse: {smtp_test['response_time_ms']}ms")
else:
    print(f"❌ Serveur SMTP injoignable")
    print(f"   Warnings: {smtp_test['warnings']}")
```

### 3. Validation automatique dans MissiveSender

Vous pouvez étendre `MissiveSender` pour validation automatique :

```python
from missive.sender import MissiveSender as BaseMissiveSender

class ValidatingMissiveSender(BaseMissiveSender):
    """Sender avec validation automatique"""
    
    @classmethod
    def send(cls, missive, validate=True):
        """Envoie avec validation optionnelle"""
        
        if validate:
            provider_class = cls.get_provider_class(missive)
            provider = provider_class(missive)
            
            risk = provider.calculate_delivery_risk()
            
            if risk['risk_score'] > 70:
                raise Exception(
                    f"Risque trop élevé ({risk['risk_score']}): "
                    f"{', '.join(risk['recommendations'])}"
                )
        
        return super().send(missive)

# Utilisation
try:
    ValidatingMissiveSender.send(missive, validate=True)
except Exception as e:
    print(f"Échec de validation: {e}")
```

## 🎓 TODO: Extensions possibles

Voici des idées pour étendre les fonctionnalités de validation :

### Pour les emails

```python
def check_spam_score(self, subject: str, body: str) -> int:
    """
    Calcule un spam score pour le contenu.
    
    Utiliser SpamAssassin ou un service comme:
    - https://www.mail-tester.com/ API
    - https://postmarkapp.com/spam-check
    """
    pass

def check_email_reputation(self, email: str) -> Dict:
    """
    Vérifie la réputation d'un email.
    
    Services possibles:
    - EmailRep.io
    - Hunter.io
    - NeverBounce
    """
    pass
```

### Pour les SMS

```python
def check_phone_hlr(self, phone: str) -> Dict:
    """
    Effectue un HLR (Home Location Register) lookup.
    
    Vérifie si le numéro est actif sur le réseau.
    Services: Twilio Lookup API, Nexmo Verify
    """
    pass

def estimate_sms_cost(self, phone: str, message: str) -> float:
    """
    Estime le coût d'envoi d'un SMS.
    
    Facteurs:
    - Pays de destination
    - Longueur du message
    - Nombre de segments
    - Opérateur
    """
    pass
```

### Pour les webhooks

```python
def verify_webhook_ip(self, ip: str) -> bool:
    """
    Vérifie que l'IP du webhook est légitime.
    
    Liste des IPs autorisées par provider:
    - SendGrid: https://docs.sendgrid.com/for-developers/tracking-events/getting-started-event-webhook-security
    - Twilio: https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    pass
```

## 📚 Ressources

- **dnspython** : https://dnspython.readthedocs.io/
- **phonenumbers** : https://github.com/daviddrysdale/python-phonenumbers
- **SendGrid Event Webhook** : https://docs.sendgrid.com/for-developers/tracking-events/event
- **Twilio Webhook Security** : https://www.twilio.com/docs/usage/webhooks/webhooks-security

## ⚠️ Limitations actuelles

Les méthodes sont **préparées mais non entièrement implémentées** par défaut pour :
- Garder les dépendances minimales
- Permettre une implémentation personnalisée selon vos besoins
- Éviter les appels API externes non nécessaires

Décommentez et adaptez le code selon vos besoins !

