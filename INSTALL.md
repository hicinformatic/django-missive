# 📦 Guide d'installation Django-Missive

## 🔧 Développement local (ce que vous utilisez maintenant)

Votre projet est en **développement local**, pas encore publié sur PyPI.

### Installation des dépendances

```bash
# 1. Core uniquement (Django + validation)
pip install -r requirements.txt

# 2. Développement (tests, linters, formatters)
pip install -r requirements-dev.txt

# 3. Tous les providers (Twilio, SendGrid, Telegram, etc.)
pip install -r requirements-all.txt
```

### Commandes de développement

```bash
# Démarrer le serveur de test
python3 dev.py runserver

# Générer des données d'exemple
python manage.py generate_recipients
python manage.py generate_missives

# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Vérifier le code
python dev.py check
```

---

## 📦 Publication sur PyPI (futur)

Quand vous voudrez publier votre package sur PyPI, les utilisateurs pourront installer avec :

```bash
pip install django-missive
```

### Extras (dépendances optionnelles)

Le fichier `pyproject.toml` définit des groupes optionnels :

```bash
# Syntaxe : pip install nom-package[extra1,extra2]

pip install django-missive[email]        # Providers email uniquement
pip install django-missive[sms]          # Providers SMS & vocal
pip install django-missive[messaging]    # Telegram, Signal, Messenger
pip install django-missive[push]         # Notifications push
pip install django-missive[professional] # Slack, Teams
pip install django-missive[postal]       # Courrier & LRE
pip install django-missive[all]          # Tous les providers
```

### Comment ça fonctionne ?

Le `pyproject.toml` définit :

```toml
[project.optional-dependencies]
email = [
    "sendgrid>=6.11",
    "mailgun>=0.1.1",
    ...
]
```

Quand un utilisateur fait `pip install django-missive[email]`, pip installe :
1. Django-missive (core)
2. Toutes les dépendances du groupe `email`

---

## 🎯 En résumé

### MAINTENANT (développement) :
```bash
pip install -r requirements.txt          # Base
pip install -r requirements-all.txt      # Tous les providers
```

### FUTUR (après publication PyPI) :
```bash
pip install django-missive              # Base
pip install django-missive[all]         # Tous les providers
```

---

## 📚 Ressources

- **pyproject.toml** : Configuration du package (dépendances, metadata)
- **requirements.txt** : Dépendances core pour développement
- **requirements-all.txt** : Tous les providers pour développement
- **requirements-dev.txt** : Outils de développement (pytest, black, etc.)

---

## 🚀 Pour publier sur PyPI (quand vous serez prêt)

```bash
# 1. Builder le package
python -m build

# 2. Publier sur PyPI
python -m twine upload dist/*
```

Ensuite les utilisateurs pourront faire `pip install django-missive` ! 🎉

