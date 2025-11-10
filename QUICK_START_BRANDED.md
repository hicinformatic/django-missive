# Quick Start - Messageries d'Applications (BRANDED)

## 🚀 En 30 Secondes

### Créer un Provider pour une Messagerie

```python
from missive.providers.base import BaseProvider
from missive.models import MissiveType

class WhatsAppProvider(BaseProvider):
    name = "whatsapp"  # ← Définit automatiquement send_whatsapp()
    supported_types = [MissiveType.BRANDED]
    
    def send_whatsapp(self) -> bool:
        phone = self.missive.get_recipient_phone()
        # ... appel API WhatsApp ...
        return True
```

### Utiliser le Provider

```python
# 1. Créer une missive
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,  # ← Toujours le même !
    recipient=recipient,
    body='Votre commande est prête'
)

# 2. Envoyer via le provider
provider = WhatsAppProvider(missive=missive)
provider.send()  # → Appelle automatiquement send_whatsapp()
```

## 💡 Principe

**1 type BRANDED + nom du provider = dispatch automatique**

- ✅ Un seul type pour TOUTES les messageries (WhatsApp, Slack, Teams, Discord, etc.)
- ✅ Le provider définit son `name` qui détermine la méthode appelée
- ✅ Dispatch automatique vers `send_{name}()`
- ✅ Pas de champ `brand_name` dans la DB

## 📦 Applications Supportées

Toutes utilisent le même type `BRANDED` :

| Provider Name | Méthode Appelée | Application |
|---------------|----------------|-------------|
| `"whatsapp"` | `send_whatsapp()` | WhatsApp |
| `"telegram"` | `send_telegram()` | Telegram |
| `"slack"` | `send_slack()` | Slack |
| `"teams"` | `send_teams()` | Microsoft Teams |
| `"discord"` | `send_discord()` | Discord |
| `"signal"` | `send_signal()` | Signal |
| ... | ... | ... |

## 🗂️ Contexte d'Organisation (Optionnel)

Pour les apps qui nécessitent un contexte (Slack, Teams, Discord) :

```python
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    recipient=recipient,
    body='Alerte système',
    metadata={
        'workspace_id': 'T123456',  # ← Contexte
        'channel_id': 'C789012'
    }
)

# Dans le provider
class SlackProvider(BaseProvider):
    name = "slack"
    
    def send_slack(self) -> bool:
        context = self._get_organization_context()
        workspace_id = context.get('workspace_id')
        channel_id = context.get('channel_id')
        # ... appel API Slack ...
```

## 📋 Checklist Provider

Pour créer un nouveau provider :

1. ✅ Définir `name = "monapp"`
2. ✅ Ajouter `MissiveType.BRANDED` dans `supported_types`
3. ✅ Implémenter `send_monapp(self)`
4. ✅ Optionnel : `get_monapp_service_info(self)`
5. ✅ Si contexte nécessaire : utiliser `self._get_organization_context()`

C'est tout ! 🎉

## 📚 Documentation Complète

- 📄 `ARCHITECTURE_FINALE.md` - Architecture détaillée
- 📄 `EVOLUTION_ARCHITECTURE.md` - Historique et comparaison
- 📄 `examples/branded_professional_providers.py` - Exemples complets

---

**Architecture ultra-simplifiée - Django Missive v3.0**

