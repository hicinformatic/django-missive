"""Missive campaign models."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..managers.campaign import MissiveCampaignManager


class MissiveCampaign(models.Model):
    """Campaign grouping missives for batch sending."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Campaign name"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Campaign description"),
    )

    objects = MissiveCampaignManager()

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = []

    def __str__(self):
        return self.name


class MissiveScheduledCampaign(models.Model):
    """Scheduled send for a campaign."""

    campaign = models.ForeignKey(
        MissiveCampaign,
        on_delete=models.CASCADE,
        related_name="to_missivecampaignsend",
        verbose_name=_("Campaign"),
        editable=False,
    )
    scheduled_send_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled send date"),
        help_text=_("Scheduled send date for the campaign (leave blank for immediate sending)"),
    )
    send_date = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Send date"),
        help_text=_("Actual send date for the campaign"),
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Ended at"),
        help_text=_("Actual ended date for the campaign"),
    )

    class Meta:
        verbose_name = _("Campaign send")
        verbose_name_plural = _("Campaign sends")
        ordering = ["-scheduled_send_date", "-ended_at", "-id"]
