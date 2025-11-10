"""
Administration pour le modèle Missive.
"""

import json

from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..helpers import get_all_provider_choices, get_providers_from_config
from ..models import Missive, Recipient


class MissiveAdminForm(forms.ModelForm):
    """Formulaire personnalisé pour l'admin des Missives"""

    # Mapping: type de missive → providers compatibles (depuis MISSIVE_PROVIDERS)
    PROVIDERS_BY_TYPE = get_providers_from_config()

    # Tous les providers disponibles (générés depuis MISSIVE_PROVIDERS)
    PROVIDER_CHOICES = get_all_provider_choices()

    provider_choice = forms.ChoiceField(
        choices=PROVIDER_CHOICES,
        required=True,
        initial="django_email",
        label=_("Provider"),
        help_text=_(
            "Provider à utiliser pour l'envoi (filtré selon le type de missive)"
        ),
    )

    class Meta:
        model = Missive
        fields = "__all__"

    class Media:
        js = ("admin/js/missive_provider_filter.js",)

    def __init__(self, *args, **kwargs):
        # Supprimer la request non utilisée
        kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Ajouter le mapping des providers au widget pour le JavaScript
        self.fields["provider_choice"].widget.attrs["data-providers-config"] = (
            json.dumps(self.PROVIDERS_BY_TYPE)
        )

        # Si on édite une missive existante, pré-remplir le provider depuis les événements
        if self.instance.pk:
            current_provider = self.instance.provider or "django_email"
            # Vérifier si le provider actuel est dans la liste
            provider_values = [choice[0] for choice in self.PROVIDER_CHOICES]
            if current_provider not in provider_values:
                # Ajouter le provider actuel s'il n'est pas dans la liste
                self.fields["provider_choice"].choices = self.PROVIDER_CHOICES + [
                    (current_provider, f"{current_provider} (personnalisé)")
                ]
            self.fields["provider_choice"].initial = current_provider
            self.fields["provider_choice"].disabled = True
            self.fields["provider_choice"].help_text = _(
                "Le provider ne peut pas être modifié après la création. "
                "Il est défini dans l'événement d'envoi initial (voir onglet Événements)."
            )
            # Rendre sender readonly en modification
            self.fields["sender"].disabled = True
        else:
            # En création, pré-remplir avec l'expéditeur par défaut
            if not self.instance.sender_id:
                default_sender = Recipient.objects.filter(
                    is_default_sender=True
                ).first()
                if default_sender:
                    self.fields["sender"].initial = default_sender

            # Filtrer les providers selon le type de missive si un type est déjà sélectionné
            if self.instance.missive_type:
                compatible_providers = self.PROVIDERS_BY_TYPE.get(
                    self.instance.missive_type, []
                )
                self.fields["provider_choice"].choices = [
                    choice
                    for choice in self.PROVIDER_CHOICES
                    if choice[0] in compatible_providers
                ]
                # Ajuster l'initial si le provider par défaut n'est pas compatible
                if "django_email" not in compatible_providers and compatible_providers:
                    self.fields["provider_choice"].initial = compatible_providers[0]

    def save(self, commit=True):
        # Vérifier si c'est une création (avant le save)
        is_new = self.instance.pk is None

        instance = super().save(commit=commit)

        # Si c'est une nouvelle missive, créer l'événement d'envoi initial
        if commit and is_new:
            provider = self.cleaned_data.get("provider_choice") or "django_email"
            instance.create_send_event(
                provider=provider,
                status=instance.status,
                description=f"Missive créée avec le provider {provider}",
            )

        return instance


@admin.register(Missive)
class MissiveAdmin(admin.ModelAdmin):
    """Interface d'administration pour les Missives"""

    form = MissiveAdminForm
    raw_id_fields = ["recipient_user"]
    autocomplete_fields = ["sender", "recipient"]

    list_display = [
        "recipient_display_short",
        "subject",
        "missive_type_badge",
        "sender",
        "related_object_display",
        "status_badge",
        "priority_badge",
        "is_registered",
        "created_at",
        "sent_at",
    ]

    list_display_links = ["recipient_display_short"]

    list_filter = [
        "missive_type",
        "status",
        "priority",
        "is_registered",
        "requires_signature",
        "created_at",
        "sent_at",
    ]

    search_fields = [
        "subject",
        "body",
        "sender__name",
        "sender__email",
        "recipient__name",
        "recipient__email",
        "external_id",
        "content_type__model",
        "content_type__app_label",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
        "read_at",
        "proof_of_delivery_display",
    ]

    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Informations générales"),
            {
                "fields": (
                    "sender",
                    "recipient",
                    "recipient_user",
                    "subject",
                    "body",
                    "body_text",
                    "context",
                )
            },
        ),
        (
            _("Type et configuration"),
            {
                "fields": (
                    "missive_type",
                    "provider_choice",
                    "provider_options",
                    "priority",
                    "is_registered",
                    "requires_signature",
                ),
                "description": _(
                    "Le provider disponible est automatiquement filtré selon le type de missive sélectionné. "
                    "Les options du provider permettent de personnaliser l'envoi (scheduled_time, track_clicks, etc.)"
                ),
            },
        ),
        (
            _("Statut et tracking"),
            {
                "fields": (
                    "status",
                    "scheduled_at",
                    "content_type",
                    "object_id",
                    "external_id",
                    "error_message",
                ),
                "description": _(
                    "Objet source optionnel pour lier cette missive à une Commande, Participant, etc."
                ),
            },
        ),
        (
            _("Dates"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "sent_at",
                    "delivered_at",
                    "read_at",
                    "proof_of_delivery_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Métadonnées"),
            {
                "fields": (
                    "attachments_count",
                    "cost",
                    "metadata",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    actions = [
        "mark_as_sent",
        "mark_as_delivered",
        "mark_as_failed",
        "check_delivery_risk_action",
    ]

    def missive_type_badge(self, obj):
        """Badge coloré pour le type de missive"""
        colors = {
            # Courrier
            "POSTAL": "#6c757d",
            "LRE": "#495057",
            # Email
            "EMAIL": "#0d6efd",
            # SMS et évolutions
            "SMS": "#198754",
            "RCS": "#20c997",
            # Vocal
            "VOICE_CALL": "#6f42c1",
            # Notifications
            "NOTIFICATION": "#fd7e14",
            "PUSH_NOTIFICATION": "#dc3545",
            # Messageries d'applications (type générique)
            "BRANDED": "#9b59b6",
        }
        color = colors.get(obj.missive_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold; white-space: nowrap;">{}</span>',
            color,
            obj.get_missive_type_display(),
        )

    missive_type_badge.short_description = _("Type")

    def status_badge(self, obj):
        """Badge coloré pour le statut"""
        colors = {
            "DRAFT": "#6c757d",
            "PENDING": "#ffc107",
            "PROCESSING": "#0dcaf0",
            "SENT": "#0d6efd",
            "DELIVERED": "#198754",
            "READ": "#20c997",
            "FAILED": "#dc3545",
            "CANCELLED": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold; white-space: nowrap;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = _("Statut")

    def priority_badge(self, obj):
        """Badge pour la priorité"""
        colors = {
            "LOW": "#6c757d",
            "NORMAL": "#0d6efd",
            "HIGH": "#ffc107",
            "URGENT": "#dc3545",
        }
        color = colors.get(obj.priority, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 10px; white-space: nowrap;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    priority_badge.short_description = _("Priorité")

    def recipient_display_short(self, obj):
        """Affichage court du destinataire"""
        display = obj.recipient_display
        if len(display) > 30:
            return display[:27] + "..."
        return display

    recipient_display_short.short_description = _("Destinataire")

    def related_object_display(self, obj):
        """Affichage de l'objet lié"""
        if obj.content_object:
            try:
                content_type = obj.content_type
                url = reverse(
                    f"admin:{content_type.app_label}_{content_type.model}_change",
                    args=[obj.object_id],
                )
                label = str(obj.content_object)
                if len(label) > 30:
                    label = label[:27] + "..."
                return format_html('<a href="{}">{}</a>', url, label)
            except Exception:
                label = str(obj.content_object)
                if len(label) > 30:
                    label = label[:27] + "..."
                return label
        return "-"

    related_object_display.short_description = _("Objet lié")

    def proof_of_delivery_display(self, obj):
        """Affiche tous les liens vers les preuves de dépôt disponibles"""
        if not obj.pk:  # Nouvelle missive
            return "-"

        try:
            proofs = obj.get_proofs_of_delivery()

            if not proofs:
                # Vérifier si le service génère des preuves
                provider_instance = self._get_provider_instance(obj)
                if provider_instance:
                    available_proofs = provider_instance.list_available_proofs()
                    service_type = provider_instance._detect_service_type()

                    if available_proofs.get(service_type):
                        return format_html(
                            '<span style="color: #ffc107; white-space: nowrap;">⏳ En attente</span>'
                        )

                return format_html(
                    '<span style="color: #ccc; white-space: nowrap;">Non disponible</span>'
                )

            # Afficher toutes les preuves
            proof_badges = []
            for proof in proofs:
                proof_label = proof.get("label", proof.get("type", "Preuve"))
                proof_format = proof.get("format", "pdf").upper()
                url = proof.get("url")
                available = proof.get("available", False)

                if available and url:
                    # Badge vert cliquable
                    proof_badges.append(
                        '<a href="{}" target="_blank" style="display: inline-block; margin: 2px;">'
                        '<span style="background-color: #198754; color: white; padding: 3px 8px; '
                        'border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap;">'
                        "📄 {} ({})</span></a>".format(url, proof_label, proof_format)
                    )
                elif available:
                    # Disponible mais sans URL
                    proof_badges.append(
                        '<span style="background-color: #198754; color: white; padding: 3px 8px; '
                        "border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap; "
                        'display: inline-block; margin: 2px;">✓ {}</span>'.format(
                            proof_label
                        )
                    )
                else:
                    # En attente
                    message = proof.get("metadata", {}).get("message", "En attente")
                    proof_badges.append(
                        '<span style="background-color: #ffc107; color: black; padding: 3px 8px; '
                        "border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap; "
                        'display: inline-block; margin: 2px;" title="{}">⏳ {}</span>'.format(
                            message, proof_label
                        )
                    )

            return format_html("".join(proof_badges))

        except Exception as e:
            return format_html(
                '<span style="color: #dc3545; white-space: nowrap;" title="{}">❌ Erreur</span>',
                str(e),
            )

    proof_of_delivery_display.short_description = _("Preuves de dépôt")

    def _get_provider_instance(self, obj):
        """Récupère une instance du provider pour cette missive"""
        try:
            from django.utils.module_loading import import_string

            provider_name = obj.provider
            if not provider_name:
                return None

            # Chercher le provider dans la config
            providers_config = getattr(settings, "MISSIVE_PROVIDERS", {})
            provider_path = None

            for missive_type, providers_list in providers_config.items():
                for prov in providers_list:
                    if provider_name.lower() in prov.lower():
                        provider_path = prov
                        break
                if provider_path:
                    break

            if not provider_path:
                provider_path = f"missive.providers.{provider_name.lower()}.{provider_name.capitalize()}Provider"

            provider_class = import_string(provider_path)
            return provider_class(missive=obj)

        except Exception:
            return None

    @admin.action(description=_("Marquer comme envoyé"))
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status="SENT", sent_at=timezone.now())
        self.message_user(
            request, _(f"{updated} missive(s) marquée(s) comme envoyée(s).")
        )

    @admin.action(description=_("Marquer comme délivré"))
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status="DELIVERED", delivered_at=timezone.now())
        self.message_user(
            request, _(f"{updated} missive(s) marquée(s) comme délivrée(s).")
        )

    @admin.action(description=_("Marquer comme échoué"))
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="FAILED")
        self.message_user(
            request, _(f"{updated} missive(s) marquée(s) comme échouée(s).")
        )

    @admin.action(description=_("🔍 Analyser le risque d'échec"))
    def check_delivery_risk_action(self, request, queryset):
        """Action pour analyser le risque d'échec des missives sélectionnées"""
        from ..sender import MissiveSender

        low_risk = 0
        medium_risk = 0
        high_risk = 0
        critical_risk = 0

        for missive in queryset:
            sender = MissiveSender()
            risk_level = sender.check_delivery_risk(missive)

            if risk_level == "LOW":
                low_risk += 1
            elif risk_level == "MEDIUM":
                medium_risk += 1
            elif risk_level == "HIGH":
                high_risk += 1
            elif risk_level == "CRITICAL":
                critical_risk += 1

        self.message_user(
            request,
            format_html(
                "🔍 <strong>Analyse de risque terminée</strong><br>"
                "✅ {} missive(s) à risque <strong>faible</strong><br>"
                "⚠️ {} missive(s) à risque <strong>moyen</strong><br>"
                "⚠️ {} missive(s) à risque <strong>élevé</strong><br>"
                "🔴 {} missive(s) à risque <strong>critique</strong>",
                low_risk,
                medium_risk,
                high_risk,
                critical_risk,
            ),
        )
