# ============================================================================
# EXEMPLE DE CONFIGURATION MISSIVE_PROVIDERS
# ============================================================================

# ============================================================================
# FORMAT RECOMMANDÉ : Liste simple (auto-catégorisation)
# ============================================================================
# Le système catégorise automatiquement chaque provider selon ses supported_types.
# Plus besoin de spécifier le type ! Le provider le déclare lui-même.

MISSIVE_PROVIDERS = [
    # Providers Email
    "missive.providers.django_email.DjangoEmailProvider",  # Toujours disponible (SMTP Django)
    "missive.providers.sendgrid.SendGridProvider",
    "missive.providers.mailgun.MailgunProvider",
    "missive.providers.brevo.BrevoProvider",  # Supporte EMAIL + SMS
    "missive.providers.ses.SESProvider",  # Amazon SES
    # Providers SMS
    "missive.providers.twilio.TwilioProvider",  # Supporte SMS + BRANDED (WhatsApp)
    "missive.providers.vonage.VonageProvider",  # Supporte SMS + VOICE_CALL
    "missive.providers.smspartner.SMSPartnerProvider",  # Supporte SMS + EMAIL + VOICE_CALL
    # Providers Messageries de marque (BRANDED)
    "missive.providers.slack.SlackProvider",
    "missive.providers.teams.TeamsProvider",
    "missive.providers.telegram.TelegramProvider",
    "missive.providers.signal.SignalProvider",
    "missive.providers.messenger.MessengerProvider",
    # Providers Push Notifications
    "missive.providers.fcm.FCMProvider",
    "missive.providers.apn.APNProvider",
    # Providers Postal
    "missive.providers.laposte.LaPosteProvider",
    "missive.providers.ar24.AR24Provider",
    "missive.providers.certeurope.CerteuropeProvider",
    # Providers Notification
    "missive.providers.notification.InAppNotificationProvider",
    # Vos providers personnalisés
    # "myapp.providers.MyCustomProvider",
]

# ============================================================================
# ANCIEN FORMAT : Dict par type (rétrocompatibilité)
# ============================================================================
# Ce format est toujours supporté mais non recommandé car redondant.
# Les providers déclarent déjà leurs supported_types.

"""
MISSIVE_PROVIDERS = {
    'EMAIL': [
        'missive.providers.django_email.DjangoEmailProvider',
        'missive.providers.sendgrid.SendGridProvider',
        'missive.providers.mailgun.MailgunProvider',
        'missive.providers.ses.SESProvider',
        'missive.providers.brevo.BrevoProvider',
    ],
    'SMS': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.vonage.VonageProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
        'missive.providers.brevo.BrevoProvider',
    ],
    'BRANDED': [
        'missive.providers.twilio.TwilioProvider',  # WhatsApp
        'missive.providers.slack.SlackProvider',
        'missive.providers.teams.TeamsProvider',
        'missive.providers.telegram.TelegramProvider',
        'missive.providers.signal.SignalProvider',
        'missive.providers.messenger.MessengerProvider',
    ],
    'VOICE_CALL': [
        'missive.providers.twilio.TwilioProvider',
        'missive.providers.vonage.VonageProvider',
        'missive.providers.smspartner.SMSPartnerProvider',
    ],
    'POSTAL': [
        'missive.providers.laposte.LaPosteProvider',
    ],
    'PUSH_NOTIFICATION': [
        'missive.providers.fcm.FCMProvider',
        'missive.providers.apn.APNProvider',
    ],
    'NOTIFICATION': [
        'missive.providers.notification.InAppNotificationProvider',
    ],
}
"""

# ============================================================================
# AVANTAGES DU NOUVEAU FORMAT (liste simple)
# ============================================================================
# ✅ Plus simple : une seule liste
# ✅ Pas de redondance : les providers déclarent leurs types
# ✅ Extensible : ajouter un provider = ajouter une ligne
# ✅ Auto-découverte : le système lit supported_types automatiquement
# ✅ Facile pour les providers multi-types (Twilio, Brevo, etc.)

