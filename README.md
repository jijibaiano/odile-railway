# 🌴 Odile - Phi Phi Paradise Travel Bot

Assistant voyage intelligent propulsé par **NVIDIA Kimi K2.5**.

## Déploiement sur Railway

### 1. Fork/Clone ce repo

```bash
git clone <ton-repo>
cd odile-railway
```

### 2. Crée un projet sur Railway

1. Va sur [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Sélectionne ce repo

### 3. Configure les variables d'environnement

Dans Railway → ton projet → Variables :

```
NVIDIA_API_KEY=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
```

### 4. Déploie !

Railway déploie automatiquement à chaque push.

---

## API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Page d'accueil |
| `/health` | GET | Health check |
| `/info` | GET | Infos agence |
| `/chat` | POST | Chat avec Odile |
| `/test` | GET | Test rapide |
| `/webhook/whatsapp` | POST | Webhook WhatsApp |

### Exemple d'utilisation

```bash
curl -X POST https://ton-app.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour! Quelles excursions proposez-vous?"}'
```

### Réponse

```json
{
  "response": "Bonjour ! 🌴 Bienvenue chez Phi Phi Paradise Travel...",
  "model": "moonshotai/kimi-k2.5"
}
```

---

## Intégration WhatsApp

Pour connecter à WhatsApp (via WAHA ou autre), configure le webhook :

```
https://ton-app.railway.app/webhook/whatsapp
```

---

## Structure

```
odile-railway/
├── main.py           # Application FastAPI
├── requirements.txt  # Dépendances Python
├── Procfile          # Commande de démarrage
├── railway.json      # Config Railway
├── .env.example      # Variables d'env (exemple)
└── README.md         # Ce fichier
```

---

## Contact

- **WhatsApp TH:** +66 99 11 58 304
- **WhatsApp FR:** +33 7 85 65 40 82
- **Site:** https://phiphiparadisetravel.com

🌴 *Phi Phi Paradise Travel - Licence TAT 33/10549*
