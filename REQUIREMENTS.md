# 📦 Guide des Requirements

Guide pour installer uniquement les dépendances dont vous avez besoin.

## 🎯 Fichiers disponibles

```
requirements.txt                # ✅ OBLIGATOIRE - Core Django + validation
requirements-dev.txt            # 🧪 Développement (pytest, black, mypy)
requirements-all.txt            # 📦 Tous les providers
├── requirements-email.txt      # 📧 Email (SendGrid, Mailgun, SES)
├── requirements-sms.txt        # 📱 SMS & Vocal (Twilio, Vonage)
├── requirements-messaging.txt  # 💬 Telegram, Signal, Messenger
├── requirements-push.txt       # 🔔 Notifications push (FCM, APN)
├── requirements-professional.txt # 🏢 Slack, Teams
└── requirements-postal.txt     # 📮 Courrier & LRE
```

## 🚀 Scénarios d'installation

### Scénario 1 : Développement complet
```bash
# Installer TOUT (recommandé pour dev)
pip install -r requirements-dev.txt
pip install -r requirements-all.txt
```

### Scénario 2 : Uniquement email
```bash
pip install -r requirements.txt
pip install -r requirements-email.txt
```

### Scénario 3 : Email + SMS
```bash
pip install -r requirements.txt
pip install -r requirements-email.txt
pip install -r requirements-sms.txt
```

### Scénario 4 : Messageries instantanées uniquement
```bash
pip install -r requirements.txt
pip install -r requirements-messaging.txt
```

### Scénario 5 : Notifications push pour app mobile
```bash
pip install -r requirements.txt
pip install -r requirements-push.txt
```

### Scénario 6 : Messageries professionnelles
```bash
pip install -r requirements.txt
pip install -r requirements-professional.txt
```

### Scénario 7 : Courrier postal & LRE
```bash
pip install -r requirements.txt
pip install -r requirements-postal.txt
```

## 📋 Détail des dépendances par fichier

### requirements.txt (Core - OBLIGATOIRE)
```
Django>=3.2
phonenumbers>=8.13
email-validator>=2.1
requests>=2.31
```
**Poids** : ~20 MB

### requirements-email.txt
```
sendgrid>=6.11
mailgun>=0.1.1
boto3>=1.28  # Amazon SES
```
**Poids** : ~50 MB (à cause de boto3)

### requirements-sms.txt
```
twilio>=8.10
vonage>=3.11
```
**Poids** : ~10 MB

### requirements-messaging.txt
```
python-telegram-bot>=20.7
```
**Poids** : ~15 MB
**Note** : Signal nécessite un service Docker externe

### requirements-push.txt
```
firebase-admin>=6.3
aioapns>=3.1
```
**Poids** : ~80 MB (à cause de firebase-admin)

### requirements-professional.txt
```
slack-sdk>=3.26
msgraph-core>=1.0
msal>=1.25
```
**Poids** : ~30 MB

### requirements-postal.txt
```
reportlab>=4.0
Pillow>=10.1
```
**Poids** : ~40 MB

### requirements-all.txt
Inclut TOUS les fichiers ci-dessus
**Poids total** : ~245 MB

## 💡 Recommandations

### Pour le développement :
```bash
# Installation minimale pour travailler
pip install -r requirements-dev.txt

# Ajouter au fur et à mesure selon vos besoins
pip install -r requirements-email.txt    # Si vous testez l'email
pip install -r requirements-sms.txt      # Si vous testez les SMS
# etc.
```

### Pour la production :
```bash
# Installer uniquement ce que vous utilisez réellement
pip install -r requirements.txt
pip install -r requirements-email.txt
pip install -r requirements-sms.txt
# Ne pas installer requirements-all.txt si vous n'utilisez pas tous les providers
```

## 🎯 Avantages de cette approche

✅ **Modulaire** : Installez uniquement ce dont vous avez besoin  
✅ **Léger** : requirements-email.txt (~50 MB) vs requirements-all.txt (~245 MB)  
✅ **Rapide** : Installation plus rapide en CI/CD  
✅ **Sécurité** : Moins de dépendances = moins de vulnérabilités potentielles  
✅ **Clair** : On sait exactement ce qui est installé  

## 📊 Arbre de dépendances

```
requirements.txt (OBLIGATOIRE)
├── requirements-dev.txt (pour dev uniquement)
└── requirements-all.txt (tous les providers)
    ├── requirements-email.txt
    ├── requirements-sms.txt
    ├── requirements-messaging.txt
    ├── requirements-push.txt
    ├── requirements-professional.txt
    └── requirements-postal.txt
```

Chaque fichier de provider inclut automatiquement `requirements.txt` via `-r requirements.txt`.

