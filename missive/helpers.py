"""
Helpers pour créer des missives depuis n'importe quel modèle.
"""

from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model

from .models import Missive, MissivePriority, MissiveType

User = get_user_model()


class MissiveBuilder:
    """
    Builder pour créer facilement des missives liées à n'importe quel objet.

    Usage:
        from missive.helpers import MissiveBuilder

        # Depuis une commande
        missive = MissiveBuilder.from_object(
            source_object=order,
            sender=order.user,
            missive_type=MissiveType.EMAIL,
            recipient_email=order.email,
            subject=f"Commande #{order.id} confirmée",
            body="Votre commande a été confirmée..."
        )
    """

    @staticmethod
    def from_object(
        source_object: Any,
        sender: User,
        missive_type: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        recipient_user: Optional[User] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        recipient_address: Optional[str] = None,
        priority: str = MissivePriority.NORMAL,
        is_registered: bool = False,
        requires_signature: bool = False,
        scheduled_at: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        **kwargs,
    ) -> Missive:
        """
        Crée une missive liée à un objet source.

        Args:
            source_object: L'objet source (Order, Participant, Invoice, etc.)
            sender: L'utilisateur expéditeur
            missive_type: Type de missive (EMAIL, SMS, POSTAL, etc.)
            subject: Sujet de la missive
            body: Corps du message (HTML pour emails, texte pour SMS)
            body_text: Version texte brut (optionnel pour emails, requis pour SMS)
            recipient_*: Informations du destinataire selon le type
            priority: Priorité de la missive
            is_registered: Si recommandé
            requires_signature: Si signature requise
            scheduled_at: Date d'envoi programmée
            metadata: Métadonnées additionnelles
            **kwargs: Autres paramètres du modèle Missive

        Returns:
            Missive: L'instance créée

        Example:
            from myapp.models import Order
            from missive.helpers import MissiveBuilder

            order = Order.objects.get(id=123)

            missive = MissiveBuilder.from_object(
                source_object=order,
                sender=order.user,
                missive_type=MissiveType.EMAIL,
                recipient_email=order.email,
                subject=f"Commande #{order.id} confirmée",
                body=f"Merci pour votre commande...",
                priority=MissivePriority.HIGH
            )
        """
        missive = Missive(
            content_object=source_object,
            sender=sender,
            missive_type=missive_type,
            subject=subject,
            body=body,
            body_text=body_text
            or body,  # Fallback: utilise body si body_text non fourni
            recipient_user=recipient_user,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            recipient_address=recipient_address,
            priority=priority,
            is_registered=is_registered,
            requires_signature=requires_signature,
            scheduled_at=scheduled_at,
            metadata=metadata or {},
            **kwargs,
        )
        missive.save()
        return missive

    @staticmethod
    def get_missives_for_object(obj: Any):
        """
        Récupère toutes les missives liées à un objet.

        Args:
            obj: L'objet source

        Returns:
            QuerySet: Les missives liées à cet objet

        Example:
            order = Order.objects.get(id=123)
            missives = MissiveBuilder.get_missives_for_object(order)

            for missive in missives:
                print(f"{missive.subject} - {missive.status}")
        """
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(obj)
        return Missive.objects.filter(content_type=content_type, object_id=obj.pk)

    @staticmethod
    def create_notification(
        source_object: Any,
        sender: User,
        recipient_user: User,
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL,
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer une notification in-app.

        Example:
            MissiveBuilder.create_notification(
                source_object=comment,
                sender=comment.author,
                recipient_user=post.author,
                subject="Nouveau commentaire",
                body=f"{comment.author} a commenté votre post"
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.NOTIFICATION,
            recipient_user=recipient_user,
            subject=subject,
            body=body,
            priority=priority,
            metadata=metadata,
        )

    @staticmethod
    def create_email(
        source_object: Any,
        sender: User,
        recipient_email: str,
        subject: str,
        body: str,
        body_text: Optional[str] = None,
        is_registered: bool = False,
        priority: str = MissivePriority.NORMAL,
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer un email.

        Example:
            MissiveBuilder.create_email(
                source_object=invoice,
                sender=request.user,
                recipient_email=invoice.customer_email,
                subject=f"Facture #{invoice.number}",
                body="Veuillez trouver ci-joint votre facture...",
                is_registered=True
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.EMAIL,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
            body_text=body_text,
            is_registered=is_registered,
            priority=priority,
            metadata=metadata,
        )

    @staticmethod
    def create_sms(
        source_object: Any,
        sender: User,
        recipient_phone: str,
        subject: str,
        body: str,
        priority: str = MissivePriority.NORMAL,
        metadata: Optional[Dict] = None,
    ) -> Missive:
        """
        Raccourci pour créer un SMS.

        Example:
            MissiveBuilder.create_sms(
                source_object=appointment,
                sender=system_user,
                recipient_phone=appointment.patient_phone,
                subject="Rappel RDV",
                body=f"RDV demain à {appointment.time}",
                priority=MissivePriority.HIGH
            )
        """
        return MissiveBuilder.from_object(
            source_object=source_object,
            sender=sender,
            missive_type=MissiveType.SMS,
            recipient_phone=recipient_phone,
            subject=subject,
            body=body,
            body_text=body,  # Pour SMS, body_text = body (texte brut)
            priority=priority,
            metadata=metadata,
        )


def get_missives_stats_for_object(obj: Any) -> Dict[str, int]:
    """
    Récupère des statistiques sur les missives liées à un objet.

    Args:
        obj: L'objet source

    Returns:
        Dict avec les stats (total, sent, delivered, failed, etc.)

    Example:
        order = Order.objects.get(id=123)
        stats = get_missives_stats_for_object(order)
        print(f"Total: {stats['total']}, Envoyés: {stats['sent']}")
    """
    from django.db.models import Count, Q

    from .models import MissiveStatus

    missives = MissiveBuilder.get_missives_for_object(obj)

    return {
        "total": missives.count(),
        "draft": missives.filter(status=MissiveStatus.DRAFT).count(),
        "pending": missives.filter(status=MissiveStatus.PENDING).count(),
        "sent": missives.filter(status=MissiveStatus.SENT).count(),
        "delivered": missives.filter(status=MissiveStatus.DELIVERED).count(),
        "read": missives.filter(status=MissiveStatus.READ).count(),
        "failed": missives.filter(status=MissiveStatus.FAILED).count(),
        "cancelled": missives.filter(status=MissiveStatus.CANCELLED).count(),
    }
