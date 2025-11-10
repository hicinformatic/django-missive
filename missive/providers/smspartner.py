"""
Provider SMSPartner pour SMS (provider français).
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from ..models import MissiveStatus
from .base import BaseProvider


class SMSPartnerProvider(BaseProvider):
    """
    Provider pour SMSPartner / VoicePartner.
    
    Supporte :
    - SMS (classique, low-cost, premium)
    - Messages vocaux (TTS)
    - Email
    """

    name = "SMS Partner"
    display_name = "SMS Partner (SMS/Email/Vocal)"
    supported_types = ["SMS", "EMAIL", "VOICE_CALL"]
    services = [
        "sms",
        "sms_low_cost",
        "sms_premium",
        "voice_message",  # Messages vocaux TTS
        "voice_call",     # Appels vocaux
        "email",          # Emails transactionnels
    ]
    config_keys = ["SMSPARTNER_API_KEY", "SMSPARTNER_SENDER"]
    required_package = "requests"

    def send_sms(self) -> bool:
        """Envoie un SMS via SMSPartner API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            # TODO: Intégrer avec SMSPartner
            # import requests
            #
            # api_key = self.config.get('SMSPARTNER_API_KEY')
            #
            # response = requests.post(
            #     'https://api.smspartner.fr/v1/send',
            #     json={
            #         'apiKey': api_key,
            #         'phoneNumbers': self.missive.recipient_phone,
            #         'message': self.missive.body,
            #         'sender': self.config.get('SMSPARTNER_SENDER'),
            #         'tag': f'missive_{self.missive.id}'
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('messageId')

            # Simulation
            external_id = f"sp_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "SMS envoyé via SMSPartner")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def send_email(self) -> bool:
        """Envoie un email via SMSPartner API"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email manquant")
            return False

        try:
            # TODO: Intégrer avec SMSPartner Email API
            # import requests
            #
            # api_key = self.config.get('SMSPARTNER_API_KEY')
            #
            # response = requests.post(
            #     'https://api.smspartner.fr/v1/email/send',
            #     json={
            #         'apiKey': api_key,
            #         'to': self.missive.recipient_email,
            #         'from': self.config.get('DEFAULT_FROM_EMAIL'),
            #         'subject': self.missive.subject,
            #         'html': self.missive.body,
            #         'text': self.missive.body_text,
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('messageId')

            # Simulation
            external_id = f"sp_email_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "Email envoyé via SMSPartner")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def send_voice_call(self) -> bool:
        """Envoie un message vocal via SMSPartner API (TTS)"""
        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_phone:
            self._update_status(MissiveStatus.FAILED, error_message="Numéro manquant")
            return False

        try:
            # TODO: Intégrer avec SMSPartner Voice API
            # import requests
            #
            # api_key = self.config.get('SMSPARTNER_API_KEY')
            #
            # response = requests.post(
            #     'https://api.voicepartner.fr/v1/voice/send',
            #     json={
            #         'apiKey': api_key,
            #         'phoneNumber': self.missive.recipient_phone,
            #         'message': self.missive.body_text,  # Texte pour TTS
            #         'language': 'fr-FR',
            #         'voice': 'female',  # male ou female
            #     }
            # )
            #
            # result = response.json()
            # external_id = result.get('messageId')

            # Simulation
            external_id = f"sp_voice_{self.missive.id}"

            self._update_status(
                MissiveStatus.SENT, provider=self.name, external_id=external_id
            )
            self._create_event("sent", "Message vocal envoyé via SMSPartner")

            return True

        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def validate_webhook_signature(
        self, payload: Dict, headers: Dict
    ) -> Tuple[bool, str]:
        """Valide la signature SMSPartner"""
        # À implémenter selon la doc SMSPartner
        return True, ""

    def extract_missive_id(self, payload: Dict) -> Optional[str]:
        """Extrait l'ID depuis SMSPartner webhook"""
        return payload.get("messageId") or payload.get("tag", "").replace(
            "missive_", ""
        )

    def extract_event_type(self, payload: Dict) -> str:
        """Extrait le type d'événement SMSPartner"""
        return payload.get("status", "unknown")

    def get_sms_service_info(self) -> dict:
        """
        Récupère les informations du service SMS de SMSPartner.
        
        Utilise l'API SMSPartner pour récupérer le solde et les crédits SMS.
        
        Returns:
            Dict avec les crédits SMS, limites, et informations du compte
        """
        import requests

        try:
            api_key = self.config.get("SMSPARTNER_API_KEY")
            if not api_key:
                return {
                    "credits": None,
                    "credits_type": "count",
                    "is_available": False,
                    "limits": {},
                    "warnings": ["SMSPARTNER_API_KEY non configurée"],
                    "details": {},
                }

            # Récupérer le solde via SMSPartner API
            url = f"https://api.smspartner.fr/v1/me?apiKey={api_key}"
            response = requests.get(url, timeout=5)
            
            # Gérer les codes d'erreur HTTP
            if response.status_code == 429:
                return {
                    "credits": None,
                    "credits_type": "count",
                    "is_available": None,
                    "limits": {},
                    "warnings": ["⚠️ Rate limit dépassé - Trop d'appels API. Réessayez dans quelques minutes."],
                    "details": {},
                }
            elif response.status_code != 200:
                return {
                    "credits": None,
                    "credits_type": "count",
                    "is_available": False,
                    "limits": {},
                    "warnings": [f"Erreur HTTP {response.status_code}"],
                    "details": {},
                }
            
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
                if total_sms < 100:
                    warnings.append(f"⚠️ Crédits SMS critiques: {total_sms} SMS restants")
                elif total_sms < 500:
                    warnings.append(f"⚠️ Crédits SMS faibles: {total_sms} SMS restants")
                
                if solde_eur < 10:
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
                return {
                    "credits": None,
                    "credits_type": "count",
                    "is_available": False,
                    "limits": {},
                    "warnings": [f"Erreur API (code {code})"],
                    "details": {},
                }
                
        except requests.exceptions.Timeout:
            return {
                "credits": None,
                "credits_type": "count",
                "is_available": None,
                "limits": {},
                "warnings": ["Timeout lors de la connexion à l'API SMSPartner"],
                "details": {},
            }
        except Exception as e:
            return {
                "credits": None,
                "credits_type": "count",
                "is_available": None,
                "limits": {},
                "warnings": [f"Erreur: {str(e)}"],
                "details": {},
            }

    def get_email_service_info(self) -> dict:
        """
        Récupère les informations du service Email de SMSPartner.
        
        Note: L'API email de SMSPartner n'est pas encore implémentée.
        Pour l'instant, retourne le solde global.
        
        Returns:
            Dict avec les informations du compte
        """
        return {
            "credits": "Non implémenté",
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {},
            "warnings": ["L'API Email de SMSPartner n'est pas encore implémentée"],
            "reputation": {},
            "details": {},
        }

    def get_voice_call_service_info(self) -> dict:
        """
        Récupère les informations du service Appel Vocal de VoicePartner (SMSPartner).
        
        Utilise l'API VoicePartner pour récupérer le solde et les crédits d'appels vocaux.
        
        Returns:
            Dict avec les crédits appels vocaux, limites, et informations du compte
        """
        import requests

        try:
            api_key = self.config.get("SMSPARTNER_API_KEY")
            if not api_key:
                return {
                    "credits": None,
                    "credits_type": "amount",
                    "is_available": False,
                    "limits": {},
                    "warnings": ["SMSPARTNER_API_KEY non configurée"],
                    "details": {},
                }

            # Récupérer le solde via VoicePartner API
            url = f"https://api.voicepartner.fr/v1/me/{api_key}"
            response = requests.get(url, timeout=5)
            
            # Gérer les codes d'erreur HTTP
            if response.status_code == 429:
                return {
                    "credits": None,
                    "credits_type": "mixed",
                    "is_available": None,
                    "limits": {},
                    "warnings": ["⚠️ Rate limit dépassé - Trop d'appels API. Réessayez dans quelques minutes."],
                    "details": {},
                }
            elif response.status_code != 200:
                return {
                    "credits": None,
                    "credits_type": "mixed",
                    "is_available": False,
                    "limits": {},
                    "warnings": [f"Erreur HTTP {response.status_code}"],
                    "details": {},
                }
            
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
                total_tts_fixe_seconds = tts_fixe_hours * 3600 + tts_fixe_minutes * 60 + tts_fixe_seconds
                
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
                    warnings.append(f"⚠️ Crédits TTS faibles: {tts_hours}h {tts_minutes}m {tts_seconds}s")
                
                if voice_messages < 10:
                    warnings.append(f"⚠️ Messages vocaux faibles: {voice_messages} messages")

                # Formater l'affichage des crédits
                credits_display = f"{credit_eur:.2f}{currency} • {voice_messages} messages vocaux"
                if total_tts_seconds > 0:
                    credits_display += f" • {tts_hours}h{tts_minutes}m TTS mobile"
                if total_tts_fixe_seconds > 0:
                    credits_display += f" • {tts_fixe_hours}h{tts_fixe_minutes}m TTS fixe"

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
                return {
                    "credits": None,
                    "credits_type": "mixed",
                    "is_available": False,
                    "limits": {},
                    "warnings": ["Erreur API VoicePartner"],
                    "details": {},
                }
                
        except requests.exceptions.Timeout:
            return {
                "credits": None,
                "credits_type": "mixed",
                "is_available": None,
                "limits": {},
                "warnings": ["Timeout lors de la connexion à l'API VoicePartner"],
                "details": {},
            }
        except Exception as e:
            return {
                "credits": None,
                "credits_type": "mixed",
                "is_available": None,
                "limits": {},
                "warnings": [f"Erreur: {str(e)}"],
                "details": {},
            }

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
            api_key = self.config.get("SMSPARTNER_API_KEY")
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
                    }
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
