## Assistant Guidelines

- Always execute project tooling through `python dev.py <command>`.
- Default to English for comments, docstrings, and translations.
- Keep comments minimal and only when they clarify non-obvious logic.
- Avoid reiterating what the code already states clearly.
- Add comments only when they resolve likely ambiguity or uncertainty.
- Keep provider changes in sync with `python-missive`: every supported service must expose consistent `send_*`, `cancel_*`, `check_*_delivery_status`, `get_*_service_info`, `calculate_*_delivery_risk`, and `handle_*_webhook` / `validate_*_webhook_signature` hooks.

