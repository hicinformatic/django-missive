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

    # Services disponibles (granularité plus fine que supported_types)
    # Format: ['service_name', ...]
    # Exemples:
    # - SendGrid: ['email']
    # - Brevo/SendinBlue: ['email', 'sms', 'email_transactional', 'email_marketing']
    # - La Poste: ['postal', 'postal_registered', 'postal_signature', 'email_ar']
    # - Twilio: ['sms', 'voice', 'whatsapp']
    services = []

    # Marques de messagerie supportées (pour type BRANDED uniquement)
    # Format: ['brand_name', ...]
    # Exemples:
    # - Twilio: ['whatsapp']  # Twilio propose WhatsApp Business API
    # - Slack: ['slack']
    # - Teams: ['teams']
    # - Un provider multi-brand pourrait avoir: ['whatsapp', 'telegram', 'messenger']
    brands = []

    # Variables de configuration requises (depuis settings.py ou .env)
    # Format: ['VARIABLE_NAME', ...]
    # Exemples:
    # - SendGrid: ['SENDGRID_API_KEY']
    # - Twilio: ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN']
    # - SMSPartner: ['SMSPARTNER_API_KEY', 'SMSPARTNER_SENDER']
    config_keys = []

    # Packages Python requis (pour vérifier l'installation)
    # Format: ['package_name', ...] ou [] si pas de dépendance externe
    # Exemples:
    # - SendGrid: ['sendgrid']
    # - Twilio: ['twilio']
    # - Teams: ['msgraph-core', 'msal']
    # - Django Email: [] (toujours disponible)
    required_packages = []

    # URL de la page de statut/SLA du service (optionnel)
    # Exemples:
    # - SMSPartner: 'https://status.smspartner.fr/status/nda-media'
    # - Twilio: 'https://status.twilio.com/'
    # - SendGrid: 'https://status.sendgrid.com/'
    status_url = None

    # URL de la documentation API du service (optionnel)
    # Exemples:
    # - SMSPartner: 'https://www.docpartner.dev/'
    # - Twilio: 'https://www.twilio.com/docs'
    # - SendGrid: 'https://docs.sendgrid.com/'
    documentation_url = None

    # URL du site web officiel du provider (optionnel)
    # Exemples:
    # - SMSPartner: 'https://www.smspartner.fr/'
    # - Twilio: 'https://www.twilio.com/'
    # - SendGrid: 'https://sendgrid.com/'
    site_url = None

    # Description du provider (texte libre, optionnel)
    # Affiché dans l'admin pour donner plus de contexte
    # Exemples:
    # - Twilio: "Plateforme cloud multi-canal (SMS, WhatsApp, Voice)"
    # - LaPoste: "Envoi de courrier recommandé sur le territoire français"
    description_text = None

    def __init__(self, missive: Optional[Missive] = None):
        """
        Initialise le provider.

        Args:
            missive: La missive à envoyer (None pour les webhooks)
        """
        self.missive = missive
        self.config = self._get_config()

    def _get_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration du provider depuis Django settings.

        Returns:
            Dict contenant toutes les clés de configuration du provider
        """
        config = {}
        for key in self.config_keys:
            value = getattr(settings, key, None)
            if value is not None:
                config[key] = value
        return config

    def supports(self, missive_type: str) -> bool:
        """
        Vérifie si ce provider supporte un type de missive.

        Args:
            missive_type: Le type de missive (MissiveType)

        Returns:
            bool: True si supporté
        """
        return missive_type in self.supported_types

    def has_service(self, service: str) -> bool:
        """
        Vérifie si ce provider offre un service spécifique.

        Args:
            service: Le service à vérifier (ex: 'email', 'sms', 'postal_registered')

        Returns:
            bool: True si le service est disponible
        """
        return service in self.services

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
            external_id: Référence externe du provider
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

    def get_proofs_of_delivery(self, service_type: Optional[str] = None) -> list:
        """
        Récupère toutes les preuves de dépôt/livraison selon le type de service.

        Un envoi peut générer plusieurs preuves :
        - LRE : Certificat de dépôt + AR électronique + copie du document
        - Courrier recommandé : Preuve de dépôt + avis de passage + AR + copie scannée
        - Email AR : Accusé de réception + logs SMTP
        - SMS : Statut de livraison + logs opérateur

        Args:
            service_type: Type de service spécifique (postal_registered, lre, email_ar, etc.)
                         Si None, déduit automatiquement depuis la missive.

        Returns:
            Liste de Dict, chaque Dict contenant :
            {
                "type": str,                    # Type de preuve (deposit_certificate, delivery_receipt, etc.)
                "label": str,                   # Label affiché (ex: "Certificat de dépôt")
                "available": bool,              # Preuve disponible ?
                "url": str,                     # URL de téléchargement
                "generated_at": datetime,       # Date de génération
                "expires_at": datetime,         # Date d'expiration (optionnel)
                "format": str,                  # Format (pdf, xml, json, etc.)
                "metadata": dict,               # Métadonnées additionnelles
            }

        Example:
            # Pour une LRE AR24
            provider = AR24Provider(missive)
            proofs = provider.get_proofs_of_delivery('lre')
            for proof in proofs:
                if proof['available']:
                    print(f"{proof['label']}: {proof['url']}")
        """
        if not self.missive:
            return []

        # Déterminer automatiquement le type de service si non fourni
        if not service_type:
            service_type = self._detect_service_type()

        # Par défaut, retourner une liste vide
        # Les providers concrets doivent override cette méthode
        return []

    def _detect_service_type(self) -> str:
        """
        Détecte automatiquement le type de service selon la missive.

        Returns:
            Type de service détecté (lre, postal_registered, email_ar, sms, etc.)
        """
        if not self.missive:
            return "unknown"

        missive_type = self.missive.missive_type

        # Mapping type de missive + options → service
        if missive_type == "LRE":
            return "lre"
        elif missive_type == "POSTAL":
            if self.missive.is_registered:
                return "postal_registered"
            return "postal"
        elif missive_type == "EMAIL":
            if self.missive.is_registered:
                return "email_ar"
            return "email"
        elif missive_type == "SMS":
            return "sms"
        elif missive_type == "BRANDED":
            # Pour le type BRANDED, utiliser le nom du provider comme service
            # Ex: WhatsAppProvider (name="whatsapp") → service "whatsapp"
            return self.name.lower() if hasattr(self, "name") else "branded"
        elif missive_type == "RCS":
            return "rcs"

        return missive_type.lower()

    def list_available_proofs(self) -> Dict[str, bool]:
        """
        Liste tous les types de preuves disponibles pour cette missive.

        Returns:
            Dict {service_type: available}

        Example:
            {
                "lre": True,
                "deposit_certificate": True,
                "delivery_receipt": False,
            }
        """
        if not self.missive:
            return {}

        service_type = self._detect_service_type()

        # Services qui génèrent des preuves
        proof_services = {
            "lre",
            "postal_registered",
            "postal_signature",
            "email_ar",
        }

        return {service_type: service_type in proof_services}

    def get_service_status(self) -> Dict[str, Any]:
        """
        Récupère le statut du service provider.

        Cette méthode doit être override par les providers concrets pour fournir
        des informations réelles (crédits, quotas, SLA, etc.).

        Returns:
            Dict avec les informations de statut :
            {
                "status": str,                  # operational, critical, unreachable, etc.
                "is_available": bool,           # Le service est-il disponible ?
                "services": list,               # Liste des services du provider
                "credits": dict,                # Informations de crédits
                "rate_limits": dict,            # Limites de taux
                "sla": dict,                    # SLA du provider
                "last_check": datetime,         # Date de dernière vérification
                "warnings": list,               # Avertissements éventuels
                "details": dict,                # Détails spécifiques
            }
        """
        return {
            "status": "unknown",
            "is_available": None,
            "services": self.services,
            "credits": None,
            "rate_limits": {},
            "sla": {},
            "last_check": timezone.now(),
            "warnings": [
                "Méthode get_service_status() non implémentée pour ce provider"
            ],
            "details": {},
        }
