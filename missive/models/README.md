# Modèles Django Missive

Les modèles sont organisés dans des fichiers séparés pour une meilleure lisibilité et maintenabilité.

## 📁 Structure

```
models/
├── __init__.py         # Exporte tous les modèles
├── choices.py          # Enums (TextChoices)
├── recipient.py        # Modèle Recipient
├── missive.py          # Modèle principal Missive
├── attachment.py       # Pièces jointes
├── event.py            # Événements de tracking
└── template.py         # Templates réutilisables
```

## 📦 Fichiers

### `choices.py`
Contient tous les enums utilisés dans les modèles :
- `RecipientType` - Type de destinataire (Particulier, Entreprise, Administration)
- `MissiveType` - Type de missive (Email, SMS, WhatsApp, Postal, Notification)
- `MissiveStatus` - Statut (Draft, Pending, Sent, Delivered, etc.)
- `MissivePriority` - Priorité (Low, Normal, High, Urgent)

### `recipient.py`
Modèle `Recipient` pour centraliser les informations des destinataires :
- Identité (civilité, prénom, nom, entreprise)
- Coordonnées (email, téléphone, mobile)
- Adresse postale complète (lignes d'adresse, code postal, ville, région, pays)
- Relations : User Django, GenericForeignKey
- Propriétés : `full_name`, `display_name`, `postal_address`

### `missive.py`
Modèle principal `Missive` :
- Gère tous les types de missives (email, SMS, WhatsApp, courrier postal, notifications)
- Relations : Sender (User), Recipient, GenericForeignKey (source object)
- Champs de contenu (subject, body)
- Options spécifiques (recommandé, signature requise)
- Tracking (statut, dates, external_id, metadata)
- Provider configuré

### `attachment.py`
Modèle `MissiveAttachment` pour les pièces jointes :
- Peut être attachée à une Missive ou à n'importe quel modèle (GenericForeignKey)
- Support fichiers locaux OU URL externes (S3, Google Drive, etc.)
- Métadonnées (filename, description, file_size, mime_type)
- Validation automatique

### `event.py`
Modèle `MissiveEvent` pour l'historique :
- Enregistre tous les événements (sent, delivered, opened, clicked, bounced, etc.)
- Stocke les métadonnées (IP, user agent, etc.)
- Lié à un provider spécifique
- Permet le tracking complet du cycle de vie

### `template.py`
Modèle `MissiveTemplate` pour réutilisation :
- Templates de sujet et corps avec variables `{{variable}}`
- Lié à un type de missive spécifique
- Géré par un utilisateur créateur
- Activation/désactivation

## 💡 Utilisation

Tous les modèles restent accessibles de la même façon :

```python
# Import des modèles
from missive.models import (
    Missive,
    Recipient,
    MissiveAttachment,
    MissiveEvent,
    MissiveTemplate,
)

# Import des choix
from missive.models import (
    RecipientType,
    MissiveType,
    MissiveStatus,
    MissivePriority,
)

# Exemple d'utilisation
recipient = Recipient.objects.create(
    first_name="Jean",
    last_name="Dupont",
    email="jean@example.com",
    phone="+33600000000",
)

missive = Missive.objects.create(
    sender=request.user,
    recipient=recipient,
    missive_type=MissiveType.EMAIL,
    subject="Bonjour",
    body="Ceci est un test",
    status=MissiveStatus.DRAFT,
)
```

## 🔗 Relations entre modèles

```
┌─────────────┐
│  Recipient  │◄──┐
└─────────────┘   │
                  │
┌─────────────┐   │ ForeignKey
│   Missive   │───┤
└──────┬──────┘   │
       │          │
       │          │
       ├──────────┴───────────┐
       │                      │
       │ ForeignKey           │ ForeignKey
       │                      │
       ▼                      ▼
┌─────────────────┐    ┌──────────────┐
│ MissiveAttachment│    │ MissiveEvent │
└─────────────────┘    └──────────────┘

┌────────────────────┐
│  MissiveTemplate   │ (indépendant)
└────────────────────┘
```

## 🎯 Avantages de cette organisation

✅ **Lisibilité** - Chaque modèle dans son propre fichier  
✅ **Maintenabilité** - Plus facile de trouver et modifier un modèle  
✅ **Modularité** - Séparation claire des responsabilités  
✅ **Testabilité** - Tests plus ciblés par modèle  
✅ **Compatibilité** - Les imports existants fonctionnent toujours  
✅ **Évolutivité** - Facile d'ajouter de nouveaux modèles  

