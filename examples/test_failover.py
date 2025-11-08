"""
Exemple de test du système de fallback.

Ce script démontre comment :
- Configurer plusieurs providers avec fallback
- Tester l'envoi avec fallback automatique
- Simuler une panne de provider
- Vérifier que le fallback fonctionne
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from unittest.mock import patch, MagicMock
from missive.models import Missive, User
from missive.sender import MissiveSender


def test_basic_send():
    """Test d'envoi basique avec un seul provider."""
    print("\n" + "="*70)
    print("TEST 1: Envoi basique avec un seul provider")
    print("="*70)
    
    # Créer une missive de test
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        recipient_email="test@example.com",
        subject="Test basique",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    
    try:
        success = MissiveSender.send(missive)
        print(f"✅ Résultat: {'Succès' if success else 'Échec'}")
        print(f"Provider utilisé: {missive.provider}")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_failover():
    """Test du fallback automatique quand le premier provider échoue."""
    print("\n" + "="*70)
    print("TEST 2: Fallback automatique")
    print("="*70)
    
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        recipient_email="test@example.com",
        subject="Test failover",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    print("Simulation: SendGrid échoue, Mailgun réussit")
    
    # Mock: Premier provider échoue, deuxième réussit
    with patch('missive.providers.sendgrid.SendGridProvider.send', return_value=False):
        with patch('missive.providers.mailgun.MailgunProvider.send', return_value=True):
            try:
                success = MissiveSender.send(missive)
                print(f"✅ Résultat: {'Succès' if success else 'Échec'}")
                print(f"Provider utilisé: {missive.provider}")
                
                if 'mailgun' in missive.provider.lower():
                    print("✅ Fallback vers Mailgun fonctionne!")
                else:
                    print("❌ Fallback n'a pas fonctionné comme prévu")
            except Exception as e:
                print(f"❌ Erreur: {e}")


def test_all_providers_fail():
    """Test quand tous les providers échouent."""
    print("\n" + "="*70)
    print("TEST 3: Tous les providers échouent")
    print("="*70)
    
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        recipient_email="test@example.com",
        subject="Test all fail",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    print("Simulation: Tous les providers échouent")
    
    # Mock: Tous les providers échouent
    with patch('missive.providers.sendgrid.SendGridProvider.send', return_value=False):
        with patch('missive.providers.mailgun.MailgunProvider.send', return_value=False):
            with patch('missive.providers.django_email.DjangoEmailProvider.send', return_value=False):
                try:
                    success = MissiveSender.send(missive)
                    print(f"❌ Ne devrait pas arriver ici: {success}")
                except RuntimeError as e:
                    print(f"✅ RuntimeError levée comme prévu")
                    print(f"Message: {str(e)[:100]}...")


def test_without_fallback():
    """Test avec fallback désactivé."""
    print("\n" + "="*70)
    print("TEST 4: Envoi sans fallback (enable_fallback=False)")
    print("="*70)
    
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        recipient_email="test@example.com",
        subject="Test no fallback",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    print("Simulation: Premier provider échoue, fallback désactivé")
    
    # Mock: Premier provider échoue
    with patch('missive.providers.sendgrid.SendGridProvider.send', return_value=False):
        try:
            success = MissiveSender.send(missive, enable_fallback=False)
            print(f"❌ Ne devrait pas arriver ici: {success}")
        except RuntimeError as e:
            print(f"✅ RuntimeError levée comme prévu (pas de fallback)")
            print(f"Message: {str(e)[:100]}...")


def test_skip_health_check():
    """Test avec health check désactivé."""
    print("\n" + "="*70)
    print("TEST 5: Envoi sans health check (skip_health_check=True)")
    print("="*70)
    
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        recipient_email="test@example.com",
        subject="Test no health check",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    print("Health check désactivé (plus rapide)")
    
    try:
        success = MissiveSender.send(missive, skip_health_check=True)
        print(f"✅ Résultat: {'Succès' if success else 'Échec'}")
        print(f"Provider utilisé: {missive.provider}")
        print("✅ Envoi sans health check fonctionne")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_explicit_provider():
    """Test avec provider explicite (pas de fallback)."""
    print("\n" + "="*70)
    print("TEST 6: Provider explicite sur la missive")
    print("="*70)
    
    user = User.objects.first()
    missive = Missive.objects.create(
        sender=user,
        missive_type="EMAIL",
        provider="missive.providers.mailgun.MailgunProvider",  # Forcer Mailgun
        recipient_email="test@example.com",
        subject="Test explicit provider",
        body="<p>Hello</p>",
    )
    
    print(f"Missive créée: {missive.id}")
    print(f"Provider forcé: {missive.provider}")
    
    try:
        success = MissiveSender.send(missive)
        print(f"✅ Résultat: {'Succès' if success else 'Échec'}")
        
        if 'mailgun' in missive.provider.lower():
            print("✅ Provider explicite respecté")
        else:
            print("❌ Provider explicite pas respecté")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def test_send_bulk():
    """Test d'envoi en masse avec fallback."""
    print("\n" + "="*70)
    print("TEST 7: Envoi en masse (send_bulk)")
    print("="*70)
    
    user = User.objects.first()
    
    # Créer plusieurs missives
    missives = []
    for i in range(5):
        missive = Missive.objects.create(
            sender=user,
            missive_type="EMAIL",
            recipient_email=f"test{i}@example.com",
            subject=f"Test bulk {i}",
            body="<p>Hello</p>",
        )
        missives.append(missive)
    
    print(f"{len(missives)} missives créées")
    
    try:
        results = MissiveSender.send_bulk(missives, skip_health_check=True)
        print(f"✅ Résultats:")
        print(f"  - Succès: {results['success']}")
        print(f"  - Échecs: {results['failed']}")
        print(f"  - Erreurs: {len(results['errors'])}")
        
        if results['errors']:
            for error in results['errors']:
                print(f"    - Missive {error['missive_id']}: {error['error']}")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def main():
    """Lance tous les tests."""
    print("\n" + "#"*70)
    print("# TEST DU SYSTÈME DE FALLBACK")
    print("#"*70)
    
    tests = [
        test_basic_send,
        test_failover,
        test_all_providers_fail,
        test_without_fallback,
        test_skip_health_check,
        test_explicit_provider,
        test_send_bulk,
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE dans {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "#"*70)
    print("# TESTS TERMINÉS")
    print("#"*70)


if __name__ == '__main__':
    main()

