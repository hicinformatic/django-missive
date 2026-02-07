"""Virtual address backend model built from Django settings."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..address_backends import build_backend_diagnostic
from virtualqueryset import InMemoryQuerySet

_slug_cleanup = re.compile(r"[^a-z0-9]+")


def _to_slug(value: str) -> str:
    slug_value = _slug_cleanup.sub("-", value.strip().lower()).strip("-")
    return slug_value or "backend"


class AddressBackendInfoQuerySet(InMemoryQuerySet):
    """In-memory queryset for address backend diagnostics."""

    pass


class AddressBackendInfoManager(models.Manager):
    """Manager returning diagnostics data as an in-memory queryset."""

    def get_queryset(self):
        backends_config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
        if not backends_config:
            return AddressBackendInfoQuerySet(model=self.model, data=[])

        diagnostics = []
        payload = {}
        try:
            from pymissive.helpers import describe_address_backends

            # Skip API test for faster queryset construction
            payload = describe_address_backends(backends_config, skip_api_test=True)
            diagnostics = payload.get("items", [])
        except Exception as e:
            # Log error but still try to build items from config
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error describing address backends: {e}")
            diagnostics = []
            payload = {"sample_result": {}, "selected_backend": None}

        items = []
        # Build items from diagnostics if available, otherwise from config
        if diagnostics:
            for idx, data in enumerate(diagnostics, start=1):
                # Ensure we have a valid backend_name
                backend_name = data.get("backend_name") or data.get("class_name")
                if not backend_name:
                    class_path = data.get("class", "")
                    class_name = (
                        class_path.split(".")[-1] if class_path else f"Backend {idx}"
                    )
                    backend_name = (
                        class_name.replace("AddressBackend", "")
                        .replace("Backend", "")
                        .lower()
                        or f"backend_{idx}"
                    )
                display_label = data.get("backend_display_name") or backend_name
                data["backend_display_name"] = display_label

                base_slug_source = backend_name or data.get("class") or str(idx)
                slug_value = _to_slug(str(base_slug_source))
                backend = AddressBackendInfo(
                    pk=backend_name,  # Use name as pk for URL generation
                    name=backend_name,
                    class_path=data.get("class") or "",
                    status=data.get("status", "unknown"),
                )
                backend._diagnostic = data
                backend._selected_backend = payload.get("selected_backend")
                backend._sample_result = payload.get("sample_result", {})
                backend._slug = slug_value
                items.append(backend)
        elif backends_config:
            # Fallback: build items directly from config if diagnostics failed
            # Try to load package and config info for each backend
            for idx, backend_config in enumerate(backends_config, start=1):
                class_path = backend_config.get("class", "")
                config = backend_config.get("config", {}) or {}
                class_name = (
                    class_path.split(".")[-1] if class_path else f"Backend {idx}"
                )
                backend_name = (
                    class_name.replace("AddressBackend", "")
                    .replace("Backend", "")
                    .lower()
                    or f"backend_{idx}"
                )
                base_slug_source = backend_name or class_path or str(idx)
                slug_value = _to_slug(str(base_slug_source))

                # Try to load backend class and get package/config info
                diagnostic = {
                    "class": class_path,
                    "class_name": class_name,
                    "status": "unknown",
                    "backend_name": backend_name,
                    "backend_display_name": backend_name,
                    "packages": {},
                    "config": {},
                    "required_packages": [],
                    "required_config_keys": [],
                }

                try:
                    # Import backend class dynamically
                    from importlib import import_module

                    module_path, class_name_attr = class_path.rsplit(".", 1)
                    module = import_module(module_path)
                    backend_class = getattr(module, class_name_attr)
                    backend_instance = backend_class(config=config)
                    diagnostic.update(
                        build_backend_diagnostic(
                            backend_instance,
                            config=config,
                            backend_name=backend_name,
                        )
                    )
                except Exception as exc:
                    diagnostic["error"] = str(exc)
                    diagnostic["status"] = "error"

                backend = AddressBackendInfo(
                    pk=backend_name,
                    name=backend_name,
                    class_path=class_path,
                    status=diagnostic.get("status", "unknown"),
                )
                backend._diagnostic = diagnostic
                backend._selected_backend = None
                backend._sample_result = {}
                backend._slug = slug_value
                items.append(backend)

        return AddressBackendInfoQuerySet(model=self.model, data=items)


class AddressBackendInfo(models.Model):
    """Virtual model describing configured address verification backends."""

    name = models.CharField(max_length=120, verbose_name=_("Backend name"))
    class_path = models.CharField(max_length=255, verbose_name=_("Import path"))
    status = models.CharField(max_length=32, verbose_name=_("Status"))

    objects = AddressBackendInfoManager()

    class Meta:
        managed = False
        verbose_name = _("Address backend")
        verbose_name_plural = _("Address backends")
        default_permissions = ()
        ordering = ["name"]

    def __str__(self):
        return self.display_name

    # Internal helpers -------------------------------------------------
    @property
    def diagnostic(self) -> Dict[str, Any]:
        diag = getattr(self, "_diagnostic", None)
        if isinstance(diag, dict):
            return diag
        return {}

    @property
    def packages(self) -> Dict[str, Any]:
        value = self.diagnostic.get("packages", {}) or {}
        return value if isinstance(value, dict) else {}

    @property
    def required_packages(self):
        return self.diagnostic.get("required_packages", [])

    @property
    def config_entries(self) -> List[Tuple[str, Dict[str, Any]]]:
        config = self.diagnostic.get("config", {}) or {}
        if not isinstance(config, dict):
            return []
        return [(key, details) for key, details in config.items()]

    @property
    def documentation_url(self):
        return self.diagnostic.get("documentation_url")

    @property
    def site_url(self):
        return self.diagnostic.get("site_url")

    @property
    def display_name(self) -> str:
        diag_name = self.diagnostic.get("backend_display_name")
        if isinstance(diag_name, str) and diag_name:
            return diag_name
        return self.name

    @property
    def error(self):
        return self.diagnostic.get("error")

    @property
    def class_name_token(self) -> str:
        if self.class_path:
            return self.class_path.split(".")[-1]
        value = self.diagnostic.get("class_name")
        if isinstance(value, str):
            return value
        return (self.name or "").replace(" ", "_")

    @property
    def slug(self) -> str:
        cached = getattr(self, "_slug", None)
        if cached:
            return str(cached)
        base = self.name or self.diagnostic.get("backend_name") or self.class_name_token
        slug_value = _to_slug(str(base))
        return slug_value

    # Status -----------------------------------------------------------
    @property
    def status_display(self):
        mapping = {
            "working": _("✅ Working"),
            "missing_packages": _("❌ Missing packages"),
            "missing_config": _("⚠️ Missing configuration"),
            "unavailable": _("⚠️ Unavailable"),
        }
        return mapping.get(self.status, _("❓ Unknown"))

    @property
    def is_selected(self):
        selected = getattr(self, "_selected_backend", None)
        return bool(selected and selected == self.diagnostic.get("backend_name"))

    # Display helpers --------------------------------------------------
    @property
    def packages_summary(self) -> List[Tuple[str, bool]]:
        summary: List[Tuple[str, bool]] = []
        packages = self.packages or {}
        if packages:
            for name, status in packages.items():
                summary.append((name, status == "installed"))
        elif self.required_packages:
            for name in self.required_packages:
                summary.append((name, False))
        return summary

    @property
    def config_summary(self) -> List[Tuple[str, bool, Optional[str]]]:
        entries: List[Tuple[str, bool, Optional[str]]] = []
        for key, details in self.config_entries:
            present = bool(details.get("present"))
            preview = details.get("value_preview")
            if preview is not None:
                preview = str(preview)
            entries.append((key, present, preview))
        return entries


__all__ = ["AddressBackendInfo"]
