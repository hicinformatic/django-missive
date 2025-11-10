"""
Mixin pour les fonctionnalités appel vocal des providers.
"""

from typing import Any, Dict


class BaseVoiceCallMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques aux appels vocaux.
    """

    def get_voice_call_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du compte/service Appel Vocal.

        Retourne les informations importantes pour le service d'appels vocaux :
        - Crédits disponibles (temps ou nombre d'appels)
        - Limites et quotas
        - État du service (actif/inactif)
        - Options disponibles (TTS, enregistrement, etc.)

        Returns:
            Dict contenant :
                - credits: Temps disponible ou nombre d'appels
                - credits_type: 'time' (durée) ou 'count' (nombre) ou 'amount' (montant)
                - is_available: bool, service accessible
                - limits: Dict avec les limites (appels/jour, durée max, etc.)
                - warnings: Liste des alertes
                - options: Liste des options disponibles (TTS, voix, etc.)
                - details: Dict avec infos supplémentaires

        À surcharger dans les providers concrets.
        """
        return {
            "credits": None,
            "credits_type": "time",
            "is_available": None,
            "limits": {},
            "warnings": [
                "Méthode get_voice_call_service_info() non implémentée pour ce provider"
            ],
            "options": [],
            "details": {},
        }

    def check_voice_call_delivery_status(self, **kwargs) -> Dict[str, Any]:
        """
        Vérifie le statut de livraison d'un appel vocal spécifique.

        Utilise l'external_id de la missive pour interroger l'API du provider
        et récupérer le statut actuel.

        Returns:
            Dict contenant :
                - status: Statut actuel ('completed', 'failed', 'no-answer', 'busy', etc.)
                - delivered_at: Date/heure de début de l'appel
                - duration: Durée de l'appel en secondes
                - error_code: Code d'erreur (si échec)
                - error_message: Message d'erreur (si échec)
                - details: Infos supplémentaires du provider

        À surcharger dans les providers concrets.
        """
        return {
            "status": "unknown",
            "delivered_at": None,
            "duration": None,
            "error_code": None,
            "error_message": "Méthode check_voice_call_delivery_status() non implémentée pour ce provider",
            "details": {},
        }

    def send_voice_call(self, **kwargs) -> bool:
        """
        Envoie un appel vocal (message vocal TTS ou appel). À surcharger dans les providers concrets.

        Args:
            **kwargs: Options propriétaires du provider

        Returns:
            bool: True si succès, False sinon
        """
        from ...models import MissiveStatus

        # Vérifier qu'on a un numéro de téléphone
        if not self.missive.get_recipient_phone():
            self._update_status(
                MissiveStatus.FAILED, error_message="Pas de numéro de téléphone"
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_voice_call()"
        )

    def cancel_voice_call(self, **kwargs) -> bool:
        """
        Annule un appel vocal programmé.

        Args:
            **kwargs: Options propriétaires du provider

        Méthode de base qui retourne False. Les providers qui supportent
        l'annulation doivent surcharger cette méthode avec leur implémentation API.

        Returns:
            bool: True si annulation réussie, False sinon
        """
        return False
