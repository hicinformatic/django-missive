"""
Mixin pour les fonctionnalités SMS des providers.
"""
import re
from typing import Any, Dict, List


class BaseSMSMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques aux SMS.
    """

    def send_sms(self) -> bool:
        """
        Envoie un SMS. À surcharger dans les providers concrets.

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
            f"{self.name} doit implémenter la méthode send_sms()"
        )

    def validate_phone_number(
        self, phone: str, country_code: str = "FR"
    ) -> Dict[str, Any]:
        """
        Valide un numéro de téléphone et évalue le risque d'échec.

        Vérifie :
        - Format du numéro (international ou national)
        - Validité selon le pays
        - Type de ligne (mobile, fixe, VoIP)
        - Opérateur (si disponible)

        Args:
            phone: Numéro de téléphone (format international recommandé)
            country_code: Code pays ISO (ex: "FR", "US", "BE")

        Returns:
            Dict contenant :
            - is_valid (bool): Numéro valide
            - is_mobile (bool): Numéro mobile (pour SMS)
            - formatted (str): Numéro formaté en international
            - carrier (str): Opérateur détecté
            - line_type (str): Type de ligne (mobile/fixed/voip)
            - risk_score (int): Score de risque 0-100
            - warnings (List[str]): Avertissements

        Example:
            result = provider.validate_phone_number("+33612345678")
            if not result['is_mobile']:
                print("Impossible d'envoyer un SMS sur ce numéro!")
        """
        warnings = []
        details = {}

        # Nettoyage du numéro
        cleaned = re.sub(r"[^\d+]", "", phone)
        details["cleaned"] = cleaned

        # Validation de base
        if not cleaned.startswith("+"):
            warnings.append("Format international recommandé (+33...)")

        # TODO: Utiliser phonenumbers library
        # import phonenumbers
        # try:
        #     parsed = phonenumbers.parse(phone, country_code)
        #     is_valid = phonenumbers.is_valid_number(parsed)
        #     formatted = phonenumbers.format_number(
        #         parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        #     )
        #     number_type = phonenumbers.number_type(parsed)
        #     is_mobile = number_type == phonenumbers.PhoneNumberType.MOBILE
        #
        #     # Carrier lookup (nécessite carrier library)
        #     from phonenumbers import carrier
        #     carrier_name = carrier.name_for_number(parsed, 'fr')
        #
        # except Exception as e:
        #     is_valid = False
        #     warnings.append(str(e))

        risk_score = len(warnings) * 20

        return {
            "is_valid": len(cleaned) >= 10,  # Validation basique
            "is_mobile": None,  # Nécessite phonenumbers
            "formatted": cleaned,
            "carrier": "",
            "line_type": "unknown",
            "risk_score": risk_score,
            "warnings": warnings,
        }

    def calculate_sms_segments(self, message: str) -> Dict[str, Any]:
        """
        Calcule le nombre de segments SMS et le coût estimé.

        Un SMS standard fait 160 caractères (GSM-7) ou 70 (Unicode).
        Les messages plus longs sont divisés en segments.

        Args:
            message: Le message SMS

        Returns:
            Dict contenant :
            - segments (int): Nombre de segments
            - characters (int): Nombre de caractères
            - encoding (str): GSM-7 ou Unicode
            - estimated_cost (float): Coût estimé (selon config)
            - per_segment_limit (int): Limite de caractères par segment

        Example:
            info = provider.calculate_sms_segments("Votre message SMS")
            print(f"Coûtera {info['segments']} segment(s)")
        """
        # Détection de l'encodage
        gsm7_chars = set(
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )

        is_gsm7 = all(c in gsm7_chars for c in message)
        encoding = "GSM-7" if is_gsm7 else "Unicode"

        # Limites par segment
        if is_gsm7:
            single_limit = 160
            multi_limit = 153  # Pour messages multi-segments
        else:
            single_limit = 70
            multi_limit = 67

        # Calcul du nombre de segments
        length = len(message)
        if length == 0:
            segments = 0
        elif length <= single_limit:
            segments = 1
        else:
            segments = (length + multi_limit - 1) // multi_limit

        # Coût estimé (à configurer selon provider)
        cost_per_segment = self.config.get("SMS_COST_PER_SEGMENT", 0.05)
        estimated_cost = segments * cost_per_segment

        return {
            "segments": segments,
            "characters": length,
            "encoding": encoding,
            "estimated_cost": estimated_cost,
            "per_segment_limit": single_limit if segments == 1 else multi_limit,
            "is_multipart": segments > 1,
        }

    def format_phone_international(self, phone: str, country_code: str = "FR") -> str:
        """
        Formate un numéro de téléphone en format international.

        Args:
            phone: Numéro de téléphone
            country_code: Code pays par défaut

        Returns:
            str: Numéro formaté (+33...)

        Example:
            formatted = provider.format_phone_international("0612345678", "FR")
            # → "+33612345678"
        """
        # Nettoyage
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Déjà en format international
        if cleaned.startswith("+"):
            return cleaned

        # TODO: Implémenter avec phonenumbers
        # import phonenumbers
        # parsed = phonenumbers.parse(phone, country_code)
        # return phonenumbers.format_number(
        #     parsed, phonenumbers.PhoneNumberFormat.E164
        # )

        # Conversion simple pour la France
        if country_code == "FR" and cleaned.startswith("0"):
            return "+33" + cleaned[1:]

        return "+" + cleaned

