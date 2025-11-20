"""Commande pour générer des missives d'exemple."""

from django.core.management.base import BaseCommand

from missive.models import Missive


class Command(BaseCommand):
    help = "Generate sample missives for each type"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing missives before generating",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = Missive.objects.count()
            Missive.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"✓ {count} missives deleted"))

        # Default sender data
        sender_data = {
            "sender_name": "MonEntreprise SAS",
            "sender_email": "contact@monentreprise.fr",
            "sender_phone": "+33 6 12 34 56 78",
            "sender_address_line1": "123 Avenue des Champs-Élysées",
            "sender_postal_code": "75008",
            "sender_city": "Paris",
            "sender_country": "FR",
        }

        # Sample recipients data
        email_recipients = [
            {"name": "Jean Dupont", "email": "jean.dupont@example.com"},
            {"name": "Marie Martin", "email": "marie.martin@example.com"},
            {"name": "TechCorp SAS", "email": "contact@techcorp.fr"},
        ]
        mobile_recipients = [
            {"name": "Luc Bernard", "phone": "+33 6 11 22 33 44"},
            {"name": "Sophie Leroy", "phone": "+33 6 55 66 77 88"},
            {"name": "Service Client", "phone": "+33 6 99 88 77 66"},
        ]
        postal_recipients = [
            {
                "name": "François Dubois",
                "address_line1": "45 Rue de la République",
                "address_line2": "Appartement 12",
                "postal_code": "69002",
                "city": "Lyon",
                "country": "FR",
            },
            {
                "name": "Claire Lambert",
                "address_line1": "78 Boulevard Saint-Germain",
                "postal_code": "75005",
                "city": "Paris",
                "country": "FR",
            },
            {
                "name": "Cabinet Juridique",
                "address_line1": "12 Place Bellecour",
                "address_line2": "3ème étage",
                "postal_code": "69002",
                "city": "Lyon",
                "country": "FR",
            },
        ]

        missives = []

        for i, recipient in enumerate(email_recipients, 1):
            missives.append(
                {
                    "missive_type": "EMAIL",
                    "subject": f"Email {i} - Information importante",
                    "body": f"<h1>Bonjour {recipient['name']}</h1><p>Ceci est un email de test numéro {i}.</p>",
                    "body_text": f"Bonjour {recipient['name']}, Ceci est un email de test numéro {i}.",
                    "priority": ["NORMAL", "HIGH", "URGENT"][i % 3],
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                    "recipient_name": recipient["name"],
                    "recipient_email": recipient["email"],
                    **sender_data,
                }
            )

        for i, recipient in enumerate(mobile_recipients, 1):
            missives.append(
                {
                    "missive_type": "SMS",
                    "subject": f"SMS {i}",
                    "body": f"Bonjour {recipient['name']}, message SMS {i}",
                    "priority": ["NORMAL", "HIGH", "URGENT"][i % 3],
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                    "recipient_name": recipient["name"],
                    "recipient_phone": recipient["phone"],
                    **sender_data,
                }
            )

        for i, recipient in enumerate(mobile_recipients[:2], 1):
            missives.append(
                {
                    "missive_type": "BRANDED",
                    "subject": f"Message App {i}",
                    "body": f"Bonjour {recipient['name']}, message via messagerie {i}",
                    "priority": "NORMAL",
                    "status": ["DRAFT", "SENT"][i % 2],
                    "recipient_name": recipient["name"],
                    "recipient_phone": recipient["phone"],
                    **sender_data,
                }
            )

        for i, recipient in enumerate(postal_recipients, 1):
            missives.append(
                {
                    "missive_type": "POSTAL",
                    "subject": f"Courrier recommandé {i}",
                    "body": f"<h2>Lettre recommandée</h2><p>Destinataire: {recipient['name']}</p><p>Contenu du courrier {i}.</p>",
                    "body_text": f"Lettre recommandée pour {recipient['name']}. Contenu du courrier {i}.",
                    "is_registered": i % 2 == 0,
                    "requires_signature": i % 3 == 0,
                    "priority": "HIGH",
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                    "recipient_name": recipient["name"],
                    "recipient_address_line1": recipient["address_line1"],
                    "recipient_address_line2": recipient.get("address_line2", ""),
                    "recipient_postal_code": recipient["postal_code"],
                    "recipient_city": recipient["city"],
                    "recipient_country": recipient["country"],
                    **sender_data,
                }
            )

        notif_recipients = email_recipients[:2]
        for i, recipient in enumerate(notif_recipients, 1):
            missives.append(
                {
                    "missive_type": "NOTIFICATION",
                    "subject": f"Notification {i}",
                    "body": f"Vous avez une nouvelle notification numéro {i}.",
                    "priority": ["NORMAL", "HIGH"][i % 2],
                    "status": ["DRAFT", "SENT"][i % 2],
                    "recipient_name": recipient["name"],
                    "recipient_email": recipient["email"],
                    **sender_data,
                }
            )

        created_count = 0
        for missive_data in missives:
            missive = Missive.objects.create(**missive_data)

            provider_map = {
                "EMAIL": "django_email",
                "SMS": "twilio",
                "BRANDED": "twilio",
                "POSTAL": "laposte",
                "NOTIFICATION": "custom",
            }

            provider = provider_map.get(missive.missive_type, "custom")
            missive.create_send_event(
                provider=provider,
                status=missive.status,
                description=f"Missive {missive.missive_type} created",
            )

            created_count += 1

            icons = {
                "EMAIL": "✉️",
                "SMS": "📱",
                "BRANDED": "💬",
                "POSTAL": "📮",
                "NOTIFICATION": "🔔",
            }
            icon = icons.get(missive.missive_type, "📋")

            recipient_display = (
                missive.recipient_name
                or missive.recipient_email
                or missive.recipient_phone
                or "Unknown"
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {icon} {missive.get_missive_type_display()} → {recipient_display} - {missive.subject}"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"\n✓ {created_count} missives created"))
        self.stdout.write(
            self.style.SUCCESS(f"✓ Total: {Missive.objects.count()} missives")
        )

        self.stdout.write("\n📊 Statistics by type:")
        for missive_type, label in [
            ("EMAIL", "Email"),
            ("SMS", "SMS"),
            ("BRANDED", "App Messaging"),
            ("POSTAL", "Postal"),
            ("NOTIFICATION", "Notification"),
        ]:
            count = Missive.objects.filter(missive_type=missive_type).count()
            self.stdout.write(f"  - {label}: {count}")

        self.stdout.write("\n📊 Statistics by status:")
        for status, label in [
            ("DRAFT", "Draft"),
            ("PENDING", "Pending"),
            ("SENT", "Sent"),
        ]:
            count = Missive.objects.filter(status=status).count()
            self.stdout.write(f"  - {label}: {count}")
