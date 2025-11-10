# 📦 Guide des Requirements Django-Missive

Ce document liste tous les fichiers requirements disponibles et comment les utiliser.

## 🎯 Installation Rapide

### Core (minimum requis)
```bash
pip install -r requirements.txt
```

### Tous les providers (installation complète)
```bash
pip install -r requirements-all.txt
```

## 📋 Requirements par Provider (Installation Sélective)

### 📧 Providers Email

#### SendGrid
```bash
pip install -r requirements-sendgrid.txt
```
- Package: `sendgrid>=6.11`

#### Mailgun
```bash
pip install -r requirements-mailgun.txt
```
- Package: `mailgun>=0.1.1`

#### Brevo (ex-Sendinblue)
```bash
pip install -r requirements-brevo.txt
```
- Package: `sib-api-v3-sdk>=7.6`

#### Django Email
Aucune dépendance supplémentaire (utilise SMTP Django)

---

### 📱 Providers SMS

#### Twilio (SMS + WhatsApp)
```bash
pip install -r requirements-twilio.txt
```
- Package: `twilio>=8.10`
- Supporte: SMS, WhatsApp (BRANDED)

#### SMSPartner (SMS + Email + Voice)
Utilise `requests` (déjà dans `requirements.txt`)
```bash
pip install -r requirements.txt
```

---

### 🏷️ Providers Messageries de Marque (BRANDED)

#### Slack
```bash
pip install -r requirements-slack.txt
```
- Package: `slack-sdk>=3.26`

#### Microsoft Teams
```bash
pip install -r requirements-teams.txt
```
- Packages: `msgraph-core>=1.0`, `msal>=1.25`

#### Telegram
```bash
pip install -r requirements-telegram.txt
```
- Package: `python-telegram-bot>=20.7`

#### Signal
Utilise `requests` (déjà dans `requirements.txt`)

#### Messenger (Facebook)
Utilise `requests` (déjà dans `requirements.txt`)

---

### 🔔 Providers Push Notifications

#### Firebase Cloud Messaging (FCM)
```bash
pip install -r requirements-fcm.txt
```
- Package: `firebase-admin>=6.3`

#### Apple Push Notification (APN)
```bash
pip install -r requirements-apn.txt
```
- Package: `aioapns>=3.1`

---

### 📮 Providers Courrier Postal

#### La Poste, AR24, CertEurope
Utilisent `requests` + `reportlab` + `Pillow` (déjà dans `requirements.txt`)

---

## 📑 Fichiers de Catégorie (Legacy - pour compatibilité)

Les anciens fichiers par catégorie existent toujours pour une installation groupée :

```bash
# Tous les providers email
pip install -r requirements-email.txt

# Tous les providers SMS
pip install -r requirements-sms.txt

# Tous les providers messageries de marque
pip install -r requirements-branded.txt

# Tous les providers push
pip install -r requirements-push.txt

# Tous les providers postal
pip install -r requirements-postal.txt
```

## 🎯 Recommandation

**Pour production** : Installez uniquement les providers dont vous avez besoin
```bash
# Exemple : Email avec SendGrid + SMS avec Twilio
pip install -r requirements-sendgrid.txt
pip install -r requirements-twilio.txt
```

**Pour développement** : Installez tous les providers
```bash
pip install -r requirements-all.txt
```

## 📊 Vue d'Ensemble

| Provider | Fichier Requirements | Packages |
|----------|---------------------|----------|
| **SendGrid** | `requirements-sendgrid.txt` | `sendgrid` |
| **Mailgun** | `requirements-mailgun.txt` | `mailgun` |
| **Brevo** | `requirements-brevo.txt` | `sib-api-v3-sdk` |
| **Twilio** | `requirements-twilio.txt` | `twilio` |
| **Slack** | `requirements-slack.txt` | `slack-sdk` |
| **Teams** | `requirements-teams.txt` | `msgraph-core`, `msal` |
| **Telegram** | `requirements-telegram.txt` | `python-telegram-bot` |
| **FCM** | `requirements-fcm.txt` | `firebase-admin` |
| **APN** | `requirements-apn.txt` | `aioapns` |
| **SMSPartner** | `requirements.txt` | `requests` (core) |
| **Django Email** | `requirements.txt` | Aucun (core Django) |
| **Signal** | `requirements.txt` | `requests` (core) |
| **Messenger** | `requirements.txt` | `requests` (core) |
| **LaPoste** | `requirements.txt` | `requests` (core) |
| **AR24** | `requirements.txt` | `requests` (core) |
| **CertEurope** | `requirements.txt` | `requests` (core) |

## 🔗 Liens Utiles

- **Documentation API** : Voir `documentation_url` dans l'admin Django
- **Status SLA** : Voir `status_url` dans l'admin Django
