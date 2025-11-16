"""Administration du modèle Missive."""

import json

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..decorators import sandbox_warning, library_presence_warning
from ..helpers import get_all_provider_choices, get_providers_from_config
from ..models import Missive, Recipient


class MissiveAdminForm(forms.ModelForm):
    """Formulaire personnalisé pour l'admin Missive."""

    PROVIDERS_BY_TYPE = get_providers_from_config()
    PROVIDER_CHOICES = get_all_provider_choices()

    provider_choice = forms.ChoiceField(
        choices=PROVIDER_CHOICES,
        required=True,
        initial="django_email",
        label=_("Provider"),
        help_text=_(
            "Provider to use for sending (filtered according to missive type)"
        ),
    )

    class Meta:
        model = Missive
        fields = "__all__"

    class Media:
        js = ("admin/js/missive_provider_filter.js",)

    def __init__(self, *args, **kwargs):
        kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields["provider_choice"].widget.attrs["data-providers-config"] = (
            json.dumps(self.PROVIDERS_BY_TYPE)
        )

        if self.instance.pk:
            current_provider = self.instance.provider or "django_email"
            provider_values = [choice[0] for choice in self.PROVIDER_CHOICES]
            if current_provider not in provider_values:
                self.fields["provider_choice"].choices = self.PROVIDER_CHOICES + [
                    (current_provider, f"{current_provider} (custom)")
                ]
            self.fields["provider_choice"].initial = current_provider
            self.fields["provider_choice"].help_text = _(
                "Provider used for sending. Change it if necessary before sending."
            )
            self.fields["sender"].disabled = True
        else:
            if not self.instance.sender_id:
                default_sender = Recipient.objects.filter(
                    is_default_sender=True
                ).first()
                if default_sender:
                    self.fields["sender"].initial = default_sender

            if self.instance.missive_type:
                compatible_providers = self.PROVIDERS_BY_TYPE.get(
                    self.instance.missive_type, []
                )
                self.fields["provider_choice"].choices = [
                    choice
                    for choice in self.PROVIDER_CHOICES
                    if choice[0] in compatible_providers
                ]
                if "django_email" not in compatible_providers and compatible_providers:
                    self.fields["provider_choice"].initial = compatible_providers[0]

    def save(self, commit=True):
        is_new = self.instance.pk is None
        instance = super().save(commit=commit)

        if commit and is_new:
            provider = self.cleaned_data.get("provider_choice") or "django_email"
            instance.create_send_event(
                provider=provider,
                status=instance.status,
                description=f"Missive created with provider {provider}",
            )

        return instance


@sandbox_warning
@library_presence_warning  # warns if 'python_missive' is not installed
@admin.register(Missive)
class MissiveAdmin(admin.ModelAdmin):
    """Interface d'administration pour les Missives."""

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
            _("General Information"),
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
            _("Type and Configuration"),
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
                    "The available provider is automatically filtered according to the selected missive type. "
                    "Provider options allow you to customize the sending (scheduled_time, track_clicks, etc.)"
                ),
            },
        ),
        (
            _("Status and Tracking"),
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
                    "Optional source object to link this missive to an Order, Participant, etc."
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
            _("Metadata"),
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
        "send_now_action",
        "mark_as_sent",
        "mark_as_delivered",
        "mark_as_failed",
        "check_delivery_risk_action",
    ]

    def missive_type_badge(self, obj):
        """Badge coloré pour le type de missive."""
        colors = {
            # Postal
            "POSTAL": "#6c757d",
            "LRE": "#495057",
            # Email
            "EMAIL": "#0d6efd",
            # SMS and evolutions
            "SMS": "#198754",
            "RCS": "#20c997",
            # Voice
            "VOICE_CALL": "#6f42c1",
            # Notifications
            "NOTIFICATION": "#fd7e14",
            "PUSH_NOTIFICATION": "#dc3545",
            # Branded messaging apps (generic type)
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
        """Badge coloré pour le statut."""
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

    status_badge.short_description = _("Status")

    def priority_badge(self, obj):
        """Badge pour la priorité."""
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

    priority_badge.short_description = _("Priority")

    def recipient_display_short(self, obj):
        """Affichage court du destinataire."""
        display = obj.recipient_display
        if len(display) > 30:
            return display[:27] + "..."
        return display

    recipient_display_short.short_description = _("Recipient")

    def related_object_display(self, obj):
        """Displays related object."""
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

    related_object_display.short_description = _("Related Object")

    def proof_of_delivery_display(self, obj):
        """Displays all proof of delivery links."""
        if not obj.pk:
            return "-"

        try:
            proofs = obj.get_proofs_of_delivery()

            if not proofs:
                provider_instance = self._get_provider_instance(obj)
                if provider_instance:
                    available_proofs = provider_instance.list_available_proofs()
                    service_type = provider_instance._detect_service_type()

                    if available_proofs.get(service_type):
                        return format_html(
                            '<span style="color: #ffc107; white-space: nowrap;">⏳ Pending</span>'
                        )

                return format_html(
                    '<span style="color: #ccc; white-space: nowrap;">Not available</span>'
                )

            proof_badges = []
            for proof in proofs:
                proof_label = proof.get("label", proof.get("type", "Proof"))
                proof_format = proof.get("format", "pdf").upper()
                url = proof.get("url")
                available = proof.get("available", False)

                if available and url:
                    proof_badges.append(
                        '<a href="{}" target="_blank" style="display: inline-block; margin: 2px;">'
                        '<span style="background-color: #198754; color: white; padding: 3px 8px; '
                        'border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap;">'
                        "📄 {} ({})</span></a>".format(url, proof_label, proof_format)
                    )
                elif available:
                    proof_badges.append(
                        '<span style="background-color: #198754; color: white; padding: 3px 8px; '
                        "border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap; "
                        'display: inline-block; margin: 2px;">✓ {}</span>'.format(
                            proof_label
                        )
                    )
                else:
                    message = proof.get("metadata", {}).get("message", "Pending")
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
                '<span style="color: #dc3545; white-space: nowrap;" title="{}">❌ Error</span>',
                str(e),
            )

    proof_of_delivery_display.short_description = _("Proof of Delivery")

    def _get_provider_instance(self, obj):
        """Gets provider instance for this missive."""
        try:
            from django.utils.module_loading import import_string

            provider_name = obj.provider
            if not provider_name:
                return None

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

    @admin.action(description=_("🚀 Send Now"))
    def send_now_action(self, request, queryset):
        """Action pour envoyer les missives sélectionnées immédiatement."""
        from ..sender import MissiveSender

        sender = MissiveSender()
        success_count = 0
        error_count = 0
        errors = []

        for missive in queryset:
            if missive.status in ["SENT", "DELIVERED", "READ"]:
                error_count += 1
                errors.append(
                    f"Missive #{missive.id} already sent (status: {missive.get_status_display()})"
                )
                continue

            if missive.status == "CANCELLED":
                error_count += 1
                errors.append(
                    f"Missive #{missive.id} cancelled, cannot be sent"
                )
                continue

            try:
                if sender.send(missive):
                    success_count += 1
                    self.message_user(
                        request,
                        _(f"✅ Missive #{missive.id} sent successfully!"),
                        level="success",
                    )
                else:
                    error_count += 1
                    error_msg = missive.error_message or "Unknown error"
                    errors.append(f"Missive #{missive.id}: {error_msg}")
            except Exception as e:
                error_count += 1
                errors.append(f"Missive #{missive.id}: {str(e)}")

        if success_count > 0:
            self.message_user(
                request,
                _(f"🎉 {success_count} missive(s) sent successfully!"),
                level="success",
            )

        if error_count > 0:
            self.message_user(
                request,
                _(
                    f"⚠️ {error_count} error(s): "
                    + " | ".join(errors[:5])
                    + ("..." if len(errors) > 5 else "")
                ),
                level="warning",
            )

    @admin.action(description=_("Mark as Sent"))
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status="SENT", sent_at=timezone.now())
        self.message_user(
            request, _(f"{updated} missive(s) marked as sent.")
        )

    @admin.action(description=_("Mark as Delivered"))
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status="DELIVERED", delivered_at=timezone.now())
        self.message_user(
            request, _(f"{updated} missive(s) marked as delivered.")
        )

    @admin.action(description=_("Mark as Failed"))
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status="FAILED")
        self.message_user(
            request, _(f"{updated} missive(s) marked as failed.")
        )

    @admin.action(description=_("🔍 Analyze Delivery Risk"))
    def check_delivery_risk_action(self, request, queryset):
        """Action pour analyser le risque de livraison des missives sélectionnées."""
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
                "🔍 <strong>Risk analysis complete</strong><br>"
                "✅ {} missive(s) with <strong>low</strong> risk<br>"
                "⚠️ {} missive(s) with <strong>medium</strong> risk<br>"
                "⚠️ {} missive(s) with <strong>high</strong> risk<br>"
                "🔴 {} missive(s) with <strong>critical</strong> risk",
                low_risk,
                medium_risk,
                high_risk,
                critical_risk,
            ),
        )
