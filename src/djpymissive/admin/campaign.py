"""Admin for MissiveCampaign model."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_boosted import AdminBoostModel

from ..models.campaign import MissiveCampaign, MissiveScheduledCampaign


@admin.register(MissiveScheduledCampaign)
class MissiveScheduledCampaignAdmin(AdminBoostModel):
    """Admin for missive scheduled campaign model."""

    list_display = [
        "campaign",
        "scheduled_send_date",
        "send_date",
        "ended_at",
    ]
    readonly_fields = [
        "campaign",
        "scheduled_send_date",
        "send_date",
        "ended_at",
    ]


class MissiveScheduledCampaignInline(admin.TabularInline):
    """Inline for missive scheduled campaign model."""

    model = MissiveScheduledCampaign
    extra = 0
    readonly_fields = [
        "campaign",
        "send_date",
        "ended_at",
    ]

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(MissiveCampaign)
class MissiveCampaignAdmin(AdminBoostModel):
    """Admin for missive campaign model."""

    list_display = [
        "name",
        "stats_display",
    ]
    search_fields = ["name", "description"]
    ordering = ["-id"]
    inlines = [MissiveScheduledCampaignInline]

    def stats_display(self, obj):
        """Display missive/recipient counts and status percentages."""
        parts = [
            f"{obj.count_missive} missive(s)",
            f"{obj.count_recipient} recipient(s)",
            f"{obj.pct_failed:.0f}% failed",
            f"{obj.pct_success:.0f}% success",
            f"{obj.pct_processing:.0f}% processing",
        ]
        return " | ".join(parts)

    stats_display.short_description = _("Stats")
