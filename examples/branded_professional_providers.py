"""
Exemples d'utilisation de l'architecture ultra-simplifiée pour les providers.

Architecture finale :
- Un seul type BRANDED pour TOUTES les messageries d'applications
- Le nom du provider (self.name) détermine automatiquement quelle méthode appeler
- Plus besoin de brand_name dans la DB !

Ce fichier contient des exemples de providers utilisant le type BRANDED
avec dispatch automatique basé sur self.name.
"""

from typing import Any, Dict
from missive.providers.base import BaseProvider
from missive.models import MissiveType, MissiveStatus


# ==================== EXEMPLE 1 : Provider WhatsApp ====================

class WhatsAppProvider(BaseProvider):
    """
    Provider WhatsApp utilisant le type BRANDED.
    
    Le nom du provider (self.name) détermine quelle méthode appeler.
    """
    
    name = "whatsapp"  # ← Définit automatiquement send_whatsapp()
    supported_types = [MissiveType.BRANDED, MissiveType.SMS]
    
    def __init__(self, missive=None, config=None):
        super().__init__(missive, config)
        # Configuration simulée
        self.api_key = config.get('API_KEY', 'demo_key') if config else 'demo_key'
    
    # -------------------- WhatsApp --------------------
    
    def send_whatsapp(self) -> bool:
        """Envoie un message WhatsApp via l'API du provider."""
        phone = self.missive.get_recipient_phone()
        if not phone:
            self._update_status(
                MissiveStatus.FAILED,
                error_message="Numéro de téléphone manquant"
            )
            return False
        
        # Formater le message pour WhatsApp
        message = self.format_whatsapp_message(
            self.missive.body,
            self.missive.body_text
        )
        
        # Simuler l'envoi via API
        print(f"[WhatsApp] Envoi vers {phone}: {message}")
        
        # Mise à jour du statut
        self._update_status(
            MissiveStatus.SENT,
            external_id=f"wa_{self.missive.id}"
        )
        
        return True
    
    def get_whatsapp_service_info(self) -> Dict[str, Any]:
        """Récupère les informations du service WhatsApp."""
        return {
            "credits": 5000,  # Nombre de messages disponibles
            "credits_type": "count",
            "is_available": True,
            "limits": {
                "messages_per_day": 10000,
                "max_attachment_size_mb": 5,
            },
            "warnings": [],
            "details": {
                "phone_number": "+33123456789",
                "business_account": True,
            },
        }
    
    def format_whatsapp_message(self, body: str, body_text: str = None) -> str:
        """Formate un message pour WhatsApp (markdown-like)."""
        message = body_text if body_text else body
        
        # Convertir HTML basique en formatage WhatsApp
        message = message.replace('<b>', '*').replace('</b>', '*')
        message = message.replace('<strong>', '*').replace('</strong>', '*')
        message = message.replace('<i>', '_').replace('</i>', '_')
        message = message.replace('<em>', '_').replace('</em>', '_')
        
        return message
    


# ==================== EXEMPLE 2 : Provider Telegram ====================

class TelegramProvider(BaseProvider):
    """
    Provider Telegram utilisant le type BRANDED.
    """
    
    name = "telegram"  # ← Définit automatiquement send_telegram()
    supported_types = [MissiveType.BRANDED]
    
    def __init__(self, missive=None, config=None):
        super().__init__(missive, config)
        self.bot_token = config.get('BOT_TOKEN', 'demo_token') if config else 'demo_token'
    
    def send_telegram(self) -> bool:
        """Envoie un message Telegram via l'API du provider."""
        # Note: Telegram utilise généralement un chat_id ou username, pas un phone
        # On peut stocker cela dans metadata
        metadata = self.missive.metadata or {}
        chat_id = metadata.get('telegram_chat_id')
        
        if not chat_id:
            self._update_status(
                MissiveStatus.FAILED,
                error_message="telegram_chat_id manquant dans metadata"
            )
            return False
        
        message = self.missive.body_text or self.missive.body
        
        print(f"[Telegram] Envoi vers chat_id {chat_id}: {message}")
        
        self._update_status(
            MissiveStatus.SENT,
            external_id=f"tg_{self.missive.id}"
        )
        
        return True
    
    def get_telegram_service_info(self) -> Dict[str, Any]:
        """Récupère les informations du service Telegram."""
        return {
            "credits": None,  # Telegram est généralement gratuit pour les bots
            "credits_type": "unlimited",
            "is_available": True,
            "limits": {
                "messages_per_second": 30,
                "max_message_length": 4096,
            },
            "warnings": [],
            "details": {
                "bot_username": "@mybot",
            },
        }


# ==================== EXEMPLE 3 : Provider Slack ====================

class SlackProvider(BaseProvider):
    """
    Provider Slack utilisant le type BRANDED.
    
    Utilise metadata pour le contexte d'organisation.
    """
    
    name = "slack"  # ← Définit automatiquement send_slack()
    supported_types = [MissiveType.BRANDED]
    
    def __init__(self, missive=None, config=None):
        super().__init__(missive, config)
        self.slack_token = config.get('SLACK_TOKEN') if config else None
    
    # -------------------- Slack --------------------
    
    def send_slack(self) -> bool:
        """Envoie un message Slack via Web API."""
        # Récupérer le contexte d'organisation
        context = self._get_organization_context()
        
        if not context or not context.get('channel_id'):
            self._update_status(
                MissiveStatus.FAILED,
                error_message="channel_id manquant dans metadata"
            )
            return False
        
        channel_id = context['channel_id']
        message = self.format_slack_message(
            self.missive.body,
            self.missive.body_text
        )
        
        # Simuler l'appel à l'API Slack
        print(f"[Slack] Envoi vers channel {channel_id}")
        print(f"Message: {message}")
        
        # Dans une vraie implémentation :
        # response = requests.post(
        #     'https://slack.com/api/chat.postMessage',
        #     headers={'Authorization': f'Bearer {self.slack_token}'},
        #     json={
        #         'channel': channel_id,
        #         'text': message,
        #     }
        # )
        
        self._update_status(
            MissiveStatus.SENT,
            external_id=f"slack_{channel_id}_{self.missive.id}"
        )
        
        return True
    
    def get_slack_service_info(self) -> Dict[str, Any]:
        """Récupère les informations du workspace Slack."""
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": True,
            "limits": {
                "messages_per_second": 1,
                "attachment_size_mb": 1000,
            },
            "warnings": [],
            "organization": {
                "workspace_id": "T123456",
                "workspace_name": "My Company",
            },
            "details": {
                "bot_user_id": "U789012",
            },
        }
    
    def format_slack_message(self, body: str, body_text: str = None) -> str:
        """Formate un message pour Slack (mrkdwn)."""
        message = body_text if body_text else body
        
        # Convertir HTML basique en mrkdwn Slack
        message = message.replace('<b>', '*').replace('</b>', '*')
        message = message.replace('<strong>', '*').replace('</strong>', '*')
        message = message.replace('<i>', '_').replace('</i>', '_')
        message = message.replace('<em>', '_').replace('</em>', '_')
        
        return message
    
    def list_slack_channels(self) -> Dict[str, Any]:
        """Liste les channels Slack disponibles."""
        # Dans une vraie implémentation, appeler l'API Slack
        return {
            "channels": [
                {"id": "C123456", "name": "general"},
                {"id": "C789012", "name": "dev-team"},
                {"id": "C345678", "name": "alerts"},
            ],
            "warnings": [],
        }
    


# ==================== EXEMPLE 4 : Provider Teams ====================

class TeamsProvider(BaseProvider):
    """
    Provider Microsoft Teams utilisant le type BRANDED.
    
    Utilise metadata pour le contexte d'organisation.
    """
    
    name = "teams"  # ← Définit automatiquement send_teams()
    supported_types = [MissiveType.BRANDED]
    
    def __init__(self, missive=None, config=None):
        super().__init__(missive, config)
        self.teams_token = config.get('TEAMS_TOKEN') if config else None
    
    def send_teams(self) -> bool:
        """Envoie un message Microsoft Teams via Graph API."""
        context = self._get_organization_context()
        
        if not context or not context.get('team_id') or not context.get('channel_id'):
            self._update_status(
                MissiveStatus.FAILED,
                error_message="team_id et channel_id manquants dans metadata"
            )
            return False
        
        team_id = context['team_id']
        channel_id = context['channel_id']
        
        message = self.missive.body
        
        print(f"[Teams] Envoi vers team {team_id}, channel {channel_id}")
        print(f"Message: {message}")
        
        # Dans une vraie implémentation :
        # response = requests.post(
        #     f'https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages',
        #     headers={'Authorization': f'Bearer {self.teams_token}'},
        #     json={'body': {'content': message}}
        # )
        
        self._update_status(
            MissiveStatus.SENT,
            external_id=f"teams_{team_id}_{channel_id}_{self.missive.id}"
        )
        
        return True
    
    def get_teams_service_info(self) -> Dict[str, Any]:
        """Récupère les informations de l'organisation Teams."""
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": True,
            "limits": {
                "messages_per_second": 4,
                "attachment_size_mb": 250,
                "max_message_length": 28000,
            },
            "warnings": [],
            "organization": {
                "tenant_id": "abc123",
                "organization_name": "My Company",
            },
            "details": {},
        }


# ==================== EXEMPLE 5 : Utilisation ====================

def exemple_utilisation():
    """Exemples d'utilisation de l'architecture ultra-simplifiée."""
    from missive.models import Missive, Recipient
    
    # -------------------- Exemple WhatsApp --------------------
    
    recipient = Recipient.objects.create(
        first_name="Jean",
        last_name="Dupont",
        mobile="+33612345678"
    )
    
    # Créer la missive (un seul type BRANDED pour toutes les apps)
    missive_whatsapp = Missive.objects.create(
        missive_type=MissiveType.BRANDED,  # ← Toujours le même type !
        recipient=recipient,
        subject='Notification',
        body='<b>Important</b> : Votre commande est prête',
        body_text='Important : Votre commande est prête'
    )
    
    # Le provider WhatsApp sait ce qu'il fait via son name="whatsapp"
    provider = WhatsAppProvider(missive=missive_whatsapp)
    success = provider.send()  # → Appelle automatiquement send_whatsapp()
    
    print(f"WhatsApp envoyé : {success}")
    
    # -------------------- Exemple Telegram --------------------
    
    missive_telegram = Missive.objects.create(
        missive_type=MissiveType.BRANDED,  # ← Même type !
        recipient=recipient,
        subject='Alerte',
        body='Nouvelle mise à jour disponible',
        metadata={'telegram_chat_id': '123456789'}  # ← Contexte optionnel
    )
    
    # Le provider Telegram sait ce qu'il fait via son name="telegram"
    provider = TelegramProvider(missive=missive_telegram)
    success = provider.send()  # → Appelle automatiquement send_telegram()
    
    print(f"Telegram envoyé : {success}")
    
    # -------------------- Exemple Slack --------------------
    
    recipient_pro = Recipient.objects.create(
        first_name="Marie",
        last_name="Martin",
        email="marie.martin@company.com"
    )
    
    missive_slack = Missive.objects.create(
        missive_type=MissiveType.BRANDED,  # ← Même type pour Slack aussi !
        recipient=recipient_pro,
        subject='Alerte système',
        body='<b>Attention</b> : Le serveur nécessite une intervention',
        body_text='Attention : Le serveur nécessite une intervention',
        metadata={
            'workspace_id': 'T123456',  # ← Contexte d'organisation
            'channel_id': 'C789012',
        }
    )
    
    # Le provider Slack sait ce qu'il fait via son name="slack"
    provider = SlackProvider(missive=missive_slack)
    success = provider.send()  # → Appelle automatiquement send_slack()
    
    print(f"Slack envoyé : {success}")
    
    # -------------------- Exemple Teams --------------------
    
    missive_teams = Missive.objects.create(
        missive_type=MissiveType.BRANDED,  # ← Même type pour Teams aussi !
        recipient=recipient_pro,
        subject='Rapport journalier',
        body='<h2>Rapport du jour</h2><p>Tout est OK</p>',
        metadata={
            'team_id': 'abc-def-ghi',  # ← Contexte d'organisation
            'channel_id': 'xyz-uvw',
        }
    )
    
    # Le provider Teams sait ce qu'il fait via son name="teams"
    provider = TeamsProvider(missive=missive_teams)
    success = provider.send()  # → Appelle automatiquement send_teams()
    
    print(f"Teams envoyé : {success}")
    
    # -------------------- RÉSUMÉ --------------------
    # 
    # Architecture ultra-simplifiée :
    # 1. Un seul type : MissiveType.BRANDED pour toutes les messageries
    # 2. Le provider définit son nom : name = "whatsapp", "slack", etc.
    # 3. Dispatch automatique vers send_{name}()
    # 4. Plus besoin de brand_name dans la DB !
    # 5. Contexte d'organisation optionnel via metadata


if __name__ == '__main__':
    print("=" * 80)
    print("EXEMPLES D'UTILISATION - ARCHITECTURE ULTRA-SIMPLIFIÉE")
    print("=" * 80)
    print()
    print("Un seul type BRANDED + nom du provider = dispatch automatique !")
    print()
    
    # Note: Ces exemples nécessitent Django et la base de données configurée
    # exemple_utilisation()
    
    print("Voir le code source pour des exemples détaillés d'implémentation.")
    print()
    print("Principe : ")
    print("  1. Un seul type BRANDED pour toutes les messageries")
    print("  2. Le provider définit son nom (name='whatsapp', 'slack', etc.)")
    print("  3. Dispatch automatique vers send_{name}()")
    print("  4. Plus besoin de brand_name dans la DB !")

