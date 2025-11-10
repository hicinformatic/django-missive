from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from ..models import Missive, MissiveStatus


class MissiveListView(ListView):
    """List view for Missives"""

    model = Missive
    template_name = "missive/missive_list.html"
    context_object_name = "missives"
    paginate_by = 20

    def get_queryset(self):
        # Note: À adapter selon le nouveau modèle où sender est un Recipient
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.order_by("-created_at")
        return Missive.objects.none()


class MissiveDetailView(LoginRequiredMixin, DetailView):
    """Detail view for Missive"""

    model = Missive
    template_name = "missive/missive_detail.html"
    context_object_name = "missive"

    def get_queryset(self):
        # Note: À adapter selon le nouveau modèle où sender est un Recipient
        return super().get_queryset()


class MissiveCreateView(LoginRequiredMixin, CreateView):
    """Create view for Missive"""

    model = Missive
    template_name = "missive/missive_form.html"
    fields = [
        "missive_type",
        "priority",
        "subject",
        "body",
        "body_text",
        "recipient",
        "recipient_user",
        "is_registered",
        "requires_signature",
        "scheduled_at",
    ]
    success_url = reverse_lazy("missive:missive-list")

    def form_valid(self, form):
        # Note: sender sera un Recipient après le refactoring
        # form.instance.sender = self.request.user
        form.instance.status = MissiveStatus.DRAFT
        messages.success(self.request, "Missive créée avec succès")
        return super().form_valid(form)


class MissiveUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for Missive"""

    model = Missive
    template_name = "missive/missive_form.html"
    fields = [
        "missive_type",
        "priority",
        "subject",
        "body",
        "body_text",
        "recipient",
        "recipient_user",
        "is_registered",
        "requires_signature",
        "scheduled_at",
    ]
    success_url = reverse_lazy("missive:missive-list")

    def get_queryset(self):
        # Note: À adapter selon le nouveau modèle où sender est un Recipient
        return (
            super()
            .get_queryset()
            .filter(
                status__in=[MissiveStatus.DRAFT, MissiveStatus.PENDING],
            )
        )

    def form_valid(self, form):
        messages.success(self.request, "Missive modifiée avec succès")
        return super().form_valid(form)


class MissiveDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for Missive"""

    model = Missive
    template_name = "missive/missive_confirm_delete.html"
    success_url = reverse_lazy("missive:missive-list")

    def get_queryset(self):
        # Note: À adapter selon le nouveau modèle où sender est un Recipient
        return super().get_queryset()
