"""
Commande pour nettoyer les destinataires en double avant d'appliquer les contraintes d'unicité.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from missive.models import Recipient


class Command(BaseCommand):
    help = "Nettoie les destinataires en double (garde le plus ancien)"

    def handle(self, *args, **options):
        removed_count = 0

        # 1. Nettoyer les doublons d'email
        self.stdout.write("\n🔍 Recherche de doublons d'email...")
        emails = (
            Recipient.objects.exclude(email="")
            .exclude(email__isnull=True)
            .values("email")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for item in emails:
            email = item["email"]
            duplicates = Recipient.objects.filter(email=email).order_by("created_at")
            self.stdout.write(f"  📧 {email}: {duplicates.count()} doublons")

            # Garder le premier (le plus ancien), supprimer les autres
            to_keep = duplicates.first()
            to_delete = duplicates.exclude(pk=to_keep.pk)

            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"    ❌ Suppression: {dup.name} (ID: {dup.id})")
                )
                dup.delete()
                removed_count += 1

        # 2. Nettoyer les doublons de mobile
        self.stdout.write("\n🔍 Recherche de doublons de mobile...")
        mobiles = (
            Recipient.objects.exclude(mobile="")
            .exclude(mobile__isnull=True)
            .values("mobile")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for item in mobiles:
            mobile = item["mobile"]
            duplicates = Recipient.objects.filter(mobile=mobile).order_by("created_at")
            self.stdout.write(f"  📱 {mobile}: {duplicates.count()} doublons")

            # Garder le premier (le plus ancien), supprimer les autres
            to_keep = duplicates.first()
            to_delete = duplicates.exclude(pk=to_keep.pk)

            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"    ❌ Suppression: {dup.name} (ID: {dup.id})")
                )
                dup.delete()
                removed_count += 1

        # 3. Nettoyer les doublons d'adresse
        self.stdout.write("\n🔍 Recherche de doublons d'adresse...")
        addresses = (
            Recipient.objects.exclude(address_line1="")
            .exclude(address_line1__isnull=True)
            .values("name", "address_line1", "postal_code", "city")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for item in addresses:
            duplicates = Recipient.objects.filter(
                name=item["name"],
                address_line1=item["address_line1"],
                postal_code=item["postal_code"],
                city=item["city"],
            ).order_by("created_at")
            self.stdout.write(
                f'  📍 {item["name"]} - {item["address_line1"]}: {duplicates.count()} doublons'
            )

            # Garder le premier (le plus ancien), supprimer les autres
            to_keep = duplicates.first()
            to_delete = duplicates.exclude(pk=to_keep.pk)

            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"    ❌ Suppression: ID {dup.id}")
                )
                dup.delete()
                removed_count += 1

        if removed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ {removed_count} doublons supprimés")
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Aucun doublon trouvé"))

        self.stdout.write(
            self.style.SUCCESS(f"✓ Total: {Recipient.objects.count()} destinataires")
        )
