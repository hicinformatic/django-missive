"""
Provider SMSPartner pour SMS (provider français).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests

from ..models import MissiveStatus
from .base import BaseProvider


class SMSPartnerProvider(BaseProvider):
    """
    Provider pour SMSPartner / VoicePartner / MailPartner.

    Supporte :
    - SMS (classique, low-cost, premium)
    - Messages vocaux (TTS)
    - Email transactionnel
    """

    # Métadonnées du provider
    name = "SMS Partner"
    display_name = "SMS Partner (SMS/Email/Vocal)"
    supported_types = ["SMS", "EMAIL", "VOICE_CALL"]
    services = [
        "sms",
        "sms_low_cost",
        "sms_premium",
        "voice_message",
        "voice_call",
        "email",
    ]
    config_keys = [
        "SMSPARTNER_API_KEY",
        "SMSPARTNER_SENDER",
        "SMSPARTNER_WEBHOOK_IPS",
    ]
    required_packages = ["requests"]
    site_url = "https://www.smspartner.fr/"
    status_url = "https://status.smspartner.fr/status/nda-media"
    documentation_url = "https://www.docpartner.dev/"
    description_text = (
        "Solution française multi-services (SMS, Email, Voice) avec API complète"
    )

    # URLs des APIs
    API_BASE_SMS = "https://api.smspartner.fr/v1"
    API_BASE_VOICE = "http://api.voicepartner.fr/v1"
    API_BASE_EMAIL = "http://api.mailpartner.fr/v1"

    # Plage IP officielle pour les webhooks SMSPartner
    WEBHOOK_IP_RANGE = "185.66.232.0/24"

    # Mappings d'erreurs communes (codes d'erreur → messages)
    ERROR_CODES = {
        1: "Clé API requise",
        2: "Numéro de téléphone requis",
        3: "ID du message requis",
        4: "Message introuvable",
        5: "L'envoi a déjà été annulé",
        6: "Impossible d'annuler moins de 5 minutes avant l'envoi",
        7: "Impossible d'annuler un message déjà envoyé",
        9: "Contraintes non respectées",
        10: "Clé API incorrecte",
        11: "Manque de crédits",
    }

    # Mappings de statuts (statuts provider → statuts standardisés)
    STATUS_MAPPING_SMS = {
        "Delivered": "delivered",
        "Not delivered": "failed",
        "Waiting": "pending",
    }

    STATUS_MAPPING_EMAIL = {
        "Delivered": "delivered",
        "Bounced": "bounced",
        "Opened": "opened",
        "Clicked": "clicked",
        "Failed": "failed",
        "Pending": "pending",
    }

    # Limites et seuils
    WARNING_THRESHOLD_SMS = 500  # Avertissement si < 500 SMS
    CRITICAL_THRESHOLD_SMS = 100  # Critique si < 100 SMS
    WARNING_THRESHOLD_BALANCE = 10.0  # Avertissement si < 10€
    MAX_EMAIL_ATTACHMENTS = 3  # Max 3 pièces jointes
    MAX_EMAIL_VARIABLES = 8  # Max 8 variables de template

    # ===========================================================================
    # HELPERS INTERNES
    # ===========================================================================

    def _get_api_key(self) -> Optional[str]:
        """Récupère la clé API depuis la config."""
        return self.config.get("SMSPARTNER_API_KEY")

    def _handle_api_response(
        self, response, service_name: str, credits_type: str
    ) -> Optional[dict]:
        """
        Helper pour gérer les réponses d'API de manière uniforme.

        Args:
            response: Response de l'API
            service_name: Nom du service (SMS, Voice, etc.)
            credits_type: Type de crédits (count, money, mixed)

        Returns:
            Dict avec erreur si problème, None si OK
        """
        if response.status_code == 429:
            return self._build_error_response(
                "⚠️ Rate limit dépassé - Trop d'appels API. Réessayez dans quelques minutes.",
                credits_type,
            )
        elif response.status_code != 200:
            return self._build_error_response(
                f"Erreur HTTP {response.status_code}", credits_type
            )
        return None

    def _build_error_response(
        self, error_msg: str, credits_type: str = "count"
    ) -> dict:
        """Helper pour construire une réponse d'erreur standardisée pour service info."""
        return {
            "credits": None,
            "credits_type": credits_type,
            "is_available": None if "Timeout" in error_msg else False,
            "limits": {},
            "warnings": [error_msg],
            "details": {},
        }

    def _build_delivery_status_error(
        self,
        error_msg: str,
        error_code: Optional[int] = None,
        include_email_fields: bool = False,
    ) -> dict:
        """Helper pour construire une réponse d'erreur standardisée pour delivery status."""
        base_error = {
            "status": "unknown",
            "delivered_at": None,
            "error_code": error_code,
            "error_message": error_msg,
            "details": {},
        }

        # Ajouter les champs spécifiques email si nécessaire
        if include_email_fields:
            base_error.update(
                {
                    "opened_at": None,
                    "clicked_at": None,
                    "opens_count": 0,
                    "clicks_count": 0,
                    "bounce_type": None,
                }
            )

        return base_error

    def _get_error_message(self, code: int, default_message: str = "") -> str:
        """Récupère le message d'erreur depuis ERROR_CODES ou retourne un message par défaut."""
        return self.ERROR_CODES.get(code, default_message or f"Erreur {code}")

    def _format_sms_errors(self, result: dict) -> str:
        """Formate les erreurs d'envoi SMS depuis la réponse API."""
        errors = result.get("errors", [])
        if errors:
            return "; ".join([err.get("message", "") for err in errors])

        code = result.get("code")
        return self._get_error_message(code)

    def _convert_timestamp_to_iso(self, timestamp: Any) -> Optional[str]:
        """Convertit un timestamp Unix en format ISO."""
        if not timestamp:
            return None
        try:
            return datetime.fromtimestamp(int(timestamp)).isoformat()
        except (ValueError, TypeError):
            return str(timestamp)

    # ===========================================================================
    # MÉTHODES D'ENVOI (SMS, EMAIL, VOICE)
    # ===========================================================================

    def send_sms(self, **kwargs) -> bool:
        """
        Envoie un SMS via SMSPartner API.

        Args:
            **kwargs: Options standardisées Django (voir BaseSMSMixin pour la liste complète)
                KWARGS STANDARDISÉS (recommandés):
                    sender (str): Nom d'émetteur
                    tag (str): Tag de tracking
                    scheduled_delivery_date (str): Date d'envoi différé (dd/mm/YYYY)
                    scheduled_time (int): Heure d'envoi (0-23)
                    scheduled_minute (int): Minute d'envoi (0-55)
                    webhook_url (str): URL de callback (sera utilisée pour DLR et réponses)
                    is_commercial (bool): True pour SMS commercial (ajoute STOP)
                    is_unicode (bool): True pour activer Unicode
                    sandbox (bool): True pour mode test
                    priority (str): 'low', 'normal', 'high' → gamme 2, 1, 3

                Note: webhook_url sera automatiquement utilisé pour webhookUrl, urlDlr et urlResponse.

                OPTIONS PROPRIÉTAIRES (compatibilité directe):
                    _format (str): 'json' ou 'xml'

        Returns:
            bool: True si succès, False sinon

        Example:
            # Avec kwargs standardisés (recommandé)
            provider.send_sms(
                sender="MonApp",
                scheduled_delivery_date="25/12/2025",
                scheduled_time=14,
                scheduled_minute=30,
                is_commercial=True,
                priority="high"
            )
        """
        import requests

        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            api_key = self._get_api_key()
            sender = self.config.get("SMSPARTNER_SENDER", "Missive")

            if not api_key:
                self._update_status(
                    MissiveStatus.FAILED,
                    error_message="SMSPARTNER_API_KEY non configurée",
                )
                return False

            # Préparer le payload avec valeurs par défaut
            payload = {
                "apiKey": api_key,
                "phoneNumbers": self.missive.recipient_phone,
                "message": self.missive.body_text or self.missive.body,
                "sender": kwargs.get("sender", sender),
                "gamme": 1,  # Par défaut: standard
            }

            # Ajouter le tag pour tracking
            if "tag" in kwargs:
                payload["tag"] = kwargs["tag"]
            elif self.missive.id:
                payload["tag"] = f"missive_{self.missive.id}"

            # Ajouter webhook si configuré (même URL pour tous les types)
            webhook_url = kwargs.get("webhook_url") or self.config.get(
                "SMSPARTNER_WEBHOOK_URL"
            )
            if webhook_url:
                # Utiliser la même URL pour tous les webhooks
                payload["webhookUrl"] = webhook_url
                payload["urlDlr"] = webhook_url  # Delivery Reports
                payload["urlResponse"] = webhook_url  # Réponses SMS

            # Mapping des kwargs standardisés Django → API SMSPartner
            kwargs_mapping = {
                # Envoi différé
                "scheduled_delivery_date": "scheduledDeliveryDate",  # dd/mm/YYYY
                "scheduled_time": "time",  # 0-24
                "scheduled_minute": "minute",  # 0-55 (intervalle 5min)
                # Options SMS
                "is_commercial": "isStopSms",  # 1 pour ajouter STOP
                "is_unicode": "isUnicode",  # 1 pour Unicode (70 car.)
                "sandbox": "sandbox",  # 1 pour mode test
                "priority": "gamme",  # Mapping priority → gamme
            }

            # Appliquer le mapping
            for django_key, api_key in kwargs_mapping.items():
                if django_key in kwargs:
                    value = kwargs[django_key]
                    # Conversions spéciales
                    if django_key == "priority":
                        # Convertir priority en gamme SMSPartner
                        priority_map = {"low": 2, "normal": 1, "high": 3}
                        payload[api_key] = priority_map.get(value, 1)
                    elif django_key in ["is_commercial", "is_unicode", "sandbox"]:
                        # Convertir bool → 1/0
                        payload[api_key] = 1 if value else 0
                    else:
                        payload[api_key] = value

            # Permettre aussi les noms directs de l'API SMSPartner (pour compatibilité)
            direct_api_options = ["_format"]  # Options qui gardent leur nom
            for option in direct_api_options:
                if option in kwargs:
                    payload[option] = kwargs[option]

            # Envoyer via l'API SMSPartner
            response = requests.post(
                "https://api.smspartner.fr/v1/send",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "cache-control": "no-cache",
                },
                timeout=10,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                # Récupérer les informations de la réponse
                message_id = result.get("message_id")
                nb_sms = result.get("nb_sms", 1)
                cost = result.get("cost", 0)
                currency = result.get("currency", "EUR")

                self._update_status(
                    MissiveStatus.SENT,
                    provider=self.name,
                    external_id=str(message_id),
                )
                self._create_event(
                    "sent",
                    f"SMS envoyé via SMSPartner ({nb_sms} segment(s), {cost}{currency})",
                )

                return True
            else:
                # Gérer les erreurs
                error_msg = self._format_sms_errors(result)
                self._update_status(MissiveStatus.FAILED, error_message=error_msg)
                self._create_event("failed", error_msg)
                return False

        except requests.exceptions.Timeout:
            error_msg = "Timeout lors de l'envoi vers l'API SMSPartner"
            self._update_status(MissiveStatus.FAILED, error_message=error_msg)
            self._create_event("failed", error_msg)
            return False
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    # ===========================================================================
    # MÉTHODES D'ANNULATION
    # ===========================================================================

    def cancel_sms(self) -> bool:
        """
        Annule l'envoi d'un SMS programmé via l'API SMSPartner.

        Utilise l'API DELETE /v1/message-cancel/{message_id}

        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        if not self.missive.external_id:
            return False

        try:
            api_key = self._get_api_key()
            if not api_key:
                return False

            message_id = self.missive.external_id

            # Annuler via l'API SMSPartner
            response = requests.delete(
                f"{self.API_BASE_SMS}/message-cancel/{message_id}?apiKey={api_key}",
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                self._create_event("cancelled", "SMS annulé via SMSPartner")
                return True
            else:
                return False

        except Exception:
            return False

    def send_email(self, **kwargs) -> bool:
        """
        Envoie un email via Mail Partner API (SMSPartner).

        Kwargs standardisés :
            cc (list|str): Destinataires en copie (non supporté par Mail Partner)
            bcc (list|str): Destinataires en copie cachée (non supporté)
            reply_to (str): Adresse de réponse
            headers (dict): Headers personnalisés (non supporté)
            tags (list|dict): Tags pour tracking
            template_vars (dict): Variables du template (max 8)
            track_opens (bool): Tracking des ouvertures (automatique)
            track_clicks (bool): Tracking des clics (automatique)
            send_at (datetime|str): Date/heure d'envoi programmé
            scheduled_delivery_date (str): Date d'envoi (dd/mm/YYYY)
            scheduled_time (int): Heure d'envoi (0-24)
            scheduled_minute (int): Minute d'envoi (0-55, par intervalle de 5)
            sandbox (bool): Mode test
            attachments (list): Liste de pièces jointes (max 3, 5Mo chacune)

        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        import requests

        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        email = self.missive.recipient_email
        if not email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            api_key = self._get_api_key()
            if not api_key:
                self._update_status(
                    MissiveStatus.FAILED,
                    error_message="SMSPARTNER_API_KEY non configurée",
                )
                return False

            # Récupérer les options depuis provider_options et kwargs
            options = self.missive.provider_options or {}
            options.update(kwargs)  # Les kwargs explicites ont la priorité

            # Préparer le payload
            payload = {
                "apiKey": api_key,
                "subject": self.missive.subject,
                "htmlContent": self.missive.body,
                "from": {
                    "email": self.config.get(
                        "DEFAULT_FROM_EMAIL", "noreply@example.com"
                    ),
                    "name": self.config.get("DEFAULT_FROM_NAME", ""),
                },
                "to": [{"email": email}],
            }

            # Ajouter le nom du destinataire si disponible
            if self.missive.recipient and hasattr(self.missive.recipient, "full_name"):
                payload["to"][0]["name"] = self.missive.recipient.full_name

            # Options optionnelles
            if options.get("reply_to"):
                reply_to = options["reply_to"]
                if isinstance(reply_to, str):
                    payload["replyTo"] = {"email": reply_to}
                elif isinstance(reply_to, dict):
                    payload["replyTo"] = reply_to

            # Variables de template (max MAX_EMAIL_VARIABLES)
            if options.get("template_vars") or options.get("variables"):
                variables = options.get("template_vars") or options.get("variables")
                if (
                    isinstance(variables, dict)
                    and len(variables) <= self.MAX_EMAIL_VARIABLES
                ):
                    payload["variables"] = variables

            # Tags
            if options.get("tags") or options.get("tag"):
                tag = options.get("tags") or options.get("tag")
                if isinstance(tag, str):
                    payload["tag"] = tag[:20].lower().replace(" ", "")

            # Pièces jointes (max MAX_EMAIL_ATTACHMENTS, 5Mo chacune)
            if options.get("attachments"):
                attachments = options["attachments"]
                if (
                    isinstance(attachments, list)
                    and len(attachments) <= self.MAX_EMAIL_ATTACHMENTS
                ):
                    payload["attachments"] = [
                        {
                            "base64Content": att.get("base64Content"),
                            "contentType": att.get(
                                "contentType", "application/octet-stream"
                            ),
                            "filename": att.get("filename", "file"),
                        }
                        for att in attachments[:3]
                    ]

            # Envoi programmé
            if options.get("scheduled_delivery_date"):
                payload["scheduledDeliveryDate"] = options["scheduled_delivery_date"]
                payload["time"] = options.get("scheduled_time", options.get("time", 12))
                payload["minute"] = options.get(
                    "scheduled_minute", options.get("minute", 0)
                )

            # Mode sandbox
            if options.get("sandbox"):
                payload["sandbox"] = 1

            # Envoyer l'email
            response = requests.post(
                f"{self.API_BASE_EMAIL}/send",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                timeout=10,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                message_id = result.get("messageId")
                cost = result.get("cost", 0)
                currency = result.get("currency", "EUR")
                nb_mail = result.get("nbMail", 1)
                scheduled_date = result.get("scheduledDeliveryDate", "")

                self._update_status(
                    MissiveStatus.SENT,
                    provider=self.name,
                    external_id=str(message_id),
                )

                event_msg = f"Email envoyé via Mail Partner ({nb_mail} email(s), {cost}{currency})"
                if scheduled_date:
                    event_msg += f" - Programmé pour {scheduled_date}"

                self._create_event("sent", event_msg)

                return True
            else:
                # Gérer les erreurs
                code = result.get("code")
                message = result.get("message", "")
                errors = result.get("errors", [])

                if errors:
                    error_messages = [err.get("message", "") for err in errors]
                    error_msg = "; ".join(error_messages)
                elif message:
                    error_msg = message
                else:
                    error_msg = self._get_error_message(code)

                self._update_status(MissiveStatus.FAILED, error_message=error_msg)
                self._create_event("failed", error_msg)
                return False

        except requests.exceptions.Timeout:
            error_msg = "Timeout lors de l'envoi vers l'API Mail Partner"
            self._update_status(MissiveStatus.FAILED, error_message=error_msg)
            self._create_event("failed", error_msg)
            return False
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def cancel_email(self, **kwargs) -> bool:
        """
        Annule l'envoi d'un email programmé via Mail Partner API.

        Attention : Il n'est pas possible d'annuler l'envoi d'un mail moins de
        5 minutes avant son envoi.

        Utilise l'API GET /v1/message-cancel

        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        if not self.missive.external_id:
            return False

        try:
            api_key = self._get_api_key()
            if not api_key:
                return False

            message_id = self.missive.external_id

            # Annuler via l'API Mail Partner
            response = requests.get(
                f"{self.API_BASE_EMAIL}/message-cancel?apiKey={api_key}&messageId={message_id}",
                timeout=5,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                message = result.get("message", "Email annulé")
                self._create_event(
                    "cancelled", f"Email annulé via Mail Partner: {message}"
                )
                return True
            else:
                # Codes d'erreur spécifiques
                code = result.get("code")
                error_map = {
                    1: "Clé API requise",
                    3: "ID du message requis",
                    4: "Message introuvable",
                    5: "L'envoi a déjà été annulé",
                    6: "Impossible d'annuler moins de 5 minutes avant l'envoi",
                    7: "Impossible d'annuler un mail déjà envoyé",
                    10: "Clé API incorrecte",
                }
                error_msg = error_map.get(
                    code, result.get("message", "Erreur d'annulation")
                )
                self._create_event("cancel_failed", f"Échec annulation: {error_msg}")
                return False

        except Exception:
            return False

    def send_voice_call(self, **kwargs) -> bool:
        """
        Envoie un message vocal via Voice Partner API (TTS - Text to Speech).

        Kwargs standardisés :
            lang (str): Langue du message ('fr', 'en', etc.)
            speech_rate (float): Vitesse de lecture (0.5 à 2.0)
            notify_url (str): URL de callback pour le statut
            scheduled_date (str): Date d'envoi différé (YYYY-mm-dd H:i:00)
            token_audio (str): ID de fichier audio (alternative à text)

        Returns:
            bool: True si l'envoi a réussi, False sinon
        """
        import requests

        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        phone = self.missive.recipient_phone
        if not phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            api_key = self._get_api_key()
            if not api_key:
                self._update_status(
                    MissiveStatus.FAILED,
                    error_message="SMSPARTNER_API_KEY non configurée",
                )
                return False

            # Récupérer les options depuis provider_options et kwargs
            options = self.missive.provider_options or {}
            options.update(kwargs)  # Les kwargs explicites ont la priorité

            # Préparer le payload
            payload = {
                "apiKey": api_key,
                "phoneNumbers": phone,
                "lang": options.get("lang", "fr"),  # Langue par défaut : français
            }

            # Texte ou audio
            if options.get("token_audio"):
                payload["tokenAudio"] = options["token_audio"]
            else:
                # Utiliser body_text ou body pour le TTS
                text = self.missive.body_text or self.missive.body
                payload["text"] = text

            # Options optionnelles
            if options.get("speech_rate"):
                payload["speechRate"] = options["speech_rate"]
            if options.get("notify_url") or options.get("webhook_url"):
                payload["notifyUrl"] = options.get("notify_url") or options.get(
                    "webhook_url"
                )
            if options.get("scheduled_date") or options.get("scheduled_delivery_date"):
                payload["scheduledDate"] = options.get("scheduled_date") or options.get(
                    "scheduled_delivery_date"
                )

            # Envoyer le message vocal
            response = requests.post(
                f"{self.API_BASE_VOICE}/tts/send",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                },
                timeout=10,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                campaign_id = result.get("campaignId")
                cost = result.get("cost", 0)
                currency = result.get("currency", "EUR")
                duration = result.get("duration", 0)
                nb_sms = result.get("nbSms", 1)

                self._update_status(
                    MissiveStatus.SENT,
                    provider=self.name,
                    external_id=str(campaign_id),
                )
                self._create_event(
                    "sent",
                    f"Message vocal envoyé via Voice Partner ({duration}s, {nb_sms} segment(s), {cost}{currency})",
                )

                return True
            else:
                # Gérer les erreurs (même format que SMS)
                error_msg = self._format_sms_errors(result)

                self._update_status(MissiveStatus.FAILED, error_message=error_msg)
                self._create_event("failed", error_msg)
                return False

        except requests.exceptions.Timeout:
            error_msg = "Timeout lors de l'envoi vers l'API Voice Partner"
            self._update_status(MissiveStatus.FAILED, error_message=error_msg)
            self._create_event("failed", error_msg)
            return False
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def cancel_voice_call(self, **kwargs) -> bool:
        """
        Annule l'envoi d'un message vocal programmé via Voice Partner API.

        Utilise l'API DELETE /v1/campaign/cancel/{apiKey}/{campaignId}

        Returns:
            bool: True si l'annulation a réussi, False sinon
        """
        if not self.missive.external_id:
            return False

        try:
            api_key = self._get_api_key()
            if not api_key:
                return False

            campaign_id = self.missive.external_id

            # Annuler via l'API Voice Partner
            response = requests.delete(
                f"{self.API_BASE_VOICE}/campaign/cancel/{api_key}/{campaign_id}",
                headers={"Cache-Control": "no-cache"},
                timeout=5,
            )

            result = response.json()

            # Vérifier le succès
            if result.get("success") is True:
                assigned_credit = result.get("assignedCredit", 0)
                self._create_event(
                    "cancelled",
                    f"Message vocal annulé via Voice Partner (crédit remboursé: {assigned_credit} EUR)",
                )
                return True
            else:
                return False

        except Exception:
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """
        Valide les webhooks SMSPartner.

        SMSPartner n'utilise pas de signature cryptographique pour les webhooks.
        La validation se fait via :

        1. Whitelist d'IPs (CIDR range par défaut: 185.66.232.0/24)
        2. Vérification que le messageId existe dans notre DB

        Configuration:
            SMSPARTNER_WEBHOOK_IPS: IPs autorisées (séparées par virgules)
                                   ou CIDR range (ex: "185.66.232.0/24")
                                   Par défaut: utilise WEBHOOK_IP_RANGE (185.66.232.0/24)

        Args:
            payload: Données du webhook
            headers: Headers HTTP

        Returns:
            Tuple (is_valid, error_message)
        """
        from ipaddress import ip_address, ip_network

        # Récupérer l'IP du client
        client_ip_str = None
        if "HTTP_X_FORWARDED_FOR" in headers:
            client_ip_str = headers["HTTP_X_FORWARDED_FOR"].split(",")[0].strip()
        elif "REMOTE_ADDR" in headers:
            client_ip_str = headers["REMOTE_ADDR"]

        if not client_ip_str:
            return False, "Impossible de déterminer l'IP du client"

        # Vérification par IP (utilise WEBHOOK_IP_RANGE par défaut)
        allowed_range = self.config.get("SMSPARTNER_WEBHOOK_IPS", self.WEBHOOK_IP_RANGE)

        if allowed_range:
            try:
                client_ip = ip_address(client_ip_str)

                # Vérifier si c'est un CIDR range ou une liste d'IPs
                if "/" in allowed_range:
                    # C'est un CIDR range
                    if client_ip not in ip_network(allowed_range, strict=False):
                        return (
                            False,
                            f"IP non autorisée: {client_ip_str} (plage autorisée: {allowed_range})",
                        )
                else:
                    # C'est une liste d'IPs séparées par des virgules
                    allowed_ips = [ip.strip() for ip in allowed_range.split(",")]
                    if client_ip_str not in allowed_ips:
                        return False, f"IP non autorisée: {client_ip_str}"
            except ValueError as e:
                return False, f"Erreur validation IP: {e}"

        # Vérification que le messageId existe (si fourni)
        message_id = payload.get("messageId") or payload.get("message_id")
        if message_id:
            # Vérifier que ce message existe dans notre DB
            from ...models import Missive

            exists = Missive.objects.filter(external_id=str(message_id)).exists()
            if not exists:
                return False, f"Message ID inconnu: {message_id}"

        # Par défaut, accepter le webhook
        # Note: SMSPartner ne fournit pas de signature HMAC dans leur API standard
        return True, ""

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis SMSPartner webhook"""
        return payload.get("messageId") or payload.get("tag", "").replace(
            "missive_", ""
        )

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement SMSPartner"""
        return payload.get("status", "unknown")

    # ===========================================================================
    # MÉTHODES DE VÉRIFICATION DE STATUT
    # ===========================================================================

    def check_sms_delivery_status(self, **kwargs) -> dict:
        """
        Vérifie le statut de livraison d'un SMS spécifique via SMSPartner API.

        Utilise l'API GET /v1/message-status

        Returns:
            Dict contenant :
                - status: 'delivered', 'failed', 'pending', 'sent'
                - delivered_at: Date/heure de livraison
                - error_code: Code d'erreur (si échec)
                - error_message: Message d'erreur (si échec)
                - details: Infos supplémentaires (coût, pays, etc.)
        """
        if not self.missive.external_id:
            return self._build_delivery_status_error("Aucun external_id disponible")

        phone = self.missive.recipient_phone
        if not phone:
            return self._build_delivery_status_error("Numéro de téléphone manquant")

        try:
            api_key = self._get_api_key()
            if not api_key:
                return self._build_delivery_status_error(
                    "SMSPARTNER_API_KEY non configurée"
                )

            message_id = self.missive.external_id

            # Récupérer le statut via SMSPartner API
            url = (
                f"{self.API_BASE_SMS}/message-status"
                f"?apiKey={api_key}&phoneNumber={phone}&messageId={message_id}"
            )
            response = requests.get(url, timeout=5)

            result = response.json()

            if result.get("success") is True:
                # Mapper le statut SMSPartner vers statut standard
                smspartner_status = result.get("statut", "Unknown")
                status = self.STATUS_MAPPING_SMS.get(smspartner_status, "unknown")

                # Date de livraison
                delivered_at = result.get("date")

                return {
                    "status": status,
                    "delivered_at": delivered_at,
                    "error_code": None,
                    "error_message": None,
                    "details": {
                        "original_status": smspartner_status,
                        "cost": result.get("cost"),
                        "currency": result.get("currency", "EUR"),
                        "country_code": result.get("countryCode"),
                        "stop_sms": result.get("stopSms", False),
                        "number": result.get("number"),
                    },
                }
            else:
                # Gérer les erreurs
                code = result.get("code")
                message = result.get("message", "")
                error_msg = self._get_error_message(code, message)

                return {
                    "status": "unknown",
                    "delivered_at": None,
                    "error_code": code,
                    "error_message": error_msg,
                    "details": result,
                }

        except Exception as e:
            return {
                "status": "unknown",
                "delivered_at": None,
                "error_code": None,
                "error_message": str(e),
                "details": {},
            }

    def get_sms_service_info(self) -> dict:
        """
        Récupère les informations du service SMS de SMSPartner.

        Utilise l'API SMSPartner pour récupérer le solde et les crédits SMS.

        Returns:
            Dict avec les crédits SMS, limites, et informations du compte
        """
        import requests

        try:
            api_key = self._get_api_key()
            if not api_key:
                return self._build_error_response("SMSPARTNER_API_KEY non configurée")

            # Récupérer le solde via SMSPartner API
            url = f"{self.API_BASE_SMS}/me?apiKey={api_key}"
            response = requests.get(url, timeout=5)

            # Gérer les erreurs HTTP avec le helper
            error_response = self._handle_api_response(response, "SMS", "count")
            if error_response:
                return error_response

            r_json = response.json()

            if r_json.get("success") is True:
                # Récupérer les crédits depuis la réponse
                credits_data = r_json.get("credits", {})
                credit_sms = int(credits_data.get("creditSms", 0))
                credit_sms_eco = int(credits_data.get("creditSmsECO", 0))
                solde_eur = float(credits_data.get("solde", 0))

                # Total de SMS disponibles
                total_sms = credit_sms + credit_sms_eco

                # Avertissements selon le solde
                warnings = []
                if total_sms < self.CRITICAL_THRESHOLD_SMS:
                    warnings.append(
                        f"⚠️ Crédits SMS critiques: {total_sms} SMS restants"
                    )
                elif total_sms < self.WARNING_THRESHOLD_SMS:
                    warnings.append(f"⚠️ Crédits SMS faibles: {total_sms} SMS restants")

                if solde_eur < self.WARNING_THRESHOLD_BALANCE:
                    warnings.append(f"⚠️ Solde critique: {solde_eur:.2f}€")

                return {
                    "credits": f"{total_sms} SMS (Classique: {credit_sms}, ECO: {credit_sms_eco})",
                    "credits_type": "count",
                    "is_available": total_sms > 0,
                    "limits": {
                        "per_second": 5,
                        "per_minute": 300,
                    },
                    "warnings": warnings,
                    "details": {
                        "credit_sms_classique": credit_sms,
                        "credit_sms_eco": credit_sms_eco,
                        "credit_hlr": int(credits_data.get("creditHlr", 0)),
                        "solde_eur": solde_eur,
                        "currency": credits_data.get("currency", "EUR"),
                        "to_send": int(credits_data.get("toSend", 0)),
                        "sender": self.config.get("SMSPARTNER_SENDER", "Non défini"),
                        "user_info": r_json.get("user", {}),
                    },
                }
            else:
                # Erreur de l'API
                code = r_json.get("code", "unknown")
                return self._build_error_response(f"Erreur API (code {code})")

        except requests.exceptions.Timeout:
            return self._build_error_response(
                "Timeout lors de la connexion à l'API SMSPartner"
            )
        except Exception as e:
            return self._build_error_response(f"Erreur: {str(e)}")

    def check_email_delivery_status(self, **kwargs) -> dict:
        """
        Vérifie le statut de livraison d'un email spécifique via Mail Partner API.

        Utilise l'API GET /v1/bulk-status

        Returns:
            Dict contenant :
                - status: 'delivered', 'bounced', 'opened', 'clicked', 'failed'
                - delivered_at: Date/heure de livraison (timestamp)
                - opened_at: Non supporté par Mail Partner
                - clicked_at: Non supporté par Mail Partner
                - opens_count: Non supporté
                - clicks_count: Non supporté
                - bounce_type: Non supporté
                - error_code: Code d'erreur (si échec)
                - error_message: Message d'erreur (si échec)
                - details: Infos supplémentaires (coût, stop_mail, etc.)
        """
        if not self.missive.external_id:
            return self._build_delivery_status_error(
                "Aucun external_id disponible", include_email_fields=True
            )

        email = self.missive.recipient_email
        if not email:
            return self._build_delivery_status_error(
                "Email destinataire manquant", include_email_fields=True
            )

        try:
            api_key = self._get_api_key()
            if not api_key:
                return self._build_delivery_status_error(
                    "SMSPARTNER_API_KEY non configurée", include_email_fields=True
                )

            message_id = self.missive.external_id

            # Récupérer le statut via Mail Partner API
            url = f"{self.API_BASE_EMAIL}/bulk-status?apiKey={api_key}&messageId={message_id}"
            response = requests.get(url, timeout=5)

            result = response.json()

            if result.get("success") is True:
                # Récupérer la liste des statuts
                status_list = result.get("StatutResponseList", [])

                # Trouver le statut pour cet email spécifique
                recipient_status = next(
                    (item for item in status_list if item.get("email") == email), None
                )

                if not recipient_status:
                    error_response = self._build_delivery_status_error(
                        f"Email {email} non trouvé dans les résultats",
                        include_email_fields=True,
                    )
                    error_response["details"] = {"status_list": status_list}
                    return error_response

                # Mapper le statut Mail Partner vers statut standard
                mailpartner_status = recipient_status.get("status", "Unknown")
                status = self.STATUS_MAPPING_EMAIL.get(mailpartner_status, "unknown")

                # Date de livraison (timestamp Unix → ISO)
                delivered_at = self._convert_timestamp_to_iso(
                    recipient_status.get("date")
                )

                return {
                    "status": status,
                    "delivered_at": delivered_at,
                    "opened_at": None,  # Non supporté par Mail Partner
                    "clicked_at": None,  # Non supporté par Mail Partner
                    "opens_count": 0,  # Non supporté
                    "clicks_count": 0,  # Non supporté
                    "bounce_type": None,  # Non supporté
                    "error_code": None,
                    "error_message": None,
                    "details": {
                        "original_status": mailpartner_status,
                        "cost": recipient_status.get("cost"),
                        "stop_mail": recipient_status.get("stopMail", False),
                        "token": recipient_status.get("token"),
                        "email": recipient_status.get("email"),
                    },
                }
            else:
                # Gérer les erreurs
                code = result.get("code")
                message = result.get("message", "")
                error_msg = self._get_error_message(code, message)

                return {
                    "status": "unknown",
                    "delivered_at": None,
                    "opened_at": None,
                    "clicked_at": None,
                    "opens_count": 0,
                    "clicks_count": 0,
                    "bounce_type": None,
                    "error_code": code,
                    "error_message": error_msg,
                    "details": result,
                }

        except Exception as e:
            return {
                "status": "unknown",
                "delivered_at": None,
                "opened_at": None,
                "clicked_at": None,
                "opens_count": 0,
                "clicks_count": 0,
                "bounce_type": None,
                "error_code": None,
                "error_message": str(e),
                "details": {},
            }

    def check_voice_call_delivery_status(self, **kwargs) -> dict:
        """
        Vérifie le statut de livraison d'un appel vocal.

        Note : Voice Partner API ne fournit pas d'endpoint pour vérifier
        le statut de livraison d'un appel vocal après son envoi.
        Utiliser les webhooks (notifyUrl) pour recevoir les notifications de statut.

        Returns:
            Dict avec message d'erreur indiquant que cette fonctionnalité
            n'est pas supportée par l'API.
        """
        return {
            "status": "unknown",
            "delivered_at": None,
            "error_code": None,
            "error_message": "Voice Partner API ne supporte pas la vérification de statut. Utilisez les webhooks (notifyUrl).",
            "details": {
                "note": "Configurez 'notify_url' dans provider_options pour recevoir les notifications de statut en temps réel."
            },
        }

    def get_email_service_info(self) -> dict:
        """
        Récupère les informations du service Email de SMSPartner (MailPartner).

        Utilise l'API MailPartner pour récupérer le solde et les crédits email.

        Returns:
            Dict avec les crédits email, limites, et informations du compte
        """
        import requests

        try:
            api_key = self._get_api_key()
            if not api_key:
                return self._build_error_response(
                    "SMSPARTNER_API_KEY non configurée", "count"
                )

            # Récupérer le solde via MailPartner API
            url = f"{self.API_BASE_EMAIL}/me?apiKey={api_key}"
            response = requests.get(url, timeout=5)

            # Gérer les erreurs HTTP avec le helper
            error_response = self._handle_api_response(response, "Email", "count")
            if error_response:
                return error_response

            r_json = response.json()

            if r_json.get("success") is True:
                # Récupérer les crédits depuis la réponse
                credits_data = r_json.get("credits", {})
                credit_mail = int(credits_data.get("creditMail", 0))
                balance = float(credits_data.get("balance", 0))
                currency = credits_data.get("currency", "EUR")
                user_info = r_json.get("user", {})

                # Avertissements selon le solde
                warnings = []
                if credit_mail < 100:
                    warnings.append(
                        f"⚠️ Crédits email critiques: {credit_mail} emails restants"
                    )
                elif credit_mail < 1000:
                    warnings.append(
                        f"⚠️ Crédits email faibles: {credit_mail} emails restants"
                    )

                if balance < 10:
                    warnings.append(f"⚠️ Solde critique: {balance:.2f}{currency}")

                return {
                    "credits": f"{credit_mail} emails • {balance:.2f}{currency}",
                    "credits_type": "count",
                    "is_available": credit_mail > 0,
                    "limits": {
                        "per_second": 10,
                        "per_minute": 600,
                    },
                    "warnings": warnings,
                    "reputation": {},
                    "details": {
                        "credit_mail": credit_mail,
                        "balance_eur": balance,
                        "currency": currency,
                        "username": user_info.get("username", "N/A"),
                    },
                }
            else:
                # Erreur de l'API
                code = r_json.get("code", "unknown")
                return self._build_error_response(f"Erreur API (code {code})", "count")

        except requests.exceptions.Timeout:
            return self._build_error_response(
                "Timeout lors de la connexion à l'API MailPartner", "count"
            )
        except Exception as e:
            return self._build_error_response(f"Erreur: {str(e)}", "count")

    def get_voice_call_service_info(self) -> dict:
        """
        Récupère les informations du service Appel Vocal de VoicePartner (SMSPartner).

        Utilise l'API VoicePartner pour récupérer le solde et les crédits d'appels vocaux.

        Returns:
            Dict avec les crédits appels vocaux, limites, et informations du compte
        """
        import requests

        try:
            api_key = self._get_api_key()
            if not api_key:
                return self._build_error_response(
                    "SMSPARTNER_API_KEY non configurée", "mixed"
                )

            # Récupérer le solde via VoicePartner API
            url = f"https://api.voicepartner.fr/v1/me/{api_key}"
            response = requests.get(url, timeout=5)

            # Gérer les erreurs HTTP avec le helper
            error_response = self._handle_api_response(response, "Voice", "mixed")
            if error_response:
                return error_response

            r_json = response.json()

            if r_json.get("success") is True:
                # Récupérer les crédits depuis la réponse
                credit_eur = float(r_json.get("credit", 0))
                currency = r_json.get("currency", "€")
                details_data = r_json.get("details", {})

                # Crédits TTS (Text-to-Speech)
                tts = details_data.get("tts", {})
                tts_hours = int(tts.get("h", 0))
                tts_minutes = int(tts.get("m", 0))
                tts_seconds = int(tts.get("s", 0))
                total_tts_seconds = tts_hours * 3600 + tts_minutes * 60 + tts_seconds

                # Crédits TTS vers fixes
                tts_fixe = details_data.get("tts_fixe", {})
                tts_fixe_hours = int(tts_fixe.get("h", 0))
                tts_fixe_minutes = int(tts_fixe.get("m", 0))
                tts_fixe_seconds = int(tts_fixe.get("s", 0))
                total_tts_fixe_seconds = (
                    tts_fixe_hours * 3600 + tts_fixe_minutes * 60 + tts_fixe_seconds
                )

                # Messages vocaux
                voice = details_data.get("voice", {})
                voice_messages = int(voice.get("message", 0))

                # Avertissements selon le solde
                warnings = []
                if credit_eur < 5:
                    warnings.append(f"⚠️ Solde critique: {credit_eur:.2f}{currency}")
                elif credit_eur < 20:
                    warnings.append(f"⚠️ Solde faible: {credit_eur:.2f}{currency}")

                if total_tts_seconds < 300:  # < 5 minutes
                    warnings.append(
                        f"⚠️ Crédits TTS faibles: {tts_hours}h {tts_minutes}m {tts_seconds}s"
                    )

                if voice_messages < 10:
                    warnings.append(
                        f"⚠️ Messages vocaux faibles: {voice_messages} messages"
                    )

                # Formater l'affichage des crédits
                credits_display = (
                    f"{credit_eur:.2f}{currency} • {voice_messages} messages vocaux"
                )
                if total_tts_seconds > 0:
                    credits_display += f" • {tts_hours}h{tts_minutes}m TTS mobile"
                if total_tts_fixe_seconds > 0:
                    credits_display += (
                        f" • {tts_fixe_hours}h{tts_fixe_minutes}m TTS fixe"
                    )

                return {
                    "credits": credits_display,
                    "credits_type": "mixed",
                    "is_available": credit_eur > 0 or voice_messages > 0,
                    "limits": {
                        "per_second": 2,
                        "per_minute": 120,
                    },
                    "warnings": warnings,
                    "details": {
                        "credit_eur": credit_eur,
                        "currency": currency,
                        "voice_messages": voice_messages,
                        "tts_mobile_seconds": total_tts_seconds,
                        "tts_mobile_formatted": f"{tts_hours}h {tts_minutes}m {tts_seconds}s",
                        "tts_fixe_seconds": total_tts_fixe_seconds,
                        "tts_fixe_formatted": f"{tts_fixe_hours}h {tts_fixe_minutes}m {tts_fixe_seconds}s",
                    },
                }
            else:
                # Erreur de l'API
                return self._build_error_response("Erreur API VoicePartner", "mixed")

        except requests.exceptions.Timeout:
            return self._build_error_response(
                "Timeout lors de la connexion à l'API VoicePartner", "mixed"
            )
        except Exception as e:
            return self._build_error_response(f"Erreur: {str(e)}", "mixed")

    def get_service_status(self) -> Dict:
        """
        Récupère le statut et les crédits SMSPartner (VoicePartner API).

        SMSPartner fonctionne avec un système de prépaiement en euros.

        Returns:
            Dict avec status, crédits en euros, etc.
        """
        import requests
        from django.utils import timezone

        try:
            api_key = self._get_api_key()
            if not api_key:
                return {
                    "status": "not_configured",
                    "is_available": False,
                    "warnings": ["SMSPARTNER_API_KEY non configurée"],
                }

            # Vérifier le solde du compte via VoicePartner API
            url = f"https://api.voicepartner.fr/v1/me/{api_key}"
            response = requests.get(url, timeout=5)

            # Parser la réponse JSON
            r_json = response.json()

            if r_json.get("success") is True:
                # Récupérer les informations du compte
                credits_remaining = float(r_json.get("credit", 0))

                # Déterminer le statut
                is_operational = credits_remaining > 0
                status = "operational" if is_operational else "critical"

                # Avertissements selon le solde
                warnings = []
                if credits_remaining < 10:
                    warnings.append(f"Solde critique: {credits_remaining}€")
                elif credits_remaining < 50:
                    warnings.append(f"Solde faible: {credits_remaining}€")

                return {
                    "status": status,
                    "is_available": is_operational,
                    "services": self.services,
                    "credits": {
                        "type": "money",
                        "remaining": credits_remaining,
                        "currency": "EUR",
                        "limit": None,  # Pas de limite, système prépayé
                        "percentage": None,
                    },
                    "rate_limits": {
                        "per_second": 5,
                        "per_minute": 300,
                    },
                    "sla": {
                        "uptime_percentage": 99.9,
                    },
                    "last_check": timezone.now(),
                    "warnings": warnings,
                    "details": {
                        "account_info": r_json,
                        "refill_url": "https://www.smspartner.fr/recharge",
                    },
                }
            else:
                # Erreur API
                error_message = r_json.get("message", "Erreur API inconnue")
                return {
                    "status": "error",
                    "is_available": False,
                    "warnings": [f"Erreur API SMSPartner: {error_message}"],
                    "last_check": timezone.now(),
                }

        except requests.exceptions.RequestException as e:
            return {
                "status": "unreachable",
                "is_available": False,
                "warnings": [f"API SMSPartner injoignable: {str(e)}"],
                "last_check": timezone.now(),
            }
        except Exception as e:
            return {
                "status": "unknown",
                "is_available": None,
                "warnings": [f"Erreur: {str(e)}"],
                "last_check": timezone.now(),
            }
