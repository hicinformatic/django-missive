"""
Fonctionnalités communes à tous les providers.
"""
from typing import Any, Dict, Optional

from django.conf import settings
from django.utils import timezone

from ...models import Missive, MissiveEvent, MissiveStatus


class BaseProviderCommon:
    """
    Classe de base avec les fonctionnalités communes à tous les providers.
    """

    # Nom du provider
    name = "Base"

    # Types de missives supportés (à définir dans les sous-classes)
    supported_types = []

    def __init__(self, missive: Optional[Missive] = None):
        """
        Initialise le provider.

        Args:
            missive: La missive à envoyer (None pour les webhooks)
        """
        self.missive = missive
        self.config = self._get_config()

    def supports(self, missive_type: str) -> bool:
        """
        Vérifie si ce provider supporte un type de missive.

        Args:
            missive_type: Le type de missive (MissiveType)

        Returns:
            bool: True si supporté
        """
        return missive_type in self.supported_types

    def _get_config(self) -> Dict[str, Any]:
        """Récupère la configuration depuis Django settings"""
        missive_config = getattr(settings, "MISSIVE_CONFIG", {})
        return missive_config

    def _update_status(
        self,
        status: MissiveStatus,
        provider: str = None,
        external_id: str = None,
        error_message: str = None,
    ):
        """
        Met à jour le statut de la missive et crée un événement.

        Args:
            status: Nouveau statut
            provider: Nom du provider
            external_id: ID externe du provider
            error_message: Message d'erreur éventuel
        """
        if not self.missive:
            return

        self.missive.status = status
        if provider:
            self.missive.provider = provider
        if external_id:
            self.missive.external_id = external_id
        if error_message:
            self.missive.error_message = error_message

        # Mettre à jour les dates selon le statut
        if status == MissiveStatus.SENT:
            self.missive.sent_at = timezone.now()
        elif status == MissiveStatus.DELIVERED:
            self.missive.delivered_at = timezone.now()
        elif status == MissiveStatus.READ:
            self.missive.read_at = timezone.now()

        self.missive.save()

    def _create_event(
        self,
        event_type: str,
        description: str = "",
        status: Optional[MissiveStatus] = None,
        metadata: Dict = None,
    ):
        """
        Crée un événement de tracking.

        Args:
            event_type: Type d'événement (sent, delivered, opened, etc.)
            description: Description de l'événement
            status: Statut associé (optionnel)
            metadata: Métadonnées additionnelles
        """
        if not self.missive:
            return

        MissiveEvent.objects.create(
            missive=self.missive,
            event_type=event_type,
            provider=self.name,
            description=description,
            status=status,
            metadata=metadata or {},
        )

    def get_status_from_event(self, event_type: str) -> Optional[MissiveStatus]:
        """
        Détermine le nouveau statut selon l'événement.

        Args:
            event_type: Type d'événement reçu

        Returns:
            MissiveStatus correspondant ou None
        """
        event_mapping = {
            "delivered": MissiveStatus.DELIVERED,
            "opened": MissiveStatus.READ,
            "clicked": MissiveStatus.READ,
            "read": MissiveStatus.READ,
            "bounced": MissiveStatus.FAILED,
            "failed": MissiveStatus.FAILED,
            "rejected": MissiveStatus.FAILED,
            "dropped": MissiveStatus.FAILED,
        }
        return event_mapping.get(event_type.lower())

