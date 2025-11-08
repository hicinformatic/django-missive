#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import django


def create_superuser():
    """Create a default superuser if none exists"""
    from django.contrib.auth.models import User
    
    if not User.objects.filter(is_superuser=True).exists():
        print("📦 Création du superuser: admin/admin")
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("✅ Superuser créé avec succès!")
        print("   Username: admin")
        print("   Password: admin")
    else:
        print("✅ Superuser déjà existant")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # If running migrations or migrate command, create superuser after
    if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'runserver']:
        # Execute the command first
        if sys.argv[1] == 'migrate':
            execute_from_command_line(sys.argv)
            # Setup Django and create superuser
            django.setup()
            create_superuser()
            return
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

