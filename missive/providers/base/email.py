"""
Mixin pour les fonctionnalités email des providers.
"""
import re
from typing import Any, Dict, List, Optional

from django.utils import timezone


class BaseEmailMixin:
    """
    Mixin fournissant les fonctionnalités spécifiques aux emails.
    """

    def get_email_service_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du compte/service Email.
        
        Retourne les informations importantes pour le service Email :
        - Crédits disponibles (nombre d'emails ou montant)
        - Limites et quotas (emails/jour, taille max, etc.)
        - État du service (actif/inactif)
        - Réputation de l'expéditeur
        
        Returns:
            Dict contenant :
                - credits: Nombre d'emails ou montant disponible
                - credits_type: 'count' (nombre) ou 'amount' (montant) ou 'unlimited'
                - is_available: bool, service accessible
                - limits: Dict avec les limites (quota_daily, max_attachment_size, etc.)
                - warnings: Liste des alertes
                - reputation: Dict avec infos de réputation (score, bounces, etc.)
                - details: Dict avec infos supplémentaires
        
        À surcharger dans les providers concrets.
        """
        return {
            "credits": None,
            "credits_type": "unlimited",
            "is_available": None,
            "limits": {},
            "warnings": ["Méthode get_email_service_info() non implémentée pour ce provider"],
            "reputation": {},
            "details": {},
        }

    def send_email(self) -> bool:
        """
        Envoie un email. À surcharger dans les providers concrets.

        Returns:
            bool: True si succès, False sinon
        """
        from ...models import MissiveStatus

        # Vérifier qu'on a un email de destinataire
        if not self.missive.get_recipient_email():
            self._update_status(
                MissiveStatus.FAILED, error_message="Pas d'email destinataire"
            )
            return False

        # À implémenter dans les sous-classes
        raise NotImplementedError(
            f"{self.name} doit implémenter la méthode send_email()"
        )

    def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Valide une adresse email et évalue le risque d'échec de délivrance.

        Vérifie :
        - Syntaxe de l'email
        - Format du domaine
        - Domaines jetables/temporaires connus
        - Existence d'enregistrements MX (DNS)

        Args:
            email: L'adresse email à valider

        Returns:
            Dict contenant :
            - is_valid (bool): Email valide syntaxiquement
            - is_deliverable (bool): Email probablement délivrable
            - risk_score (int): Score de risque 0-100 (0=sûr, 100=très risqué)
            - warnings (List[str]): Liste des avertissements
            - details (Dict): Détails techniques (MX records, etc.)

        Example:
            result = provider.validate_email("user@example.com")
            if result['risk_score'] > 70:
                print("Risque élevé d'échec!")
        """
        warnings = []
        details = {}

        # Validation syntaxique de base
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid = bool(re.match(email_regex, email))

        if not is_valid:
            return {
                "is_valid": False,
                "is_deliverable": False,
                "risk_score": 100,
                "warnings": ["Format d'email invalide"],
                "details": {},
            }

        # Extraction du domaine
        domain = email.split("@")[1].lower()
        details["domain"] = domain

        # TODO: Vérifier les domaines jetables/temporaires
        # disposable_domains = ['tempmail.com', 'guerrillamail.com', ...]
        # if domain in disposable_domains:
        #     warnings.append("Domaine jetable détecté")

        # TODO: Vérifier les enregistrements MX
        # try:
        #     import dns.resolver
        #     mx_records = dns.resolver.resolve(domain, 'MX')
        #     details['mx_records'] = [str(r.exchange) for r in mx_records]
        # except:
        #     warnings.append("Aucun enregistrement MX trouvé")

        # Calcul du score de risque
        risk_score = self._calculate_email_risk_score(email, domain, warnings, details)

        return {
            "is_valid": is_valid,
            "is_deliverable": len(warnings) == 0,
            "risk_score": risk_score,
            "warnings": warnings,
            "details": details,
        }

    def _calculate_email_risk_score(
        self, email: str, domain: str, warnings: List[str], details: Dict
    ) -> int:
        """
        Calcule un score de risque pour une adresse email.

        Args:
            email: L'adresse email
            domain: Le domaine
            warnings: Liste des avertissements détectés
            details: Détails de validation

        Returns:
            int: Score de risque entre 0 (sûr) et 100 (très risqué)
        """
        score = 0

        # Pénalités selon les avertissements
        if "Domaine jetable détecté" in warnings:
            score += 80
        if "Aucun enregistrement MX trouvé" in warnings:
            score += 60
        if "Serveur SMTP injoignable" in warnings:
            score += 50

        # TODO: Ajouter d'autres critères
        # - Réputation du domaine
        # - Historique d'envois précédents
        # - Blacklists

        return min(score, 100)

    def test_smtp_server(self, domain: str) -> Dict[str, Any]:
        """
        Teste la disponibilité et la configuration d'un serveur SMTP.

        Vérifie :
        - Résolution DNS des enregistrements MX
        - Connexion au serveur SMTP
        - Support TLS/SSL
        - Réponse du serveur

        Args:
            domain: Le domaine à tester (ex: "example.com")

        Returns:
            Dict contenant :
            - is_reachable (bool): Serveur joignable
            - mx_records (List[str]): Liste des serveurs MX
            - supports_tls (bool): Support TLS/SSL
            - smtp_banner (str): Bannière du serveur
            - response_time_ms (int): Temps de réponse en ms
            - warnings (List[str]): Avertissements

        Example:
            result = provider.test_smtp_server("example.com")
            if not result['is_reachable']:
                print("Serveur SMTP injoignable!")
        """
        # TODO: Implémenter la logique de test SMTP
        # import dns.resolver
        # import smtplib
        # import socket
        # from time import time
        #
        # try:
        #     # Résolution MX
        #     mx_records = dns.resolver.resolve(domain, 'MX')
        #     mx_host = str(mx_records[0].exchange)
        #
        #     # Test de connexion
        #     start = time()
        #     server = smtplib.SMTP(mx_host, timeout=10)
        #     response_time = int((time() - start) * 1000)
        #
        #     # Test TLS
        #     supports_tls = hasattr(server, 'starttls')
        #     banner = server.ehlo_resp.decode() if server.ehlo_resp else ""
        #
        #     server.quit()
        #
        #     return {
        #         'is_reachable': True,
        #         'mx_records': [str(r.exchange) for r in mx_records],
        #         'supports_tls': supports_tls,
        #         'smtp_banner': banner,
        #         'response_time_ms': response_time,
        #         'warnings': []
        #     }
        # except Exception as e:
        #     return {
        #         'is_reachable': False,
        #         'warnings': [str(e)]
        #     }

        return {
            "is_reachable": None,
            "mx_records": [],
            "supports_tls": None,
            "smtp_banner": "",
            "response_time_ms": 0,
            "warnings": ["Test SMTP non implémenté"],
        }

    def add_attachment_email(self, attachment) -> Any:
        """
        Prépare une pièce jointe pour un email.

        Args:
            attachment: Instance de MissiveAttachment

        Returns:
            Objet d'attachment formaté selon le provider
            (ex: tuple (filename, content, mimetype) pour certains providers)
        """
        # Par défaut, retourne un dict standard
        # Les providers concrets peuvent override pour leur format spécifique
        return {
            "filename": attachment.filename,
            "content": attachment.file.read() if attachment.file else None,
            "url": attachment.external_url,
            "mime_type": attachment.mime_type,
        }

    def calculate_spam_score(self, subject: str, body: str) -> Dict[str, Any]:
        """
        Calcule un score de spam pour le contenu d'un email.

        Vérifie :
        - Mots-clés spam courants
        - Ratio majuscules/minuscules
        - Nombre de liens
        - Utilisation excessive de ponctuation

        Args:
            subject: Sujet de l'email
            body: Corps de l'email

        Returns:
            Dict contenant :
            - spam_score (int): Score 0-100 (0=sûr, 100=spam)
            - triggers (List[str]): Mots/patterns déclencheurs
            - recommendations (List[str]): Conseils d'amélioration
        """
        score = 0
        triggers = []
        recommendations = []

        # TODO: Implémenter la détection de spam
        # - Mots-clés : GRATUIT, URGENT, CLIQUEZ ICI, etc.
        # - Ratio ALL CAPS
        # - Trop de liens
        # - Trop de ! ou ???
        # - Utiliser SpamAssassin ou un service externe

        return {
            "spam_score": score,
            "triggers": triggers,
            "recommendations": recommendations,
        }

