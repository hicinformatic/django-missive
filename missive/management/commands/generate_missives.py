"""
Commande pour générer des missives d'exemple.
"""

from django.core.management.base import BaseCommand

from missive.models import Missive, Recipient


class Command(BaseCommand):
    help = "Génère des missives d'exemple pour chaque type"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Supprimer toutes les missives existantes avant de générer",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            count = Missive.objects.count()
            Missive.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"✓ {count} missives supprimées"))

        # Récupérer un expéditeur par défaut
        sender = Recipient.objects.filter(can_be_sender=True).first()
        if not sender:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Aucun expéditeur disponible. Lancez "python dev.py generate_recipients" d\'abord.'
                )
            )
            return

        # Récupérer des destinataires selon leur type de contact
        email_recipients = (
            Recipient.objects.exclude(email="")
            .exclude(email__isnull=True)
            .filter(can_be_sender=False)[:3]
        )
        mobile_recipients = (
            Recipient.objects.exclude(mobile="")
            .exclude(mobile__isnull=True)
            .filter(can_be_sender=False)[:3]
        )
        postal_recipients = (
            Recipient.objects.exclude(address_line1="")
            .exclude(address_line1__isnull=True)
            .filter(can_be_sender=False)[:3]
        )

        missives = []

        # MISSIVES EMAIL
        for i, recipient in enumerate(email_recipients, 1):
            missives.append(
                {
                    "missive_type": "EMAIL",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": f"Email {i} - Information importante",
                    "body": f"<h1>Bonjour {recipient.full_name}</h1><p>Ceci est un email de test numéro {i}.</p>",
                    "body_text": f"Bonjour {recipient.full_name}, Ceci est un email de test numéro {i}.",
                    "priority": ["NORMAL", "HIGH", "URGENT"][i % 3],
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                }
            )

        # MISSIVES SMS
        for i, recipient in enumerate(mobile_recipients, 1):
            missives.append(
                {
                    "missive_type": "SMS",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": f"SMS {i}",
                    "body": f"Bonjour {recipient.full_name}, message SMS {i}",
                    "priority": ["NORMAL", "HIGH", "URGENT"][i % 3],
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                }
            )

        # MISSIVES BRANDED (Messageries d'applications)
        for i, recipient in enumerate(mobile_recipients[:2], 1):
            missives.append(
                {
                    "missive_type": "BRANDED",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": f"Message App {i}",
                    "body": f"Bonjour {recipient.full_name}, message via messagerie {i}",
                    "priority": "NORMAL",
                    "status": ["DRAFT", "SENT"][i % 2],
                }
            )

        # MISSIVES POSTAL
        for i, recipient in enumerate(postal_recipients, 1):
            missives.append(
                {
                    "missive_type": "POSTAL",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": f"Courrier recommandé {i}",
                    "body": f"<h2>Lettre recommandée</h2><p>Destinataire: {recipient.full_name}</p><p>Contenu du courrier {i}.</p>",
                    "body_text": f"Lettre recommandée pour {recipient.full_name}. Contenu du courrier {i}.",
                    "is_registered": i % 2 == 0,
                    "requires_signature": i % 3 == 0,
                    "priority": "HIGH",
                    "status": ["DRAFT", "PENDING", "SENT"][i % 3],
                }
            )

        # MISSIVES NOTIFICATION
        notif_recipients = list(email_recipients[:2])
        for i, recipient in enumerate(notif_recipients, 1):
            missives.append(
                {
                    "missive_type": "NOTIFICATION",
                    "sender": sender,
                    "recipient": recipient,
                    "subject": f"Notification {i}",
                    "body": f"Vous avez une nouvelle notification numéro {i}.",
                    "priority": ["NORMAL", "HIGH"][i % 2],
                    "status": ["DRAFT", "SENT"][i % 2],
                }
            )

        created_count = 0
        for missive_data in missives:
            missive = Missive.objects.create(**missive_data)

            # Créer l'événement d'envoi initial avec le provider approprié
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
                description=f"Missive {missive.missive_type} créée",
            )

            created_count += 1

            # Afficher avec icône selon le type
            icons = {
                "EMAIL": "✉️",
                "SMS": "📱",
                "BRANDED": "💬",
                "POSTAL": "📮",
                "NOTIFICATION": "🔔",
            }
            icon = icons.get(missive.missive_type, "📋")

            self.stdout.write(
                self.style.SUCCESS(
                    f"  {icon} {missive.get_missive_type_display()} → {missive.recipient.full_name} - {missive.subject}"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"\n✓ {created_count} missives créées"))
        self.stdout.write(
            self.style.SUCCESS(f"✓ Total: {Missive.objects.count()} missives")
        )

        # Statistiques
        self.stdout.write("\n📊 Statistiques par type:")
        for missive_type, label in [
            ("EMAIL", "Email"),
            ("SMS", "SMS"),
            ("BRANDED", "Messagerie App"),
            ("POSTAL", "Postal"),
            ("NOTIFICATION", "Notification"),
        ]:
            count = Missive.objects.filter(missive_type=missive_type).count()
            self.stdout.write(f"  - {label}: {count}")

        self.stdout.write("\n📊 Statistiques par statut:")
        for status, label in [
            ("DRAFT", "Brouillon"),
            ("PENDING", "En attente"),
            ("SENT", "Envoyé"),
        ]:
            count = Missive.objects.filter(status=status).count()
            self.stdout.write(f"  - {label}: {count}")
