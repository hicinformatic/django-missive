"""Legacy local providers module.

Local provider implementations have been archived.
Use `python_missive.providers` instead.
This file keeps DjangoEmail provider available for local sending.
"""

from .django_email import DjangoEmailProvider  # noqa: F401

__all__ = ["DjangoEmailProvider"]
