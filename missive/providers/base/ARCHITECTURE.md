# Architecture des Providers - Django Missive

## Vue d'ensemble

L'architecture des providers utilise une composition de mixins pour supporter différents types de missives. Cette architecture a été récemment refactorisée pour utiliser un système générique basé sur `brand_name` au lieu d'avoir un type spécifique pour chaque application de messagerie.

## Types de Missives

### Types Classiques
- `EMAIL` : Email standard
- `SMS` : SMS classique
- `RCS` : SMS enrichi (Rich Communication Services)
- `POSTAL` : Courrier postal
- `LRE` : Lettre recommandée électronique
- `VOICE_CALL` : Appel vocal automatisé
- `NOTIFICATION` : Notification in-app
- `PUSH_NOTIFICATION` : Notification push mobile

### Types Génériques (Nouvelle Architecture)

#### `BRANDED` - Messageries d'applications
Type générique pour toutes les messageries liées à une application spécifique.

**Caractéristiques :**
- Identifiant unique et global (généralement un numéro de téléphone)
- Pas besoin d'appartenir à une organisation
- Portable entre services

**Applications supportées via `brand_name` :**
- `whatsapp` : WhatsApp
- `telegram` : Telegram
- `signal` : Signal
- `discord` : Discord
- `messenger` : Facebook Messenger
- `viber` : Viber
- `line` : Line
- `wechat` : WeChat

**Exemple d'utilisation :**
```python
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    brand_name='whatsapp',
    recipient=recipient,
    subject='Notification',
    body='Votre commande est prête'
)
```

#### `PROFESSIONAL` - Messageries professionnelles
Type générique pour les messageries professionnelles avec gestion d'organisation.

**Caractéristiques :**
- Authentification OAuth ou API keys spécifiques
- Contexte d'organisation/workspace requis
- Identifiants non-portables (liés à l'organisation)
- Gestion de channels/teams/espaces
- Permissions et rôles

**Plateformes supportées via `brand_name` :**
- `slack` : Slack
- `teams` : Microsoft Teams
- `googlechat` : Google Chat
- `mattermost` : Mattermost
- `rocket` : Rocket.Chat

**Exemple d'utilisation :**
```python
missive = Missive.objects.create(
    missive_type=MissiveType.PROFESSIONAL,
    brand_name='slack',
    recipient=recipient,
    subject='Alerte système',
    body='Le serveur nécessite une intervention',
    metadata={
        'workspace_id': 'T123456',
        'channel_id': 'C789012'
    }
)
```

## Architecture des Mixins

### Mixins Communs
- **BaseProviderCommon** : Fonctions communes (config, status, events)
- **BaseMonitoringMixin** : Monitoring, crédits, SLA, health check

### Mixins par Type Classique
- **BaseEmailMixin** : Validation email, spam score, attachments
- **BaseSMSMixin** : Validation phone, calcul segments, formatage
- **BasePostalMixin** : Validation adresse, calcul coût postal
- **BaseNotificationMixin** : Formatage notifications, préférences user
- **BaseVoiceCallMixin** : Appels vocaux, TTS, messages vocaux

### Mixins Génériques (Nouvelle Architecture)

#### BaseBrandedMixin
Mixin générique pour les messageries d'applications.

**Méthodes principales :**
- `send_branded()` : Dispatch vers `send_{brand_name}()`
- `get_branded_service_info()` : Dispatch vers `get_{brand_name}_service_info()`
- `validate_branded_identifier()` : Validation de l'identifiant
- `format_branded_message()` : Formatage du message

**Implémentation dans un provider :**
```python
class MyProvider(BaseProvider):
    supported_types = [MissiveType.BRANDED]
    
    def send_whatsapp(self) -> bool:
        """Implémentation spécifique WhatsApp"""
        # Utiliser l'API du provider pour WhatsApp
        pass
    
    def send_telegram(self) -> bool:
        """Implémentation spécifique Telegram"""
        # Utiliser l'API du provider pour Telegram
        pass
```

#### BaseProfessionalMixin
Mixin générique pour les messageries professionnelles.

**Méthodes principales :**
- `send_professional()` : Dispatch vers `send_{brand_name}()`
- `get_professional_service_info()` : Dispatch vers `get_{brand_name}_service_info()`
- `validate_professional_identifier()` : Validation avec contexte d'organisation
- `format_professional_message()` : Formatage du message
- `list_channels()` : Liste les channels disponibles
- `_get_organization_context()` : Récupère le contexte d'organisation

**Implémentation dans un provider :**
```python
class MyProvider(BaseProvider):
    supported_types = [MissiveType.PROFESSIONAL]
    
    def send_slack(self) -> bool:
        """Implémentation spécifique Slack"""
        context = self._get_organization_context()
        workspace_id = context.get('workspace_id')
        channel_id = context.get('channel_id')
        # Utiliser l'API Slack
        pass
    
    def send_teams(self) -> bool:
        """Implémentation spécifique Teams"""
        context = self._get_organization_context()
        team_id = context.get('team_id')
        # Utiliser l'API Microsoft Graph
        pass
```

### Mixins Spécifiques (Référence)
- **BaseWhatsAppMixin** : DÉPRÉCIÉ - utiliser BaseBrandedMixin
- **BaseSlackMixin** : Implémentation de référence pour Slack
- **BaseTeamsMixin** : Implémentation de référence pour Teams

## Dispatch Automatique

Le `BaseProvider` gère automatiquement le dispatch vers les bonnes méthodes :

```python
def send(self) -> bool:
    if self.missive.missive_type == MissiveType.EMAIL:
        return self.send_email()
    elif self.missive.missive_type == MissiveType.BRANDED:
        return self.send_branded()  # → Appelle send_{brand_name}()
    elif self.missive.missive_type == MissiveType.PROFESSIONAL:
        return self.send_professional()  # → Appelle send_{brand_name}()
    # ...
```

## Migration depuis l'Ancienne Architecture

### Avant (déprécié)
```python
# Ancien système avec type spécifique
missive = Missive.objects.create(
    missive_type=MissiveType.WHATSAPP,  # ❌ Type spécifique
    recipient=recipient,
    body='Message'
)
```

### Après (nouveau système)
```python
# Nouveau système générique
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,   # ✅ Type générique
    brand_name='whatsapp',               # ✅ Application spécifique
    recipient=recipient,
    body='Message'
)
```

## Avantages de la Nouvelle Architecture

1. **Extensibilité** : Ajouter une nouvelle application ne nécessite plus de modifier l'enum `MissiveType`
2. **Maintenabilité** : Code centralisé dans les mixins génériques
3. **Cohérence** : Toutes les applications suivent le même pattern
4. **Flexibilité** : Facile d'ajouter des applications similaires sans duplication
5. **Clarté** : Séparation claire entre types (BRANDED vs PROFESSIONAL)

## Exemples Complets

### Provider supportant WhatsApp et Telegram (BRANDED)
```python
from missive.providers.base import BaseProvider

class MyMessagingProvider(BaseProvider):
    name = "mymessaging"
    supported_types = [MissiveType.BRANDED]
    
    def send_whatsapp(self) -> bool:
        """Envoie via API WhatsApp"""
        phone = self.missive.get_recipient_phone()
        message = self.format_branded_message(
            self.missive.body, 
            self.missive.body_text,
            'whatsapp'
        )
        # Appel API...
        return True
    
    def send_telegram(self) -> bool:
        """Envoie via API Telegram"""
        # Implémentation Telegram...
        return True
    
    def get_whatsapp_service_info(self) -> Dict[str, Any]:
        return {
            "credits": 1000,
            "is_available": True,
            # ...
        }
```

### Provider supportant Slack et Teams (PROFESSIONAL)
```python
from missive.providers.base import BaseProvider

class MyEnterpriseProvider(BaseProvider):
    name = "myenterprise"
    supported_types = [MissiveType.PROFESSIONAL]
    
    def send_slack(self) -> bool:
        """Envoie via Slack API"""
        context = self._get_organization_context()
        workspace_id = context['workspace_id']
        channel_id = context['channel_id']
        # Appel Slack API...
        return True
    
    def send_teams(self) -> bool:
        """Envoie via Microsoft Graph API"""
        context = self._get_organization_context()
        team_id = context['team_id']
        # Appel Graph API...
        return True
    
    def list_slack_channels(self) -> Dict[str, Any]:
        """Liste les channels Slack"""
        # Implémentation...
        return {"channels": [...]}
```

## Contexte d'Organisation pour PROFESSIONAL

Le contexte d'organisation peut être fourni de deux façons :

### 1. Via metadata de la missive (recommandé)
```python
missive.metadata = {
    'workspace_id': 'T123456',
    'channel_id': 'C789012'
}
```

### 2. Via configuration du provider
```python
# settings.py
MISSIVE_PROVIDERS = {
    'PROFESSIONAL': [
        'myapp.providers.SlackProvider',
    ]
}

SLACK_WORKSPACE_ID = 'T123456'
SLACK_DEFAULT_CHANNEL = 'C789012'
```

Le mixin `BaseProfessionalMixin` essaiera d'abord les metadata de la missive, puis la configuration du provider.

