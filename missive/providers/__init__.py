"""
Providers pour l'envoi de missives et le traitement des webhooks.
Chaque provider gère à la fois l'envoi et la réception des webhooks.

Providers multi-types :
- LaPosteProvider : POSTAL + EMAIL (Email AR)
- BrevoProvider : EMAIL + SMS
- TwilioProvider : SMS + BRANDED (WhatsApp)
- VonageProvider : SMS + VOICE_CALL

Providers mono-type :
- SendGridProvider : EMAIL uniquement
- MailgunProvider : EMAIL uniquement
- SESProvider : EMAIL uniquement
- SMSPartnerProvider : SMS uniquement
- DjangoEmailProvider : EMAIL uniquement
- InAppNotificationProvider : NOTIFICATION uniquement
"""

from .base import BaseProvider
from .brevo import BrevoProvider
from .django_email import DjangoEmailProvider
from .laposte import LaPosteProvider
from .mailgun import MailgunProvider
from .notification import InAppNotificationProvider
from .sendgrid import SendGridProvider
from .ses import SESProvider
from .smspartner import SMSPartnerProvider
from .twilio import TwilioProvider
from .vonage import VonageProvider

__all__ = [
    "BaseProvider",
    "SendGridProvider",
    "MailgunProvider",
    "SESProvider",
    "DjangoEmailProvider",
    "TwilioProvider",
    "VonageProvider",
    "SMSPartnerProvider",
    "LaPosteProvider",
    "BrevoProvider",
    "InAppNotificationProvider",
]
