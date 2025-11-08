from django import forms

from .models import Missive, MissiveType


class MissiveForm(forms.ModelForm):
    """Form for Missive"""

    class Meta:
        model = Missive
        fields = [
            "missive_type",
            "priority",
            "subject",
            "body",
            "body_text",
            "recipient_user",
            "recipient_email",
            "recipient_phone",
            "recipient_address",
            "is_registered",
            "requires_signature",
            "scheduled_at",
        ]
        widgets = {
            "missive_type": forms.Select(attrs={"class": "form-control"}),
            "priority": forms.Select(attrs={"class": "form-control"}),
            "subject": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Sujet de la missive"}
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 8,
                    "placeholder": "Contenu du message (HTML pour emails)",
                }
            ),
            "body_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Version texte brut (fallback email, obligatoire SMS)",
                }
            ),
            "recipient_user": forms.Select(attrs={"class": "form-control"}),
            "recipient_email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "email@example.com"}
            ),
            "recipient_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+33600000000"}
            ),
            "recipient_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Adresse postale complète",
                }
            ),
            "is_registered": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "requires_signature": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "scheduled_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
        }
