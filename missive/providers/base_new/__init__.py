"""
Provider de base avec toutes les fonctionnalités (composition de mixins).
"""
from typing import Any, Dict, Optional, Tuple

from django.utils import timezone

from ...models import Missive

from .common import BaseProviderCommon
from .email import BaseEmailMixin
from .notification import BaseNotificationMixin
from .postal import BasePostalMixin
from .sms import BaseSMSMixin
from .whatsapp import BaseWhatsAppMixin


class BaseProvider(
    BaseProviderCommon,
    BaseEmailMixin,
    BaseSMSMixin,
    BaseWhatsAppMixin,
    BasePostalMixin,
    BaseNotificationMixin,
):
    """
    Classe de base pour tous les providers.

    Hérite de tous les mixins pour supporter tous les types de missives.
    Les providers concrets héritent de cette classe et implémentent
    uniquement les méthodes send_* dont ils ont besoin.

    Architecture par mixins :
    - BaseProviderCommon : Fonctions communes (config, status, events)
    - BaseEmailMixin : Validation email, spam score, attachments email
    - BaseSMSMixin : Validation phone, calcul segments, formatage
    - BaseWhatsAppMixin : Formatage WhatsApp, attachments média
    - BasePostalMixin : Validation adresse, calcul coût postal
    - BaseNotificationMixin : Formatage notifications, préférences user

    À implémenter dans les sous-classes :
    - supported_types : Liste des MissiveType supportés
    - send_email() / send_sms() / send_whatsapp() / send_postal() / send_notification()
    - handle_webhook() : pour traiter les webhooks
    """

    def send(self) -> bool:
        """
        Envoie la missive en dispatchant vers la bonne méthode selon le type.

        Returns:
            bool: True si succès, False sinon
        """
        if not self.missive:
            return False

        # Vérifier que le provider supporte ce type
        from ...models import MissiveStatus

        if not self.supports(self.missive.missive_type):
            error = (
                f"{self.name} ne supporte pas {self.missive.get_missive_type_display()}"
            )
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        # Dispatcher vers la bonne méthode
        from ...models import MissiveType

        if self.missive.missive_type == MissiveType.EMAIL:
            return self.send_email()
        elif self.missive.missive_type == MissiveType.SMS:
            return self.send_sms()
        elif self.missive.missive_type == MissiveType.WHATSAPP:
            return self.send_whatsapp()
        elif self.missive.missive_type == MissiveType.POSTAL:
            return self.send_postal()
        elif self.missive.missive_type == MissiveType.NOTIFICATION:
            return self.send_notification()

        return False

    # ==================== WEBHOOKS ====================

    def handle_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Tuple[bool, str, Optional[Missive]]:
        """
        Traite un webhook reçu d'un provider.

        À implémenter dans les sous-classes.

        Args:
            payload: Données du webhook (JSON)
            headers: Headers HTTP de la requête

        Returns:
            Tuple de (success, error_message, missive)
            - success (bool): True si traité avec succès
            - error_message (str): Message d'erreur si échec
            - missive (Missive): Missive mise à jour (si trouvée)

        Example:
            success, error, missive = provider.handle_webhook(payload, headers)
            if success:
                print(f"Webhook traité pour missive #{missive.id}")
        """
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode handle_webhook()"
        )

    def validate_webhook_signature(
        self, payload: Any, headers: Dict[str, str]
    ) -> Tuple[bool, str]:
        """
        Valide la signature du webhook pour sécurité.

        À implémenter dans les sous-classes selon leur méthode de signature.

        Args:
            payload: Données brutes du webhook
            headers: Headers HTTP

        Returns:
            Tuple (is_valid, error_message)
        """
        # Par défaut, pas de validation (à override)
        return True, ""

    def extract_missive_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """
        Extrait l'ID de la missive depuis le payload du webhook.

        À implémenter dans les sous-classes.

        Args:
            payload: Données du webhook

        Returns:
            str: external_id de la missive, ou None
        """
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode extract_missive_id()"
        )

    # ==================== VALIDATION GLOBALE ====================

    def check_service_availability(self) -> Dict[str, Any]:
        """
        Vérifie la disponibilité du service du provider.

        Teste :
        - Accessibilité de l'API
        - Temps de réponse
        - Quota disponible
        - Statut du service

        Returns:
            Dict contenant :
            - is_available (bool): Service disponible
            - response_time_ms (int): Temps de réponse
            - quota_remaining (int): Crédits/quota restant
            - status (str): Statut du service
            - last_check (datetime): Date du dernier check
            - warnings (List[str]): Avertissements

        Example:
            result = provider.check_service_availability()
            if result['quota_remaining'] < 100:
                print("Attention, quota presque épuisé!")
        """
        # TODO: Implémenter selon le provider
        # Chaque provider concret devrait override cette méthode
        # pour vérifier son propre service (SendGrid API, Twilio API, etc.)

        return {
            "is_available": None,
            "response_time_ms": 0,
            "quota_remaining": None,
            "status": "unknown",
            "last_check": timezone.now(),
            "warnings": ["Check de disponibilité non implémenté pour ce provider"],
        }

    def calculate_delivery_risk(
        self, missive: Optional[Missive] = None
    ) -> Dict[str, Any]:
        """
        Calcule un score de risque global d'échec de délivrance pour une missive.

        Combine plusieurs facteurs :
        - Validation du destinataire (email/phone)
        - Disponibilité du service
        - Historique d'échecs précédents avec ce destinataire
        - Réputation de l'expéditeur
        - Qualité du contenu (spam score pour emails)

        Args:
            missive: La missive à analyser (utilise self.missive si None)

        Returns:
            Dict contenant :
            - risk_score (int): Score global 0-100 (0=sûr, 100=échec probable)
            - risk_level (str): 'low', 'medium', 'high', 'critical'
            - factors (Dict): Détail des facteurs de risque
            - recommendations (List[str]): Recommandations
            - should_send (bool): Recommandation d'envoi

        Example:
            risk = provider.calculate_delivery_risk(missive)
            if risk['risk_score'] > 70:
                print(f"Risque élevé: {risk['recommendations']}")
        """
        if missive is None:
            missive = self.missive

        if not missive:
            return {
                "risk_score": 100,
                "risk_level": "critical",
                "factors": {},
                "recommendations": ["Aucune missive à analyser"],
                "should_send": False,
            }

        factors = {}
        recommendations = []
        total_risk = 0

        # Validation du destinataire selon le type
        from ...models import MissiveType

        if missive.missive_type == MissiveType.EMAIL:
            email = missive.get_recipient_email()
            if email:
                email_validation = self.validate_email(email)
                factors["email_validation"] = email_validation
                total_risk += email_validation["risk_score"] * 0.6  # 60% du poids
                if email_validation["warnings"]:
                    recommendations.extend(email_validation["warnings"])

        elif missive.missive_type in [MissiveType.SMS, MissiveType.WHATSAPP]:
            phone = missive.get_recipient_phone()
            if phone:
                phone_validation = self.validate_phone_number(phone)
                factors["phone_validation"] = phone_validation
                total_risk += phone_validation["risk_score"] * 0.6
                if phone_validation["warnings"]:
                    recommendations.extend(phone_validation["warnings"])

        # Check service disponibilité
        service_check = self.check_service_availability()
        factors["service_availability"] = service_check
        if not service_check.get("is_available"):
            total_risk += 20
            recommendations.append("Service temporairement indisponible")

        # TODO: Ajouter d'autres facteurs
        # - Historique d'échecs avec ce destinataire
        # - Spam score du contenu
        # - Réputation de l'expéditeur
        # - Heure d'envoi (meilleur taux de délivrance selon l'heure)

        # Normalisation du score
        risk_score = min(int(total_risk), 100)

        # Détermination du niveau
        if risk_score < 25:
            risk_level = "low"
        elif risk_score < 50:
            risk_level = "medium"
        elif risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "critical"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "factors": factors,
            "recommendations": recommendations,
            "should_send": risk_score < 70,  # Seuil configurable
        }


# Export pour compatibilité
__all__ = ["BaseProvider"]

