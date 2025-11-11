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

import re
import uuid
from typing import Dict, Optional

from django.conf import settings

from .exceptions import MissiveValidationError
from .models import Missive, MissiveType, Recipient
from .sender import MissiveSender


# ============================================================================
# FONCTIONS DE VALIDATION
# ============================================================================


def _validate_email(email: str) -> None:
    """
    Valide le format d'un email.

    Args:
        email: L'adresse email à valider

    Raises:
        MissiveValidationError: Si l'email est invalide
    """
    if not email:
        raise MissiveValidationError("L'adresse email ne peut pas être vide")

    # Regex simple pour validation basique
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise MissiveValidationError(f"Format d'email invalide : {email}")


def _validate_phone(phone: str) -> None:
    """
    Valide le format d'un numéro de téléphone.

    Args:
        phone: Le numéro de téléphone à valider

    Raises:
        MissiveValidationError: Si le téléphone est invalide
    """
    if not phone:
        raise MissiveValidationError("Le numéro de téléphone ne peut pas être vide")

    # Doit commencer par + suivi de chiffres
    phone_pattern = r"^\+[1-9]\d{1,14}$"
    if not re.match(phone_pattern, phone):
        raise MissiveValidationError(
            f"Format de téléphone invalide : {phone}. "
            "Le format attendu est E.164 (ex: +33612345678)"
        )


def _validate_content(content: str, missive_type: str = "") -> None:
    """
    Valide le contenu d'une missive.

    Args:
        content: Le contenu à valider
        missive_type: Type de missive (pour messages d'erreur contextuels)

    Raises:
        MissiveValidationError: Si le contenu est invalide
    """
    if not content or not content.strip():
        raise MissiveValidationError(
            f"Le contenu {'du ' + missive_type if missive_type else ''} ne peut pas être vide"
        )


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

    Raises:
        MissiveValidationError: Si les données sont invalides (email, phone, content)

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
    # VALIDATIONS
    # =========================================================================

    # Valider le contenu
    _validate_content(content, missive_type)

    # Valider les champs requis selon le type
    if missive_type in ("SMS", "VOICE_CALL"):
        if not phone:
            raise MissiveValidationError(
                f"Le champ 'phone' est obligatoire pour les missives de type {missive_type}"
            )
        _validate_phone(phone)

    elif missive_type == "EMAIL":
        if not email:
            raise MissiveValidationError(
                "Le champ 'email' est obligatoire pour les missives de type EMAIL"
            )
        _validate_email(email)

    elif missive_type == "BRANDED":
        # Pour les branded (WhatsApp, Slack, etc.), vérifier phone OU email
        if not phone and not email:
            raise MissiveValidationError(
                "Au moins un des champs 'phone' ou 'email' est requis pour les missives BRANDED"
            )
        if phone:
            _validate_phone(phone)
        if email:
            _validate_email(email)

    elif missive_type == "POSTAL":
        if not address or not isinstance(address, dict):
            raise MissiveValidationError(
                "Le champ 'address' (dict) est obligatoire pour les missives POSTAL"
            )
        # Valider les champs requis de l'adresse
        required_fields = ["street", "city", "postal_code", "country"]
        missing = [f for f in required_fields if not address.get(f)]
        if missing:
            raise MissiveValidationError(
                f"Champs manquants dans l'adresse : {', '.join(missing)}"
            )

    # Valider les emails/phones de l'expéditeur si fournis
    if sender_email:
        _validate_email(sender_email)
    if sender_phone:
        _validate_phone(sender_phone)

    # =========================================================================
    # 1. CRÉER OU RÉCUPÉRER L'EXPÉDITEUR
    # =========================================================================
    sender = None

    # Essayer de récupérer un expéditeur existant
    if sender_email or sender_phone:
        sender = Recipient.objects.filter(
            email=sender_email, mobile=sender_phone
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
                "name": default_name,
                "mobile": default_phone,
                "is_active": True,
                "can_be_sender": True,
            },
        )

    # =========================================================================
    # 2. CRÉER LE DESTINATAIRE
    # =========================================================================

    # Générer un nom si pas fourni
    recipient_name = ""
    if first_name and last_name:
        recipient_name = f"{first_name} {last_name}"
    elif first_name:
        recipient_name = first_name
    elif last_name:
        recipient_name = last_name
    elif denomination:
        recipient_name = denomination
    else:
        # Générer un UID unique
        unique_id = str(uuid.uuid4())[:8]
        recipient_name = f"User_{unique_id}"

    # Données du recipient
    recipient_data = {
        "is_active": True,
        "name": recipient_name,
    }

    if phone:
        recipient_data["mobile"] = phone
    if email:
        recipient_data["email"] = email
    if address:
        recipient_data["address_line1"] = address.get("street", "")
        recipient_data["city"] = address.get("city", "")
        recipient_data["postal_code"] = address.get("postal_code", "")
        recipient_data["country"] = address.get("country", "FR")

    # Créer ou récupérer le recipient
    lookup_fields = {}
    if email:
        lookup_fields["email"] = email
    elif phone:
        lookup_fields["mobile"] = phone
    else:
        # Pas d'email ni téléphone, utiliser le nom
        lookup_fields["name"] = recipient_name

    recipient, _ = Recipient.objects.get_or_create(
        **lookup_fields, defaults=recipient_data
    )

    # =========================================================================
    # 3. CRÉER LA MISSIVE
    # =========================================================================

    # Auto-générer le subject pour les emails si absent
    if missive_type == "EMAIL" and not subject:
        sender_display = getattr(sender, "display_name", None) or sender.name or "System"
        subject = f"Message de {sender_display}"

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
        phone: Numéro de téléphone (format E.164, ex: +33612345678)
        content: Contenu du SMS
        **kwargs: Options (sender, provider_options, etc.)

    Returns:
        Missive créée et envoyée

    Raises:
        MissiveValidationError: Si le téléphone ou le contenu est invalide

    Example:
        >>> send_sms('+33612345678', 'Bonjour!')
        <Missive: SMS to +33612345678>
    """
    # Validations explicites pour un meilleur message d'erreur
    if not phone:
        raise MissiveValidationError("Le numéro de téléphone est obligatoire pour envoyer un SMS")
    if not content:
        raise MissiveValidationError("Le contenu du SMS ne peut pas être vide")

    return send_missive("sms", phone=phone, content=content, **kwargs)


def send_email(email: str, subject: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un email.

    Args:
        email: Adresse email du destinataire
        subject: Sujet de l'email
        content: Contenu de l'email
        **kwargs: Options (sender, cc, bcc, etc.)

    Returns:
        Missive créée et envoyée

    Raises:
        MissiveValidationError: Si l'email, le sujet ou le contenu est invalide

    Example:
        >>> send_email('user@example.com', 'Test', 'Bonjour!')
        <Missive: Email to user@example.com>
    """
    # Validations explicites
    if not email:
        raise MissiveValidationError("L'adresse email est obligatoire pour envoyer un email")
    if not subject:
        raise MissiveValidationError("Le sujet est obligatoire pour envoyer un email")
    if not content:
        raise MissiveValidationError("Le contenu de l'email ne peut pas être vide")

    return send_missive(
        "email", email=email, subject=subject, content=content, **kwargs
    )


def send_whatsapp(phone: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un message WhatsApp.

    Args:
        phone: Numéro de téléphone (format E.164, ex: +33612345678)
        content: Contenu du message
        **kwargs: Options (provider='twilio', etc.)

    Returns:
        Missive créée et envoyée

    Raises:
        MissiveValidationError: Si le téléphone ou le contenu est invalide

    Example:
        >>> send_whatsapp('+33612345678', 'Hello WhatsApp!')
        <Missive: WhatsApp to +33612345678>
    """
    # Validations explicites
    if not phone:
        raise MissiveValidationError("Le numéro de téléphone est obligatoire pour WhatsApp")
    if not content:
        raise MissiveValidationError("Le contenu du message WhatsApp ne peut pas être vide")

    if "provider" not in kwargs:
        kwargs["provider"] = "twilio"  # Twilio par défaut pour WhatsApp
    return send_missive("branded", phone=phone, content=content, **kwargs)


def send_slack(channel_id: str, content: str, **kwargs) -> Missive:
    """
    Raccourci pour envoyer un message Slack.

    Args:
        channel_id: ID du canal Slack (ex: C0123456789)
        content: Contenu du message
        **kwargs: Options (provider='slack', etc.)

    Returns:
        Missive créée et envoyée

    Raises:
        MissiveValidationError: Si le channel_id ou le contenu est invalide

    Example:
        >>> send_slack('C0123456789', 'Hello Slack!')
        <Missive: Slack to C0123456789>
    """
    # Validations explicites
    if not channel_id:
        raise MissiveValidationError("Le channel_id est obligatoire pour envoyer un message Slack")
    if not content:
        raise MissiveValidationError("Le contenu du message Slack ne peut pas être vide")

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
        chat_id: ID du chat Telegram (ex: 123456789)
        content: Contenu du message
        **kwargs: Options (provider='telegram', etc.)

    Returns:
        Missive créée et envoyée

    Raises:
        MissiveValidationError: Si le chat_id ou le contenu est invalide

    Example:
        >>> send_telegram('123456789', 'Hello Telegram!')
        <Missive: Telegram to 123456789>
    """
    # Validations explicites
    if not chat_id:
        raise MissiveValidationError("Le chat_id est obligatoire pour envoyer un message Telegram")
    if not content:
        raise MissiveValidationError("Le contenu du message Telegram ne peut pas être vide")

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
