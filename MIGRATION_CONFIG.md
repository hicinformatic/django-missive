# 🔄 Migration vers le nouveau format MISSIVE_PROVIDERS

## 📋 Changement

Le nouveau format de configuration **MISSIVE_PROVIDERS** est maintenant **une liste simple** au lieu d'un dictionnaire par type.

### ❌ Ancien Format (toujours supporté)

```python
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.mailgun.MailgunProvider',
    ],
    'SMS': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    'BRANDED': [
        'missive.providers.slack.SlackProvider',
        'missive.providers.teams.TeamsProvider',
    ],
}
```

### ✅ Nouveau Format (recommandé)

```python
MISSIVE_PROVIDERS = [
    # Liste simple - auto-catégorisation
    'missive.providers.sendgrid.SendGridProvider',
    'missive.providers.mailgun.MailgunProvider',
    'missive.providers.twilio.TwilioProvider',
    'missive.providers.smspartner.SMSPartnerProvider',
    'missive.providers.slack.SlackProvider',
    'missive.providers.teams.TeamsProvider',
]
```

## 🎯 Avantages du Nouveau Format

| Ancien Format | Nouveau Format |
|---------------|----------------|
| ❌ Redondant (providers déclarent déjà `supported_types`) | ✅ DRY - une seule source de vérité |
| ❌ Répétition pour providers multi-types (Twilio dans EMAIL + SMS + BRANDED) | ✅ Déclaré une seule fois |
| ❌ Maintenance difficile | ✅ Facile d'ajouter/retirer un provider |
| ❌ Mapping manuel des noms de classes | ✅ Auto-découverte depuis le path |
| ❌ Erreurs si catégorie oubliée | ✅ Impossible d'oublier |

## 🔄 Comment Migrer

### Étape 1 : Convertir votre configuration

**Avant :**
```python
MISSIVE_PROVIDERS = {
    'EMAIL': ['missive.providers.sendgrid.SendGridProvider', ...],
    'SMS': ['missive.providers.twilio.TwilioProvider', ...],
}
```

**Après :**
```python
MISSIVE_PROVIDERS = [
    'missive.providers.sendgrid.SendGridProvider',
    'missive.providers.twilio.TwilioProvider',
    # ... tous vos providers en une liste
]
```

### Étape 2 : Supprimer les duplications

Si un provider apparaît dans plusieurs catégories (ex: Twilio), **ne le listez qu'une fois** :

```python
# Avant (répétition)
MISSIVE_PROVIDERS = {
    'SMS': ['missive.providers.twilio.TwilioProvider'],
    'BRANDED': ['missive.providers.twilio.TwilioProvider'],  # ← Doublon !
    'VOICE_CALL': ['missive.providers.twilio.TwilioProvider'],  # ← Doublon !
}

# Après (une seule fois)
MISSIVE_PROVIDERS = [
    'missive.providers.twilio.TwilioProvider',  # ✓ Auto-catégorisé dans SMS, BRANDED, VOICE_CALL
]
```

### Étape 3 : Providers Personnalisés

Ajoutez simplement le chemin complet de votre provider :

```python
MISSIVE_PROVIDERS = [
    # Providers Django-Missive
    'missive.providers.sendgrid.SendGridProvider',
    
    # Votre provider personnalisé
    'myapp.providers.MyCustomSMSProvider',
]
```

Votre provider doit juste déclarer ses `supported_types` :

```python
class MyCustomSMSProvider(BaseProvider):
    name = "mycustom"
    display_name = "My Custom SMS"
    supported_types = ["SMS"]  # ← Auto-catégorisé !
    
    def send_sms(self, **kwargs):
        # Votre implémentation
        pass
```

## 🔧 Rétrocompatibilité

L'ancien format (dict) est **toujours supporté** pour la compatibilité. Vous pouvez migrer à votre rythme.

## ✨ Auto-catégorisation

Le système lit automatiquement `supported_types` de chaque provider :

```python
# TwilioProvider déclare :
supported_types = ["SMS", "BRANDED"]  # SMS + WhatsApp

# → Automatiquement ajouté dans :
#   - providers_by_type["SMS"]
#   - providers_by_type["BRANDED"]
```

## 📝 Exemple Complet

Voir le fichier `MISSIVE_PROVIDERS_EXAMPLE.py` pour une configuration complète.

## ✅ Migration Réussie Si

- [ ] Tous vos providers sont dans une liste simple
- [ ] Aucun provider n'est dupliqué
- [ ] L'admin affiche tous les providers correctement
- [ ] Les descriptions s'affichent
- [ ] L'envoi de missives fonctionne

## 🆘 Support

En cas de problème, l'ancien format (dict) reste fonctionnel.

