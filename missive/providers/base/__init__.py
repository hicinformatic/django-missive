"""
Provider de base avec toutes les fonctionnalités (composition de mixins).
"""

from typing import Any, Dict, Optional, Tuple

from django.utils import timezone

from ...models import Missive

# Architecture générique pour les messageries
from .branded import BaseBrandedMixin
from .common import BaseProviderCommon
from .email import BaseEmailMixin
from .monitoring import BaseMonitoringMixin
from .notification import BaseNotificationMixin
from .postal import BasePostalMixin
from .slack import BaseSlackMixin
from .sms import BaseSMSMixin
from .teams import BaseTeamsMixin
from .voice_call import BaseVoiceCallMixin

# Mixins spécifiques (pour compatibilité et implémentations de référence)
from .whatsapp import BaseWhatsAppMixin  # DÉPRÉCIÉ : utiliser BaseBrandedMixin


class BaseProvider(
    BaseProviderCommon,
    BaseEmailMixin,
    BaseSMSMixin,
    BasePostalMixin,
    BaseNotificationMixin,
    BaseVoiceCallMixin,
    BaseMonitoringMixin,
    # Mixin générique pour TOUTES les messageries d'applications
    BaseBrandedMixin,
    # Mixins spécifiques (compatibilité et référence)
    BaseWhatsAppMixin,
    BaseSlackMixin,
    BaseTeamsMixin,
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
    - BasePostalMixin : Validation adresse, calcul coût postal
    - BaseNotificationMixin : Formatage notifications, préférences user
    - BaseVoiceCallMixin : Appels vocaux, TTS, messages vocaux
    - BaseMonitoringMixin : Monitoring, crédits, SLA, health check
    - BaseBrandedMixin : TOUTES les messageries d'applications (WhatsApp, Slack, Teams, Discord, Telegram, etc.)
    - BaseWhatsAppMixin : DÉPRÉCIÉ - utiliser BaseBrandedMixin
    - BaseSlackMixin : Implémentation de référence pour Slack
    - BaseTeamsMixin : Implémentation de référence pour Teams

    Architecture ultra-simplifiée pour messageries :
    Pour le type BRANDED, le nom du provider (self.name) détermine automatiquement
    quelle méthode appeler. Le dispatch se fait vers send_{self.name}().

    Plus besoin de brand_name ! Le provider sait ce qu'il fait via son nom.

    À implémenter dans les sous-classes :
    - name : Nom du provider (ex: "whatsapp", "slack", "telegram")
    - supported_types : Liste des MissiveType supportés
    - send_email() / send_sms() / send_postal() / send_notification() / send_voice_call()
    - send_{name}() pour le type BRANDED (ex: send_whatsapp, send_slack, send_telegram)
    - handle_webhook() : pour traiter les webhooks

    Exemples d'utilisation :
        # Provider WhatsApp
        class WhatsAppProvider(BaseProvider):
            name = "whatsapp"
            supported_types = [MissiveType.BRANDED]

            def send_whatsapp(self):  # ← Appelé automatiquement
                pass

        # Provider Slack
        class SlackProvider(BaseProvider):
            name = "slack"
            supported_types = [MissiveType.BRANDED]

            def send_slack(self):  # ← Appelé automatiquement
                context = self._get_organization_context()
                workspace_id = context.get('workspace_id')
                # ...
                pass

        # Utilisation
        missive = Missive.objects.create(
            missive_type=MissiveType.BRANDED,
            recipient=recipient,
            body='Message',
            metadata={'workspace_id': 'T123456'}  # ← Si contexte nécessaire
        )
    """

    def send(self) -> bool:
        """
        Envoie la missive en dispatchant vers la bonne méthode selon le type.

        Pour le type BRANDED, utilise self.name du provider pour dispatcher
        automatiquement vers send_{self.name}().

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
        elif self.missive.missive_type == MissiveType.POSTAL:
            return self.send_postal()
        elif self.missive.missive_type == MissiveType.NOTIFICATION:
            return self.send_notification()
        elif self.missive.missive_type == MissiveType.VOICE_CALL:
            return self.send_voice_call()
        elif self.missive.missive_type == MissiveType.BRANDED:
            # Dispatch automatique via self.name
            return self.send_branded()

        return False

    def cancel(self) -> bool:
        """
        Annule l'envoi de la missive en dispatchant vers la bonne méthode selon le type.

        Pour le type BRANDED, utilise self.name du provider pour dispatcher
        automatiquement vers cancel_{self.name}().

        Returns:
            bool: True si l'annulation a réussi, False sinon

        Example:
            provider = TwilioProvider(missive=my_missive)
            if provider.cancel():
                print("Missive annulée avec succès")
        """
        if not self.missive:
            return False

        # Vérifier que la missive a un external_id (déjà envoyée au provider)
        if not self.missive.external_id:
            return False

        # Dispatcher vers la bonne méthode
        from ...models import MissiveType

        if self.missive.missive_type == MissiveType.EMAIL:
            return self.cancel_email()
        elif self.missive.missive_type == MissiveType.SMS:
            return self.cancel_sms()
        elif self.missive.missive_type == MissiveType.POSTAL:
            return self.cancel_postal()
        elif self.missive.missive_type == MissiveType.NOTIFICATION:
            return self.cancel_notification()
        elif self.missive.missive_type == MissiveType.VOICE_CALL:
            return self.cancel_voice_call()
        elif self.missive.missive_type == MissiveType.BRANDED:
            # Méthode générique pour toutes les messageries de marque
            return self.cancel_branded()

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

        elif missive.missive_type in [MissiveType.SMS, MissiveType.BRANDED]:
            # SMS ou messagerie de marque (WhatsApp, Telegram, etc.) nécessitent un téléphone
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
