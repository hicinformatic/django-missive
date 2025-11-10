"""
Mixin pour les fonctionnalités appel vocal des providers.
"""
from typing import Any, Dict, Optional


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
            "warnings": ["Méthode get_voice_call_service_info() non implémentée pour ce provider"],
            "options": [],
            "details": {},
        }

    def send_voice_call(self) -> bool:
        """
        Envoie un appel vocal (message vocal TTS ou appel). À surcharger dans les providers concrets.

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

