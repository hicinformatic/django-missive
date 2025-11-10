# Architecture Ultra-Simplifiée pour les Messageries

## 🎯 Principe Final

**Un seul type `BRANDED` + le nom du provider = dispatch automatique**

Plus besoin de :
- ❌ Champ `brand_name` dans la DB
- ❌ Type `PROFESSIONAL` séparé
- ❌ Distinction artificielle entre apps

## 📐 Architecture

### 1. Type Unique : `BRANDED`

```python
class MissiveType(models.TextChoices):
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    POSTAL = "POSTAL", _("Courrier postal")
    VOICE_CALL = "VOICE_CALL", _("Appel vocal")
    NOTIFICATION = "NOTIFICATION", _("Notification in-app")
    
    # Type unique pour TOUTES les messageries d'applications
    BRANDED = "BRANDED", _("Messagerie d'application")
```

### 2. Le Provider Définit Son Nom

```python
class WhatsAppProvider(BaseProvider):
    name = "whatsapp"  # ← C'est ça qui compte !
    supported_types = [MissiveType.BRANDED]
    
    def send_whatsapp(self):  # ← send_{self.name}()
        """Implémentation WhatsApp"""
        phone = self.missive.get_recipient_phone()
        # ...

class SlackProvider(BaseProvider):
    name = "slack"  # ← C'est ça qui compte !
    supported_types = [MissiveType.BRANDED]
    
    def send_slack(self):  # ← send_{self.name}()
        """Implémentation Slack"""
        context = self._get_organization_context()
        # ...
```

### 3. Dispatch Automatique

```python
# Dans BaseBrandedMixin
def send_branded(self) -> bool:
    method_name = f"send_{self.name.lower()}"  # ← Utilise self.name
    return getattr(self, method_name)()
```

## 💡 Utilisation

### Création d'une Missive

```python
# Pour toutes les apps : un seul type !
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,  # ← Toujours le même
    recipient=recipient,
    body='Message',
    metadata={...}  # ← Contexte optionnel si nécessaire
)
```

### Le Provider Sait Ce Qu'Il Fait

```python
# WhatsApp Provider
provider = WhatsAppProvider(missive=missive)
provider.send()  # → Appelle automatiquement send_whatsapp()

# Slack Provider
provider = SlackProvider(missive=missive)
provider.send()  # → Appelle automatiquement send_slack()
```

## 🗂️ Contexte d'Organisation (Optionnel)

Pour les apps qui en ont besoin (Slack, Teams, Discord servers), le contexte est dans `metadata` :

```python
# Slack
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    recipient=recipient,
    body='Alerte',
    metadata={
        'workspace_id': 'T123456',
        'channel_id': 'C789012'
    }
)

# Dans le provider
context = self._get_organization_context()
workspace_id = context.get('workspace_id')
```

## 📦 Applications Supportées

Toutes les messageries utilisent le même type `BRANDED` :

- ✅ WhatsApp (name="whatsapp")
- ✅ Telegram (name="telegram")
- ✅ Signal (name="signal")
- ✅ Slack (name="slack")
- ✅ Teams (name="teams")
- ✅ Discord (name="discord")
- ✅ Messenger (name="messenger")
- 🔜 Viber (name="viber")
- 🔜 Line (name="line")
- 🔜 WeChat (name="wechat")

## 🎨 Avantages de Cette Architecture

1. **Maximum de simplicité** : Un seul type, pas de champ DB supplémentaire
2. **Auto-documenté** : Le nom du provider dit exactement ce qu'il fait
3. **Extensible à l'infini** : Ajouter une app = créer un provider avec le bon `name`
4. **Pas de duplication** : Toutes les apps partagent le même mixin
5. **Flexible** : Le contexte d'organisation reste disponible via `metadata`

## 📋 Checklist Provider

Pour créer un nouveau provider de messagerie :

1. ✅ Définir `name = "monapp"`
2. ✅ Ajouter `MissiveType.BRANDED` dans `supported_types`
3. ✅ Implémenter `send_monapp(self)`
4. ✅ Optionnel : implémenter `get_monapp_service_info(self)`
5. ✅ Si contexte nécessaire : utiliser `self._get_organization_context()`

C'est tout ! 🎉

## 🔄 Migration depuis l'Ancienne Architecture

La migration `0002_simplify_branded_types.py` convertit automatiquement :
- `WHATSAPP` → `BRANDED`
- `TELEGRAM` → `BRANDED`
- `SLACK` → `BRANDED`
- `TEAMS` → `BRANDED`
- etc.

## 🏗️ Structure des Fichiers

```
missive/
├── models/
│   └── choices.py              # MissiveType.BRANDED
│   └── missive.py              # Modèle Missive (pas de brand_name)
├── providers/
│   └── base/
│       └── __init__.py         # BaseProvider avec dispatch
│       └── branded.py          # BaseBrandedMixin (dispatch automatique)
│       └── slack.py            # Référence Slack
│       └── teams.py            # Référence Teams
│   └── whatsapp_provider.py   # Exemple : name="whatsapp"
│   └── slack_provider.py      # Exemple : name="slack"
└── migrations/
    └── 0002_simplify_branded_types.py  # Migration
```

## 📝 Exemple Complet

```python
# providers/whatsapp_provider.py
from missive.providers.base import BaseProvider
from missive.models import MissiveType

class WhatsAppProvider(BaseProvider):
    """Provider pour WhatsApp Business API"""
    
    name = "whatsapp"
    supported_types = [MissiveType.BRANDED]
    
    def __init__(self, missive=None, config=None):
        super().__init__(missive, config)
        self.api_key = config.get('WHATSAPP_API_KEY')
    
    def send_whatsapp(self) -> bool:
        """Envoie un message WhatsApp"""
        phone = self.missive.get_recipient_phone()
        if not phone:
            self._update_status(MissiveStatus.FAILED, "No phone")
            return False
        
        # Formater le message
        message = self.missive.body_text or self.missive.body
        
        # Appel API WhatsApp
        response = requests.post(
            f"{self.api_url}/messages",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "to": phone,
                "text": {"body": message}
            }
        )
        
        if response.ok:
            self._update_status(
                MissiveStatus.SENT,
                external_id=response.json()['id']
            )
            return True
        
        return False
    
    def get_whatsapp_service_info(self):
        """Infos du service WhatsApp"""
        return {
            "credits": 5000,
            "is_available": True,
            "limits": {"messages_per_day": 10000}
        }


# Utilisation
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    recipient=recipient,
    body='Votre commande est prête !'
)

provider = WhatsAppProvider(missive=missive)
success = provider.send()  # → Appelle send_whatsapp() automatiquement
```

---

**Cette architecture est le résultat final d'une simplification progressive :**
1. ~~Types spécifiques par app~~ → ❌ Trop rigide
2. ~~BRANDED + PROFESSIONAL avec brand_name~~ → ❌ Distinction inutile + champ DB inutile
3. **BRANDED + nom du provider** → ✅ Parfait !

**Principe KISS (Keep It Simple, Stupid) appliqué avec succès !** 🎯

