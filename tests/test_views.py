"""
Tests for Missive views
"""

import pytest
from django.urls import reverse

from missive.models import Missive, MissiveType


@pytest.mark.django_db
class TestMissiveViews:
    """Tests for Missive views"""

    def test_missive_list_view(self, client, user):
        """Test the missive list view"""
        client.force_login(user)

        Missive.objects.create(
            sender=user,
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            subject="Test",
            body="Content",
        )

        url = reverse("missive:missive-list")
        response = client.get(url)

        assert response.status_code == 200
        assert "missives" in response.context

    def test_missive_detail_view(self, client, user):
        """Test the missive detail view"""
        client.force_login(user)

        missive = Missive.objects.create(
            sender=user,
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            subject="Test",
            body="Content",
        )

        url = reverse("missive:missive-detail", kwargs={"pk": missive.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context["missive"] == missive

    def test_missive_create_view_requires_login(self, client):
        """Test that create view requires authentication"""
        url = reverse("missive:missive-create")
        response = client.get(url)

        # Should redirect to login
        assert response.status_code == 302

    def test_missive_create_view_authenticated(self, client, user):
        """Test creating a missive while authenticated"""
        client.force_login(user)
        url = reverse("missive:missive-create")

        response = client.post(
            url,
            {
                "missive_type": MissiveType.EMAIL,
                "subject": "New Test",
                "body": "New Content",
                "recipient_email": "test@example.com",
                "priority": "NORMAL",
            },
        )

        assert response.status_code == 302  # Redirect after success
        assert Missive.objects.filter(subject="New Test").exists()
