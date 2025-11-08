"""
Providers pour l'envoi de missives et le traitement des webhooks.
Chaque provider gère à la fois l'envoi et la réception des webhooks.

Providers multi-types :
- LaPosteProvider : POSTAL + EMAIL (Email AR)
- SendinBlueProvider : EMAIL + SMS
- TwilioProvider : SMS + WHATSAPP

Providers mono-type :
- SendGridProvider : EMAIL uniquement
- MailgunProvider : EMAIL uniquement
- SMSPartnerProvider : SMS uniquement
- DjangoEmailProvider : EMAIL uniquement
- InAppNotificationProvider : NOTIFICATION uniquement
"""

from .base import BaseProvider
from .django_email import DjangoEmailProvider
from .laposte import LaPosteProvider
from .mailgun import MailgunProvider
from .notification import InAppNotificationProvider
from .sendgrid import SendGridProvider
from .sendinblue import SendinBlueProvider
from .smspartner import SMSPartnerProvider
from .twilio import TwilioProvider

__all__ = [
    "BaseProvider",
    "SendGridProvider",
    "MailgunProvider",
    "DjangoEmailProvider",
    "TwilioProvider",
    "SMSPartnerProvider",
    "LaPosteProvider",
    "SendinBlueProvider",
    "InAppNotificationProvider",
]
