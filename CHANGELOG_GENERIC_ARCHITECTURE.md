# Changements Majeurs : Architecture Générique pour les Messageries

## 📋 Résumé

Refonte majeure de l'architecture des providers pour supporter les messageries d'applications (WhatsApp, Telegram, Discord, etc.) et professionnelles (Slack, Teams, etc.) de manière générique via un système de `brand_name` au lieu de types spécifiques.

## 🎯 Motivation

### Avant (❌ Problème)
```python
# Chaque application nécessitait un type spécifique dans l'enum
class MissiveType(models.TextChoices):
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    SLACK = "SLACK", _("Slack")
    TEAMS = "TEAMS", _("Microsoft Teams")
    DISCORD = "DISCORD", _("Discord")
    TELEGRAM = "TELEGRAM", _("Telegram")
    # ... et ainsi de suite pour chaque nouvelle app

# Nécessitait de modifier l'enum à chaque nouvelle application
# Beaucoup de duplication de code
# Dispatch statique dans BaseProvider
```

### Après (✅ Solution)
```python
# Deux types génériques suffisent
class MissiveType(models.TextChoices):
    BRANDED = "BRANDED", _("Messagerie d'application")
    PROFESSIONAL = "PROFESSIONAL", _("Messagerie professionnelle")

# Le champ brand_name identifie l'application spécifique
missive.missive_type = MissiveType.BRANDED
missive.brand_name = 'whatsapp'  # ou 'telegram', 'discord', etc.

# Dispatch dynamique automatique vers send_{brand_name}()
```

## 🔄 Changements Principaux

### 1. Modèle `Missive`

**Ajout du champ `brand_name`**
```python
brand_name = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    verbose_name=_("Nom de l'application"),
    help_text=_(
        "Pour les types BRANDED/PROFESSIONAL : nom de l'application "
        "(whatsapp, slack, teams, discord, telegram, signal, messenger, etc.)"
    ),
)
```

**Nouvel index**
```python
models.Index(fields=["missive_type", "brand_name"])
```

### 2. Enum `MissiveType`

**Remplacement des types spécifiques par des types génériques**

Supprimés :
- `WHATSAPP`, `TELEGRAM`, `SIGNAL`, `MESSENGER`
- `SLACK`, `TEAMS`

Ajoutés :
- `BRANDED` : Pour les messageries d'applications (WhatsApp, Telegram, Discord, etc.)
- `PROFESSIONAL` : Pour les messageries professionnelles (Slack, Teams, etc.)

### 3. Nouveaux Mixins Génériques

#### `BaseBrandedMixin`
Gère les messageries d'applications avec dispatch dynamique.

**Méthodes principales :**
- `send_branded()` → dispatch vers `send_{brand_name}()`
- `get_branded_service_info()` → dispatch vers `get_{brand_name}_service_info()`
- `validate_branded_identifier()`
- `format_branded_message()`

**Caractéristiques :**
- Identifiant unique global (généralement phone)
- Pas de contexte d'organisation requis
- Applications : whatsapp, telegram, signal, discord, messenger, viber, line, wechat

#### `BaseProfessionalMixin`
Gère les messageries professionnelles avec contexte d'organisation.

**Méthodes principales :**
- `send_professional()` → dispatch vers `send_{brand_name}()`
- `get_professional_service_info()` → dispatch vers `get_{brand_name}_service_info()`
- `_get_organization_context()` → récupère workspace_id, team_id, channel_id
- `validate_professional_identifier()`
- `format_professional_message()`
- `list_channels()`

**Caractéristiques :**
- Authentification OAuth/API keys
- Contexte d'organisation requis (workspace, team, channel)
- Identifiants non-portables
- Plateformes : slack, teams, googlechat, mattermost, rocket

### 4. Mixins Spécifiques (Référence)

Créés pour servir de référence d'implémentation :
- `BaseSlackMixin` : Implémentation de référence pour Slack
- `BaseTeamsMixin` : Implémentation de référence pour Teams

`BaseWhatsAppMixin` marqué comme DÉPRÉCIÉ (conservé pour compatibilité).

### 5. Dispatch Automatique dans `BaseProvider`

```python
def send(self) -> bool:
    # ...
    if self.missive.missive_type == MissiveType.BRANDED:
        return self.send_branded()  # → appelle send_{brand_name}()
    elif self.missive.missive_type == MissiveType.PROFESSIONAL:
        return self.send_professional()  # → appelle send_{brand_name}()
```

## 📊 Migration des Données

La migration `0002_add_brand_name_and_update_missive_types.py` :

1. Ajoute le champ `brand_name`
2. Ajoute l'index sur `(missive_type, brand_name)`
3. Migre automatiquement les données existantes :
   - `WHATSAPP` → `BRANDED` avec `brand_name='whatsapp'`
   - `TELEGRAM` → `BRANDED` avec `brand_name='telegram'`
   - `SLACK` → `PROFESSIONAL` avec `brand_name='slack'`
   - `TEAMS` → `PROFESSIONAL` avec `brand_name='teams'`

La migration est réversible.

## 📝 Exemples d'Utilisation

### Messagerie d'Application (BRANDED)

```python
from missive.models import Missive, MissiveType

# WhatsApp
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    brand_name='whatsapp',
    recipient=recipient,
    subject='Notification',
    body='Votre commande est prête',
)

# Telegram
missive = Missive.objects.create(
    missive_type=MissiveType.BRANDED,
    brand_name='telegram',
    recipient=recipient,
    subject='Alerte',
    body='Mise à jour disponible',
    metadata={'telegram_chat_id': '123456789'}
)
```

### Messagerie Professionnelle (PROFESSIONAL)

```python
# Slack
missive = Missive.objects.create(
    missive_type=MissiveType.PROFESSIONAL,
    brand_name='slack',
    recipient=recipient,
    subject='Alerte système',
    body='Le serveur nécessite une intervention',
    metadata={
        'workspace_id': 'T123456',
        'channel_id': 'C789012',
    }
)

# Microsoft Teams
missive = Missive.objects.create(
    missive_type=MissiveType.PROFESSIONAL,
    brand_name='teams',
    recipient=recipient,
    subject='Rapport',
    body='<h2>Rapport du jour</h2>',
    metadata={
        'team_id': 'abc-def-ghi',
        'channel_id': 'xyz-uvw',
    }
)
```

### Implémentation d'un Provider

```python
from missive.providers.base import BaseProvider
from missive.models import MissiveType

class MyProvider(BaseProvider):
    name = "myprovider"
    supported_types = [MissiveType.BRANDED]
    
    def send_whatsapp(self) -> bool:
        """Implémentation spécifique WhatsApp"""
        phone = self.missive.get_recipient_phone()
        message = self.format_branded_message(
            self.missive.body,
            self.missive.body_text,
            'whatsapp'
        )
        # Appel API WhatsApp...
        return True
    
    def send_telegram(self) -> bool:
        """Implémentation spécifique Telegram"""
        # Appel API Telegram...
        return True
    
    def get_whatsapp_service_info(self) -> Dict[str, Any]:
        return {
            "credits": 1000,
            "is_available": True,
            # ...
        }
```

## ✅ Avantages

1. **Extensibilité** : Ajouter une nouvelle messagerie ne nécessite plus de modifier `MissiveType`
2. **Maintenabilité** : Code centralisé dans les mixins génériques
3. **Cohérence** : Pattern uniforme pour toutes les messageries
4. **Flexibilité** : Facile d'ajouter de nouvelles applications sans duplication
5. **Clarté** : Séparation claire entre BRANDED et PROFESSIONAL
6. **DRY** : Pas de duplication de code entre applications similaires

## 📚 Documentation

- **Architecture complète** : `/missive/providers/base/ARCHITECTURE.md`
- **Exemples de code** : `/examples/branded_professional_providers.py`
- **Migration** : `/missive/migrations/0002_add_brand_name_and_update_missive_types.py`

## 🔧 Actions Requises

### Pour les Développeurs

1. **Mettre à jour les créations de missives** :
   ```python
   # Avant
   missive_type=MissiveType.WHATSAPP
   
   # Après
   missive_type=MissiveType.BRANDED,
   brand_name='whatsapp'
   ```

2. **Créer des providers avec la nouvelle architecture** :
   - Hériter de `BaseProvider`
   - Implémenter `send_{brand_name}()` pour chaque application supportée
   - Optionnel : implémenter `get_{brand_name}_service_info()`

3. **Appliquer la migration** :
   ```bash
   python manage.py migrate missive
   ```

### Compatibilité Rétrograde

- `BaseWhatsAppMixin` est conservé mais marqué comme DÉPRÉCIÉ
- La migration convertit automatiquement les anciennes données
- Les anciens providers continuent de fonctionner
- Migration progressive recommandée

## 🚀 Applications Supportées

### BRANDED (Messageries d'Applications)
- ✅ whatsapp
- ✅ telegram
- ✅ signal
- ✅ discord
- ✅ messenger
- 🔜 viber
- 🔜 line
- 🔜 wechat

### PROFESSIONAL (Messageries Professionnelles)
- ✅ slack
- ✅ teams
- 🔜 googlechat
- 🔜 mattermost
- 🔜 rocket

*Note : ✅ = Mixin de référence disponible, 🔜 = À implémenter par les providers*

## 📞 Contact

Pour toute question sur cette refonte, consultez :
- La documentation complète dans `/missive/providers/base/ARCHITECTURE.md`
- Les exemples dans `/examples/branded_professional_providers.py`

---

**Date de création** : 2025-11-10  
**Version** : 2.0.0  
**Breaking Changes** : Non (rétrocompatible avec migration automatique)

