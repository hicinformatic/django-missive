#!/usr/bin/env python3
"""
Exemples d'utilisation rapide de django-missive avec les fonctions shortcuts.

Ce script montre comment envoyer différents types de missives de manière simple
en utilisant les fonctions raccourcis.

Usage:
    python examples/quickstart.py
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

import django

django.setup()

# Imports après setup Django
from missive import send_email, send_sms, send_telegram, send_whatsapp
from missive.exceptions import MissiveValidationError

# =============================================================================
# EXEMPLES D'UTILISATION
# =============================================================================


def example_sms():
    """Exemple d'envoi de SMS."""
    print("\n" + "=" * 70)
    print("EXEMPLE 1 : Envoi d'un SMS")
    print("=" * 70)

    try:
        missive = send_sms(
            phone="+33612345678",
            content="Bonjour ! Ceci est un test depuis django-missive.",
            sender_name="MonApp",
        )
        print(f"✅ SMS envoyé avec succès !")
        print(f"   ID: {missive.id}")
        print(f"   Status: {missive.status}")
        print(f"   Provider: {missive.provider_info.name if missive.provider_info else 'N/A'}")
    except MissiveValidationError as e:
        print(f"❌ Erreur de validation : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def example_email():
    """Exemple d'envoi d'email."""
    print("\n" + "=" * 70)
    print("EXEMPLE 2 : Envoi d'un Email")
    print("=" * 70)

    try:
        missive = send_email(
            email="test@example.com",
            subject="Test django-missive",
            content="Ceci est un email de test envoyé via django-missive.\n\nCordialement,",
            sender_name="Équipe Support",
        )
        print(f"✅ Email envoyé avec succès !")
        print(f"   ID: {missive.id}")
        print(f"   Status: {missive.status}")
        print(f"   Provider: {missive.provider_info.name if missive.provider_info else 'N/A'}")
    except MissiveValidationError as e:
        print(f"❌ Erreur de validation : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def example_whatsapp():
    """Exemple d'envoi de message WhatsApp."""
    print("\n" + "=" * 70)
    print("EXEMPLE 3 : Envoi d'un message WhatsApp")
    print("=" * 70)

    try:
        missive = send_whatsapp(
            phone="+33612345678",
            content="Hello from django-missive! 👋",
        )
        print(f"✅ Message WhatsApp envoyé avec succès !")
        print(f"   ID: {missive.id}")
        print(f"   Status: {missive.status}")
        print(f"   Provider: {missive.provider_info.name if missive.provider_info else 'N/A'}")
    except MissiveValidationError as e:
        print(f"❌ Erreur de validation : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def example_telegram():
    """Exemple d'envoi de message Telegram."""
    print("\n" + "=" * 70)
    print("EXEMPLE 4 : Envoi d'un message Telegram")
    print("=" * 70)

    try:
        missive = send_telegram(
            chat_id="123456789",
            content="Message de test depuis django-missive 🚀",
        )
        print(f"✅ Message Telegram envoyé avec succès !")
        print(f"   ID: {missive.id}")
        print(f"   Status: {missive.status}")
        print(f"   Provider: {missive.provider_info.name if missive.provider_info else 'N/A'}")
    except MissiveValidationError as e:
        print(f"❌ Erreur de validation : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def example_validation_errors():
    """Exemples de gestion des erreurs de validation."""
    print("\n" + "=" * 70)
    print("EXEMPLE 5 : Gestion des erreurs de validation")
    print("=" * 70)

    # Test 1 : SMS sans numéro
    print("\n📝 Test 1 : Tentative d'envoi de SMS sans numéro")
    try:
        send_sms(phone="", content="Test")
    except MissiveValidationError as e:
        print(f"✅ Erreur capturée correctement : {e}")

    # Test 2 : Email invalide
    print("\n📝 Test 2 : Tentative d'envoi avec email invalide")
    try:
        send_email(email="pas-un-email", subject="Test", content="Test")
    except MissiveValidationError as e:
        print(f"✅ Erreur capturée correctement : {e}")

    # Test 3 : Téléphone invalide (sans +)
    print("\n📝 Test 3 : Tentative d'envoi avec téléphone invalide")
    try:
        send_sms(phone="0612345678", content="Test")
    except MissiveValidationError as e:
        print(f"✅ Erreur capturée correctement : {e}")

    # Test 4 : Contenu vide
    print("\n📝 Test 4 : Tentative d'envoi avec contenu vide")
    try:
        send_sms(phone="+33612345678", content="")
    except MissiveValidationError as e:
        print(f"✅ Erreur capturée correctement : {e}")


def example_with_options():
    """Exemple avec des options avancées."""
    print("\n" + "=" * 70)
    print("EXEMPLE 6 : Envoi avec options avancées")
    print("=" * 70)

    try:
        missive = send_sms(
            phone="+33612345678",
            content="SMS avec options personnalisées",
            sender_name="CustomSender",
            sender_phone="+33123456789",
            priority=5,
            provider_options={
                "scheduled_time": 14,  # Heure d'envoi préférée
                "is_commercial": False,
            },
        )
        print(f"✅ SMS avec options envoyé avec succès !")
        print(f"   ID: {missive.id}")
        print(f"   Priority: {missive.priority}")
        print(f"   Options: {missive.provider_options}")
    except MissiveValidationError as e:
        print(f"❌ Erreur de validation : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def main():
    """Fonction principale pour lancer tous les exemples."""
    print("\n" + "=" * 70)
    print(" EXEMPLES DJANGO-MISSIVE - QUICKSTART")
    print("=" * 70)
    print("\nCe script démontre l'utilisation des fonctions shortcuts de django-missive.")
    print("Certains exemples peuvent échouer si les providers ne sont pas configurés.")
    print("\n⚠️  Mode SANDBOX activé - Aucun message ne sera réellement envoyé.")

    # Lancer tous les exemples
    example_sms()
    example_email()
    example_whatsapp()
    example_telegram()
    example_validation_errors()
    example_with_options()

    print("\n" + "=" * 70)
    print("✅ Exemples terminés !")
    print("=" * 70)
    print(
        "\n💡 Pour en savoir plus, consultez la documentation dans /docs/ ou utilisez --help"
    )
    print()


if __name__ == "__main__":
    main()

