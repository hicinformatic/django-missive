# Actions Admin - Django Missive

Django Missive inclut des actions personnalisées dans l'interface d'administration pour faciliter la gestion et la validation des missives et destinataires.

## 📧 Actions sur les Recipients

Depuis `/admin/missive/recipient/`, sélectionnez un ou plusieurs destinataires et choisissez une action :

### 🔍 Valider les emails

**Action** : `🔍 Valider les emails`

Teste la validité et le risque d'échec pour tous les emails des destinataires sélectionnés.

**Ce qui se passe** :
1. Validation syntaxique de chaque email
2. Vérification du domaine
3. Calcul du score de risque (0-100)
4. Les emails invalides → destinataire désactivé (`is_active = False`)
5. Les emails risqués → note ajoutée avec le score
6. Message récapitulatif affiché

**Exemple de résultat** :
```
✅ Validation terminée : 10 recipient(s) analysé(s)
❌ 2 invalide(s)
⚠️ 3 à risque
```

**Modifications automatiques** :
- Email **invalide** : `is_active = False` + note "❌ Email invalide: Format d'email invalide"
- Email **risqué** (score > 50) : note "⚠️ Email risqué (score: 75): Domaine jetable détecté"

### 📞 Valider les téléphones

**Action** : `📞 Valider les téléphones`

Teste la validité des numéros de téléphone (mobile ou fixe).

**Ce qui se passe** :
1. Validation du format (international recommandé)
2. Détection du type de ligne (mobile/fixe)
3. Les numéros invalides → note ajoutée
4. Les numéros fixes → note ajoutée (SMS impossibles)

**Exemple de résultat** :
```
✅ Validation terminée : 10 recipient(s) analysé(s)
❌ 1 invalide(s)
⚠️ 2 numéro(s) fixe(s)
```

**Modifications automatiques** :
- Téléphone **invalide** : note "❌ Téléphone invalide: Format international recommandé (+33...)"
- Numéro **fixe** : note "⚠️ Numéro fixe détecté (pas de SMS possible)"

### ✨ Valider tout (email + téléphone)

**Action** : `✨ Valider tout (email + téléphone)`

Validation complète de tous les moyens de contact.

**Ce qui se passe** :
1. Valide l'email (si présent)
2. Valide le téléphone (si présent)
3. Compile tous les problèmes dans les notes
4. Compte les destinataires 100% valides

**Exemple de résultat** :
```
✅ Validation complète terminée :
✅ 5 recipient(s) 100% valide(s)
⚠️ 3 avec problème(s) email
⚠️ 2 avec problème(s) téléphone
```

**Note ajoutée** :
```
⚠️ Validation:
  - Email: Domaine jetable détecté
  - Téléphone: Format international recommandé (+33...)
```

## 📨 Actions sur les Missives

Depuis `/admin/missive/missive/`, sélectionnez une ou plusieurs missives et choisissez une action :

### Marquer comme envoyé

**Action** : `Marquer comme envoyé`

Change le statut à `SENT` et enregistre la date d'envoi.

**Utilisation** : Pour marquer manuellement des missives comme envoyées (envoi externe, test, etc.)

### Marquer comme délivré

**Action** : `Marquer comme délivré`

Change le statut à `DELIVERED` et enregistre la date de délivrance.

**Utilisation** : Confirmation manuelle de délivrance (courrier postal reçu, etc.)

### Marquer comme échoué

**Action** : `Marquer comme échoué`

Change le statut à `FAILED`.

**Utilisation** : Annuler ou marquer des échecs d'envoi

### 🔍 Analyser le risque d'échec

**Action** : `🔍 Analyser le risque d'échec`

**NOUVEAU !** Analyse détaillée du risque d'échec avant envoi.

**Ce qui se passe** :
1. Pour chaque missive sélectionnée
2. Détecte le provider approprié
3. Calcule le score de risque :
   - Validation du destinataire (email/phone)
   - Disponibilité du service
   - Autres facteurs
4. Stocke le résultat dans `missive.metadata["risk_analysis"]`
5. Affiche un récapitulatif par niveau de risque

**Exemple de résultat** :
```
✅ Analyse de risque terminée :
🟢 5 risque faible
🟡 2 risque moyen
🟠 1 risque élevé
🔴 0 risque critique
Les résultats sont dans le champ 'metadata' de chaque missive
```

**Métadonnées ajoutées** :
```python
missive.metadata = {
    'risk_analysis': {
        'score': 25,
        'level': 'low',
        'recommendations': [],
        'checked_at': '2025-11-08T10:30:00'
    }
}
```

**Niveaux de risque** :
- 🟢 **Low** (0-24) : Envoi sûr
- 🟡 **Medium** (25-49) : Envoi avec surveillance
- 🟠 **High** (50-74) : Vérification recommandée
- 🔴 **Critical** (75-100) : Envoi déconseillé

## 🎯 Workflow recommandé

### Pour les nouveaux destinataires

1. **Importer/créer** les destinataires
2. **Sélectionner tous** les nouveaux
3. **Action** : "✨ Valider tout (email + téléphone)"
4. **Vérifier** les notes pour les problèmes détectés
5. **Corriger** les coordonnées si nécessaire
6. **Désactiver** les destinataires invalides

### Avant une campagne d'envoi

1. **Créer** toutes les missives (brouillon)
2. **Sélectionner toutes** les missives
3. **Action** : "🔍 Analyser le risque d'échec"
4. **Filtrer** par métadonnées pour voir les risques élevés
5. **Corriger** ou **annuler** les missives à risque
6. **Envoyer** les missives sûres

### Nettoyage périodique

```python
# Script de maintenance
from missive.models import Recipient
from missive.providers.base import BaseProvider

provider = BaseProvider()

# Valider tous les emails actifs
for recipient in Recipient.objects.filter(is_active=True, email__isnull=False):
    validation = provider.validate_email(recipient.email)
    
    if not validation['is_valid']:
        recipient.is_active = False
        recipient.notes = f"Auto-désactivé: {validation['warnings']}"
        recipient.save()
```

## 🔧 Personnalisation

Vous pouvez ajouter vos propres actions dans `RecipientAdmin` ou `MissiveAdmin` :

```python
from django.contrib import admin
from missive.admin import RecipientAdmin as BaseRecipientAdmin

class CustomRecipientAdmin(BaseRecipientAdmin):
    """Admin personnalisé avec vos propres actions"""
    
    actions = BaseRecipientAdmin.actions + ["export_valid_emails"]
    
    @admin.action(description="📤 Exporter les emails valides")
    def export_valid_emails(self, request, queryset):
        """Exporte les emails validés en CSV"""
        from ..providers.base import BaseProvider
        import csv
        from django.http import HttpResponse
        
        provider = BaseProvider()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="valid_emails.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Nom', 'Risk Score'])
        
        for recipient in queryset:
            if recipient.email:
                validation = provider.validate_email(recipient.email)
                if validation['is_valid'] and validation['risk_score'] < 50:
                    writer.writerow([
                        recipient.email,
                        recipient.display_name,
                        validation['risk_score']
                    ])
        
        return response

# Ne pas oublier de désenregistrer et réenregistrer
admin.site.unregister(Recipient)
admin.site.register(Recipient, CustomRecipientAdmin)
```

## 📊 Informations affichées

### Dans la liste des Recipients

Après validation, consultez la colonne **Notes** pour voir :
- ❌ Les erreurs de validation
- ⚠️ Les avertissements
- Scores de risque
- Recommandations

### Dans les détails d'une Missive

Après analyse de risque, consultez le champ **Métadonnées** (JSON) :

```json
{
  "risk_analysis": {
    "score": 35,
    "level": "medium",
    "recommendations": [
      "Format international recommandé (+33...)"
    ],
    "checked_at": "2025-11-08T10:30:00",
    "factors": {
      "email_validation": {
        "is_valid": true,
        "risk_score": 35,
        "warnings": ["..."]
      },
      "service_availability": {
        "is_available": true,
        "quota_remaining": 1000
      }
    }
  }
}
```

## 🚀 Exemples concrets

### Exemple 1 : Nettoyer une base de données

Vous importez 1000 contacts depuis un fichier Excel :

1. Allez dans `/admin/missive/recipient/`
2. Sélectionnez **Tous les 1000 destinataires**
3. Choisissez l'action : **"✨ Valider tout (email + téléphone)"**
4. Résultat affiché :
   ```
   ✅ 750 recipients 100% valides
   ⚠️ 150 avec problèmes email
   ⚠️ 100 avec problèmes téléphone
   ```
5. Filtrez par `is_active = False` pour voir les invalides
6. Vérifiez les notes pour les détails des problèmes

### Exemple 2 : Campagne d'envoi sécurisée

Vous préparez une campagne email importante :

1. Créez toutes vos missives en brouillon
2. Allez dans `/admin/missive/missive/`
3. Sélectionnez toutes les missives de la campagne
4. Action : **"🔍 Analyser le risque d'échec"**
5. Résultat :
   ```
   🟢 80 risque faible
   🟡 15 risque moyen
   🟠 4 risque élevé
   🔴 1 risque critique
   ```
6. Filtrez et vérifiez les missives à risque
7. Corrigez les emails problématiques
8. Relancez l'analyse
9. Envoyez uniquement les missives à faible risque

### Exemple 3 : Validation avant import

Avant même de créer les Recipients :

```python
from missive.providers.base import BaseProvider

# Liste d'emails à importer
emails = ['user1@example.com', 'bad@tempmail.com', 'user3@company.com']

provider = BaseProvider()

valid_emails = []
for email in emails:
    validation = provider.validate_email(email)
    if validation['is_valid'] and validation['risk_score'] < 50:
        valid_emails.append(email)
        # Créer le recipient
        Recipient.objects.create(email=email, ...)

print(f"Importé {len(valid_emails)} sur {len(emails)} emails")
```

## ⚙️ Configuration

Pour activer toutes les fonctionnalités de validation, installez les dépendances optionnelles :

```bash
pip install dnspython phonenumbers
```

Puis décommentez le code correspondant dans `missive/providers/base.py`.

## 💡 Conseils

### Validation régulière

Créez une tâche Celery ou un cron pour validation périodique :

```python
# tasks.py (Celery)
from celery import shared_task
from missive.models import Recipient
from missive.providers.base import BaseProvider

@shared_task
def validate_recipients_monthly():
    """Valide tous les recipients actifs chaque mois"""
    provider = BaseProvider()
    
    for recipient in Recipient.objects.filter(is_active=True):
        if recipient.email:
            validation = provider.validate_email(recipient.email)
            if validation['risk_score'] > 70:
                recipient.is_active = False
                recipient.notes = f"Auto-désactivé: risque {validation['risk_score']}"
                recipient.save()
```

### Filtres personnalisés

Ajoutez des filtres dans l'admin pour voir rapidement les problèmes :

```python
class RecipientAdmin(admin.ModelAdmin):
    list_filter = [
        'is_active',
        'recipient_type',
        EmailValidFilter,  # Filtre personnalisé
    ]

class EmailValidFilter(admin.SimpleListFilter):
    title = 'Validité email'
    parameter_name = 'email_valid'
    
    def lookups(self, request, model_admin):
        return (
            ('valid', 'Emails valides'),
            ('invalid', 'Emails invalides'),
            ('risky', 'Emails risqués'),
        )
    
    def queryset(self, request, queryset):
        from missive.providers.base import BaseProvider
        provider = BaseProvider()
        
        if self.value() == 'invalid':
            # Filtrer les emails invalides
            invalid_ids = []
            for obj in queryset.filter(email__isnull=False):
                if not provider.validate_email(obj.email)['is_valid']:
                    invalid_ids.append(obj.id)
            return queryset.filter(id__in=invalid_ids)
        
        # ... autres conditions
```

## 📚 Documentation associée

- **VALIDATION.md** - Guide complet sur la validation et le risque d'échec
- **RECIPIENTS.md** - Documentation du modèle Recipient
- **PROVIDERS.md** - Détails sur les providers et leurs fonctionnalités

## ✅ Résumé des actions disponibles

| Modèle | Action | Description | Modifications |
|--------|--------|-------------|---------------|
| **Recipient** | 🔍 Valider les emails | Teste la validité des emails | Désactive si invalide, ajoute notes |
| **Recipient** | 📞 Valider les téléphones | Teste la validité des téléphones | Ajoute notes si problème |
| **Recipient** | ✨ Valider tout | Validation complète | Notes détaillées |
| **Missive** | Marquer comme envoyé | Change statut → SENT | Met à jour sent_at |
| **Missive** | Marquer comme délivré | Change statut → DELIVERED | Met à jour delivered_at |
| **Missive** | Marquer comme échoué | Change statut → FAILED | - |
| **Missive** | 🔍 Analyser le risque | Calcule le score de risque | Ajoute risk_analysis dans metadata |

## 🎓 Cas d'usage avancés

### 1. Pré-validation avant campagne

```python
# Dans votre code de préparation de campagne
from missive.models import Recipient
from missive.providers.base import BaseProvider

provider = BaseProvider()

# Marquer les destinataires à risque
campaign_recipients = Recipient.objects.filter(
    tags__contains=['campaign_2025']
)

risky_count = 0
for recipient in campaign_recipients:
    if recipient.email:
        validation = provider.validate_email(recipient.email)
        if validation['risk_score'] > 50:
            risky_count += 1
            recipient.notes = f"⚠️ Exclu de campagne: risque {validation['risk_score']}"
            recipient.save()

print(f"{risky_count} destinataires exclus pour risque élevé")
```

### 2. Audit de qualité des données

```python
# Script d'audit
from missive.models import Recipient
from missive.providers.base import BaseProvider

provider = BaseProvider()

stats = {
    'total': 0,
    'valid_emails': 0,
    'valid_phones': 0,
    'complete_addresses': 0,
}

for recipient in Recipient.objects.all():
    stats['total'] += 1
    
    if recipient.email:
        if provider.validate_email(recipient.email)['is_valid']:
            stats['valid_emails'] += 1
    
    if recipient.mobile or recipient.phone:
        phone = recipient.mobile or recipient.phone
        if provider.validate_phone_number(phone)['is_valid']:
            stats['valid_phones'] += 1
    
    if recipient.postal_address:
        stats['complete_addresses'] += 1

print(f"""
Qualité de la base de données :
- Total: {stats['total']} recipients
- Emails valides: {stats['valid_emails']} ({stats['valid_emails']/stats['total']*100:.1f}%)
- Téléphones valides: {stats['valid_phones']} ({stats['valid_phones']/stats['total']*100:.1f}%)
- Adresses complètes: {stats['complete_addresses']} ({stats['complete_addresses']/stats['total']*100:.1f}%)
""")
```

### 3. Alertes automatiques

```python
# Dans votre code d'envoi
from missive import MissiveSender
from missive.providers import get_provider_class

def send_with_risk_check(missive, max_risk=70):
    """Envoie uniquement si le risque est acceptable"""
    
    provider_class = MissiveSender.get_provider_class(missive)
    provider = provider_class(missive)
    
    risk = provider.calculate_delivery_risk()
    
    if risk['risk_score'] > max_risk:
        # Alerter l'admin
        send_admin_notification(
            subject=f"Missive #{missive.id} à risque élevé",
            body=f"Score: {risk['risk_score']}\n"
                 f"Recommendations: {risk['recommendations']}"
        )
        return False
    
    return MissiveSender.send(missive)
```

## 🎨 Interface Admin

Les actions apparaissent dans le menu déroulant en haut de la liste :

```
┌─────────────────────────────────────────┐
│  Action: ▼ ---------                    │
│           🔍 Valider les emails          │
│           📞 Valider les téléphones      │
│           ✨ Valider tout                │
│                                   [Go]   │
└─────────────────────────────────────────┘

☑️ Recipient 1 - john@example.com
☑️ Recipient 2 - jane@tempmail.com  ⚠️
☑️ Recipient 3 - bob@company.com
```

Sélectionnez les destinataires souhaités (ou cochez "Tout sélectionner"), choisissez l'action, et cliquez sur **Go** !

## 📈 Métriques et reporting

Après avoir utilisé les actions de validation, vous pouvez générer des rapports :

```python
from missive.models import Recipient
from django.db.models import Q

# Recipients avec problèmes détectés
problematic = Recipient.objects.filter(
    Q(notes__contains='❌') | Q(notes__contains='⚠️')
)

print(f"{problematic.count()} recipients avec des problèmes")

# Recipients désactivés après validation
auto_disabled = Recipient.objects.filter(
    is_active=False,
    notes__contains='Email invalide'
)

print(f"{auto_disabled.count()} recipients auto-désactivés")
```

