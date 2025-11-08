"""
Mixin pour les fonctionnalités WhatsApp des providers.
"""
from typing import Any, Dict


class BaseWhatsAppMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques à WhatsApp.
    """

    def send_whatsapp(self) -> bool:
        """
        Envoie un message WhatsApp. À surcharger dans les providers concrets.

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
            f"{self.name} doit implémenter la méthode send_whatsapp()"
        )

    def validate_whatsapp_number(self, phone: str) -> Dict[str, Any]:
        """
        Vérifie si un numéro de téléphone est enregistré sur WhatsApp.

        Args:
            phone: Numéro de téléphone (format international)

        Returns:
            Dict contenant :
            - is_whatsapp (bool): Numéro enregistré sur WhatsApp
            - is_business (bool): Compte WhatsApp Business
            - warnings (List[str]): Avertissements

        Example:
            result = provider.validate_whatsapp_number("+33612345678")
            if not result['is_whatsapp']:
                print("Ce numéro n'est pas sur WhatsApp!")
        """
        # TODO: Utiliser l'API du provider (Twilio, etc.)
        # pour vérifier si le numéro est sur WhatsApp
        #
        # Twilio Lookup API:
        # https://www.twilio.com/docs/lookup/v2-api

        return {
            "is_whatsapp": None,  # Nécessite API du provider
            "is_business": None,
            "warnings": ["Validation WhatsApp non implémentée"],
        }

    def format_whatsapp_message(self, body: str, body_text: str = None) -> str:
        """
        Formate un message pour WhatsApp.

        WhatsApp supporte un formatage simple :
        - *texte* pour gras
        - _texte_ pour italique
        - ~texte~ pour barré
        - ```texte``` pour monospace

        Args:
            body: Corps du message (peut contenir du HTML)
            body_text: Version texte brut (prioritaire)

        Returns:
            str: Message formaté pour WhatsApp

        Example:
            formatted = provider.format_whatsapp_message(
                "<b>Important</b>: RDV demain",
                "Important: RDV demain"
            )
            # → "*Important*: RDV demain"
        """
        # Utiliser body_text si disponible
        message = body_text if body_text else body

        # TODO: Convertir le HTML basique en formatage WhatsApp
        # message = message.replace('<b>', '*').replace('</b>', '*')
        # message = message.replace('<i>', '_').replace('</i>', '_')
        # message = message.replace('<strong>', '*').replace('</strong>', '*')
        # message = message.replace('<em>', '_').replace('</em>', '_')

        return message

    def add_attachment_whatsapp(self, attachment) -> Dict[str, Any]:
        """
        Prépare une pièce jointe pour WhatsApp.

        WhatsApp supporte :
        - Images (JPEG, PNG) : max 5 MB
        - Documents (PDF, DOC, etc.) : max 100 MB
        - Vidéos (MP4, 3GP) : max 16 MB
        - Audio (MP3, OGG) : max 16 MB

        Args:
            attachment: Instance de MissiveAttachment

        Returns:
            Dict avec les informations de l'attachment formaté
        """
        # Vérifications de type et taille
        max_sizes = {
            "image": 5 * 1024 * 1024,  # 5 MB
            "video": 16 * 1024 * 1024,  # 16 MB
            "audio": 16 * 1024 * 1024,  # 16 MB
            "document": 100 * 1024 * 1024,  # 100 MB
        }

        # Déterminer le type
        mime_type = attachment.mime_type or ""
        if mime_type.startswith("image/"):
            media_type = "image"
        elif mime_type.startswith("video/"):
            media_type = "video"
        elif mime_type.startswith("audio/"):
            media_type = "audio"
        else:
            media_type = "document"

        return {
            "filename": attachment.filename,
            "url": attachment.file_url,
            "mime_type": mime_type,
            "media_type": media_type,
            "size": attachment.file_size,
            "max_size": max_sizes.get(media_type, 100 * 1024 * 1024),
        }

