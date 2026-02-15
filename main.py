"""
OLIVIA 5.0 - AGENT PARFAIT
==========================
- Attente 2-3 minutes avant réponse (humain occupé)
- Mémoire complète et persistante
- Fiches clients Slack
- Pas de liens direct - qualifier d'abord
- Flux ultra réaliste
"""

import os
import json
import requests
import httpx
import asyncio
import random
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

app = FastAPI(title="Olivia 6.0 - Ultra Intelligente", version="6.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ============================================
# Configuration
# ============================================
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
MODEL = os.getenv("MODEL", "meta/llama-3.3-70b-instruct")
WAHA_API_URL = os.getenv("WAHA_API_URL", "")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "C05R37D3LRM")

# Mémoire
DATA_DIR = Path("/tmp/olivia_data")
DATA_DIR.mkdir(exist_ok=True)
CLIENTS_DIR = DATA_DIR / "clients"
CLIENTS_DIR.mkdir(exist_ok=True)

# ============================================
# TIMING HUMAIN - 2-3 MINUTES !
# ============================================
TIMING = {
    # Délai INITIAL avant toute action (humain occupé)
    "initial_wait_min": 90,   # 1.5 minutes minimum
    "initial_wait_max": 180,  # 3 minutes maximum
    
    # Délai après seen, avant de commencer à taper
    "after_seen_min": 30,     # 30 secondes
    "after_seen_max": 90,     # 1.5 minutes
    
    # Vitesse de frappe (lente pour être réaliste)
    "typing_speed": 20,       # 20 caractères/seconde (lent)
    
    # Délai avant envoi final
    "before_send_min": 2,
    "before_send_max": 5,
    
    # Pause entre messages multiples
    "between_messages_min": 15,
    "between_messages_max": 45,
}

# ============================================
# BASE DE CONNAISSANCES (sans liens directs)
# ============================================
KNOWLEDGE = """
## PHI PHI PARADISE TRAVEL

### AGENCE
- Site: phiphiparadisetravel.com
- WhatsApp TH: +66 99 11 58 304
- WhatsApp FR: +33 7 85 65 40 82
- Licence TAT: 33/10549

### POLITIQUE
✅ Aucun acompte
✅ Guides francophones
✅ Petits groupes (10-12 max)
✅ Transfert hôtel inclus
👶 -9 ans: -50% | -3 ans: gratuit

### EXCURSIONS PHI PHI
- Matin Maya: ฿800 (lever soleil Maya Bay)
- Magique Turquoise: ฿700
- Bateau Pirate Phoenix: ฿1,800 (familles)
- Bateau Pirate Dragon: ฿1,800 (festif sunset)
- Long Tail Privé: ฿4,200 (6h)

### PLONGÉE PHI PHI
- Baptême: ฿4,000 (tout inclus)
- Fun Dive: ฿3,300
- Open Water PADI: ฿13,700

### KRABI
- Hong Island Sunset BBQ: ฿2,500 (planctons!)
- 4 Islands Sunset: ฿2,500
- James Bond Island: ฿2,500
- Éléphants + Cascades: ฿3,000

### PHUKET
- Phi Phi Sunrise Premium: ฿3,500
- Similan Islands: ฿2,000

### BANGKOK
- Temples (Grand Palace): demi-journée
- Ayutthaya: journée
- Marchés flottants: matinée

### RECOMMANDATIONS
- Familles → Bateau Phoenix, Éléphants
- Couples → Matin Maya, Hong Island Sunset
- Fêtards → Bateau Dragon
- Budget → Matin Maya (฿800)
"""

# ============================================
# MÉMOIRE CLIENT COMPLÈTE
# ============================================
def get_client_file(phone: str) -> Path:
    h = hashlib.md5(phone.encode()).hexdigest()[:12]
    return CLIENTS_DIR / f"{h}.json"

def load_client(phone: str) -> dict:
    f = get_client_file(phone)
    if f.exists():
        return json.loads(f.read_text())
    return {
        "phone": phone,
        "phone_hash": hashlib.md5(phone.encode()).hexdigest()[:12],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        
        # Infos client
        "prenom": None,
        "langue": None,  # fr ou en
        "localisation": None,  # phi phi, krabi, phuket, bangkok
        "dates_voyage": None,
        "nb_personnes": None,
        "type_groupe": None,  # famille, couple, amis, solo
        "budget": None,  # petit, moyen, premium
        "interets": [],  # plongée, nature, fête, culture, etc.
        
        # État commercial
        "statut": "nouveau",  # nouveau, qualifié, intéressé, prêt_réserver, réservé
        "excursions_interessees": [],
        "excursions_recommandees": [],
        "lien_envoye": False,
        
        # Historique complet
        "messages": [],
        "total_messages": 0,
        "derniere_interaction": None,
        
        # Notes
        "notes": [],
        "slack_notified": False
    }

def save_client(phone: str, client: dict):
    client["updated_at"] = datetime.now().isoformat()
    get_client_file(phone).write_text(json.dumps(client, ensure_ascii=False, indent=2))

def add_message(phone: str, role: str, content: str) -> dict:
    client = load_client(phone)
    client["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # Garder TOUT l'historique (pas de limite)
    client["total_messages"] += 1
    client["derniere_interaction"] = datetime.now().isoformat()
    
    # Détecter la langue
    if not client["langue"]:
        fr_words = ["bonjour", "salut", "merci", "excursion", "combien", "je", "nous", "prix"]
        en_words = ["hello", "hi", "thanks", "trip", "how much", "i", "we", "price"]
        content_lower = content.lower()
        fr_count = sum(1 for w in fr_words if w in content_lower)
        en_count = sum(1 for w in en_words if w in content_lower)
        if fr_count > en_count:
            client["langue"] = "fr"
        elif en_count > fr_count:
            client["langue"] = "en"
    
    save_client(phone, client)
    return client

def extract_client_info(phone: str, message: str):
    """Extrait et sauvegarde les infos du message"""
    client = load_client(phone)
    msg = message.lower()
    
    # Prénom
    if not client["prenom"]:
        patterns = [
            r"je m'appelle\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)",
            r"my name is\s+([A-Za-z]+)",
            r"moi c'est\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)",
            r"i'm\s+([A-Za-z]+)",
            r"c'est\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)\s+[!.,]",
        ]
        for p in patterns:
            m = re.search(p, message, re.I)
            if m:
                client["prenom"] = m.group(1).title()
                break
    
    # Localisation
    if not client["localisation"]:
        lieux = {
            "phi phi": "Phi Phi",
            "krabi": "Krabi",
            "ao nang": "Ao Nang",
            "phuket": "Phuket",
            "bangkok": "Bangkok",
            "chiang mai": "Chiang Mai",
            "lanta": "Koh Lanta"
        }
        for key, val in lieux.items():
            if key in msg:
                client["localisation"] = val
                break
    
    # Nombre de personnes
    if not client["nb_personnes"]:
        m = re.search(r"(\d+)\s*(?:personnes?|pers|people|pax|adultes?|nous sommes)", msg)
        if m:
            client["nb_personnes"] = int(m.group(1))
    
    # Type de groupe
    if not client["type_groupe"]:
        if any(w in msg for w in ["famille", "family", "enfant", "kid", "bébé", "baby"]):
            client["type_groupe"] = "famille"
        elif any(w in msg for w in ["couple", "amoureux", "honeymoon", "lune de miel", "romantique"]):
            client["type_groupe"] = "couple"
        elif any(w in msg for w in ["amis", "friends", "groupe", "group"]):
            client["type_groupe"] = "amis"
        elif any(w in msg for w in ["seul", "solo", "alone"]):
            client["type_groupe"] = "solo"
    
    # Intérêts
    interets_map = {
        "plongée": ["plongée", "plonger", "diving", "scuba", "snorkeling"],
        "nature": ["nature", "éléphant", "elephant", "jungle", "cascade", "waterfall"],
        "fête": ["fête", "party", "festif", "ambiance", "bar", "alcool"],
        "culture": ["temple", "culture", "histoire", "history", "buddha"],
        "aventure": ["aventure", "adventure", "kayak", "escalade"],
        "détente": ["détente", "relax", "tranquille", "calme", "peaceful"],
        "photo": ["photo", "instagram", "sunset", "coucher de soleil", "lever du soleil"]
    }
    for interet, keywords in interets_map.items():
        if any(kw in msg for kw in keywords) and interet not in client["interets"]:
            client["interets"].append(interet)
    
    # Dates
    if not client["dates_voyage"]:
        # Format DD/MM ou DD-MM
        m = re.search(r"(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)", message)
        if m:
            client["dates_voyage"] = m.group(1)
        # Mois
        mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", 
                "août", "septembre", "octobre", "novembre", "décembre",
                "january", "february", "march", "april", "may", "june", 
                "july", "august", "september", "october", "november", "december"]
        for m in mois:
            if m in msg:
                client["dates_voyage"] = m.capitalize()
                break
    
    # Mettre à jour le statut
    if client["statut"] == "nouveau" and (client["prenom"] or client["localisation"] or client["nb_personnes"]):
        client["statut"] = "qualifié"
    
    if any(w in msg for w in ["intéressé", "interested", "réserver", "book", "combien", "prix", "price", "how much"]):
        client["statut"] = "intéressé"
    
    save_client(phone, client)
    return client

def get_client_context(phone: str) -> str:
    """Génère le contexte COMPLET pour l'IA"""
    client = load_client(phone)
    
    ctx = "\n## FICHE CLIENT:\n"
    ctx += f"- Téléphone: {phone}\n"
    ctx += f"- Statut: {client['statut']}\n"
    
    if client["prenom"]:
        ctx += f"- Prénom: {client['prenom']}\n"
    if client["langue"]:
        ctx += f"- Langue: {client['langue']}\n"
    if client["localisation"]:
        ctx += f"- Localisation: {client['localisation']}\n"
    if client["dates_voyage"]:
        ctx += f"- Dates voyage: {client['dates_voyage']}\n"
    if client["nb_personnes"]:
        ctx += f"- Nombre personnes: {client['nb_personnes']}\n"
    if client["type_groupe"]:
        ctx += f"- Type groupe: {client['type_groupe']}\n"
    if client["interets"]:
        ctx += f"- Intérêts: {', '.join(client['interets'])}\n"
    if client["excursions_recommandees"]:
        ctx += f"- Excursions déjà recommandées: {', '.join(client['excursions_recommandees'])}\n"
    if client["lien_envoye"]:
        ctx += f"- Lien réservation déjà envoyé: OUI\n"
    
    ctx += f"\n## HISTORIQUE COMPLET ({len(client['messages'])} messages):\n"
    for msg in client["messages"][-15:]:  # 15 derniers pour le contexte
        who = "Client" if msg["role"] == "user" else "Olivia"
        ts = msg["timestamp"][:16].replace("T", " ")
        ctx += f"[{ts}] {who}: {msg['content']}\n"
    
    return ctx

# ============================================
# SLACK - Fiches clients
# ============================================
async def send_slack_notification(client: dict, message_type: str = "new"):
    """Envoie une notification Slack"""
    if not SLACK_WEBHOOK:
        print("SLACK_WEBHOOK non configuré")
        return
    
    if message_type == "new":
        emoji = "🆕"
        title = "Nouveau client WhatsApp"
    elif message_type == "update":
        emoji = "📝"
        title = "Mise à jour client"
    elif message_type == "hot":
        emoji = "🔥"
        title = "Client CHAUD - Prêt à réserver!"
    else:
        emoji = "💬"
        title = "Activité client"
    
    # Construire le message Slack
    fields = []
    
    if client.get("prenom"):
        fields.append({"title": "Prénom", "value": client["prenom"], "short": True})
    
    fields.append({"title": "Téléphone", "value": client["phone"][:15] + "...", "short": True})
    fields.append({"title": "Statut", "value": client["statut"].upper(), "short": True})
    
    if client.get("localisation"):
        fields.append({"title": "Localisation", "value": client["localisation"], "short": True})
    if client.get("nb_personnes"):
        fields.append({"title": "Personnes", "value": str(client["nb_personnes"]), "short": True})
    if client.get("type_groupe"):
        fields.append({"title": "Type", "value": client["type_groupe"], "short": True})
    if client.get("dates_voyage"):
        fields.append({"title": "Dates", "value": client["dates_voyage"], "short": True})
    if client.get("interets"):
        fields.append({"title": "Intérêts", "value": ", ".join(client["interets"]), "short": False})
    
    # Dernier message
    if client.get("messages"):
        last_msg = client["messages"][-1]
        if last_msg["role"] == "user":
            fields.append({"title": "Dernier message", "value": last_msg["content"][:200], "short": False})
    
    payload = {
        "channel": SLACK_CHANNEL,
        "username": "Olivia Bot",
        "icon_emoji": ":palm_tree:",
        "attachments": [{
            "color": "#36a64f" if message_type == "new" else "#ff9900" if message_type == "hot" else "#439FE0",
            "pretext": f"{emoji} {title}",
            "fields": fields,
            "footer": "Phi Phi Paradise Travel",
            "ts": int(datetime.now().timestamp())
        }]
    }
    
    try:
        async with httpx.AsyncClient() as http:
            await http.post(SLACK_WEBHOOK, json=payload, timeout=10)
            print(f"📤 Slack notifié: {message_type}")
    except Exception as e:
        print(f"Slack error: {e}")

# ============================================
# WAHA - Ultra humain
# ============================================
async def waha_call(endpoint: str, data: dict):
    if not WAHA_API_KEY:
        return None
    try:
        async with httpx.AsyncClient() as http:
            r = await http.post(
                f"{WAHA_API_URL}/api/{endpoint}",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, **data},
                timeout=15
            )
            return r
    except Exception as e:
        print(f"WAHA {endpoint}: {e}")
        return None

async def waha_seen(chat_id: str):
    await waha_call("sendSeen", {"chatId": chat_id})

async def waha_typing_start(chat_id: str):
    await waha_call("startTyping", {"chatId": chat_id})

async def waha_typing_stop(chat_id: str):
    await waha_call("stopTyping", {"chatId": chat_id})

async def waha_send(chat_id: str, text: str):
    r = await waha_call("sendText", {"chatId": chat_id, "text": text})
    return r and r.status_code in [200, 201]

async def waha_react(chat_id: str, msg_id: str, emoji: str):
    await waha_call("reaction", {"chatId": chat_id, "messageId": msg_id, "reaction": emoji})

# ============================================
# IA - Prompt intelligent
# ============================================
SYSTEM_PROMPT = f"""Tu es Olivia, assistante voyage experte de Phi Phi Paradise Travel.

## QUI TU ES
Tu es une vraie assistante passionnée par la Thaïlande, pas un bot. Tu as vécu à Krabi pendant des années, tu connais chaque île, chaque plage, chaque recoin secret. Tu parles aux clients comme à des amis que tu veux aider à passer des vacances inoubliables.

## TA PERSONNALITÉ
- Chaleureuse, enthousiaste, authentique
- Tu ADORES parler de la Thaïlande et partager tes connaissances
- Tu poses des questions parce que tu veux vraiment comprendre ce que le client cherche
- Tu donnes des conseils personnalisés, pas des réponses génériques
- Bilingue FR/EN - tu t'adaptes naturellement

## COMMENT TU RÉPONDS
- Des réponses DÉVELOPPÉES et NATURELLES (comme une vraie conversation)
- Tu expliques POURQUOI tu recommandes quelque chose
- Tu partages des anecdotes, des conseils d'initiée
- Tu décris les expériences de manière vivante
- Tu utilises des emojis naturellement (🌴🌊🐘✨)

## PROCESSUS DE QUALIFICATION (naturel, pas robotique)
Tu veux comprendre le client pour lui proposer L'EXCURSION PARFAITE:
- D'où part-il ? (Phi Phi, Krabi, Phuket, Bangkok, Chiang Mai?)
- Quand voyage-t-il ?
- Avec qui ? (couple, famille avec enfants, groupe d'amis, solo?)
- Qu'est-ce qui le fait rêver ? (plongée, plages désertes, nature, fête, temples?)
- Budget ? (économique ou premium?)

Pose ces questions NATURELLEMENT au fil de la conversation, pas comme un interrogatoire.

## RECOMMANDATIONS PERSONNALISÉES
Une fois que tu comprends le client:
- Recommande 1-3 excursions PARFAITES pour lui
- Explique POURQUOI chaque excursion lui correspond
- Donne les prix en Baht (฿)
- Décris ce qu'il va vivre, pas juste une liste

## LIENS DE RÉSERVATION
- N'envoie le lien QUE quand le client veut réserver
- Format: https://booking.myrezapp.com/fr/online/booking/step1/16686/[ID]
- IDs: Matin Maya=100673, Pirate=71115, Hong Island=86352, Baptême=71911, etc.

## INFOS IMPORTANTES
- Aucun acompte requis (argument de vente!)
- Enfants -9 ans: -50%, -3 ans: gratuit
- Guides francophones disponibles
- Transfert hôtel toujours inclus
- Contact direct: +66 99 11 58 304 (Jiji)

{KNOWLEDGE}
"""

def call_ai(messages: list) -> str:
    if not NVIDIA_API_KEY:
        raise Exception("NVIDIA_API_KEY manquante")
    
    r = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": 1024,  # Réponses développées
            "temperature": 0.8,
            "top_p": 0.9,
            "stream": True,
            "chat_template_kwargs": {"thinking": True}
        },
        stream=True,
        timeout=120
    )
    
    content = ""
    for line in r.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: ") and line[6:] != "[DONE]":
                try:
                    chunk = json.loads(line[6:])
                    content += chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                except:
                    pass
    return content.strip()

# ============================================
# TRAITEMENT MESSAGE - ULTRA LENT ET HUMAIN
# ============================================
async def process_message(chat_id: str, message: str, msg_id: str = None):
    """Traite un message avec timing TRÈS humain (2-3 min)"""
    try:
        print(f"📩 [{chat_id[:12]}...] Message reçu, attente longue...")
        
        # ═══════════════════════════════════════════════════
        # PHASE 1: ATTENTE INITIALE LONGUE (2-3 MINUTES)
        # Simule un humain occupé qui ne répond pas tout de suite
        # ═══════════════════════════════════════════════════
        initial_wait = random.uniform(TIMING["initial_wait_min"], TIMING["initial_wait_max"])
        print(f"⏳ Attente initiale: {initial_wait:.0f}s ({initial_wait/60:.1f} min)")
        await asyncio.sleep(initial_wait)
        
        # ═══════════════════════════════════════════════════
        # PHASE 2: MARQUER COMME LU
        # ═══════════════════════════════════════════════════
        await waha_seen(chat_id)
        print(f"✓✓ Message vu")
        
        # ═══════════════════════════════════════════════════
        # PHASE 3: PAUSE APRÈS LECTURE (réflexion)
        # ═══════════════════════════════════════════════════
        after_seen = random.uniform(TIMING["after_seen_min"], TIMING["after_seen_max"])
        print(f"🤔 Réflexion: {after_seen:.0f}s")
        await asyncio.sleep(after_seen)
        
        # ═══════════════════════════════════════════════════
        # PHASE 4: SAUVEGARDER & EXTRAIRE INFOS
        # ═══════════════════════════════════════════════════
        add_message(chat_id, "user", message)
        client = extract_client_info(chat_id, message)
        
        # Notification Slack si nouveau client ou client chaud
        if not client.get("slack_notified"):
            await send_slack_notification(client, "new")
            client["slack_notified"] = True
            save_client(chat_id, client)
        elif client["statut"] == "intéressé":
            await send_slack_notification(client, "hot")
        
        # ═══════════════════════════════════════════════════
        # PHASE 5: GÉNÉRER RÉPONSE IA
        # ═══════════════════════════════════════════════════
        context = get_client_context(chat_id)
        ai_messages = [
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\n## CONTEXTE CLIENT ACTUEL:\n{context}"},
            {"role": "user", "content": message}
        ]
        
        # Start typing AVANT l'appel IA
        await waha_typing_start(chat_id)
        print(f"⌨️ Typing started...")
        
        response = call_ai(ai_messages)
        
        # ═══════════════════════════════════════════════════
        # PHASE 6: SIMULER LA FRAPPE
        # ═══════════════════════════════════════════════════
        typing_time = len(response) / TIMING["typing_speed"]
        # Ajouter variation humaine
        typing_time *= random.uniform(0.9, 1.3)
        typing_time = max(3, min(typing_time, 30))  # Entre 3 et 30 sec
        
        print(f"⌨️ Frappe simulée: {typing_time:.0f}s")
        await asyncio.sleep(typing_time)
        
        await waha_typing_stop(chat_id)
        
        # ═══════════════════════════════════════════════════
        # PHASE 7: PAUSE FINALE (relecture)
        # ═══════════════════════════════════════════════════
        before_send = random.uniform(TIMING["before_send_min"], TIMING["before_send_max"])
        await asyncio.sleep(before_send)
        
        # ═══════════════════════════════════════════════════
        # PHASE 8: ENVOYER
        # ═══════════════════════════════════════════════════
        await waha_send(chat_id, response)
        add_message(chat_id, "assistant", response)
        
        total_time = initial_wait + after_seen + typing_time + before_send
        print(f"✅ [{chat_id[:12]}...] Répondu en {total_time/60:.1f} min")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        await waha_typing_stop(chat_id)
        await waha_send(chat_id, "Désolée, petit souci technique! Contacte Jiji au +66 99 11 58 304 🙏")

# ============================================
# ROUTES API
# ============================================
@app.get("/")
async def root():
    clients = list(CLIENTS_DIR.glob("*.json"))
    return {
        "name": "Olivia 6.0 - Ultra Intelligente (Llama 3.3 70B)",
        "version": "6.0",
        "status": "online",
        "model": MODEL,
        "features": [
            "llama-3.3-70b (ultra intelligent)",
            "réponses développées naturelles",
            "mémoire complète persistante",
            "qualification personnalisée",
            "timing humain (2-3 min)",
            "slack notifications"
        ],
        "whatsapp": "connected" if WAHA_API_KEY else "not configured",
        "slack": "configured" if SLACK_WEBHOOK else "not configured",
        "clients": len(clients),
        "timing": {
            "initial_wait": f"{TIMING['initial_wait_min']}-{TIMING['initial_wait_max']}s",
            "after_seen": f"{TIMING['after_seen_min']}-{TIMING['after_seen_max']}s"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/webhook/waha")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        
        if body.get("event") == "message":
            payload = body.get("payload", {})
            
            if payload.get("fromMe"):
                return {"status": "ignored"}
            
            chat_id = payload.get("from", "")
            message = payload.get("body", "")
            msg_type = payload.get("type", "")
            msg_id = payload.get("id", "")
            
            if msg_type == "chat" and message:
                background_tasks.add_task(process_message, chat_id, message, msg_id)
                return {"status": "queued", "wait": "2-3 minutes"}
        
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/clients")
async def list_clients():
    clients = []
    for f in CLIENTS_DIR.glob("*.json"):
        c = json.loads(f.read_text())
        clients.append({
            "hash": c["phone_hash"],
            "prenom": c.get("prenom"),
            "statut": c["statut"],
            "localisation": c.get("localisation"),
            "messages": c["total_messages"],
            "last": c.get("derniere_interaction")
        })
    return sorted(clients, key=lambda x: x.get("last") or "", reverse=True)

@app.get("/clients/{phone_hash}")
async def get_client(phone_hash: str):
    for f in CLIENTS_DIR.glob("*.json"):
        c = json.loads(f.read_text())
        if c["phone_hash"] == phone_hash:
            return c
    raise HTTPException(404)

@app.post("/test-slack")
async def test_slack():
    """Test Slack notification"""
    test_client = {
        "phone": "+33612345678",
        "prenom": "Test",
        "statut": "nouveau",
        "localisation": "Krabi",
        "nb_personnes": 2,
        "interets": ["plongée", "nature"],
        "messages": [{"role": "user", "content": "Bonjour, je cherche une excursion!", "timestamp": datetime.now().isoformat()}]
    }
    await send_slack_notification(test_client, "new")
    return {"status": "sent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
