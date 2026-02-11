"""Webhook model for storing webhook configurations."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from djproviderkit.models.service import define_provider_fields
from .choices import MissiveType

from pymissive.config import MISSIVE_WEBHOOK_FIELDS
from djproviderkit import fields_associations
from ..managers.webhook import MissiveWebhookManager

from djproviderkit import ProviderField

class MissiveWebhook(models.Model):
    """Webhook configuration for missive events."""
    provider = ProviderField(
        package_name='pymissive',
        blank=True,
        null=True,
        verbose_name=_("Provider"),
        help_text=_("Provider used to send this missive"),
    )
    webhook_id = models.CharField(
        max_length=255,
        verbose_name=_("Webhook ID"),
        help_text=_("Webhook ID"),
        primary_key=True,
    )

    objects = MissiveWebhookManager()

    class Meta:
        managed = False
        verbose_name = _("Webhook")
        verbose_name_plural = _("Webhooks")
        ordering = ["-created_at"]

    def get_provider(self):
        from ..models.provider import MissiveProviderModel
        provider = self.webhook_id.split("-")[0]
        return MissiveProviderModel.objects.get(name=provider)

    @property
    def provider_name(self):
        return self.webhook_id.split("-")[0]

    def __str__(self):
        return self.webhook_id

    def update_webhook(self):
        service = f"update_webhook_{self.type}"
        if hasattr(self.provider._provider, service):
            self.provider._provider.call_service(service)

    def delete(self):
        service = f"delete_webhook_{self.type}".lower()
        provider = self.get_provider()
        if hasattr(provider._provider, service):
            provider._provider.call_service(service, webhook_id=self.webhook_id)


for field, cfg in MISSIVE_WEBHOOK_FIELDS.items():
    if field != 'webhook_id':
        field_cfg = {
            "verbose_name": cfg['label'],
            "help_text": cfg['description'],
        }
        if field == "type":
            field_cfg["choices"] = MissiveType.choices
        db_field = fields_associations[cfg['format']](**field_cfg)
        MissiveWebhook.add_to_class(field, db_field)
