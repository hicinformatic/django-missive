"""Views for Missive model."""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.forms import modelform_factory

from ..models.missive import Missive


@staff_member_required
def missive_preview(request, pk):
    """Preview a missive (email, SMS, postal, etc.) - Show existing object."""
    missive = get_object_or_404(Missive, pk=pk)
    
    template_map = {
        "EMAIL": "djpymissive/email_preview.html",
        "SMS": "djpymissive/sms_preview.html",
        "POSTAL": "djpymissive/postal_preview.html",
    }
    
    template_name = template_map.get(missive.missive_type, "djpymissive/base_preview.html")
    
    context = {
        "missive": missive,
        "title": _("Preview: {}").format(missive),
    }
    
    return TemplateResponse(
        request,
        template_name,
        context,
    )


@staff_member_required
@require_http_methods(["POST"])
def missive_preview_form(request):
    """Preview a missive from form data - Preview what it will look like."""
    pk = request.POST.get("id") or request.POST.get("_save")
    
    if pk:
        try:
            missive = Missive.objects.get(pk=pk)
            MissiveForm = modelform_factory(Missive, fields="__all__")
            form = MissiveForm(request.POST, instance=missive)
        except Missive.DoesNotExist:
            MissiveForm = modelform_factory(Missive, fields="__all__")
            form = MissiveForm(request.POST)
    else:
        MissiveForm = modelform_factory(Missive, fields="__all__")
        form = MissiveForm(request.POST)
    
    if form.is_valid():
        missive = form.save(commit=False)
    else:
        # If form is not valid, try to get values from cleaned_data first
        # (some fields might be valid even if the whole form is not)
        missive = form.instance if form.instance.pk else Missive()
        
        # Populate from cleaned_data if available
        if hasattr(form, 'cleaned_data') and form.cleaned_data:
            for field_name, value in form.cleaned_data.items():
                if value is not None:
                    try:
                        setattr(missive, field_name, value)
                    except (ValueError, TypeError):
                        pass
        
        # Also populate from POST data for fields that might not be in cleaned_data
        # This ensures we get all the data even if validation fails
        for field_name in form.fields:
            if field_name in request.POST:
                value = request.POST[field_name]
                # Only set if value is not empty and field is not already set
                if value and (not hasattr(missive, field_name) or getattr(missive, field_name, None) is None):
                    try:
                        # Use the form field's widget to extract the value from POST
                        # This handles special fields like PhoneNumberField correctly
                        field = form.fields[field_name]
                        if hasattr(field, 'widget') and hasattr(field.widget, 'value_from_datadict'):
                            widget_value = field.widget.value_from_datadict(request.POST, None, field_name)
                            if widget_value:
                                # Try to clean the value using the field
                                try:
                                    cleaned_value = field.clean(widget_value)
                                    setattr(missive, field_name, cleaned_value)
                                except (ValueError, TypeError):
                                    # If cleaning fails, set the raw widget value
                                    setattr(missive, field_name, widget_value)
                        else:
                            # Fallback: try to clean the value directly
                            try:
                                cleaned_value = field.clean(value)
                                setattr(missive, field_name, cleaned_value)
                            except (ValueError, TypeError, AttributeError):
                                # If cleaning fails, set the raw value
                                setattr(missive, field_name, value)
                    except (ValueError, TypeError, AttributeError):
                        # If all else fails, try to set the raw value
                        try:
                            setattr(missive, field_name, value)
                        except (ValueError, TypeError):
                            pass
    
    template_map = {
        "EMAIL": "djpymissive/email_preview.html",
        "SMS": "djpymissive/sms_preview.html",
        "POSTAL": "djpymissive/postal_preview.html",
    }
    
    missive_type = getattr(missive, 'missive_type', None) or request.POST.get('missive_type')
    if missive_type:
        missive.missive_type = missive_type
    
    template_name = template_map.get(missive_type, "djpymissive/base_preview.html")
    
    context = {
        "missive": missive,
        "title": _("Preview: {}").format(missive_type or "Missive"),
    }
    
    return TemplateResponse(
        request,
        template_name,
        context,
    )
