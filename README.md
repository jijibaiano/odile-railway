# 🌴 Olivia 2.0 - Phi Phi Paradise Travel Assistant

Assistant voyage intelligent avec mémoire, base de connaissances, et intégrations complètes.

## Fonctionnalités

| Feature | Description |
|---------|-------------|
| 🧠 **Mémoire** | Conversations séparées par client |
| 📚 **Knowledge Base** | Toutes les excursions, prix, liens MyRezz |
| 📱 **WhatsApp** | Réponses automatiques via WAHA |
| 📧 **Email Recap** | Résumé automatique par client |
| 🔗 **Liens Réservation** | MyRezz intégré |

## Variables d'environnement

```bash
# NVIDIA API (obligatoire)
NVIDIA_API_KEY=nvapi-xxx
MODEL=moonshotai/kimi-k2.5  # optionnel

# WAHA WhatsApp
WAHA_API_URL=https://xxx.railway.app
WAHA_API_KEY=wak_xxx
WAHA_SESSION=default

# Email Recap (optionnel)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=phiphiparadis@gmail.com
SMTP_PASS=xxx
RECAP_EMAIL=phiphiparadis@gmail.com
```

## Endpoints API

| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Status & infos |
| `/health` | GET | Health check |
| `/chat` | POST | Chat avec Olivia |
| `/webhook/waha` | POST | Webhook WhatsApp |
| `/conversations` | GET | Liste conversations |
| `/conversations/{id}` | GET | Détail conversation |
| `/conversations/{id}/email-recap` | POST | Envoyer récap email |

## Exemple Chat

```bash
curl -X POST https://xxx.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Quelles excursions depuis Krabi?", "phone": "+33612345678"}'
```

## Base de Connaissances

Olivia connaît:
- ✅ Toutes les excursions (Phi Phi, Krabi, Phuket, Bangkok, Chiang Mai)
- ✅ Prix en Baht
- ✅ Horaires
- ✅ Liens de réservation MyRezz
- ✅ Politiques (pas d'acompte, réductions enfants)
- ✅ Contacts

## Mémoire

Chaque client a sa propre conversation:
- Historique des 20 derniers messages
- Infos collectées (prénom, dates, hôtel, nombre de personnes)
- Intérêts détectés

---

🌴 *Phi Phi Paradise Travel - Licence TAT 33/10549*
