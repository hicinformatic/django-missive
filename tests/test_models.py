"""Missive model tests."""

import pytest
from django.contrib.auth import get_user_model

from djgeoaddress.fields import AddressFormField
from djmissive.models import Missive, MissiveStatus, MissiveType

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
        assert str(MissiveStatus.DRAFT.label) in str(missive)

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

    def test_structured_address_populates_legacy_fields(self, user):
        """Structured address should hydrate legacy address columns."""
        missive = Missive.objects.create(
            sender_name="Sender",
            sender_email="sender@example.com",
            missive_type=MissiveType.POSTAL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            recipient_address={
                "line1": "221B Baker Street",
                "city": "London",
                "postal_code": "NW1",
                "country": "UK",
            },
            subject="Adresse",
            body="Adresse test",
        )
        assert missive.recipient_address_line1 == "221B Baker Street"
        assert missive.recipient_city == "London"
        assert missive.recipient_postal_code == "NW1"
        assert missive.recipient_country == "UK"

    def test_legacy_fields_populate_structured_address(self, user):
        """Legacy charfields should backfill the structured JSON field."""
        missive = Missive.objects.create(
            sender_name="Sender",
            sender_email="sender@example.com",
            missive_type=MissiveType.POSTAL,
            recipient_email="test@example.com",
            recipient_name="Test Recipient",
            recipient_address_line1="10 Downing Street",
            recipient_city="London",
            recipient_postal_code="SW1A 2AA",
            recipient_country="UK",
            subject="Adresse",
            body="Adresse test",
        )
        assert missive.recipient_address
        assert missive.recipient_address.get("line1") == "10 Downing Street"
        assert missive.recipient_address.get("city") == "London"
        assert missive.recipient_address.get("postal_code") == "SW1A 2AA"


class TestAddressField:
    """Tests for the AddressFormField manual fallback logic."""

    def test_manual_entry_sets_user_backend(self, user):
        field = AddressFormField(use_backend=False)
        field.set_current_user(user)
        result = field.clean(
            [
                "221B Baker Street",
                "",
                "",
                "NW1",
                "London",
                "",
                "UK",
            ]
        )
        assert result["backend_used"] == "user"
        assert result["backend_reference"] == str(user.pk)
