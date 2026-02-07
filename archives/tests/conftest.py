"""Pytest configuration and fixtures."""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Creates test user."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def admin_user(db):
    """Creates test admin user."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )
