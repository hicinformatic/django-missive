"""
Administration pour le modèle virtuel ProviderInfo.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from ..models import MissiveType, ProviderInfo
from ..models.provider import ProviderInfoQuerySet


class MissiveTypeFilter(admin.SimpleListFilter):
    """Filtre personnalisé pour afficher les types avec leurs labels traduits"""

    title = _("Type de missive")
    parameter_name = "missive_type"

    def lookups(self, request, model_admin):
        """Retourne les choix avec les labels traduits"""
        return [(choice.value, choice.label) for choice in MissiveType]

    def queryset(self, request, queryset):
        """Filtre le queryset selon le type sélectionné"""
        if self.value():
            # Filtrer les providers qui supportent ce type (cherche dans la liste CSV)
            filtered = []
            for provider in queryset:
                if self.value() in provider.missive_types_list:
                    filtered.append(provider)
            return ProviderInfoQuerySet(
                model=queryset.model,
                data=filtered,
                query=queryset.query,
                using=queryset._db,
                hints=queryset._hints,
            )
        return queryset


@admin.register(ProviderInfo)
class ProviderInfoAdmin(admin.ModelAdmin):
    """Admin en lecture seule pour voir l'état des providers"""

    class Media:
        js = ("admin/js/config_vars_toggle.js",)

    ordering = ["name"]  # Tri alphabétique par nom de provider

    list_display = [
        "name_display",
        "missive_type_display",
        "brands_display",
        "status_display",
        "usage_display",
        "requirements_file",
    ]

    list_filter = [MissiveTypeFilter]

    search_fields = ["name", "missive_type"]

    readonly_fields = [
        "name",
        "missive_type_display_detail",
        "brands_display",
        "status_display_detail",
        "config_vars_display_detail",
        "installation_display",
        "configuration_display",
        "webhook_urls_display",
        "site_url_display",
        "status_url_display",
        "documentation_url_display",
        "usage_count",
        "requirements_file",
    ]

    def get_fieldsets(self, request, obj=None):
        """Génère les fieldsets dynamiquement en fonction des types de missive"""
        if obj is None:
            return [
                (_("Informations générales"), {"fields": ("name",)}),
            ]

        # Fieldsets de base
        fieldsets = [
            (
                _("Informations générales"),
                {
                    "fields": (
                        "name",
                        "site_url_display",
                        "missive_type_display_detail",
                        "brands_display",
                        "status_display_detail",
                    )
                },
            ),
        ]

        # Ajouter une section par type de missive pour les crédits
        missive_types = obj.missive_types_list
        for missive_type in missive_types:
            # Récupérer le label traduit
            try:
                label = MissiveType(missive_type).label
            except ValueError:
                label = missive_type

            # Créer un nom de méthode unique pour ce type
            field_name = f"credits_{missive_type.lower()}_display"

            # Ajouter la section
            fieldsets.append(
                (
                    label,
                    {
                        "fields": (field_name,),
                        "description": f"Crédits et informations pour {label}",
                    },
                )
            )

        # Sections restantes
        fieldsets.extend(
            [
                (
                    _("Configuration"),
                    {
                        "fields": (
                            "documentation_url_display",
                            "config_vars_display_detail",
                            "webhook_urls_display",
                        ),
                        "description": _(
                            "Variables d'environnement et URLs de webhook pour ce provider"
                        ),
                    },
                ),
                (
                    _("État du service"),
                    {
                        "fields": (
                            "installation_display",
                            "configuration_display",
                            "status_url_display",
                        )
                    },
                ),
                (_("Statistiques"), {"fields": ("usage_count", "requirements_file")}),
            ]
        )

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Ajoute dynamiquement les champs readonly pour chaque type de missive"""
        readonly = list(self.readonly_fields)

        if obj:
            # Ajouter les champs de crédits pour chaque type
            for missive_type in obj.missive_types_list:
                field_name = f"credits_{missive_type.lower()}_display"
                if field_name not in readonly:
                    readonly.append(field_name)

        return readonly

    def __getattr__(self, name):
        """Génère dynamiquement les méthodes credits_{type}_display"""
        if name.startswith("credits_") and name.endswith("_display"):
            # Extraire le type de missive
            missive_type = name[8:-8].upper()  # Enlever 'credits_' et '_display'

            def credits_method(obj):
                # Récupérer les crédits en temps réel depuis le provider
                try:
                    provider_class = obj._get_provider_class()
                    if provider_class:
                        # Instancier le provider (sans missive pour juste récupérer le statut)
                        provider_instance = provider_class()

                        # Mapper le type de missive à la méthode get_*_service_info()
                        method_map = {
                            "SMS": "get_sms_service_info",
                            "EMAIL": "get_email_service_info",
                            "POSTAL": "get_postal_service_info",
                            "VOICE_CALL": "get_voice_call_service_info",
                            "NOTIFICATION": "get_notification_service_info",
                            "PUSH_NOTIFICATION": "get_notification_service_info",
                            "BRANDED": "get_branded_service_info",  # Utilise la méthode générique
                        }

                        method_name = method_map.get(missive_type)

                        if method_name and hasattr(provider_instance, method_name):
                            # Appeler la méthode spécifique au type
                            service_info = getattr(provider_instance, method_name)()
                        else:
                            # Pas de méthode spécifique implémentée
                            service_info = {
                                "credits": "Non implémenté",
                                "credits_type": "unknown",
                                "is_available": None,
                                "warnings": [
                                    f"Méthode {method_name} non implémentée pour {provider_instance.name}"
                                ],
                            }

                        # Récupérer les crédits
                        credits = service_info.get("credits")
                        is_available = service_info.get("is_available")
                        warnings = service_info.get("warnings", [])

                        # Construire l'affichage
                        credits_html = ""

                        if credits is not None:
                            # Afficher les crédits (déjà formatés par la méthode)
                            credits_html = format_html(
                                '<p style="font-size: 20px; font-weight: bold; color: #198754; margin: 10px 0;">{}</p>',
                                str(credits),
                            )
                        else:
                            # Pas de crédits disponibles
                            credits_html = format_html(
                                '<p style="color: #6c757d; font-style: italic; font-size: 16px; margin: 10px 0;">Crédits non disponibles</p>'
                            )

                        # Ajouter le statut de disponibilité
                        if is_available is not None:
                            if is_available:
                                credits_html += format_html(
                                    '<p style="margin: 5px 0; font-size: 14px;"><span style="color: #198754;">✓ Service disponible</span></p>'
                                )
                            else:
                                credits_html += format_html(
                                    '<p style="margin: 5px 0; font-size: 14px;"><span style="color: #dc3545;">✗ Service indisponible</span></p>'
                                )

                        # Ajouter les avertissements (toujours, même si credits est None)
                        if warnings:
                            warnings_html = "<br>".join(
                                [
                                    f'<span style="color: #ffc107;">{w}</span>'
                                    for w in warnings
                                ]
                            )
                            credits_html += format_html(
                                '<p style="margin: 10px 0; font-size: 13px;">{}</p>',
                                mark_safe(warnings_html),
                            )

                        return credits_html
                    else:
                        return format_html(
                            '<p style="color: #6c757d; font-style: italic; margin: 0;">Provider non chargé</p>'
                        )

                except Exception as e:
                    return format_html(
                        '<p style="color: #dc3545; margin: 0;">Erreur : {}</p>', str(e)
                    )

            credits_method.short_description = _("Crédits disponibles")
            return credits_method

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def has_add_permission(self, request):
        """Pas de création manuelle"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Pas de suppression"""
        return False

    def has_change_permission(self, request, obj=None):
        """Autoriser la visualisation mais pas la modification"""
        return True

    def get_search_results(self, request, queryset, search_term):
        """
        Implémente la recherche manuelle car on utilise un QuerySet custom.
        """
        if not search_term:
            return queryset, False

        # Recherche dans le nom et les types de missive
        search_term_lower = search_term.lower()
        filtered = []

        for provider in queryset:
            # Rechercher dans le nom
            if search_term_lower in provider.name.lower():
                filtered.append(provider)
                continue

            # Rechercher dans les types de missive supportés
            if search_term_lower in provider.missive_type.lower():
                filtered.append(provider)
                continue

            # Rechercher dans la liste des types (CSV)
            for missive_type in provider.missive_types_list:
                if search_term_lower in missive_type.lower():
                    filtered.append(provider)
                    break

        # Retourner un nouveau QuerySet avec les résultats filtrés
        from ..models.provider import ProviderInfoQuerySet

        filtered_qs = ProviderInfoQuerySet(
            model=queryset.model,
            data=filtered,
            query=queryset.query,
            using=queryset._db,
            hints=queryset._hints,
        )

        return filtered_qs, False

    def name_display(self, obj):
        """Affiche le nom du provider avec sa description"""
        description = obj.description_text
        if description:
            return format_html(
                '<strong>{}</strong><br><span style="color: #6c757d; font-size: 11px; font-style: italic;">{}</span>',
                obj.name.capitalize(),
                description,
            )
        else:
            return format_html("<strong>{}</strong>", obj.name.capitalize())

    name_display.short_description = _("Provider")

    def missive_type_display(self, obj):
        """Badges colorés pour tous les types supportés"""
        colors = {
            "POSTAL": "#6c757d",
            "LRE": "#495057",
            "EMAIL": "#0d6efd",
            "SMS": "#198754",
            "RCS": "#20c997",
            "VOICE_CALL": "#6f42c1",
            "NOTIFICATION": "#fd7e14",
            "PUSH_NOTIFICATION": "#dc3545",
            "BRANDED": "#9b59b6",  # Purple pour toutes les messageries d'applications
        }

        # Afficher tous les types supportés
        badges = []
        for missive_type in obj.missive_types_list:
            color = colors.get(missive_type, "#6c757d")

            # Récupérer le label traduit depuis MissiveType
            try:
                label = MissiveType(missive_type).label
            except ValueError:
                label = missive_type

            badges.append(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                "border-radius: 3px; font-size: 10px; font-weight: bold; "
                'margin: 2px; display: inline-block; white-space: nowrap;">{}</span>'.format(
                    color, label
                )
            )

        return format_html(" ".join(badges))

    missive_type_display.short_description = _("Types supportés")

    def missive_type_display_detail(self, obj):
        """Affiche les types de missive avec labels traduits dans la page de détail"""
        return self.missive_type_display(obj)

    missive_type_display_detail.short_description = _("Types supportés")

    def brands_display(self, obj):
        """Affiche les marques de messagerie supportées (pour providers BRANDED)"""
        brands = obj.brands

        if not brands:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">—</span>'
            )

        # Couleurs pour les brands
        brand_colors = {
            "whatsapp": "#25D366",
            "slack": "#4A154B",
            "teams": "#6264A7",
            "telegram": "#0088cc",
            "messenger": "#0084FF",
            "signal": "#3A76F0",
            "discord": "#5865F2",
        }

        badges = []
        for brand in brands:
            color = brand_colors.get(brand.lower(), "#6c757d")
            badges.append(
                f'<span style="background-color: {color}; color: white; padding: 3px 10px; '
                f"border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 4px; "
                f'white-space: nowrap;">{brand.upper()}</span>'
            )

        return format_html(
            '<span style="white-space: nowrap;">{}</span>', mark_safe("".join(badges))
        )

    brands_display.short_description = _("Marques supportées")

    def status_display(self, obj):
        """Badge pour le statut global"""
        if obj.status == "ready":
            return format_html(
                '<span style="background-color: #d1e7dd; color: #0f5132; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">✅ Prêt</span>'
            )
        elif obj.status == "needs_config":
            return format_html(
                '<span style="background-color: #fff3cd; color: #664d03; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">⚠️ Config requise</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #f8d7da; color: #842029; padding: 5px 12px; '
                'border-radius: 4px; font-size: 12px; font-weight: bold; white-space: nowrap;">❌ Non installé</span>'
            )

    status_display.short_description = _("Statut")

    def credits_display(self, obj):
        """Affiche les crédits disponibles"""
        credits_info = obj.credits_info

        if not credits_info:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">-</span>'
            )

        credit_type = credits_info.get("type")
        remaining = credits_info.get("remaining")
        currency = credits_info.get("currency", "")

        if remaining is None:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">-</span>'
            )

        # Formatage selon le type
        if credit_type == "money":
            # Crédits en euros
            if remaining < 10:
                color = "#dc3545"  # Rouge
            elif remaining < 50:
                color = "#ffc107"  # Orange
            else:
                color = "#198754"  # Vert

            return format_html(
                '<span style="color: {}; font-weight: bold; white-space: nowrap;">{:.2f} {}</span>',
                color,
                remaining,
                currency,
            )
        elif credit_type == "count" or credit_type == "sms_units":
            # Crédits en unités (SMS, etc.)
            if remaining < 100:
                color = "#dc3545"  # Rouge
            elif remaining < 500:
                color = "#ffc107"  # Orange
            else:
                color = "#198754"  # Vert

            return format_html(
                '<span style="color: {}; font-weight: bold; white-space: nowrap;">{} SMS</span>',
                color,
                int(remaining),
            )
        elif credit_type == "unlimited":
            return format_html(
                '<span style="color: #198754; font-weight: bold; white-space: nowrap;">∞ Illimité</span>'
            )
        else:
            # Type mixte ou inconnu
            return format_html(
                '<span style="white-space: nowrap;">{}</span>', str(remaining)
            )

    credits_display.short_description = _("Crédits")

    def installation_display(self, obj):
        """Affiche les packages requis et leur statut d'installation individuel"""
        packages = obj.required_packages

        if packages:
            # Vérifier le statut de chaque package individuellement
            package_statuses = []
            for package in packages:
                try:
                    __import__(package)
                    # Package installé : icône verte + nom normal
                    package_statuses.append(
                        f'<span style="color: #198754;">✓</span> <code>{package}</code>'
                    )
                except ImportError:
                    # Package manquant : icône rouge + nom en rouge
                    package_statuses.append(
                        f'<span style="color: #dc3545;">✗ <code style="color: #dc3545;">{package}</code></span>'
                    )

            # Joindre tous les packages avec leur statut
            return format_html(
                '<span style="white-space: nowrap;">{}</span>',
                mark_safe(", ".join(package_statuses)),
            )
        else:
            # Pas de package requis (toujours disponible)
            return format_html(
                '<span style="color: #6c757d; white-space: nowrap; font-style: italic;">Aucun (toujours dispo)</span>'
            )

    installation_display.short_description = _("Packages")

    def configuration_display(self, obj):
        """Indique si les credentials sont configurés"""
        if obj.is_configured:
            return format_html(
                '<span style="color: #198754; white-space: nowrap;">✓ Configuré</span>'
            )
        else:
            return format_html(
                '<span style="color: #ffc107; white-space: nowrap;">✗ Manquant</span>'
            )

    configuration_display.short_description = _("Credentials")

    def status_url_display(self, obj):
        """Affiche le lien vers la page de statut/SLA du provider"""
        url = obj.status_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">🔗 Page de statut</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Non disponible</span>'
            )

    status_url_display.short_description = _("Statut SLA")

    def documentation_url_display(self, obj):
        """Affiche le lien vers la documentation API du provider"""
        url = obj.documentation_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">📖 Documentation API</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Non disponible</span>'
            )

    def site_url_display(self, obj):
        """Affiche le lien vers le site web officiel du provider"""
        url = obj.site_url

        if url:
            return format_html(
                '<a href="{}" target="_blank" style="white-space: nowrap;">'
                '<span style="color: #0d6efd;">🌐 Site officiel</span>'
                "</a>",
                url,
            )
        else:
            return format_html(
                '<span style="color: #6c757d; font-style: italic; white-space: nowrap;">Non disponible</span>'
            )

    site_url_display.short_description = _("Site officiel")
    documentation_url_display.short_description = _("Documentation")

    def webhook_urls_display(self, obj):
        """Affiche les URLs de webhook pour chaque type de service supporté"""
        from django.conf import settings

        types = obj.missive_types_list
        if not types:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">Aucun service configuré</span>'
            )

        # Mapping des types de missive vers des noms lisibles
        type_labels = {
            "EMAIL": "📧 Email",
            "SMS": "📱 SMS",
            "VOICE_CALL": "📞 Appel vocal",
            "BRANDED": "💬 Messageries",
            "POSTAL": "📮 Courrier",
            "LRE": "📨 LRE",
            "NOTIFICATION": "🔔 Notification",
            "PUSH_NOTIFICATION": "📲 Push",
            "RCS": "💬 RCS",
        }

        # Récupérer le domaine de base depuis la config
        base_domain = getattr(
            settings, "MISSIVE_WEBHOOK_BASE_URL", "https://example.com"
        )
        # Retirer le slash final si présent
        base_domain = base_domain.rstrip("/")

        # Construire les URLs de webhook
        provider_slug = obj.name.lower().replace(" ", "")

        html_parts = []
        html_parts.append('<div style="margin-top: 5px;">')

        for missive_type in types:
            label = type_labels.get(missive_type, missive_type)
            # URL spécifique par type
            type_slug = missive_type.lower().replace("_", "-")
            webhook_url = f"{base_domain}/webhooks/{provider_slug}/{type_slug}/"

            html_parts.append(
                f'<div style="margin-bottom: 8px; padding: 8px; background: #f8f9fa; border-left: 3px solid #0d6efd; border-radius: 3px;">'
                f'<div style="font-weight: 500; color: #495057; margin-bottom: 4px;">{label}</div>'
                f'<code style="background: #fff; padding: 4px 8px; border-radius: 3px; font-size: 11px; color: #0d6efd;">{webhook_url}</code>'
                f"</div>"
            )

        html_parts.append("</div>")

        # Note d'aide avec info sur la config
        if base_domain == "https://example.com":
            note_color = "#dc3545"  # Rouge si pas configuré
            note_icon = "⚠️"
            note_text = (
                f"{note_icon} <strong>Configuration requise:</strong> "
                f"Ajoutez <code>MISSIVE_WEBHOOK_BASE_URL = 'https://votre-domaine.com'</code> "
                f"dans settings.py pour obtenir les vraies URLs."
            )
        else:
            note_color = "#856404"  # Jaune si configuré
            note_icon = "💡"
            note_text = (
                f"{note_icon} <strong>Note:</strong> Configurez ces URLs dans le dashboard de votre provider "
                f"pour recevoir les notifications de statut."
            )

        html_parts.append(
            f'<div style="margin-top: 10px; padding: 8px; background: #fff3cd; border-left: 3px solid #ffc107; border-radius: 3px;">'
            f'<small style="color: {note_color};">{note_text}</small>'
            f"</div>"
        )

        return format_html("".join(html_parts))

    webhook_urls_display.short_description = _("URLs de Webhook")

    def usage_display(self, obj):
        """Affiche le nombre d'utilisations"""
        count = obj.usage_count
        if count > 0:
            return format_html(
                '<strong style="white-space: nowrap;">{}</strong> utilisation{}',
                count,
                "s" if count > 1 else "",
            )
        else:
            return format_html(
                '<span style="color: #ccc; white-space: nowrap;">Jamais utilisé</span>'
            )

    usage_display.short_description = _("Utilisation")

    def status_display_detail(self, obj):
        """Affiche le statut détaillé dans la page de changement"""
        return self.status_display(obj)

    status_display_detail.short_description = _("Statut")

    def config_vars_display(self, obj):
        """Affiche les variables de configuration dans la liste"""
        config_vars = obj.required_config_keys

        if not config_vars:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">Aucune</span>'
            )

        # Créer une liste des variables dans des balises <code>
        vars_list = []
        for var in config_vars:
            vars_list.append(format_html("<code>{}</code>", var))

        return format_html(
            '<span style="white-space: nowrap;">{}</span>',
            mark_safe(", ".join(vars_list)),
        )

    config_vars_display.short_description = _("Variables")

    def config_vars_display_detail(self, obj):
        """Affiche toutes les variables de configuration dans la page de changement"""
        config_vars = obj.required_config_keys

        if not config_vars:
            return format_html(
                '<p style="color: #666;">Aucune configuration spécifique requise pour ce provider.</p>'
            )

        # Récupérer le statut de chaque variable
        config_status = obj.config_status

        rows = []
        for var_name in config_vars:
            status = config_status.get(var_name, {})
            is_configured = status.get("configured", False)

            if is_configured:
                # Variable configurée
                icon = '<span style="color: #198754; font-weight: bold;">✓</span>'
                status_text = '<span style="color: #198754;">Configurée</span>'
                actual_value = str(status.get("value", ""))
                # Masquer la valeur par défaut avec une icône pour l'afficher
                value_html = (
                    '<span class="config-eye" data-var="{}" style="cursor: pointer; color: #6c757d; margin-right: 8px;" '
                    'title="Cliquer pour afficher/masquer">👁️</span>'
                    '<span class="config-value-masked" data-var="{}" style="color: #6c757d;">••••••••</span>'
                    '<span class="config-value-revealed" data-var="{}" style="display: none;"><code>{}</code></span>'
                ).format(var_name, var_name, var_name, actual_value)
            else:
                # Variable manquante
                # Cas spécial pour SMSPARTNER_WEBHOOK_IPS : afficher la valeur par défaut
                if var_name == "SMSPARTNER_WEBHOOK_IPS":
                    icon = '<span style="color: #0d6efd; font-weight: bold;">ℹ️</span>'
                    status_text = '<span style="color: #0d6efd;">Par défaut</span>'
                    value_html = (
                        '<code style="color: #0d6efd;">185.66.232.0/24</code> '
                        '<small style="color: #6c757d;">(plage officielle SMSPartner)</small>'
                    )
                else:
                    icon = '<span style="color: #dc3545; font-weight: bold;">✗</span>'
                    status_text = '<span style="color: #dc3545;">Manquante</span>'
                    value_html = "<code>Non définie</code>"

            rows.append(
                "<tr>"
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;"><code>{}</code></td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                '<td style="padding: 8px; border-bottom: 1px solid #ddd;">{}</td>'
                "</tr>".format(icon, var_name, status_text, value_html)
            )

        table_html = """
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6; width: 30px;"></th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Variable</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Statut</th>
                    <th style="padding: 10px; text-align: left; border-bottom: 2px solid #dee2e6;">Valeur</th>
                </tr>
            </thead>
            <tbody>
                {}
            </tbody>
        </table>
        <p style="margin-top: 15px; padding: 10px; background-color: #cfe2ff; border-left: 4px solid #0d6efd; color: #084298;">
            <strong>💡 Pour configurer :</strong> Éditez le fichier <code>.env</code> à la racine du projet et redémarrez le serveur.
        </p>
        """.format(
            "".join(rows)
        )

        return format_html(table_html)

    config_vars_display_detail.short_description = _("Variables de configuration")

    def changelist_view(self, request, extra_context=None):
        """Ajoute du contexte à la vue de liste"""
        extra_context = extra_context or {}

        # Ajouter des statistiques globales
        from ..models import Missive

        extra_context["total_missives"] = Missive.objects.count()

        # Compter les providers par statut
        all_providers = list(ProviderInfo.objects.all())
        extra_context["ready_count"] = sum(
            1 for p in all_providers if p.status == "ready"
        )
        extra_context["needs_config_count"] = sum(
            1 for p in all_providers if p.status == "needs_config"
        )
        extra_context["not_installed_count"] = sum(
            1 for p in all_providers if p.status == "not_installed"
        )

        return super().changelist_view(request, extra_context)
