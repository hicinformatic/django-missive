"""Shared constants for Django Missive."""

MISSIVE_TYPE_COLORS = {
    "POSTAL": "#6c757d",
    "POSTAL_REGISTERED": "#495057",
    "LRE": "#495057",
    "EMAIL": "#0d6efd",
    "SMS": "#198754",
    "RCS": "#20c997",
    "VOICE_CALL": "#6f42c1",
    "NOTIFICATION": "#fd7e14",
    "PUSH_NOTIFICATION": "#dc3545",
    "BRANDED": "#9b59b6",
}

MISSIVE_STATUS_COLORS = {
    "DRAFT": "#6c757d",
    "PENDING": "#ffc107",
    "PROCESSING": "#0dcaf0",
    "SENT": "#0d6efd",
    "DELIVERED": "#198754",
    "READ": "#20c997",
    "FAILED": "#dc3545",
    "CANCELLED": "#6c757d",
}
