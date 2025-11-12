"""Amazon SES email provider."""

from typing import Dict

from ..models import MissiveStatus
from .base import BaseProvider


class SESProvider(BaseProvider):
    """
    Amazon SES (Simple Email Service) provider.

    Required configuration:
        AWS_ACCESS_KEY_ID: Clé d'accès AWS
        AWS_SECRET_ACCESS_KEY: Clé secrète AWS
        AWS_REGION: Région AWS (ex: eu-west-1, us-east-1)
        SES_FROM_EMAIL: Email expéditeur vérifié dans SES

    Supports:
    - Email transactionnel
    - Email marketing (avec SES v2)
    - Reputation management
    """

    name = "ses"
    display_name = "Amazon SES"
    supported_types = ["EMAIL"]
    services = ["email", "email_transactional", "email_marketing"]
    config_keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "SES_FROM_EMAIL",
    ]
    required_packages = ["boto3"]
    site_url = "https://aws.amazon.com/ses/"
    status_url = "https://health.aws.amazon.com/health/status"
    documentation_url = "https://docs.aws.amazon.com/ses/"
    description_text = "Amazon Simple Email Service - AWS transactional email"

    def send_email(self, **kwargs) -> bool:
        """Send an email via Amazon SES"""
        import boto3
        from botocore.exceptions import ClientError

        # Validation
        is_valid, error = self.validate()
        if not is_valid:
            self._update_status(MissiveStatus.FAILED, error_message=error)
            return False

        if not self.missive.recipient_email:
            self._update_status(MissiveStatus.FAILED, error_message="Email missing")
            return False

        try:
            # Configuration AWS
            aws_access_key = self.config.get("AWS_ACCESS_KEY_ID")
            aws_secret_key = self.config.get("AWS_SECRET_ACCESS_KEY")
            aws_region = self.config.get("AWS_REGION", "eu-west-1")
            from_email = self.config.get("SES_FROM_EMAIL")

            if not all([aws_access_key, aws_secret_key, from_email]):
                self._update_status(
                    MissiveStatus.FAILED,
                    error_message="Configuration AWS SES incomplète",
                )
                return False

            # Créer le client SES
            client = boto3.client(
                "ses",
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region,
            )

            # Préparer l'email
            destination = {"ToAddresses": [self.missive.recipient_email]}

            # Cc et Bcc depuis kwargs ou metadata
            if "cc" in kwargs:
                destination["CcAddresses"] = (
                    kwargs["cc"] if isinstance(kwargs["cc"], list) else [kwargs["cc"]]
                )
            if "bcc" in kwargs:
                destination["BccAddresses"] = (
                    kwargs["bcc"]
                    if isinstance(kwargs["bcc"], list)
                    else [kwargs["bcc"]]
                )

            message = {
                "Subject": {"Data": self.missive.subject, "Charset": "UTF-8"},
                "Body": {},
            }

            # HTML ou texte
            if self.missive.body_html:
                message["Body"]["Html"] = {
                    "Data": self.missive.body_html,
                    "Charset": "UTF-8",
                }
            if self.missive.body_text or self.missive.body:
                message["Body"]["Text"] = {
                    "Data": self.missive.body_text or self.missive.body,
                    "Charset": "UTF-8",
                }

            # Options SES depuis kwargs
            send_params = {
                "Source": from_email,
                "Destination": destination,
                "Message": message,
            }

            # Ajouter ReplyToAddresses si fourni
            if "reply_to" in kwargs:
                send_params["ReplyToAddresses"] = [kwargs["reply_to"]]

            # Ajouter ConfigurationSetName si fourni (pour tracking)
            if "configuration_set" in kwargs:
                send_params["ConfigurationSetName"] = kwargs["configuration_set"]

            # Tags SES
            if "tags" in kwargs:
                send_params["Tags"] = kwargs["tags"]

            # Envoyer l'email
            response = client.send_email(**send_params)

            # Récupérer le MessageId
            message_id = response.get("MessageId")

            self._update_status(
                MissiveStatus.SENT,
                provider=self.name,
                external_id=message_id,
            )
            self._create_event(
                "sent", f"Email sent via Amazon SES (ID: {message_id})"
            )

            return True

        except ClientError as e:
            error_msg = e.response["Error"]["Message"]
            self._update_status(MissiveStatus.FAILED, error_message=error_msg)
            self._create_event("failed", error_msg)
            return False
        except Exception as e:
            self._update_status(MissiveStatus.FAILED, error_message=str(e))
            self._create_event("failed", str(e))
            return False

    def get_email_service_info(self) -> Dict:
        """
        Gets Amazon SES service information.

        Returns:
            Dict with quotas, credits, reputation, etc.
        """
        import boto3
        from botocore.exceptions import ClientError

        try:
            aws_access_key = self.config.get("AWS_ACCESS_KEY_ID")
            aws_secret_key = self.config.get("AWS_SECRET_ACCESS_KEY")
            aws_region = self.config.get("AWS_REGION", "eu-west-1")

            if not all([aws_access_key, aws_secret_key]):
                return {
                    "credits": None,
                    "credits_type": "quota",
                    "is_available": False,
                    "limits": {},
                    "warnings": ["Configuration AWS incomplète"],
                    "reputation": {},
                    "details": {},
                }

            client = boto3.client(
                "ses",
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region,
            )

            # Récupérer le quota d'envoi
            quota = client.get_send_quota()

            max_24h = int(quota.get("Max24HourSend", 0))
            sent_last_24h = int(quota.get("SentLast24Hours", 0))
            max_per_second = int(quota.get("MaxSendRate", 0))
            remaining = max_24h - sent_last_24h

            # Warnings
            warnings = []
            if remaining < 1000:
                warnings.append(
                    f"⚠️ Quota critique: {remaining} emails restants sur 24h"
                )
            elif remaining < max_24h * 0.2:
                warnings.append(f"⚠️ Quota faible: {remaining} emails restants sur 24h")

            # Vérifier les statistiques d'envoi
            stats = client.get_send_statistics()
            data_points = stats.get("SendDataPoints", [])

            # Calculer le taux de bounce/complaint récent
            recent_bounces = 0
            recent_complaints = 0
            recent_total = 0
            for point in data_points[:10]:  # 10 derniers points
                recent_bounces += point.get("Bounces", 0)
                recent_complaints += point.get("Complaints", 0)
                recent_total += point.get("DeliveryAttempts", 0)

            bounce_rate = (
                (recent_bounces / recent_total * 100) if recent_total > 0 else 0
            )
            complaint_rate = (
                (recent_complaints / recent_total * 100) if recent_total > 0 else 0
            )

            if bounce_rate > 5:
                warnings.append(f"⚠️ Taux de bounce élevé: {bounce_rate:.2f}%")
            if complaint_rate > 0.1:
                warnings.append(f"⚠️ Taux de plaintes élevé: {complaint_rate:.2f}%")

            return {
                "credits": f"{remaining} / {max_24h}",
                "credits_type": "quota",
                "is_available": remaining > 0,
                "limits": {
                    "max_24h": max_24h,
                    "max_per_second": max_per_second,
                    "sent_last_24h": sent_last_24h,
                    "remaining_24h": remaining,
                },
                "warnings": warnings,
                "reputation": {
                    "bounce_rate": f"{bounce_rate:.2f}%",
                    "complaint_rate": f"{complaint_rate:.2f}%",
                },
                "details": {
                    "region": aws_region,
                    "data_points_count": len(data_points),
                },
            }

        except ClientError as e:
            error_msg = e.response["Error"]["Message"]
            return {
                "credits": None,
                "credits_type": "quota",
                "is_available": False,
                "limits": {},
                "warnings": [f"Erreur AWS: {error_msg}"],
                "reputation": {},
                "details": {},
            }
        except Exception as e:
            return {
                "credits": None,
                "credits_type": "quota",
                "is_available": False,
                "limits": {},
                "warnings": [f"Erreur: {str(e)}"],
                "reputation": {},
                "details": {},
            }
