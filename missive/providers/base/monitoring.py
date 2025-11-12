"""Provider monitoring mixin."""

from typing import Any, Dict

from django.utils import timezone


class BaseMonitoringMixin:
    """Provider monitoring functionality mixin."""

    def get_service_status(self) -> Dict[str, Any]:
        """Returns provider service status. Override in subclasses."""
        return {
            "status": "unknown",
            "is_available": None,
            "services": self.services,
            "credits": {
                "type": "unknown",
                "remaining": None,
                "currency": "",
                "limit": None,
                "percentage": None,
            },
            "rate_limits": {
                "per_second": None,
                "per_minute": None,
                "per_hour": None,
                "per_day": None,
            },
            "sla": {
                "uptime_percentage": None,
                "response_time_ms": None,
                "success_rate": None,
            },
            "last_check": timezone.now(),
            "warnings": ["Monitoring non implémenté pour ce provider"],
            "details": {},
        }

    def check_credits(self) -> Dict[str, Any]:
        """
        Specifically check available credits.

        Returns:
            Dict containing:
            - type (str): Type de crédit ('money', 'emails', 'sms', 'unlimited')
            - remaining (float|int): Crédits restants
            - currency (str): Devise ('EUR', 'USD') ou unité ('emails', 'sms')
            - limit (float|int): Limite totale
            - percentage (float): Pourcentage restant
            - threshold_warning (int): Seuil d'alerte (ex: 10%)
            - needs_refill (bool): Recharge nécessaire
            - refill_url (str): URL pour recharger

        Example:
            credits = provider.check_credits()
            if credits['needs_refill']:
                send_alert(f"Provider {self.name} nécessite une recharge!")
        """
        # Par défaut, appelle get_service_status et extrait les crédits
        status = self.get_service_status()
        credits = status.get("credits", {})

        # Calculate if recharge is needed
        threshold = 10  # 10% by default
        percentage = credits.get("percentage")
        needs_refill = percentage is not None and percentage < threshold

        return {
            "type": credits.get("type", "unknown"),
            "remaining": credits.get("remaining"),
            "currency": credits.get("currency", ""),
            "limit": credits.get("limit"),
            "percentage": percentage,
            "threshold_warning": threshold,
            "needs_refill": needs_refill,
            "refill_url": "",  # À définir dans les providers concrets
        }

    def check_rate_limits(self) -> Dict[str, Any]:
        """
        Vérifie les limites de débit actuelles.

        Returns:
            Dict containing:
            - limits (Dict): Limites configurées
            - current_usage (Dict): Utilisation actuelle
            - remaining (Dict): Requêtes restantes
            - reset_at (datetime): Quand les compteurs se réinitialisent
            - is_throttled (bool): Si actuellement limité

        Example:
            limits = provider.check_rate_limits()
            if limits['is_throttled']:
                time.sleep(60)  # Attendre 1 minute
        """
        status = self.get_service_status()
        rate_limits = status.get("rate_limits", {})

        return {
            "limits": rate_limits,
            "current_usage": {},  # À implémenter dans providers concrets
            "remaining": {},
            "reset_at": None,
            "is_throttled": False,
        }

    def get_sla_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques SLA du provider.

        Returns:
            Dict containing:
            - uptime_percentage (float): % d'uptime (ex: 99.99)
            - uptime_target (float): Objectif SLA (ex: 99.9)
            - meets_sla (bool): Respecte le SLA
            - incidents_30d (int): Nombre d'incidents sur 30 jours
            - mttr_minutes (int): Mean Time To Recovery en minutes
            - response_time_avg_ms (int): Average response time
            - response_time_p95_ms (int): 95e percentile
            - success_rate (float): Taux de succès %
            - last_incident (datetime): Dernier incident
            - status_page_url (str): URL de la page de statut publique

        Example:
            sla = provider.get_sla_metrics()
            if not sla['meets_sla']:
                print(f"⚠️ SLA non respecté: {sla['uptime_percentage']}%")
        """
        status = self.get_service_status()
        sla = status.get("sla", {})

        uptime = sla.get("uptime_percentage")
        target = 99.9  # Default target
        meets_sla = uptime is not None and uptime >= target

        return {
            "uptime_percentage": uptime,
            "uptime_target": target,
            "meets_sla": meets_sla,
            "incidents_30d": None,
            "mttr_minutes": None,
            "response_time_avg_ms": sla.get("response_time_ms"),
            "response_time_p95_ms": None,
            "success_rate": sla.get("success_rate"),
            "last_incident": None,
            "status_page_url": "",  # À définir dans providers concrets
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Effectue un health check complet du provider.

        Combine :
        - Statut opérationnel
        - Crédits disponibles
        - Rate limits
        - SLA

        Returns:
            Dict containing:
            - is_healthy (bool): Provider healthy and operational
            - status (str): 'healthy', 'warning', 'critical', 'down'
            - issues (List[str]): Liste des problèmes détectés
            - recommendations (List[str]): Actions recommandées
            - summary (str): Résumé textuel

        Example:
            health = provider.health_check()
            if not health['is_healthy']:
                send_alert(f"Provider {self.name}: {health['summary']}")
        """
        issues = []
        recommendations = []

        # Vérifier le statut
        status = self.get_service_status()
        if status["status"] == "down":
            issues.append("Service indisponible")
        elif status["status"] == "degraded":
            issues.append("Service dégradé")

        # Vérifier les crédits
        credits = self.check_credits()
        if credits.get("needs_refill"):
            issues.append(
                f"Crédits faibles: {credits['remaining']} {credits['currency']}"
            )
            recommendations.append("Recharger le compte provider")

        # Vérifier les rate limits
        rate_limits = self.check_rate_limits()
        if rate_limits.get("is_throttled"):
            issues.append("Rate limit atteint")
            recommendations.append("Réduire la cadence d'envoi")

        # Déterminer l'état global
        if not issues:
            health_status = "healthy"
            is_healthy = True
            summary = f"{self.name} : Tout fonctionne normalement ✅"
        elif len(issues) == 1 and "faibles" in issues[0]:
            health_status = "warning"
            is_healthy = True
            summary = f"{self.name} : Attention - {issues[0]} ⚠️"
        elif status["status"] == "down":
            health_status = "down"
            is_healthy = False
            summary = f"{self.name} : Service indisponible ❌"
        else:
            health_status = "critical"
            is_healthy = False
            summary = f"{self.name} : Problèmes critiques - {len(issues)} issue(s) ⚠️"

        return {
            "is_healthy": is_healthy,
            "status": health_status,
            "issues": issues,
            "recommendations": recommendations,
            "summary": summary,
        }
