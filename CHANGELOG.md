# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

### Added
- **Système de fallback automatique** : Nouveau système `MISSIVE_PROVIDERS` permettant de définir plusieurs providers par ordre de priorité
  - Configuration avec liste de providers : `MISSIVE_PROVIDERS = {'EMAIL': ['provider1', 'provider2', ...]}`
  - Health check automatique avant envoi pour détecter les providers indisponibles
  - Bascule automatique vers le provider suivant en cas d'échec
  - Options `enable_fallback` et `skip_health_check` pour contrôler le comportement
  - Logging détaillé de toutes les tentatives
  - Mise à jour automatique du champ `missive.provider` avec le provider réellement utilisé
- **Système de services par provider** : Chaque provider expose maintenant une liste détaillée des services qu'il offre (ex: SendinBlue = `['email', 'sms', 'contacts', 'automation']`)
- **Monitoring avancé des providers** :
  - Méthode `get_service_status()` pour récupérer le statut opérationnel
  - Méthode `check_credits()` pour vérifier les crédits/quotas restants
  - Méthode `check_rate_limits()` pour les limites de débit
  - Méthode `get_sla_metrics()` pour les métriques SLA (uptime, response time)
  - Méthode `health_check()` pour un diagnostic complet
  - Méthode `has_service()` pour vérifier si un service spécifique est disponible
- **Mixin BaseMonitoringMixin** dans `providers/base/monitoring.py`
- **Documentation complète** : `docs/MONITORING.md` avec exemples et bonnes pratiques
- **Script d'exemple** : `examples/monitor_providers.py` pour surveiller les providers

### Changed
- **`MissiveSender.send()`** : Refactorisation complète avec support du fallback
  - Nouveau paramètre `enable_fallback` (défaut: True)
  - Nouveau paramètre `skip_health_check` (défaut: False)
  - Gestion d'erreurs améliorée avec détails des tentatives
  - Lève `RuntimeError` si tous les providers échouent
- **Configuration MISSIVE_PROVIDERS** : Remplace `MISSIVE_CONFIG['PROVIDERS']` (ancienne config toujours supportée avec warning)
- **DEFAULT_PROVIDERS** : Maintenant des listes de providers au lieu de strings simples
- Tous les providers incluent maintenant un attribut `services` définissant leurs fonctionnalités
- `BaseProvider` hérite maintenant de `BaseMonitoringMixin`
- Architecture modulaire étendue avec le monitoring

### Provider Services
- **SendGrid** : `['email', 'email_transactional', 'email_marketing']`
- **Brevo/SendinBlue** : `['email', 'email_transactional', 'email_marketing', 'sms', 'contacts', 'automation']`
- **La Poste** : `['postal', 'postal_registered', 'postal_signature', 'email_ar', 'colissimo']`
- **Twilio** : `['sms', 'whatsapp', 'voice', 'verify']`
- **SMSPartner** : `['sms', 'sms_low_cost', 'sms_premium']`
- **Mailgun** : `['email', 'email_validation', 'email_routing']`
- **Django Email** : `['email']`
- **In-App Notification** : `['notification', 'push_notification', 'badge']`

### Technical Details

**Fallback & Failover:**
- Ordre de priorité : `missive.provider` > `MISSIVE_PROVIDERS` > `MISSIVE_CONFIG['PROVIDERS']` (deprecated) > `DEFAULT_PROVIDERS`
- Health check via `provider.health_check()` avant chaque tentative
- Logging structuré avec niveau INFO/WARNING/ERROR
- Méthode `get_provider_classes()` retourne une liste ordonnée de providers
- Méthode `is_provider_healthy()` pour vérifier la santé d'un provider
- Documentation complète dans `docs/FAILOVER.md`

**Monitoring:**
- Chaque provider a un template de code commenté dans `get_service_status()` prêt à être implémenté
- Support des différents types de crédits : `money` (EUR/USD), `emails`, `sms`, `mixed`, `unlimited`
- Système d'alertes configurable basé sur des seuils de crédits
- Intégration possible avec Celery pour monitoring périodique
- Exemples de tableaux de bord Django Admin

## [0.1.0] - 2025-11-08

### Added
- Structure initiale du projet
- Modèles Django : `Missive`, `MissiveAttachment`, `MissiveEvent`, `MissiveTemplate`, `Recipient`
- Providers intégrés : SendGrid, Mailgun, Twilio, La Poste, SendinBlue, SMSPartner, Django Email, In-App
- Système de webhooks unifié
- Validation avancée (email, téléphone, adresse)
- Admin Django complet avec actions personnalisées
- Tests unitaires
- Documentation exhaustive
- Architecture modulaire avec mixins

---

**Note** : Ce fichier sera mis à jour à chaque release avec les changements importants.

