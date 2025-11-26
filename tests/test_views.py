"""Missive diagnostics and webhook view tests."""

import pytest
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
class TestMissiveViews:
    """Validate JSON diagnostics and webhook helper endpoints."""

    def test_system_status_view(self, client):
        """System status endpoint should return missive/provider stats."""
        response = client.get(reverse("missive:system-status"))
        assert response.status_code == 200
        data = response.json()
        assert "missives" in data
        assert "providers" in data

    def test_address_backends_status_view(self, client):
        """Address backend diagnostics should include configuration summary."""
        response = client.get(reverse("missive:address-backends-status"))
        assert response.status_code == 200
        data = response.json()
        assert "configured" in data
        assert "items" in data

    def test_webhook_status_view(self, client, admin_user):
        """Webhook status view exposes provider details for staff users."""
        client.force_login(admin_user)
        response = client.get(reverse("missive:webhook-status"))
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data.get("admin") is True
        assert "providers" in data

    @override_settings(DEBUG=True)
    def test_webhook_test_view_get_lists_providers(self, client):
        """GET on webhook test view returns provider hints."""
        response = client.get(reverse("missive:webhook-test"))
        assert response.status_code == 200
        data = response.json()
        assert "providers_available" in data
        assert isinstance(data["providers_available"], list)
