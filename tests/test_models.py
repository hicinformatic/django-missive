"""Missive model tests."""

import pytest
from django.contrib.auth import get_user_model

from missive.models import Missive, MissiveStatus, MissiveType

User = get_user_model()


@pytest.mark.django_db
class TestMissive:
    """Missive model tests."""

    def test_create_missive(self, user):
        """Tests Missive creation."""
        missive = Missive.objects.create(
            sender_name=user.get_full_name() or user.username,
            sender_email=getattr(user, "email", "sender@example.com"),
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            subject="Test Subject",
            body="Test content",
        )
        assert missive.id is not None
        assert missive.subject == "Test Subject"
        assert missive.body == "Test content"
        assert missive.sender_email == getattr(user, "email", "sender@example.com")
        assert missive.status == MissiveStatus.DRAFT

    def test_missive_str(self, user):
        """Tests Missive string representation."""
        missive = Missive.objects.create(
            sender_name=user.get_full_name() or user.username,
            sender_email=getattr(user, "email", "sender@example.com"),
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            subject="Test Subject",
            body="Test content",
        )
        assert "Email" in str(missive)
        assert "Test Subject" in str(missive)
        assert "Brouillon" in str(missive)

    def test_missive_ordering(self, user):
        """Tests Missive ordering by created_at descending."""
        missive1 = Missive.objects.create(
            sender_name="Sender 1",
            sender_email="sender1@example.com",
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            subject="First",
            body="Content 1",
        )
        missive2 = Missive.objects.create(
            sender_name="Sender 2",
            sender_email="sender2@example.com",
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            subject="Second",
            body="Content 2",
        )

        missives = list(Missive.objects.all())
        assert missives[0] == missive2
        assert missives[1] == missive1

    def test_missive_can_send(self, user):
        """Tests can_send method."""
        missive = Missive.objects.create(
            sender_name="Sender",
            sender_email="sender@example.com",
            missive_type=MissiveType.EMAIL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            subject="Test",
            body="Test",
        )
        assert missive.can_send() is True

        missive.status = MissiveStatus.SENT
        missive.save()
        assert missive.can_send() is False
