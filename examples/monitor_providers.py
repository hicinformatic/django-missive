"""
Exemple d'utilisation du système de monitoring des providers.

Ce script démontre comment :
- Vérifier le statut opérationnel d'un provider
- Consulter les crédits/quotas disponibles
- Effectuer un health check complet
- Surveiller les services disponibles
"""

from missive.providers.sendgrid import SendGridProvider
from missive.providers.twilio import TwilioProvider
from missive.providers.sendinblue import SendinBlueProvider
from missive.providers.smspartner import SMSPartnerProvider


def check_provider_status(provider_class):
    """
    Vérifie et affiche le statut complet d'un provider.
    
    Args:
        provider_class: Classe du provider à vérifier
    """
    provider = provider_class()
    
    print(f"\n{'='*70}")
    print(f"Provider: {provider.name}")
    print(f"{'='*70}")
    
    # 1. Services disponibles
    print(f"\n📋 Services disponibles:")
    for service in provider.services:
        print(f"  ✓ {service}")
    
    # 2. Statut opérationnel
    status = provider.get_service_status()
    
    status_emoji = {
        'operational': '✅',
        'degraded': '⚠️',
        'down': '❌',
        'unknown': '❓'
    }
    
    print(f"\n📊 Statut opérationnel:")
    print(f"  Status: {status_emoji.get(status['status'], '?')} {status['status']}")
    print(f"  Disponible: {'Oui' if status['is_available'] else 'Non'}")
    print(f"  Dernière vérification: {status['last_check']}")
    
    # 3. Crédits/Quotas
    credits = status.get('credits', {})
    print(f"\n💰 Crédits/Quotas:")
    print(f"  Type: {credits.get('type', 'N/A')}")
    
    if credits.get('type') == 'money':
        remaining = credits.get('remaining', 0)
        currency = credits.get('currency', '')
        print(f"  Solde: {remaining} {currency}")
    elif credits.get('type') == 'emails':
        remaining = credits.get('remaining', 0)
        limit = credits.get('limit', 0)
        percentage = credits.get('percentage', 0)
        print(f"  Emails restants: {remaining} / {limit} ({percentage:.1f}%)")
    elif credits.get('type') == 'mixed':
        print(f"  Email: {credits.get('email', {})}")
        print(f"  SMS: {credits.get('sms', {})}")
    elif credits.get('type') == 'unlimited':
        print(f"  Illimité ♾️")
    else:
        print(f"  Inconnu")
    
    # 4. Rate limits
    rate_limits = status.get('rate_limits', {})
    print(f"\n⏱️  Rate Limits:")
    if rate_limits.get('per_second'):
        print(f"  Par seconde: {rate_limits['per_second']}")
    if rate_limits.get('per_minute'):
        print(f"  Par minute: {rate_limits['per_minute']}")
    if rate_limits.get('per_hour'):
        print(f"  Par heure: {rate_limits['per_hour']}")
    if rate_limits.get('per_day'):
        print(f"  Par jour: {rate_limits['per_day']}")
    if not any(rate_limits.values()):
        print(f"  Aucune limite connue")
    
    # 5. SLA
    sla = status.get('sla', {})
    print(f"\n📈 SLA:")
    if sla.get('uptime_percentage'):
        print(f"  Uptime: {sla['uptime_percentage']}%")
    if sla.get('response_time_ms'):
        print(f"  Temps de réponse: {sla['response_time_ms']}ms")
    if sla.get('success_rate'):
        print(f"  Taux de succès: {sla['success_rate']}%")
    
    # 6. Avertissements
    warnings = status.get('warnings', [])
    if warnings:
        print(f"\n⚠️  Avertissements:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # 7. Health check
    print(f"\n🏥 Health Check:")
    health = provider.health_check()
    print(f"  Status: {health['status']}")
    print(f"  Healthy: {'✅' if health['is_healthy'] else '❌'}")
    print(f"  Summary: {health['summary']}")
    
    if health.get('issues'):
        print(f"\n  Issues:")
        for issue in health['issues']:
            print(f"    - {issue}")
    
    if health.get('recommendations'):
        print(f"\n  Recommandations:")
        for rec in health['recommendations']:
            print(f"    → {rec}")
    
    # 8. Détails additionnels
    details = status.get('details', {})
    if details:
        print(f"\n🔍 Détails:")
        for key, value in details.items():
            print(f"  {key}: {value}")


def check_credits_only(provider_class):
    """
    Vérifie uniquement les crédits d'un provider.
    
    Args:
        provider_class: Classe du provider à vérifier
    """
    provider = provider_class()
    credits = provider.check_credits()
    
    print(f"\n💰 {provider.name} - Crédits:")
    print(f"  Type: {credits.get('type')}")
    print(f"  Restant: {credits.get('remaining')} {credits.get('currency')}")
    
    if credits.get('percentage'):
        print(f"  Pourcentage: {credits['percentage']:.1f}%")
    
    if credits.get('needs_refill'):
        print(f"  ⚠️ RECHARGE NÉCESSAIRE!")
        if credits.get('refill_url'):
            print(f"  URL: {credits['refill_url']}")


def monitor_all_providers():
    """
    Surveille tous les providers et affiche un résumé.
    """
    providers = [
        SendGridProvider,
        TwilioProvider,
        SendinBlueProvider,
        SMSPartnerProvider,
    ]
    
    print("\n" + "="*70)
    print("MONITORING - TOUS LES PROVIDERS")
    print("="*70)
    
    summary = []
    
    for provider_class in providers:
        provider = provider_class()
        health = provider.health_check()
        
        summary.append({
            'name': provider.name,
            'status': health['status'],
            'is_healthy': health['is_healthy'],
            'summary': health['summary'],
        })
    
    # Afficher le tableau récapitulatif
    print(f"\n{'Provider':<20} {'Status':<15} {'Health':<10} {'Summary'}")
    print("-" * 70)
    
    for item in summary:
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'down': '❌'
        }
        
        health_icon = '✅' if item['is_healthy'] else '❌'
        status_icon = status_emoji.get(item['status'], '❓')
        
        print(f"{item['name']:<20} {status_icon} {item['status']:<12} {health_icon:<10} {item['summary'][:40]}")
    
    # Compter les problèmes
    issues_count = sum(1 for item in summary if not item['is_healthy'])
    
    if issues_count > 0:
        print(f"\n⚠️  {issues_count} provider(s) nécessite(nt) votre attention!")
    else:
        print(f"\n✅ Tous les providers sont opérationnels!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'all':
            # Vérifier tous les providers en détail
            for ProviderClass in [SendGridProvider, TwilioProvider, SendinBlueProvider, SMSPartnerProvider]:
                check_provider_status(ProviderClass)
        
        elif command == 'credits':
            # Vérifier uniquement les crédits
            for ProviderClass in [SendGridProvider, TwilioProvider, SMSPartnerProvider]:
                check_credits_only(ProviderClass)
        
        elif command == 'summary':
            # Résumé rapide
            monitor_all_providers()
        
        else:
            print(f"Commande inconnue: {command}")
            print("Usage: python monitor_providers.py [all|credits|summary]")
    
    else:
        # Par défaut, afficher le résumé
        monitor_all_providers()
        
        # Puis un provider en détail
        print("\n" + "="*70)
        print("EXEMPLE DÉTAILLÉ - SendGrid")
        print("="*70)
        check_provider_status(SendGridProvider)

