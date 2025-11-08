# Guide de Développement - Django Missive

Guide complet pour développer et tester Django Missive en local.

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Installer les dépendances de développement
python dev.py install-dev

# Créer la base de données et le superuser
python dev.py migrate

# Lancer le serveur de développement
python dev.py runserver
```

### 2. Accès à l'interface

Le serveur démarre sur **http://127.0.0.1:8000/**

**Admin Django:**
- URL: http://127.0.0.1:8000/admin/
- Username: `admin`
- Password: `admin`

**Interface Missive:**
- URL: http://127.0.0.1:8000/missive/

## 📋 Commandes Django

### Gestion de la base de données

```bash
# Créer les migrations
python dev.py makemigrations

# Appliquer les migrations
python dev.py migrate

# Créer un superuser manuellement
python dev.py createsuperuser
```

### Serveur de développement

```bash
# Lancer le serveur (auto-création du superuser admin/admin)
python dev.py runserver

# Ou directement avec manage.py
python manage.py runserver

# Sur un port différent
python manage.py runserver 8080
```

### Shell Django

```bash
# Ouvrir un shell Django interactif
python dev.py shell

# Ou directement
python manage.py shell
```

### Autres commandes Django

```bash
# N'importe quelle commande Django fonctionne
python manage.py <command>

# Exemples:
python manage.py showmigrations
python manage.py dbshell
python manage.py check
python manage.py collectstatic
```

## 🧪 Tests et Développement

### Tests

```bash
# Tests rapides
python dev.py test

# Tests verbeux
python dev.py test-verbose

# Avec couverture
python dev.py coverage

# Nettoyer les fichiers de test (htmlcov/, .coverage, etc.)
python dev.py clean-test
```

### Qualité du code

```bash
# Formater le code
python dev.py format

# Vérifier le style
python dev.py lint

# Tout vérifier
python dev.py check
```

## 🔧 Structure du Projet de Test

```
django-missive/
├── manage.py              # Django management (auto-crée superuser)
├── db.sqlite3            # Base de données de développement (auto-créée)
├── tests/
│   ├── settings.py       # Configuration Django pour tests
│   └── urls.py           # URLs avec admin et missive
└── missive/              # Votre app Django
    ├── models.py
    ├── views.py
    ├── admin.py
    └── templates/
```

## 💡 Workflow de Développement

### 1. Modifier le code

```bash
# Éditer les fichiers dans missive/
vim missive/models.py
vim missive/views.py
```

### 2. Créer les migrations

```bash
python dev.py makemigrations
```

### 3. Appliquer les migrations

```bash
python dev.py migrate
```

### 4. Tester dans le navigateur

```bash
python dev.py runserver
# Ouvrir http://127.0.0.1:8000/admin/
```

### 5. Tester avec pytest

```bash
python dev.py test
```

### 6. Formater et vérifier

```bash
python dev.py format
python dev.py check
```

## 🎨 Personnalisation de l'Admin

L'admin est configuré dans `missive/admin.py`:

```python
from django.contrib import admin
from .models import ExampleModel

@admin.register(ExampleModel)
class ExampleModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
```

## 🔍 Debug

### Afficher les requêtes SQL

Dans `tests/settings.py`, ajoutez:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Django Debug Toolbar

```bash
# Installer
pip install django-debug-toolbar

# Ajouter dans tests/settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

## 🗃️ Réinitialiser la Base de Données

```bash
# Supprimer la base de données
rm db.sqlite3

# Recréer tout
python dev.py migrate
```

## 📝 Créer des Données de Test

### Via le Shell

```bash
python dev.py shell
```

```python
from django.contrib.auth.models import User
from missive.models import ExampleModel

# Créer un utilisateur
user = User.objects.create_user('testuser', 'test@example.com', 'password')

# Créer des données
for i in range(10):
    ExampleModel.objects.create(
        user=user,
        title=f'Test {i}',
        content=f'Contenu de test {i}'
    )
```

### Via une Fixture

Créer `missive/fixtures/demo_data.json`:

```json
[
  {
    "model": "missive.examplemodel",
    "pk": 1,
    "fields": {
      "user": 1,
      "title": "Premier test",
      "content": "Contenu de test"
    }
  }
]
```

Charger:

```bash
python manage.py loaddata demo_data
```

## 🚨 Résolution de Problèmes

### Erreur "No migrations to apply"

```bash
python dev.py makemigrations missive
python dev.py migrate
```

### Port 8000 déjà utilisé

```bash
python manage.py runserver 8080
```

### Base de données corrompue

```bash
rm db.sqlite3
python dev.py migrate
```

### Superuser perdu

```bash
python dev.py createsuperuser
```

## 📚 Ressources

- [Documentation Django](https://docs.djangoproject.com/)
- [Django Admin](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)

## 🎯 Checklist avant Commit

- [ ] `python dev.py format` - Code formaté
- [ ] `python dev.py lint` - Pas d'erreurs de lint
- [ ] `python dev.py test` - Tous les tests passent
- [ ] `python dev.py runserver` - L'interface fonctionne
- [ ] Tester l'admin Django
- [ ] Vérifier les migrations

---

**Bon développement ! 🚀**

