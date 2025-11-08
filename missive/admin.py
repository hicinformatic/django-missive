from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Missive, MissiveAttachment, MissiveEvent, MissiveTemplate, Recipient


class MissiveAttachmentInline(admin.TabularInline):
    """Inline pour les pièces jointes"""

    model = MissiveAttachment
    extra = 1
    readonly_fields = ["created_at", "file_url_display"]
    fields = [
        "file",
        "external_url",
        "filename",
        "description",
        "file_size",
        "mime_type",
        "created_at",
        "file_url_display",
    ]

    def file_url_display(self, obj):
        """Affiche le lien vers le fichier"""
        if obj and obj.file_url:
            from django.utils.html import format_html

            icon = "🔗" if obj.is_external else "📎"
            return format_html(
                '<a href="{}" target="_blank">{} Voir le fichier</a>',
                obj.file_url,
                icon,
            )
        return "-"

    file_url_display.short_description = _("Lien")


class MissiveEventInline(admin.TabularInline):
    """Inline pour l'historique des événements"""

    model = MissiveEvent
    extra = 0
    readonly_fields = ["event_type", "provider", "status", "description", "created_at"]
    fields = ["event_type", "provider", "status", "description", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Missive)
class MissiveAdmin(admin.ModelAdmin):
    """Interface d'administration pour les Missives"""

    list_display = [
        "id",
        "subject",
        "missive_type_badge",
        "sender",
        "recipient_display_short",
        "related_object_display",
        "status_badge",
        "priority_badge",
        "is_registered",
        "created_at",
        "sent_at",
    ]

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
        "sender__username",
        "sender__email",
        "recipient_email",
        "recipient_phone",
        "external_id",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
        "read_at",
        "recipient_display",
    ]

    date_hierarchy = "created_at"

    inlines = [MissiveAttachmentInline, MissiveEventInline]

    fieldsets = (
        (
            _("Informations générales"),
            {
                "fields": (
                    "sender",
                    "recipient_user",
                    "subject",
                    "body",
                    "body_text",
                )
            },
        ),
        (
            _("Objet source (optionnel)"),
            {
                "fields": (
                    "content_type",
                    "object_id",
                ),
                "classes": ("collapse",),
                "description": _(
                    "Associer cette missive à un objet source (Commande, Participant, etc.)"
                ),
            },
        ),
        (
            _("Type et configuration"),
            {
                "fields": (
                    "missive_type",
                    "priority",
                    "is_registered",
                    "requires_signature",
                )
            },
        ),
        (
            _("Destinataire"),
            {
                "fields": (
                    "recipient_display",
                    "recipient_email",
                    "recipient_phone",
                    "recipient_address",
                ),
                "description": _("Remplir selon le type de missive"),
            },
        ),
        (
            _("Statut et tracking"),
            {
                "fields": (
                    "status",
                    "scheduled_at",
                    "provider",
                    "external_id",
                    "error_message",
                ),
                "description": _(
                    "Le provider peut être spécifié pour forcer un provider particulier"
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
            "POSTAL": "#6c757d",
            "EMAIL": "#0d6efd",
            "SMS": "#198754",
            "WHATSAPP": "#25D366",
            "NOTIFICATION": "#fd7e14",
        }
        color = colors.get(obj.missive_type, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
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
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
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
            'border-radius: 3px; font-size: 10px;">{}</span>',
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
            # Créer un lien vers l'admin de l'objet lié si possible
            try:
                from django.urls import reverse
                from django.utils.html import format_html

                content_type = obj.content_type
                url = reverse(
                    f"admin:{content_type.app_label}_{content_type.model}_change",
                    args=[obj.object_id],
                )
                label = str(obj.content_object)
                if len(label) > 30:
                    label = label[:27] + "..."
                return format_html('<a href="{}">{}</a>', url, label)
            except:
                label = str(obj.content_object)
                if len(label) > 30:
                    label = label[:27] + "..."
                return label
        return "-"

    related_object_display.short_description = _("Objet lié")

    @admin.action(description=_("Marquer comme envoyé"))
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone

        updated = queryset.update(status="SENT", sent_at=timezone.now())
        self.message_user(
            request, _(f"{updated} missive(s) marquée(s) comme envoyée(s).")
        )

    @admin.action(description=_("Marquer comme délivré"))
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone

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
            try:
                # Obtenir le provider
                provider_class = MissiveSender.get_provider_class(missive)
                provider = provider_class(missive)

                # Calculer le risque
                risk = provider.calculate_delivery_risk()

                # Mettre à jour les métadonnées de la missive
                if not missive.metadata:
                    missive.metadata = {}

                missive.metadata["risk_analysis"] = {
                    "score": risk["risk_score"],
                    "level": risk["risk_level"],
                    "recommendations": risk["recommendations"],
                    "checked_at": str(timezone.now()),
                }
                missive.save()

                # Compter par niveau
                if risk["risk_level"] == "low":
                    low_risk += 1
                elif risk["risk_level"] == "medium":
                    medium_risk += 1
                elif risk["risk_level"] == "high":
                    high_risk += 1
                else:
                    critical_risk += 1

            except Exception as e:
                self.message_user(
                    request,
                    format_html(f"❌ Erreur pour missive #{missive.id}: {str(e)}"),
                    level="error",
                )

        self.message_user(
            request,
            format_html(
                "✅ Analyse de risque terminée :<br>"
                "🟢 {} risque faible<br>"
                "🟡 {} risque moyen<br>"
                "🟠 {} risque élevé<br>"
                "🔴 {} risque critique<br>"
                "<small>Les résultats sont dans le champ 'metadata' de chaque missive</small>",
                low_risk,
                medium_risk,
                high_risk,
                critical_risk,
            ),
        )


@admin.register(MissiveAttachment)
class MissiveAttachmentAdmin(admin.ModelAdmin):
    """Admin pour les pièces jointes"""

    list_display = [
        "filename",
        "order",
        "attached_to_display",
        "storage_type_badge",
        "file_size_display",
        "mime_type",
        "created_at",
    ]
    list_filter = ["mime_type", "content_type", "created_at"]
    search_fields = ["filename", "description", "missive__subject"]
    readonly_fields = ["created_at", "file_url_display", "attached_to_display"]
    list_editable = ["order"]
    list_display_links = ["filename"]

    fieldsets = (
        (_("Fichier"), {"fields": ("filename", "description", "order")}),
        (
            _("Attaché à"),
            {
                "fields": (
                    "missive",
                    "content_type",
                    "object_id",
                    "attached_to_display",
                ),
                "description": _("Attacher soit à une missive, soit à un autre objet"),
            },
        ),
        (
            _("Source du fichier"),
            {
                "fields": ("file", "external_url", "file_url_display"),
                "description": _("Fournir soit un fichier local, soit une URL externe"),
            },
        ),
        (
            _("Métadonnées"),
            {"fields": ("file_size", "created_at"), "classes": ("collapse",)},
        ),
    )

    def storage_type_badge(self, obj):
        """Badge pour le type de stockage"""
        from django.utils.html import format_html

        if obj.is_external:
            return format_html(
                '<span style="background-color: #0dcaf0; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px;">🔗 Externe</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #198754; color: white; padding: 2px 8px; '
                'border-radius: 3px; font-size: 10px;">📎 Local</span>'
            )

    storage_type_badge.short_description = _("Stockage")

    def attached_to_display(self, obj):
        """Affiche l'objet auquel le fichier est attaché"""
        attached = obj.attached_to
        if not attached:
            return "-"

        try:
            from django.contrib.contenttypes.models import ContentType
            from django.urls import reverse
            from django.utils.html import format_html

            if obj.missive:
                # Lien vers la missive
                url = reverse("admin:missive_missive_change", args=[obj.missive.id])
                return format_html(
                    '<a href="{}">📧 Missive #{}</a>', url, obj.missive.id
                )
            elif obj.content_object:
                # Lien vers l'objet lié
                ct = obj.content_type
                url = reverse(
                    f"admin:{ct.app_label}_{ct.model}_change", args=[obj.object_id]
                )
                label = str(obj.content_object)
                if len(label) > 40:
                    label = label[:37] + "..."
                return format_html('<a href="{}">{}</a>', url, label)
        except:
            return str(attached)

        return str(attached)

    attached_to_display.short_description = _("Attaché à")

    def file_size_display(self, obj):
        """Affichage formaté de la taille"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"

    file_size_display.short_description = _("Taille")

    def file_url_display(self, obj):
        """Affiche le lien vers le fichier"""
        if obj.file_url:
            from django.utils.html import format_html

            icon = "🔗" if obj.is_external else "📎"
            return format_html(
                '<a href="{}" target="_blank">{} Télécharger/Voir</a>',
                obj.file_url,
                icon,
            )
        return "-"

    file_url_display.short_description = _("Lien")


@admin.register(MissiveEvent)
class MissiveEventAdmin(admin.ModelAdmin):
    """Admin pour les événements"""

    list_display = ["event_type", "provider", "missive", "status", "created_at"]
    list_filter = ["event_type", "provider", "status", "created_at"]
    search_fields = ["missive__subject", "description", "provider"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(MissiveTemplate)
class MissiveTemplateAdmin(admin.ModelAdmin):
    """Admin pour les templates"""

    list_display = ["name", "missive_type", "is_active", "created_by", "created_at"]
    list_filter = ["missive_type", "is_active", "created_at"]
    search_fields = ["name", "subject_template", "body_template"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            _("Informations"),
            {"fields": ("name", "missive_type", "is_active", "created_by")},
        ),
        (
            _("Template"),
            {
                "fields": ("subject_template", "body_template"),
                "description": _("Utilisez {{variable}} pour les variables dynamiques"),
            },
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Admin pour les destinataires"""

    list_display = [
        "display_name",
        "recipient_type",
        "email",
        "phone",
        "city",
        "country",
        "is_active",
        "created_at",
    ]
    list_filter = ["recipient_type", "is_active", "country", "created_at"]
    search_fields = [
        "first_name",
        "last_name",
        "company_name",
        "email",
        "phone",
        "mobile",
        "city",
        "postal_code",
    ]
    readonly_fields = ["created_at", "updated_at", "postal_address_display"]
    actions = ["validate_email_action", "validate_phone_action", "validate_all_action"]

    fieldsets = (
        (
            _("Type et lien"),
            {
                "fields": (
                    "recipient_type",
                    "user",
                    "content_type",
                    "object_id",
                    "is_active",
                )
            },
        ),
        (
            _("Identité"),
            {"fields": ("civility", "first_name", "last_name", "company_name")},
        ),
        (
            _("Coordonnées"),
            {"fields": ("email", "phone", "mobile")},
        ),
        (
            _("Adresse postale"),
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "address_line3",
                    "postal_code",
                    "city",
                    "state",
                    "country",
                    "postal_address_display",
                )
            },
        ),
        (
            _("Notes"),
            {"fields": ("notes",)},
        ),
        (
            _("Dates"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def postal_address_display(self, obj):
        """Affiche l'adresse formatée"""
        if obj.postal_address:
            return format_html("<pre>{}</pre>", obj.postal_address)
        return "-"

    postal_address_display.short_description = _("Adresse formatée")

    @admin.action(description=_("🔍 Valider les emails"))
    def validate_email_action(self, request, queryset):
        """Action pour valider les emails des destinataires sélectionnés"""
        from ..providers.base import BaseProvider

        provider = BaseProvider()
        results = []
        invalid_count = 0
        high_risk_count = 0

        for recipient in queryset:
            if recipient.email:
                validation = provider.validate_email(recipient.email)

                if not validation["is_valid"]:
                    invalid_count += 1
                    recipient.notes = f"❌ Email invalide: {', '.join(validation['warnings'])}\n{recipient.notes}"
                    recipient.is_active = False
                    recipient.save()
                elif validation["risk_score"] > 50:
                    high_risk_count += 1
                    recipient.notes = f"⚠️ Email risqué (score: {validation['risk_score']}): {', '.join(validation['warnings'])}\n{recipient.notes}"
                    recipient.save()

        self.message_user(
            request,
            format_html(
                "✅ Validation terminée : {} recipient(s) analysé(s)<br>"
                "❌ {} invalide(s)<br>"
                "⚠️ {} à risque",
                queryset.count(),
                invalid_count,
                high_risk_count,
            ),
        )

    @admin.action(description=_("📞 Valider les téléphones"))
    def validate_phone_action(self, request, queryset):
        """Action pour valider les téléphones des destinataires sélectionnés"""
        from ..providers.base import BaseProvider

        provider = BaseProvider()
        invalid_count = 0
        non_mobile_count = 0

        for recipient in queryset:
            phone = recipient.mobile or recipient.phone
            if phone:
                validation = provider.validate_phone_number(phone)

                if not validation["is_valid"]:
                    invalid_count += 1
                    recipient.notes = f"❌ Téléphone invalide: {', '.join(validation['warnings'])}\n{recipient.notes}"
                    recipient.save()
                elif validation.get("is_mobile") is False:
                    non_mobile_count += 1
                    recipient.notes = f"⚠️ Numéro fixe détecté (pas de SMS possible)\n{recipient.notes}"
                    recipient.save()

        self.message_user(
            request,
            format_html(
                "✅ Validation terminée : {} recipient(s) analysé(s)<br>"
                "❌ {} invalide(s)<br>"
                "⚠️ {} numéro(s) fixe(s)",
                queryset.count(),
                invalid_count,
                non_mobile_count,
            ),
        )

    @admin.action(description=_("✨ Valider tout (email + téléphone)"))
    def validate_all_action(self, request, queryset):
        """Action pour valider tous les moyens de contact"""
        from ..providers.base import BaseProvider

        provider = BaseProvider()
        email_issues = 0
        phone_issues = 0
        all_valid = 0

        for recipient in queryset:
            issues = []

            # Valider l'email
            if recipient.email:
                email_validation = provider.validate_email(recipient.email)
                if (
                    not email_validation["is_valid"]
                    or email_validation["risk_score"] > 50
                ):
                    email_issues += 1
                    issues.append(f"Email: {', '.join(email_validation['warnings'])}")

            # Valider le téléphone
            phone = recipient.mobile or recipient.phone
            if phone:
                phone_validation = provider.validate_phone_number(phone)
                if (
                    not phone_validation["is_valid"]
                    or phone_validation["risk_score"] > 30
                ):
                    phone_issues += 1
                    issues.append(
                        f"Téléphone: {', '.join(phone_validation['warnings'])}"
                    )

            # Mettre à jour les notes
            if issues:
                recipient.notes = (
                    f"⚠️ Validation:\n"
                    + "\n".join(f"  - {i}" for i in issues)
                    + f"\n\n{recipient.notes}"
                )
                recipient.save()
            else:
                all_valid += 1

        self.message_user(
            request,
            format_html(
                "✅ Validation complète terminée :<br>"
                "✅ {} recipient(s) 100% valide(s)<br>"
                "⚠️ {} avec problème(s) email<br>"
                "⚠️ {} avec problème(s) téléphone",
                all_valid,
                email_issues,
                phone_issues,
            ),
        )
