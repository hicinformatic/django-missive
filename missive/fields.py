"""Custom Django fields to store structured addresses."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

try:
    from python_missive.address import Address as PMAddress
except ImportError:  # pragma: no cover - optional dependency
    PMAddress = None


class AddressWidget(forms.MultiWidget):
    """Render address components as multiple inputs."""

    template_name = "django/forms/widgets/multiwidget.html"

    def __init__(self, attrs: Optional[Dict[str, Any]] = None):
        widgets = [
            forms.TextInput(attrs={"placeholder": _("Address line 1")}),
            forms.TextInput(attrs={"placeholder": _("Address line 2")}),
            forms.TextInput(attrs={"placeholder": _("Address line 3")}),
            forms.TextInput(attrs={"placeholder": _("Postal code")}),
            forms.TextInput(attrs={"placeholder": _("City")}),
            forms.TextInput(attrs={"placeholder": _("State / Region")}),
            forms.TextInput(attrs={"placeholder": _("Country (ISO code)")}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value: Any) -> List[Optional[str]]:
        if not value:
            return ["", "", "", "", "", "", ""]
        source = value if isinstance(value, dict) else {}
        return [
            source.get("line1") or source.get("address_line1") or "",
            source.get("line2") or source.get("address_line2") or "",
            source.get("line3") or source.get("address_line3") or "",
            source.get("postal_code") or "",
            source.get("city") or "",
            source.get("state") or "",
            source.get("country") or "",
        ]


class AddressFormField(forms.MultiValueField):
    """Form field that exposes structured address inputs."""

    widget = AddressWidget

    def __init__(self, *, use_backend: bool = True, **kwargs: Any):
        # JSONField forwards encoder/decoder that MultiValueField does not support.
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        fields = [
            forms.CharField(required=False, label=_("Address line 1")),
            forms.CharField(required=False, label=_("Address line 2")),
            forms.CharField(required=False, label=_("Address line 3")),
            forms.CharField(required=False, label=_("Postal code")),
            forms.CharField(required=False, label=_("City")),
            forms.CharField(required=False, label=_("State / Region")),
            forms.CharField(required=False, label=_("Country (ISO code)")),
        ]
        super().__init__(
            fields=fields,
            require_all_fields=False,
            **kwargs,
        )
        self.use_backend = use_backend
        self.current_user = None

    def compress(self, data_list: Iterable[Any]) -> Dict[str, str]:
        items = list(data_list or [])
        if len(items) < 7:
            items.extend([""] * (7 - len(items)))
        address = {
            "line1": items[0] or "",
            "line2": items[1] or "",
            "line3": items[2] or "",
            "postal_code": items[3] or "",
            "city": items[4] or "",
            "state": items[5] or "",
            "country": items[6] or "",
        }
        return {key: value for key, value in address.items() if value}

    def clean(self, value: Any) -> Dict[str, Any]:
        data = super().clean(value)
        if not data:
            return {}
        normalized = self._normalize_with_backend(data)
        return self._apply_manual_backend(normalized, data)

    def set_current_user(self, user: Any) -> None:
        self.current_user = user

    def _normalize_with_backend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.use_backend or PMAddress is None:
            return data

        backends_config = getattr(settings, "MISSIVE_ADDRESS_BACKENDS", None)
        if not backends_config:
            return data

        try:
            normalized, payload = PMAddress.normalize_with_backends(
                backends_config,
                **data,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise ValidationError(
                _("Address normalization failed: %(error)s") % {"error": exc}
            )

        result: Dict[str, Any] = normalized.to_dict()
        if payload.get("errors"):
            raise ValidationError(
                _("Address validation failed: %(errors)s")
                % {"errors": ", ".join(payload.get("errors", []))}
            )
        return result

    def _apply_manual_backend(
        self, result: Dict[str, Any], original_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not result:
            return result
        if result.get("backend_used"):
            return result
        if not any(original_data.values()):
            return result
        result["backend_used"] = "user"
        if self.current_user and getattr(self.current_user, "pk", None) is not None:
            result["backend_reference"] = str(self.current_user.pk)
        return result


class AddressField(models.JSONField):
    """Store structured addresses validated via python-missive backends."""

    def __init__(self, *args: Any, use_backend: bool = True, **kwargs: Any):
        kwargs.setdefault("default", dict)
        kwargs.setdefault("blank", True)
        kwargs.setdefault("null", True)
        super().__init__(*args, **kwargs)
        self.use_backend = use_backend

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if not kwargs.get("default"):
            kwargs["default"] = dict
        kwargs["use_backend"] = self.use_backend
        return name, path, args, kwargs

    def to_python(self, value: Any):
        data = super().to_python(value)
        if isinstance(data, dict):
            return data
        return {}

    def formfield(
        self,
        form_class: type[forms.Field] | None = None,
        choices_form_class: type[forms.Field] | None = None,
        **kwargs: Any,
    ):
        defaults: Dict[str, Any] = {"use_backend": self.use_backend}
        if form_class is None:
            defaults["form_class"] = AddressFormField
        else:
            defaults["form_class"] = form_class
        if choices_form_class is not None:
            defaults["choices_form_class"] = choices_form_class
        defaults.update(kwargs)
        return super().formfield(**defaults)
