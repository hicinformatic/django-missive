# Exemples d'utilisation - Django Missive

Ce fichier contient des exemples concrets d'utilisation de Django Missive.

## 📦 Créer des missives liées à vos modèles

### Exemple 1 : Notification de commande

```python
from django.db import models
from django.contrib.auth import get_user_model
from missive.helpers import MissiveBuilder
from missive.models import MissiveType, MissivePriority

User = get_user_model()

class Order(models.Model):
    """Modèle de commande"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.CharField(max_length=50)
    email = models.EmailField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Commande #{self.number}"
    
    def send_confirmation_email(self):
        """Envoie un email de confirmation lié à cette commande"""
        from missive.services import MissiveSender
        
        missive = MissiveBuilder.create_email(
            source_object=self,  # Lie la missive à cette commande
            sender=self.user,
            recipient_email=self.email,
            subject=f"Commande #{self.number} confirmée",
            body=f"""
            Bonjour,
            
            Votre commande #{self.number} d'un montant de {self.total}€ 
            a bien été confirmée.
            
            Merci pour votre confiance !
            """,
            is_registered=True,  # Email recommandé
            priority=MissivePriority.HIGH
        )
        
        # Envoyer immédiatement
        MissiveSender.send(missive)
        
        return missive
    
    def get_all_missives(self):
        """Récupère toutes les missives liées à cette commande"""
        return MissiveBuilder.get_missives_for_object(self)
```

### Exemple 2 : Notifications pour un système de participants

```python
from django.db import models
from django.contrib.auth import get_user_model
from missive.helpers import MissiveBuilder
from missive.models import MissiveType

User = get_user_model()

class Event(models.Model):
    """Événement"""
    title = models.CharField(max_length=255)
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    
    def __str__(self):
        return self.title


class Participant(models.Model):
    """Participant à un événement"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20)  # confirmed, pending, cancelled
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"
    
    def send_invitation(self):
        """Envoie une invitation par email ET SMS"""
        from missive.services import MissiveSender
        
        # Email
        email_missive = MissiveBuilder.create_email(
            source_object=self,
            sender=self.event.organizer,  # supposons que Event a un organizer
            recipient_email=self.email,
            subject=f"Invitation : {self.event.title}",
            body=f"""
            Bonjour {self.user.first_name},
            
            Vous êtes invité à {self.event.title}
            Date : {self.event.date}
            Lieu : {self.event.location}
            
            Confirmez votre présence en cliquant sur le lien...
            """
        )
        MissiveSender.send(email_missive)
        
        # SMS de rappel
        sms_missive = MissiveBuilder.create_sms(
            source_object=self,
            sender=self.event.organizer,
            recipient_phone=self.phone,
            subject="Invitation événement",
            body=f"Invitation: {self.event.title} le {self.event.date.strftime('%d/%m/%Y')}"
        )
        MissiveSender.send(sms_missive)
        
        return email_missive, sms_missive
    
    def send_reminder(self):
        """Rappel 24h avant l'événement"""
        missive = MissiveBuilder.create_notification(
            source_object=self,
            sender=self.event.organizer,
            recipient_user=self.user,
            subject="Rappel : Événement demain",
            body=f"N'oubliez pas : {self.event.title} demain à {self.event.date.strftime('%H:%M')}",
            priority=MissivePriority.HIGH
        )
        
        from missive.services import MissiveSender
        MissiveSender.send(missive)
        
        return missive
```

### Exemple 3 : Factures avec pièces jointes

```python
from django.db import models
from missive.helpers import MissiveBuilder
from missive.models import MissiveAttachment

class Invoice(models.Model):
    """Facture"""
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='invoices/')
    
    def __str__(self):
        return f"Facture {self.number}"
    
    def send_invoice_email(self):
        """Envoie la facture par email avec PDF en pièce jointe"""
        from missive.services import MissiveSender
        
        # Créer la missive
        missive = MissiveBuilder.create_email(
            source_object=self,
            sender=self.customer,  # ou un user système
            recipient_email=self.customer.email,
            subject=f"Facture {self.number}",
            body=f"""
            Bonjour,
            
            Veuillez trouver ci-joint votre facture {self.number}
            d'un montant de {self.amount}€.
            
            Cordialement,
            """
        )
        
        # Ajouter la pièce jointe (fichier local)
        attachment = MissiveAttachment.objects.create(
            missive=missive,
            file=self.pdf_file,
            filename=f"facture_{self.number}.pdf",
            file_size=self.pdf_file.size,
            content_type='application/pdf',
            description=f"Facture {self.number}"
        )
        
        # Mettre à jour le compteur
        missive.attachments_count = 1
        missive.save()
        
        # Envoyer
        MissiveSender.send(missive)
        
        return missive
    
    def send_invoice_with_external_link(self, s3_url):
        """Envoie la facture avec lien S3"""
        from missive.services import MissiveSender
        
        missive = MissiveBuilder.create_email(
            source_object=self,
            sender=self.customer,
            recipient_email=self.customer.email,
            subject=f"Facture {self.number}",
            body=f"Votre facture est disponible en téléchargement."
        )
        
        # Ajouter une pièce jointe externe (URL S3, Google Drive, etc.)
        attachment = MissiveAttachment.objects.create(
            missive=missive,
            external_url=s3_url,
            filename=f"facture_{self.number}.pdf",
            file_size=None,  # Optionnel pour les fichiers externes
            content_type='application/pdf',
            description=f"Facture {self.number} hébergée sur S3"
        )
        
        missive.attachments_count = 1
        missive.save()
        
        MissiveSender.send(missive)
        
        return missive
```

### Exemple 4 : Statistiques et reporting

```python
from missive.helpers import get_missives_stats_for_object, MissiveBuilder
from django.db.models import Count, Q

def order_report(order):
    """Génère un rapport des missives pour une commande"""
    stats = get_missives_stats_for_object(order)
    
    print(f"Statistiques pour {order}:")
    print(f"  Total: {stats['total']}")
    print(f"  Envoyés: {stats['sent']}")
    print(f"  Délivrés: {stats['delivered']}")
    print(f"  Échecs: {stats['failed']}")
    
    # Liste détaillée
    missives = MissiveBuilder.get_missives_for_object(order)
    for missive in missives:
        print(f"  - {missive.get_missive_type_display()}: {missive.subject} [{missive.get_status_display()}]")


def global_stats():
    """Statistiques globales"""
    from missive.models import Missive, MissiveStatus, MissiveType
    
    total = Missive.objects.count()
    
    # Par type
    by_type = Missive.objects.values('missive_type').annotate(
        count=Count('id')
    )
    
    # Taux de succès
    success = Missive.objects.filter(
        status__in=[MissiveStatus.DELIVERED, MissiveStatus.READ]
    ).count()
    success_rate = (success / total * 100) if total > 0 else 0
    
    print(f"Total missives: {total}")
    print(f"Taux de succès: {success_rate:.2f}%")
    print("\nPar type:")
    for item in by_type:
        print(f"  {item['missive_type']}: {item['count']}")
```

### Exemple 5 : Signal Django pour automatisation

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from missive.helpers import MissiveBuilder
from missive.services import MissiveSender

@receiver(post_save, sender=Order)
def send_order_notifications(sender, instance, created, **kwargs):
    """Envoie automatiquement des notifications lors de la création/modification d'une commande"""
    if created:
        # Nouvelle commande : email de confirmation
        missive = MissiveBuilder.create_email(
            source_object=instance,
            sender=instance.user,
            recipient_email=instance.email,
            subject=f"Commande #{instance.number} reçue",
            body="Votre commande a bien été reçue et est en cours de traitement."
        )
        MissiveSender.send(missive)
    
    elif instance.status == 'shipped':
        # Commande expédiée : SMS + email
        email = MissiveBuilder.create_email(
            source_object=instance,
            sender=instance.user,
            recipient_email=instance.email,
            subject=f"Commande #{instance.number} expédiée",
            body=f"Votre commande a été expédiée. Numéro de suivi: {instance.tracking_number}"
        )
        MissiveSender.send(email)
        
        if instance.phone:
            sms = MissiveBuilder.create_sms(
                source_object=instance,
                sender=instance.user,
                recipient_phone=instance.phone,
                subject="Commande expédiée",
                body=f"Commande #{instance.number} expédiée. Suivi: {instance.tracking_number}"
            )
            MissiveSender.send(sms)


@receiver(post_save, sender=Participant)
def participant_notifications(sender, instance, created, **kwargs):
    """Notifications pour les participants"""
    if created:
        # Nouveau participant : invitation
        instance.send_invitation()
    
    elif instance.status == 'confirmed':
        # Confirmation : notification
        missive = MissiveBuilder.create_notification(
            source_object=instance,
            sender=instance.event.organizer,
            recipient_user=instance.user,
            subject="Participation confirmée",
            body=f"Votre participation à {instance.event.title} est confirmée !"
        )
        MissiveSender.send(missive)
```

### Exemple 6 : Tâche Celery pour envois programmés

```python
from celery import shared_task
from django.utils import timezone
from missive.models import Missive, MissiveStatus
from missive.services import MissiveSender

@shared_task
def send_scheduled_missives():
    """
    Tâche Celery à exécuter périodiquement (toutes les minutes par exemple)
    pour envoyer les missives programmées
    """
    now = timezone.now()
    
    # Récupérer les missives programmées dont l'heure est arrivée
    missives = Missive.objects.filter(
        status=MissiveStatus.PENDING,
        scheduled_at__lte=now
    )
    
    results = {'sent': 0, 'failed': 0}
    
    for missive in missives:
        if MissiveSender.send(missive):
            results['sent'] += 1
        else:
            results['failed'] += 1
    
    return results


@shared_task
def send_event_reminders():
    """Envoie des rappels 24h avant les événements"""
    from datetime import timedelta
    tomorrow = timezone.now() + timedelta(days=1)
    
    # Événements de demain
    events = Event.objects.filter(
        date__date=tomorrow.date()
    )
    
    for event in events:
        for participant in event.participants.filter(status='confirmed'):
            participant.send_reminder()


# Dans votre celerybeat_schedule:
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'send-scheduled-missives': {
        'task': 'myapp.tasks.send_scheduled_missives',
        'schedule': crontab(minute='*/1'),  # Toutes les minutes
    },
    'send-event-reminders': {
        'task': 'myapp.tasks.send_event_reminders',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h
    },
}
```

### Exemple 7 : Vue Django avec création de missive

```python
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from missive.helpers import MissiveBuilder
from missive.services import MissiveSender
from missive.models import MissiveType

class SendNotificationView(LoginRequiredMixin, View):
    """Vue pour envoyer une notification"""
    
    def post(self, request, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            recipient = User.objects.get(id=user_id)
            message = request.POST.get('message')
            
            # Créer et envoyer la notification
            missive = MissiveBuilder.create_notification(
                source_object=request.user,  # L'expéditeur comme objet source
                sender=request.user,
                recipient_user=recipient,
                subject="Nouveau message",
                body=message
            )
            
            success = MissiveSender.send(missive)
            
            return JsonResponse({
                'status': 'success' if success else 'failed',
                'missive_id': missive.id,
                'missive_status': missive.status
            })
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
```

## 📎 Exemples de pièces jointes

### Fichier local

```python
from missive.models import MissiveAttachment

# Avec un fichier uploadé
attachment = MissiveAttachment.objects.create(
    missive=missive,
    file=uploaded_file,
    filename="document.pdf",
    file_size=uploaded_file.size,
    content_type="application/pdf",
    description="Contrat de vente"
)
```

### Fichier externe (S3, Google Drive, etc.)

```python
# Avec une URL externe
attachment = MissiveAttachment.objects.create(
    missive=missive,
    external_url="https://s3.amazonaws.com/bucket/file.pdf",
    filename="rapport_mensuel.pdf",
    content_type="application/pdf",
    description="Rapport hébergé sur S3"
)

# Récupérer l'URL du fichier (local ou externe)
url = attachment.file_url  # Retourne file.url ou external_url

# Vérifier si externe
if attachment.is_external:
    print("Fichier hébergé en externe")
```

## 🔍 Requêtes utiles

```python
from missive.models import Missive, MissiveType, MissiveStatus
from django.contrib.contenttypes.models import ContentType

# Toutes les missives liées à un type d'objet
order_ct = ContentType.objects.get_for_model(Order)
missives_for_orders = Missive.objects.filter(content_type=order_ct)

# Missives d'un objet spécifique
order = Order.objects.get(id=123)
missives = MissiveBuilder.get_missives_for_object(order)

# Emails recommandés non délivrés
failed_registered_emails = Missive.objects.filter(
    missive_type=MissiveType.EMAIL,
    is_registered=True,
    status=MissiveStatus.FAILED
)

# Statistiques par objet source
stats_by_model = Missive.objects.values('content_type__model').annotate(
    total=Count('id'),
    sent=Count('id', filter=Q(status=MissiveStatus.SENT))
)
```

## 📚 Plus d'informations

Consultez le fichier [USAGE.md](USAGE.md) pour la documentation complète.

