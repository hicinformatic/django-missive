# Guide d'utilisation - Django Missive

## 🚀 Démarrage rapide

```bash
# Lancer le serveur de développement
python3 dev.py runserver
```

Accédez à http://127.0.0.1:8000/admin/ avec :
- **Username:** `admin`
- **Password:** `admin`

## 📦 Types de missives supportés

Django Missive permet d'envoyer 5 types de missives :

### 1. 📮 Courrier Postal (POSTAL)
- Courrier simple ou recommandé
- Avec ou sans signature
- **Champs requis:** `recipient_address`
- **Provider:** LaPoste API (à intégrer)

```python
from missive.models import Missive, MissiveType

missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.POSTAL,
    subject="Convocation",
    body="Vous êtes convoqué le...",
    recipient_address="John Doe\n123 Rue Example\n75001 Paris",
    is_registered=True,
    requires_signature=True
)
```

### 2. 📧 Email (EMAIL)
- Email simple ou recommandé (avec AR)
- Support des pièces jointes
- **Champs requis:** `recipient_email`
- **Provider:** Django Email / SendGrid / Mailgun

```python
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    subject="Confirmation de commande",
    body="Votre commande #12345 est confirmée",
    recipient_email="client@example.com",
    is_registered=True  # Email avec accusé de réception
)
```

### 3. 📱 SMS (SMS)
- Messages courts
- **Champs requis:** `recipient_phone` (format international)
- **Provider:** Twilio / OVH SMS

```python
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.SMS,
    subject="Code de vérification",
    body="Votre code est: 123456",
    recipient_phone="+33600000000"
)
```

### 4. 💬 WhatsApp (WHATSAPP)
- Messages WhatsApp Business
- **Champs requis:** `recipient_phone` (format international)
- **Provider:** WhatsApp Business API / Twilio

```python
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.WHATSAPP,
    subject="Rappel rendez-vous",
    body="N'oubliez pas votre RDV demain à 14h",
    recipient_phone="+33600000000"
)
```

### 5. 🔔 Notification in-app (NOTIFICATION)
- Notifications dans l'application
- **Champs requis:** `recipient_user`
- **Provider:** In-app / Firebase / OneSignal

```python
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.NOTIFICATION,
    subject="Nouveau message",
    body="Vous avez reçu un nouveau message",
    recipient_user=target_user
)
```

## 🎯 Envoyer une missive

### Méthode 1 : Via le code

```python
from missive.services import MissiveSender
from missive.models import Missive

# Créer la missive
missive = Missive.objects.create(...)

# Envoyer
success = MissiveSender.send(missive)

if success:
    print(f"Missive envoyée ! Statut: {missive.status}")
else:
    print(f"Échec: {missive.error_message}")
```

### Méthode 2 : Via l'admin Django

1. Allez dans l'admin : http://127.0.0.1:8000/admin/missive/missive/
2. Cliquez sur "Ajouter Missive"
3. Remplissez les champs selon le type
4. Sauvegardez
5. Sélectionnez la missive et utilisez l'action "Marquer comme envoyé"

## 📊 Statuts des missives

| Statut | Description |
|--------|-------------|
| `DRAFT` | Brouillon, non envoyé |
| `PENDING` | En attente d'envoi |
| `PROCESSING` | En cours de traitement |
| `SENT` | Envoyé |
| `DELIVERED` | Délivré au destinataire |
| `READ` | Lu par le destinataire |
| `FAILED` | Échec d'envoi |
| `CANCELLED` | Annulé |

## 🎨 Priorités

- `LOW` - Basse
- `NORMAL` - Normale (par défaut)
- `HIGH` - Haute
- `URGENT` - Urgente

## 📎 Pièces jointes

```python
from missive.models import MissiveAttachment

attachment = MissiveAttachment.objects.create(
    missive=missive,
    file=uploaded_file,
    filename="document.pdf",
    file_size=uploaded_file.size,
    content_type="application/pdf"
)

# Mettre à jour le compteur
missive.attachments_count = missive.attachments.count()
missive.save()
```

## 📈 Tracking et événements

Les événements sont automatiquement créés lors de l'envoi :

```python
from missive.models import MissiveEvent

# Créer un événement personnalisé
MissiveEvent.objects.create(
    missive=missive,
    event_type='opened',
    description='Email ouvert',
    metadata={'ip': '192.168.1.1', 'user_agent': '...'}
)

# Consulter l'historique
for event in missive.events.all():
    print(f"{event.created_at}: {event.event_type} - {event.description}")
```

## 📝 Templates

Créez des templates réutilisables :

```python
from missive.models import MissiveTemplate

template = MissiveTemplate.objects.create(
    name="Bienvenue nouveau client",
    missive_type=MissiveType.EMAIL,
    subject_template="Bienvenue {{first_name}} {{last_name}}",
    body_template="Bonjour {{first_name}},\n\nNous sommes ravis...",
    created_by=user
)

# Utiliser le template
from django.template import Template, Context

context = Context({'first_name': 'John', 'last_name': 'Doe'})
subject = Template(template.subject_template).render(context)
body = Template(template.body_template).render(context)

missive = Missive.objects.create(
    sender=user,
    missive_type=template.missive_type,
    subject=subject,
    body=body,
    ...
)
```

## 🔧 Configuration

Dans votre `settings.py` :

```python
# Django Missive Configuration
MISSIVE_CONFIG = {
    # Configuration des providers
    'EMAIL_PROVIDER': 'sendgrid',  # ou 'mailgun', 'aws_ses'
    'SMS_PROVIDER': 'twilio',      # ou 'ovh'
    'POSTAL_PROVIDER': 'laposte',  # ou 'lob'
    
    # API Keys (utiliser des variables d'environnement)
    'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    
    # Options
    'ENABLE_TRACKING': True,
    'AUTO_RETRY_FAILED': True,
    'MAX_RETRIES': 3,
}

# Configuration email Django
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

## 🔄 Envoi programmé

```python
from django.utils import timezone
from datetime import timedelta

# Programmer l'envoi dans 2 heures
missive = Missive.objects.create(
    sender=user,
    missive_type=MissiveType.EMAIL,
    subject="Rappel",
    body="Votre rendez-vous est dans 1 heure",
    recipient_email="user@example.com",
    scheduled_at=timezone.now() + timedelta(hours=2)
)

# Créer une tâche Celery pour traiter les missives programmées
# (voir documentation Celery)
```

## 📊 Statistiques

```python
from missive.models import Missive, MissiveStatus
from django.db.models import Count, Q

# Statistiques par statut
stats = Missive.objects.values('status').annotate(count=Count('id'))

# Taux de succès
total = Missive.objects.count()
success = Missive.objects.filter(
    status__in=[MissiveStatus.DELIVERED, MissiveStatus.READ]
).count()
success_rate = (success / total * 100) if total > 0 else 0

# Par type
by_type = Missive.objects.values('missive_type').annotate(
    total=Count('id'),
    sent=Count('id', filter=Q(status=MissiveStatus.SENT))
)
```

## 🎯 Intégration avec votre application

### Dans vos vues Django

```python
from django.views import View
from missive.models import Missive, MissiveType
from missive.services import MissiveSender

class SendNotificationView(View):
    def post(self, request):
        # Créer et envoyer une notification
        missive = Missive.objects.create(
            sender=request.user,
            missive_type=MissiveType.NOTIFICATION,
            recipient_user=target_user,
            subject="Nouveau message",
            body="Vous avez un nouveau message"
        )
        
        MissiveSender.send(missive)
        
        return JsonResponse({'status': 'sent', 'id': missive.id})
```

### Avec des signaux Django

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from myapp.models import Order
from missive.models import Missive, MissiveType
from missive.services import MissiveSender

@receiver(post_save, sender=Order)
def send_order_confirmation(sender, instance, created, **kwargs):
    if created:
        missive = Missive.objects.create(
            sender=instance.user,
            missive_type=MissiveType.EMAIL,
            recipient_email=instance.user.email,
            subject=f"Commande #{instance.id} confirmée",
            body=f"Merci pour votre commande...",
        )
        MissiveSender.send(missive)
```

## 🧪 Tests

```bash
# Lancer les tests
python3 dev.py test

# Avec couverture
python3 dev.py coverage
```

## 📚 Commandes utiles

```bash
# Développement
python3 dev.py runserver       # Lancer le serveur
python3 dev.py shell           # Shell Django
python3 dev.py makemigrations  # Créer migrations
python3 dev.py migrate         # Appliquer migrations

# Code quality
python3 dev.py format          # Formater le code
python3 dev.py lint            # Vérifier le code
python3 dev.py test            # Tests

# Build & publish
python3 dev.py build           # Builder le package
python3 dev.py upload-test     # Upload sur TestPyPI
python3 dev.py upload          # Upload sur PyPI
```

## 🤝 Contribution

Voir [CONTRIBUTING.md](CONTRIBUTING.md) pour plus de détails.

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

