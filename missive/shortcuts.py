"""
Fonctions raccourcis pour envoyer rapidement des missives.

Usage simplifié pour tests et envois rapides :

    from missive.shortcuts import send_missive

    # SMS
    send_missive('sms', phone='+33612345678', content='Test SMS')

    # Email
    send_missive('email', email='user@example.com', subject='Test', content='Hello!')

    # WhatsApp (branded)
    send_missive('branded', phone='+33612345678', content='Hello WhatsApp')
"""

import uuid
from typing import Any, Dict, Optional

from django.conf import settings

from .models import Missive, MissiveType, Recipient
from .sender import MissiveSender


def send_missive(
    missive_type: str,
    content: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address: Optional[Dict] = None,
    sender_email: Optional[str] = None,
    sender_phone: Optional[str] = None,
    sender_name: Optional[str] = None,
    subject: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    denomination: Optional[str] = None,
    provider: Optional[str] = None,
    **kwargs,
) -> Missive:
    """
    Envoie rapidement une missive avec un minimum d'informations.

    Tout ce qui est facultatif est généré automatiquement :
    - UID généré si pas de nom/dénomination
    - Expéditeur par défaut depuis settings
    - Provider auto-sélectionné si non spécifié
    - Subject auto-généré pour les emails

    Args:
        missive_type: Type de missive ('sms', 'email', 'branded', 'postal', etc.)
        content: Contenu du message
        phone: Numéro de téléphone du destinataire (pour SMS/WhatsApp/Voice)
        email: Email du destinataire (pour Email)
        address: Adresse postale (dict avec street, city, postal_code, country)
        sender_email: Email de l'expéditeur (défaut: settings.DEFAULT_FROM_EMAIL)
        sender_phone: Téléphone de l'expéditeur (défaut: settings ou None)
        sender_name: Nom de l'expéditeur (défaut: settings ou 'System')
        subject: Sujet (pour email, auto-généré si absent)
        first_name: Prénom destinataire (optionnel, sinon UID)
        last_name: Nom destinataire (optionnel, sinon UID)
        denomination: Dénomination (pour les organisations)
        provider: Provider spécifique à utiliser (sinon auto-sélectionné)
        **kwargs: Options additionnelles (provider_options, priority, etc.)

    Returns:
        Missive: La missive créée et envoyée

    Examples:
        # SMS simple
        >>> send_missive('sms', phone='+33612345678', content='Test')
        <Missive: SMS to +33612345678>

        # Email avec sujet
        >>> send_missive('email',
        ...     email='user@example.com',
        ...     subject='Bienvenue',
        ...     content='Bonjour !'
        ... )
        <Missive: Email to user@example.com>

        # WhatsApp (branded)
        >>> send_missive('branded',
        ...     phone='+33612345678',
        ...     content='Hello WhatsApp',
        ...     provider='twilio'  # Force Twilio pour WhatsApp
        ... )
        <Missive: WhatsApp to +33612345678>

        # Avec options provider
        >>> send_missive('sms',
        ...     phone='+33612345678',
        ...     content='Test planifié',
        ...     provider_options={'scheduled_time': 14, 'is_commercial': False}
        ... )
        <Missive: SMS to +33612345678>
    """
    # Normaliser le type
    missive_type = missive_type.upper()
    if not hasattr(MissiveType, missive_type):
        # Essayer de mapper les noms courants
        type_mapping = {
            "SMS": "SMS",
            "EMAIL": "EMAIL",
            "MAIL": "EMAIL",
            "POSTAL": "POSTAL",
            "LETTER": "POSTAL",
            "COURRIER": "POSTAL",
            "LRE": "LRE",
            "NOTIFICATION": "NOTIFICATION",
            "NOTIF": "NOTIFICATION",
            "PUSH": "PUSH_NOTIFICATION",
            "PUSH_NOTIFICATION": "PUSH_NOTIFICATION",
            "VOICE": "VOICE_CALL",
            "VOICE_CALL": "VOICE_CALL",
            "CALL": "VOICE_CALL",
            "VOCAL": "VOICE_CALL",
            "BRANDED": "BRANDED",
            "WHATSAPP": "BRANDED",
            "SLACK": "BRANDED",
            "TEAMS": "BRANDED",
            "TELEGRAM": "BRANDED",
            "MESSENGER": "BRANDED",
            "SIGNAL": "BRANDED",
            "DISCORD": "BRANDED",
        }
        missive_type = type_mapping.get(missive_type, "EMAIL")

    # =========================================================================
    # 1. CRÉER OU RÉCUPÉRER L'EXPÉDITEUR
    # =========================================================================
    sender = None

    # Essayer de récupérer un expéditeur existant
    if sender_email or sender_phone:
        sender = Recipient.objects.filter(
            email=sender_email, phone=sender_phone
        ).first()

    # Sinon créer un expéditeur par défaut
    if not sender:
        default_email = sender_email or getattr(
            settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
        )
        default_phone = sender_phone or getattr(settings, "MISSIVE_DEFAULT_PHONE", None)
        default_name = sender_name or getattr(
            settings, "MISSIVE_DEFAULT_SENDER_NAME", "System"
        )

        sender, _ = Recipient.objects.get_or_create(
            email=default_email,
            defaults={
                "first_name": default_name,
                "phone": default_phone,
                "is_active": True,
            },
        )

    # =========================================================================
    # 2. CRÉER LE DESTINATAIRE
    # =========================================================================

    # Générer un UID si pas de nom fourni
    if not first_name and not last_name and not denomination:
        unique_id = str(uuid.uuid4())[:8]
        first_name = f"User_{unique_id}"

    # Données du recipient
    recipient_data = {
        "is_active": True,
    }

    if first_name:
        recipient_data["first_name"] = first_name
    if last_name:
        recipient_data["last_name"] = last_name
    if denomination:
        recipient_data["denomination"] = denomination
    if phone:
        recipient_data["phone"] = phone
    if email:
        recipient_data["email"] = email
    if address:
        recipient_data["address"] = address.get("street", "")
        recipient_data["city"] = address.get("city", "")
        recipient_data["postal_code"] = address.get("postal_code", "")
        recipient_data["country"] = address.get("country", "FR")

    # Créer ou récupérer le recipient
    lookup_fields = {}
    if email:
        lookup_fields["email"] = email
    elif phone:
        lookup_fields["phone"] = phone
    else:
        # Pas d'email ni téléphone, utiliser le nom
        lookup_fields["first_name"] = recipient_data.get("first_name")

    recipient, _ = Recipient.objects.get_or_create(
        **lookup_fields, defaults=recipient_data
    )

    # =========================================================================
    # 3. CRÉER LA MISSIVE
    # =========================================================================

    # Auto-générer le subject pour les emails si absent
    if missive_type == "EMAIL" and not subject:
        subject = f"Message de {sender.display_name}"

    # Données de la missive
    missive_data = {
        "missive_type": missive_type,
        "sender": sender,
        "recipient": recipient,
        "body": content,
        "subject": subject or "",
    }

    # Ajouter les kwargs optionnels
    if "priority" in kwargs:
        missive_data["priority"] = kwargs.pop("priority")
    if "is_registered" in kwargs:
        missive_data["is_registered"] = kwargs.pop("is_registered")
    if "requires_signature" in kwargs:
        missive_data["requires_signature"] = kwargs.pop("requires_signature")
    if "provider_options" in kwargs:
        missive_data["provider_options"] = kwargs.pop("provider_options")

    # Créer la missive
    missive = Missive.objects.create(**missive_data)

    # Forcer le provider si spécifié
    if provider:
        missive._provider_name = provider

    # =========================================================================
    # 4. ENVOYER LA MISSIVE
    # =========================================================================

    sender_instance = MissiveSender()
    sender_instance.send(missive)

    return missive


def send_sms(phone: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un SMS.

    Args:
        phone: Numéro de téléphone
        content: Contenu du SMS
        **kwargs: Options (sender, provider_options, etc.)

    Returns:
        Missive créée et envoyée

    Example:
        >>> send_sms('+33612345678', 'Bonjour!')
        <Missive: SMS to +33612345678>
    """
    return send_missive("sms", phone=phone, content=content, **kwargs)


def send_email(email: str, subject: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un email.

    Args:
        email: Adresse email
        subject: Sujet
        content: Contenu
        **kwargs: Options (sender, cc, bcc, etc.)

    Returns:
        Missive créée et envoyée

    Example:
        >>> send_email('user@example.com', 'Test', 'Bonjour!')
        <Missive: Email to user@example.com>
    """
    return send_missive(
        "email", email=email, subject=subject, content=content, **kwargs
    )


def send_whatsapp(phone: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un message WhatsApp.

    Args:
        phone: Numéro de téléphone
        content: Contenu du message
        **kwargs: Options (provider='twilio', etc.)

    Returns:
        Missive créée et envoyée

    Example:
        >>> send_whatsapp('+33612345678', 'Hello WhatsApp!')
        <Missive: WhatsApp to +33612345678>
    """
    if "provider" not in kwargs:
        kwargs["provider"] = "twilio"  # Twilio par défaut pour WhatsApp
    return send_missive("branded", phone=phone, content=content, **kwargs)


def send_slack(channel_id: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un message Slack.

    Args:
        channel_id: ID du canal Slack
        content: Contenu du message
        **kwargs: Options (provider='slack', etc.)

    Returns:
        Missive créée et envoyée

    Example:
        >>> send_slack('C0123456789', 'Hello Slack!')
        <Missive: Slack to C0123456789>
    """
    if "provider" not in kwargs:
        kwargs["provider"] = "slack"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["channel_id"] = channel_id

    # Pour Slack, utiliser le channel_id comme identifiant
    return send_missive(
        "branded",
        email=f"{channel_id}@slack.com",  # Email fictif pour lookup
        content=content,
        **kwargs,
    )


def send_telegram(chat_id: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un message Telegram.

    Args:
        chat_id: ID du chat Telegram
        content: Contenu du message
        **kwargs: Options (provider='telegram', etc.)

    Returns:
        Missive créée et envoyée

    Example:
        >>> send_telegram('123456789', 'Hello Telegram!')
        <Missive: Telegram to 123456789>
    """
    if "provider" not in kwargs:
        kwargs["provider"] = "telegram"
    if "provider_options" not in kwargs:
        kwargs["provider_options"] = {}
    kwargs["provider_options"]["chat_id"] = chat_id

    return send_missive(
        "branded",
        email=f"{chat_id}@telegram.org",  # Email fictif
        content=content,
        **kwargs,
    )
