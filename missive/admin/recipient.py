"""
Administration pour le modèle Recipient.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Admin pour les destinataires"""

    class Media:
        js = ('admin/js/recipient_context_filter.js',)

    def get_search_results(self, request, queryset, search_term):
        """Filtre les résultats de recherche selon le contexte (sender vs recipient)"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Si on cherche pour le champ sender, filtrer sur can_be_sender
        if 'field_name=sender' in request.get_full_path():
            queryset = queryset.filter(can_be_sender=True)

        return queryset, use_distinct

    list_display = [
        "name_display",
        "recipient_type",
        "email_display",
        "phone_display",
        "address_display",
        "is_active",
        "can_be_sender",
        "is_default_sender",
    ]
    list_filter = ["recipient_type", "is_active", "can_be_sender", "is_default_sender", "country", "created_at"]
    search_fields = [
        "name",
        "email",
        "mobile",
        "city",
        "postal_code",
        "content_type__model",
        "content_type__app_label",
    ]
    readonly_fields = ["created_at", "updated_at", "postal_address_display"]
    actions = ["validate_email_action", "validate_phone_action", "validate_all_action"]

    fieldsets = (
        (
            _("Type et lien"),
            {
                "fields": (
                    "recipient_type",
                    "content_type",
                    "object_id",
                    "is_active",
                )
            },
        ),
        (
            _("Configuration expéditeur"),
            {
                "fields": (
                    "can_be_sender",
                    "is_default_sender",
                ),
                "description": _("Configurer si ce destinataire peut être utilisé comme expéditeur"),
            },
        ),
        (
            _("Identité"),
            {"fields": ("civility", "name")},
        ),
        (
            _("Coordonnées"),
            {"fields": ("email", "mobile")},
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

    def name_display(self, obj):
        """Affiche le nom avec civilité"""
        name = obj.full_name or f"Recipient #{obj.id}"
        if obj.is_active:
            return format_html('<strong style="white-space: nowrap;">{}</strong>', name)
        else:
            return format_html('<strong style="color: #6c757d; white-space: nowrap;">{}</strong> <span style="color: #dc3545;">●</span>', name)

    name_display.short_description = _("Nom")

    def email_display(self, obj):
        """Affiche l'email avec icône"""
        if not obj.email:
            return format_html('<span style="color: #ccc; white-space: nowrap;">-</span>')

        return format_html(
            '<span style="white-space: nowrap;"><span style="color: #0d6efd;">✉️</span> {}</span>'.format(obj.email)
        )

    email_display.short_description = _("Email")

    def phone_display(self, obj):
        """Affiche le numéro de téléphone mobile avec icône"""
        if not obj.mobile:
            return format_html('<span style="color: #ccc; white-space: nowrap;">-</span>')

        return format_html(
            '<span style="white-space: nowrap;"><span style="color: #198754;">📱</span> {}</span>'.format(obj.mobile)
        )

    phone_display.short_description = _("Mobile")

    def address_display(self, obj):
        """Affiche l'adresse courte sur une ligne avec truncation"""
        if not obj.address_line1:
            return format_html('<span style="color: #ccc; white-space: nowrap;">-</span>')

        # Adresse courte : ligne1, code postal ville (tout sur une ligne)
        parts = [obj.address_line1]
        if obj.postal_code and obj.city:
            parts.append(f"{obj.postal_code} {obj.city}")
        elif obj.city:
            parts.append(obj.city)

        address_text = ", ".join(parts)

        # Tronquer si trop long (max 50 caractères)
        if len(address_text) > 50:
            address_text = address_text[:47] + "..."

        return format_html(
            '<span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: inline-block; max-width: 300px;" title="{}">📍 {}</span>'.format(
                ", ".join(parts),  # Tooltip avec adresse complète
                address_text
            )
        )

    address_display.short_description = _("Adresse")

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
            if recipient.mobile:
                validation = provider.validate_phone_number(recipient.mobile)

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
            if recipient.mobile:
                phone_validation = provider.validate_phone_number(recipient.mobile)
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
                    "⚠️ Validation:\n"
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



