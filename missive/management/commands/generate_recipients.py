"""Commande pour générer des destinataires d'exemple."""

from django.core.management.base import BaseCommand

from missive.models import Recipient


class Command(BaseCommand):
    help = "Generate sample recipients to test different missive types"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing recipients before generating",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = Recipient.objects.count()
            Recipient.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"✓ {count} recipients deleted"))

        recipients = [
            {
                "name": "MonEntreprise SAS",
                "recipient_type": "COMPANY",
                "email": "contact@monentreprise.fr",
                "mobile": "+33 6 12 34 56 78",
                "address_line1": "123 Avenue des Champs-Élysées",
                "postal_code": "75008",
                "city": "Paris",
                "country": "FR",
                "can_be_sender": True,
                "is_default_sender": True,
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "Pierre Directeur",
                "recipient_type": "INDIVIDUAL",
                "email": "p.directeur@monentreprise.fr",
                "mobile": "+33 6 98 76 54 32",
                "address_line1": "123 Avenue des Champs-Élysées",
                "postal_code": "75008",
                "city": "Paris",
                "country": "FR",
                "can_be_sender": True,
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "Jean Dupont",
                "recipient_type": "INDIVIDUAL",
                "email": "jean.dupont@example.com",
                "is_active": True,
            },
            {
                "civility": "Mme",
                "name": "Marie Martin",
                "recipient_type": "INDIVIDUAL",
                "email": "marie.martin@example.com",
                "is_active": True,
            },
            {
                "name": "TechCorp SAS",
                "recipient_type": "COMPANY",
                "email": "contact@techcorp.fr",
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "Luc Bernard",
                "recipient_type": "INDIVIDUAL",
                "mobile": "+33 6 11 22 33 44",
                "is_active": True,
            },
            {
                "civility": "Mme",
                "name": "Sophie Leroy",
                "recipient_type": "INDIVIDUAL",
                "mobile": "+33 6 55 66 77 88",
                "is_active": True,
            },
            {
                "name": "Service Client Express",
                "recipient_type": "COMPANY",
                "mobile": "+33 6 99 88 77 66",
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "François Dubois",
                "recipient_type": "INDIVIDUAL",
                "address_line1": "45 Rue de la République",
                "address_line2": "Appartement 12",
                "postal_code": "69002",
                "city": "Lyon",
                "country": "FR",
                "is_active": True,
            },
            {
                "civility": "Mme",
                "name": "Claire Lambert",
                "recipient_type": "INDIVIDUAL",
                "address_line1": "78 Boulevard Saint-Germain",
                "postal_code": "75005",
                "city": "Paris",
                "country": "FR",
                "is_active": True,
            },
            {
                "name": "Cabinet Juridique Associés",
                "recipient_type": "COMPANY",
                "address_line1": "12 Place Bellecour",
                "address_line2": "3ème étage",
                "postal_code": "69002",
                "city": "Lyon",
                "country": "FR",
                "is_active": True,
            },
            {
                "name": "Préfecture du Rhône",
                "recipient_type": "ADMINISTRATION",
                "address_line1": "106 Rue Pierre Corneille",
                "postal_code": "69003",
                "city": "Lyon",
                "country": "FR",
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "Thomas Petit",
                "recipient_type": "INDIVIDUAL",
                "email": "thomas.petit@example.com",
                "mobile": "+33 6 44 55 66 77",
                "address_line1": "89 Rue Nationale",
                "postal_code": "59000",
                "city": "Lille",
                "country": "FR",
                "is_active": True,
            },
            {
                "name": "Solutions Innovantes SARL",
                "recipient_type": "COMPANY",
                "email": "contact@solutions-innovantes.fr",
                "mobile": "+33 6 22 33 44 55",
                "address_line1": "34 Avenue Victor Hugo",
                "postal_code": "75116",
                "city": "Paris",
                "country": "FR",
                "is_active": True,
            },
            {
                "civility": "M.",
                "name": "Ancien Client",
                "recipient_type": "INDIVIDUAL",
                "email": "ancien@example.com",
                "is_active": False,
            },
        ]

        created_count = 0
        for recipient_data in recipients:
            if recipient_data.get("email"):
                recipient, created = Recipient.objects.get_or_create(
                    email=recipient_data["email"], defaults=recipient_data
                )
            elif recipient_data.get("mobile"):
                recipient, created = Recipient.objects.get_or_create(
                    mobile=recipient_data["mobile"], defaults=recipient_data
                )
            elif recipient_data.get("address_line1") and recipient_data.get("name"):
                recipient, created = Recipient.objects.get_or_create(
                    name=recipient_data["name"],
                    address_line1=recipient_data["address_line1"],
                    postal_code=recipient_data.get("postal_code", ""),
                    city=recipient_data.get("city", ""),
                    defaults=recipient_data,
                )
            else:
                recipient, created = Recipient.objects.create(**recipient_data), True

            if created:
                created_count += 1
                if recipient.email:
                    icon = "✉️"
                elif recipient.mobile:
                    icon = "📱"
                elif recipient.address_line1:
                    icon = "📍"
                else:
                    icon = "📋"

                self.stdout.write(
                    self.style.SUCCESS(
                        f'  {icon} {recipient.full_name} - {recipient.primary_contact or "No contact"}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ {created_count} recipients created")
        )
        self.stdout.write(
            self.style.SUCCESS(f"✓ Total: {Recipient.objects.count()} recipients")
        )

        self.stdout.write("\n📊 Statistics:")
        self.stdout.write(
            f"  - Senders: {Recipient.objects.filter(can_be_sender=True).count()}"
        )
        self.stdout.write(
            f'  - With email: {Recipient.objects.exclude(email="").exclude(email__isnull=True).count()}'
        )
        self.stdout.write(
            f'  - With mobile: {Recipient.objects.exclude(mobile="").exclude(email__isnull=True).count()}'
        )
        self.stdout.write(
            f'  - With address: {Recipient.objects.exclude(address_line1="").exclude(address_line1__isnull=True).count()}'
        )
        self.stdout.write(
            f"  - Active: {Recipient.objects.filter(is_active=True).count()}"
        )
