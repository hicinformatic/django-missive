from __future__ import annotations

from django.db import models
from django.db.models.sql import Query
from django.utils.translation import gettext_lazy as _


class AddressLookupQuerySet(models.QuerySet):
    def __init__(self, model=None, data=None, query=None, using=None, hints=None):
        if query is None and model is not None:
            query = Query(model)
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._result_cache = list(data or [])
        self._prefetch_done = True

    def __len__(self):
        return len(self._result_cache)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return AddressLookupQuerySet(
                self.model,
                self._result_cache[k],
                self.query.clone(),
                using=self._db,
                hints=self._hints,
            )
        return self._result_cache[k]

    def _clone(self):
        return AddressLookupQuerySet(
            self.model,
            list(self._result_cache),
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )


class AddressLookupManager(models.Manager):
    def get_queryset(self):
        return AddressLookupQuerySet(model=self.model, data=[])


class AddressLookup(models.Model):
    label = models.CharField(max_length=512, verbose_name=_("Suggested address"))
    backend_used = models.CharField(
        max_length=64, blank=True, verbose_name=_("Backend used")
    )
    backend_reference = models.CharField(
        max_length=128, blank=True, verbose_name=_("Backend reference")
    )
    raw_payload = models.JSONField(default=dict, blank=True)

    objects = AddressLookupManager()

    class Meta:
        managed = False
        verbose_name = _("Address suggestion")
        verbose_name_plural = _("Address suggestions")
        ordering = ["label"]
        default_permissions = ()

    def __str__(self):
        return self.label or _("Address suggestion")
