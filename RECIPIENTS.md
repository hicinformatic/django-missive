# Gestion des Destinataires - Django Missive

Guide pour utiliser le modèle `Recipient` pour gérer les destinataires.

## 📋 Pourquoi un modèle Recipient ?

Au lieu d'avoir plein de champs optionnels dans `Missive` :
- ✅ **Réutilisable** : Un même destinataire pour plusieurs missives
- ✅ **Complet** : Adresse postale complète (3 lignes + ville + région + pays)
- ✅ **Structuré** : Civilité, prénom, nom, entreprise
- ✅ **Multi-coordonnées** : Email, téléphone fixe, mobile
- ✅ **GenericFK** : Lier à vos modèles (Customer, Contact, etc.)
- ✅ **Formatage** : Adresse postale formatée automatiquement

## 🎯 Utilisation

### Créer un destinataire

```python
from missive import Recipient, RecipientType

# Particulier
recipient = Recipient.objects.create(
    recipient_type=RecipientType.INDIVIDUAL,
    civility="M.",
    first_name="Jean",
    last_name="Dupont",
    email="jean.dupont@example.com",
    phone="+33600000000",
    address_line1="123 Rue de la Paix",
    postal_code="75001",
    city="Paris",
    country="FR"
)

# Entreprise
company = Recipient.objects.create(
    recipient_type=RecipientType.COMPANY,
    company_name="ACME Corp",
    email="contact@acme.com",
    phone="+33100000000",
    address_line1="456 Avenue des Champs",
    address_line2="Bâtiment A",
    postal_code="75008",
    city="Paris",
    country="FR"
)
```

### Lier à votre modèle métier

```python
from django.db import models
from missive.models import Recipient

class Customer(models.Model):
    name = models.CharField(max_length=100)
    # ... autres champs
    
    def get_or_create_recipient(self):
        """Crée ou récupère le Recipient lié à ce Customer"""
        recipient, created = Recipient.objects.get_or_create(
            content_object=self,
            defaults={
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,
                'phone': self.phone,
                # ... mapper vos champs
            }
        )
        return recipient
```

### Créer une missive avec un Recipient

```python
from missive import MissiveBuilder, MissiveSender, Recipient

# Avec un Recipient existant
recipient = Recipient.objects.get(email='user@example.com')

missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient=recipient,  # ← Utilise le Recipient
    subject="Test",
    body="..."
)

MissiveSender.send(missive)
# → Utilise automatiquement recipient.email
```

### Méthodes pratiques

```python
# Récupérer les coordonnées (gère automatiquement Recipient OU champs directs)
missive.get_recipient_email()    # → Email du Recipient ou recipient_email
missive.get_recipient_phone()    # → Mobile/Phone du Recipient ou recipient_phone
missive.get_recipient_address()  # → Adresse formatée du Recipient ou recipient_address

# Affichage
recipient.display_name           # → "ACME Corp (M. Jean Dupont)"
recipient.full_name              # → "M. Jean Dupont"
recipient.postal_address         # → Adresse formatée multi-lignes
```

## 📮 Exemple : Courrier postal avec adresse complète

```python
# Créer le destinataire avec adresse complète
recipient = Recipient.objects.create(
    recipient_type=RecipientType.COMPANY,
    company_name="Cabinet d'Avocats Dupont & Associés",
    civility="Me",
    first_name="Marie",
    last_name="Dupont",
    address_line1="Tour Montparnasse",
    address_line2="33 Avenue du Maine",
    address_line3="Bureau 504",
    postal_code="75015",
    city="Paris",
    state="Île-de-France",
    country="FR"
)

# Adresse formatée automatiquement :
print(recipient.postal_address)
# Cabinet d'Avocats Dupont & Associés
# Me Marie Dupont
# Tour Montparnasse
# 33 Avenue du Maine
# Bureau 504
# 75015 Paris
# Île-de-France

# Créer la missive
missive = Missive.objects.create(
    sender=system_user,
    missive_type=MissiveType.POSTAL,
    recipient=recipient,  # ← Toute l'adresse est incluse
    subject="Mise en demeure",
    body="...",
    is_registered=True,
    requires_signature=True,
    provider="laposte"
)

MissiveSender.send(missive)
# → La Poste reçoit l'adresse complète et formatée
```

## 🔄 Compatibilité

Les deux méthodes fonctionnent :

### Méthode 1 : Avec Recipient (recommandé)

```python
recipient = Recipient.objects.create(
    first_name="Jean",
    last_name="Dupont",
    email="jean@example.com"
)

missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient=recipient,  # ← Utilise Recipient
    subject="Test",
    body="..."
)
```

### Méthode 2 : Sans Recipient (legacy)

```python
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient_email="jean@example.com",  # ← Champs directs
    subject="Test",
    body="..."
)
```

Les providers utilisent `get_recipient_email()` qui gère les deux cas !

## 📊 Réutilisation

```python
# Créer un destinataire une fois
recipient = Recipient.objects.create(
    first_name="Jean",
    last_name="Dupont",
    email="jean@example.com",
    phone="+33600000000"
)

# Réutiliser pour plusieurs missives
email = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    recipient=recipient,  # Même destinataire
    subject="Email 1",
    body="..."
)

sms = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.SMS,
    recipient=recipient,  # Même destinataire
    subject="SMS 1",
    body="..."
)

# Toutes les missives du destinataire
recipient.missives.all()
```

## 🔗 Lier à vos modèles

```python
# Exemple avec un Customer
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    
# Créer un Recipient lié
recipient = Recipient.objects.create(
    content_object=customer,  # GenericForeignKey
    first_name=customer.name.split()[0],
    email=customer.email,
    # ...
)

# Retrouver tous les Recipients d'un Customer
from django.contrib.contenttypes.models import ContentType
ct = ContentType.objects.get_for_model(Customer)
recipients = Recipient.objects.filter(content_type=ct, object_id=customer.id)
```

## 📝 Dans l'admin Django

L'admin `Recipient` permet de :
- ✅ Créer/modifier des destinataires
- ✅ Voir l'adresse formatée
- ✅ Lier à un User ou un objet quelconque
- ✅ Filtrer par type, pays, ville
- ✅ Chercher par nom, email, téléphone
- ✅ Voir toutes les missives envoyées à ce destinataire

## 💡 Bonnes pratiques

1. **Utiliser Recipient** pour les adresses postales complexes
2. **Champs directs** pour les cas simples (email one-shot)
3. **Réutiliser** les Recipients fréquents
4. **Lier aux modèles** métier avec GenericFK
5. **Valider** les données (email, téléphone) avant création

```python
# Helper pour créer depuis vos modèles
def create_recipient_from_customer(customer):
    return Recipient.objects.create(
        content_object=customer,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        phone=customer.phone,
        address_line1=customer.address,
        postal_code=customer.zip_code,
        city=customer.city,
        country=customer.country_code,
    )
```

## 🎨 Types de destinataires

- `INDIVIDUAL` - Particulier (par défaut)
- `COMPANY` - Entreprise
- `ADMINISTRATION` - Administration publique

Utile pour :
- Adapter le ton des messages
- Filtrer par type
- Statistiques par segment

## 📈 Statistiques

```python
from missive.models import Recipient
from django.db.models import Count

# Nombre de missives par destinataire
top_recipients = Recipient.objects.annotate(
    missive_count=Count('missives')
).order_by('-missive_count')[:10]

for r in top_recipients:
    print(f"{r.display_name}: {r.missive_count} missives")
```

