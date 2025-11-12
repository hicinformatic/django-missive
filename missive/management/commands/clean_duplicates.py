"""Commande pour nettoyer les destinataires en double."""

from django.core.management.base import BaseCommand
from django.db.models import Count

from missive.models import Recipient


class Command(BaseCommand):
    help = "Clean duplicate recipients (keeps the oldest)"

    def handle(self, *args, **options):
        removed_count = 0

        self.stdout.write("\n🔍 Searching for email duplicates...")
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
            self.stdout.write(f"  📧 {email}: {duplicates.count()} duplicates")

            to_keep = duplicates.first()
            to_delete = duplicates.exclude(pk=to_keep.pk)

            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"    ❌ Suppression: {dup.name} (ID: {dup.id})")
                )
                dup.delete()
                removed_count += 1

        self.stdout.write("\n🔍 Searching for mobile duplicates...")
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
            self.stdout.write(f"  📱 {mobile}: {duplicates.count()} duplicates")

            to_keep = duplicates.first()
            to_delete = duplicates.exclude(pk=to_keep.pk)

            for dup in to_delete:
                self.stdout.write(
                    self.style.WARNING(f"    ❌ Suppression: {dup.name} (ID: {dup.id})")
                )
                dup.delete()
                removed_count += 1

        self.stdout.write("\n🔍 Searching for address duplicates...")
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
                f'  📍 {item["name"]} - {item["address_line1"]}: {duplicates.count()} duplicates'
            )

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
                self.style.SUCCESS(f"\n✓ {removed_count} duplicates removed")
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ No duplicates found"))

        self.stdout.write(
            self.style.SUCCESS(f"✓ Total: {Recipient.objects.count()} recipients")
        )
