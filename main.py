"""
OLIVIA 4.0 - ULTRA HUMAINE
==========================
Comportement indiscernable d'un humain:
- Temps de réponse variables et réalistes
- Typing indicator avec durée calculée
- Réactions aux messages (👍, ❤️, etc.)
- Messages courts et naturels
- Parfois plusieurs messages au lieu d'un long
- Présence (online/offline)
- Erreurs de frappe simulées (optionnel)
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

app = FastAPI(
    title="Olivia 4.0 - Ultra Humaine",
    description="Agent conversationnel indiscernable d'un humain",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Configuration
# ============================================
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = os.getenv("MODEL", "moonshotai/kimi-k2.5")

# WAHA
WAHA_API_URL = os.getenv("WAHA_API_URL", "")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

# Mémoire
DATA_DIR = Path("/tmp/olivia_data")
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR = DATA_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)

# ============================================
# COMPORTEMENT HUMAIN - Configuration
# ============================================
HUMAN_CONFIG = {
    # Délai avant de lire le message (secondes)
    "read_delay_min": 1.5,
    "read_delay_max": 8.0,
    
    # Délai de réflexion après lecture (secondes)
    "think_delay_min": 2.0,
    "think_delay_max": 6.0,
    
    # Vitesse de frappe (caractères par seconde)
    "typing_speed_min": 25,  # Frappe lente
    "typing_speed_max": 50,  # Frappe rapide
    
    # Délai entre l'arrêt de frappe et l'envoi
    "send_delay_min": 0.3,
    "send_delay_max": 1.2,
    
    # Probabilité de réagir au message (0-1)
    "reaction_probability": 0.15,
    
    # Probabilité de diviser un long message
    "split_message_probability": 0.4,
    
    # Longueur max avant de considérer un message comme "long"
    "long_message_threshold": 300,
    
    # Réactions possibles avec leurs probabilités
    "reactions": {
        "👍": 0.3,
        "😊": 0.25,
        "🌴": 0.2,
        "❤️": 0.15,
        "🙏": 0.1,
    }
}

# ============================================
# BASE DE CONNAISSANCES
# ============================================
KNOWLEDGE_BASE = """
## 🌴 PHI PHI PARADISE TRAVEL

### INFOS AGENCE
- Site: https://phiphiparadisetravel.com
- WhatsApp TH: +66 99 11 58 304
- WhatsApp FR: +33 7 85 65 40 82
- Email: phiphiparadis@gmail.com
- Licence TAT: 33/10549

### POLITIQUE
✅ Aucun acompte requis
✅ Guides francophones
✅ Petits groupes (max 10-12)
✅ Transfert hôtel inclus
👶 Enfants 3-9 ans: -50%
👶 Enfants -3 ans: GRATUIT

---

## EXCURSIONS PHI PHI

### ⭐ Matin Maya - ฿800/pers
- 6h30-11h30 (5h)
- Maya Bay au lever du soleil (avant la foule!)
- Pileh Lagoon, Viking Cave, Monkey Beach
- 🔗 MyRezz: https://booking.myrezapp.com/fr/online/booking/step1/16686/100673
- 🌐 Site: https://phiphiparadisetravel.com/excursion/matin-maya

### Magique Turquoise - ฿700/pers
- Pileh Lagoon, Viking Cave, Loh Samah
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/98661

### Bateau Pirate Phoenix - ฿1,800/pers
- 9h30-15h30 (6h) - Ambiance calme, familles
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71115

### Bateau Pirate Dragon - ฿1,800/pers
- 11h30-19h00 - Ambiance festive, sunset
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71115

### Long Tail Privé - ฿4,200/bateau (6h)
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71403

---

## PLONGÉE PHI PHI

### Baptême - ฿3,400 + ฿600 parc
- 2 plongées 50min, instructeur francophone
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71911

### Fun Dive - ฿2,700 + ฿600 parc
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71667

### Open Water PADI - ฿12,900 + ฿800
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/71669

---

## EXCURSIONS KRABI

### ⭐ Hong Island Sunset BBQ - ฿2,500/pers
- 11h-20h - Lagon secret, planctons bioluminescents!
- 🌐 https://phiphiparadisetravel.com/excursion/hong-island-sunset

### 4 Islands Sunset BBQ - ฿2,500/pers
- Tup Island, Chicken Island, Poda
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/86354

### James Bond Island - ฿2,500/pers
- Canoë mangroves, village flottant
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/84187

### 🐘 Éléphants + Cascades - ฿3,000/pers
- 3h avec éléphants + Parc National Bencha
- 🌐 https://phiphiparadisetravel.com/excursion/elephant-sanctuary

### Seul au Monde - ฿2,500/pers
- Koh Yao Yai, île sauvage secrète

---

## EXCURSIONS PHUKET

### Phi Phi Sunrise Premium - ฿3,500/pers
- Maya Bay au lever du soleil, max 15 pers
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/84448

### Similan Islands - ฿2,000/pers
- Meilleur snorkeling de Thaïlande
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/84442

---

## BANGKOK

### Temples (Grand Palace, Wat Pho)
- Guide FR: https://booking.myrezapp.com/fr/online/booking/step1/16686/86582

### Ayutthaya
- Guide FR: https://booking.myrezapp.com/fr/online/booking/step1/16686/86588

### Marchés flottants
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/86552

---

## CHIANG MAI

### Éléphants - ฿1,500/pers
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/86591

### Temples Chiang Rai - ฿1,900/pers
- 🔗 https://booking.myrezapp.com/fr/online/booking/step1/16686/86592

---

## FERRIES
- Phi Phi → Phuket: ฿1,100
- Phi Phi → Krabi: ฿1,100

---

## RECOMMANDATIONS
- **Familles**: Bateau Phoenix, Éléphants
- **Couples**: Matin Maya, Hong Island Sunset
- **Fêtards**: Bateau Dragon
- **Aventuriers**: Plongée, Temple du Tigre
- **Budget**: Matin Maya (฿800), Magique Turquoise (฿700)
"""

# ============================================
# Mémoire persistante
# ============================================
def get_hash(phone: str) -> str:
    return hashlib.md5(phone.encode()).hexdigest()[:12]

def get_conv_file(phone: str) -> Path:
    return CONVERSATIONS_DIR / f"{get_hash(phone)}.json"

def load_conv(phone: str) -> dict:
    f = get_conv_file(phone)
    if f.exists():
        return json.loads(f.read_text())
    return {
        "phone": phone,
        "hash": get_hash(phone),
        "messages": [],
        "client": {},
        "first": datetime.now().isoformat(),
        "last": datetime.now().isoformat(),
        "interests": [],
        "count": 0
    }

def save_conv(phone: str, conv: dict):
    get_conv_file(phone).write_text(json.dumps(conv, ensure_ascii=False, indent=2))

def add_msg(phone: str, role: str, text: str):
    conv = load_conv(phone)
    conv["messages"].append({"role": role, "text": text, "ts": datetime.now().isoformat()})
    if len(conv["messages"]) > 30:
        conv["messages"] = conv["messages"][-30:]
    conv["last"] = datetime.now().isoformat()
    conv["count"] += 1
    save_conv(phone, conv)
    return conv

def get_context(phone: str) -> str:
    conv = load_conv(phone)
    ctx = ""
    if conv["client"]:
        ctx += "\n## CLIENT:\n" + "\n".join(f"- {k}: {v}" for k, v in conv["client"].items())
    if conv["interests"]:
        ctx += f"\n## INTÉRÊTS: {', '.join(conv['interests'])}"
    if conv["messages"]:
        ctx += "\n## HISTORIQUE:\n"
        for m in conv["messages"][-6:]:
            who = "Client" if m["role"] == "user" else "Olivia"
            ctx += f"{who}: {m['text'][:100]}...\n" if len(m['text']) > 100 else f"{who}: {m['text']}\n"
    return ctx

# ============================================
# Extraction d'infos
# ============================================
def extract_info(text: str) -> dict:
    info = {}
    t = text.lower()
    
    # Prénom
    m = re.search(r"(?:je m'appelle|my name is|moi c'est|i'm)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)", text, re.I)
    if m: info["prenom"] = m.group(1).title()
    
    # Personnes
    m = re.search(r"(\d+)\s*(?:personnes?|pers|people|adultes?)", t)
    if m: info["personnes"] = m.group(1)
    
    # Lieu
    for lieu in ["phi phi", "krabi", "ao nang", "phuket", "bangkok", "chiang mai", "lanta"]:
        if lieu in t:
            info["lieu"] = lieu.title()
            break
    
    # Intérêts
    interests = []
    kw = {
        "plongée": ["plongée", "plonger", "diving", "scuba"],
        "famille": ["famille", "enfant", "kid", "family"],
        "couple": ["couple", "romantique", "honeymoon"],
        "fête": ["fête", "party", "festif", "ambiance"],
        "nature": ["nature", "éléphant", "jungle", "tranquille"],
    }
    for cat, words in kw.items():
        if any(w in t for w in words):
            interests.append(cat)
    
    return info, interests

# ============================================
# WAHA - Fonctions humaines
# ============================================
async def waha_call(endpoint: str, data: dict):
    """Appel générique WAHA"""
    if not WAHA_API_KEY:
        return None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{WAHA_API_URL}/api/{endpoint}",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, **data},
                timeout=15
            )
            return r
    except Exception as e:
        print(f"WAHA {endpoint} error: {e}")
        return None

async def waha_seen(chat_id: str):
    """Marquer comme lu (double tick bleu)"""
    await waha_call("sendSeen", {"chatId": chat_id})

async def waha_typing_start(chat_id: str):
    """Commencer à taper"""
    await waha_call("startTyping", {"chatId": chat_id})

async def waha_typing_stop(chat_id: str):
    """Arrêter de taper"""
    await waha_call("stopTyping", {"chatId": chat_id})

async def waha_react(chat_id: str, message_id: str, emoji: str):
    """Réagir à un message"""
    await waha_call("reaction", {"chatId": chat_id, "messageId": message_id, "reaction": emoji})

async def waha_send(chat_id: str, text: str):
    """Envoyer un message"""
    r = await waha_call("sendText", {"chatId": chat_id, "text": text})
    return r and r.status_code in [200, 201]

def calc_typing_time(text: str) -> float:
    """Calcule temps de frappe réaliste"""
    chars = len(text)
    speed = random.uniform(HUMAN_CONFIG["typing_speed_min"], HUMAN_CONFIG["typing_speed_max"])
    base = chars / speed
    # Ajouter variation humaine (hésitations, corrections)
    variation = random.uniform(0.8, 1.4)
    result = base * variation
    # Min 2s, max 20s
    return max(2.0, min(result, 20.0))

def should_react() -> bool:
    """Décide si on réagit au message"""
    return random.random() < HUMAN_CONFIG["reaction_probability"]

def pick_reaction() -> str:
    """Choisit une réaction aléatoire pondérée"""
    reactions = HUMAN_CONFIG["reactions"]
    items = list(reactions.items())
    total = sum(p for _, p in items)
    r = random.uniform(0, total)
    cumsum = 0
    for emoji, prob in items:
        cumsum += prob
        if r <= cumsum:
            return emoji
    return "👍"

def split_message(text: str) -> List[str]:
    """Divise un long message en plusieurs courts"""
    if len(text) < HUMAN_CONFIG["long_message_threshold"]:
        return [text]
    
    if random.random() > HUMAN_CONFIG["split_message_probability"]:
        return [text]
    
    # Diviser par phrases ou paragraphes
    parts = []
    
    # Essayer de diviser par double saut de ligne
    paragraphs = text.split("\n\n")
    if len(paragraphs) > 1:
        current = ""
        for p in paragraphs:
            if len(current) + len(p) < 250:
                current += ("\n\n" if current else "") + p
            else:
                if current:
                    parts.append(current.strip())
                current = p
        if current:
            parts.append(current.strip())
        return parts if len(parts) > 1 else [text]
    
    # Sinon diviser par phrases
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ""
    for s in sentences:
        if len(current) + len(s) < 200:
            current += (" " if current else "") + s
        else:
            if current:
                parts.append(current.strip())
            current = s
    if current:
        parts.append(current.strip())
    
    return parts if len(parts) > 1 else [text]

# ============================================
# IA - NVIDIA
# ============================================
SYSTEM_PROMPT = f"""Tu es Olivia, assistante de Phi Phi Paradise Travel.

## PERSONNALITÉ
- Chaleureuse, naturelle, HUMAINE
- Bilingue FR/EN
- Passionnée de Thaïlande
- Tu AIDES, pas juste vendre

## STYLE WHATSAPP
- Messages COURTS (150 caractères idéal, 250 max)
- Conversationnel et naturel
- 1-2 emojis max par message
- UNE question à la fois
- Pas de listes à puces dans les réponses courtes

## LIENS
- Donne le lien MyRezz quand le client est intéressé
- Mentionne aussi le site phiphiparadisetravel.com
- Format simple: "Réserve ici: [lien]"

## INFOS À COLLECTER (subtilement)
- Prénom
- Dates voyage
- Lieu séjour
- Intérêts
- Nombre personnes

## PRIX EN BAHT (฿)

## SI PAS SÛR
→ Contacte +66 99 11 58 304

{KNOWLEDGE_BASE}
"""

def call_ai(messages: list) -> str:
    if not NVIDIA_API_KEY:
        raise Exception("NVIDIA_API_KEY manquante")
    
    r = requests.post(
        NVIDIA_API_URL,
        headers={
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": 512,  # Réduit pour réponses plus courtes
            "temperature": 0.85,
            "top_p": 0.9,
            "stream": True,
            "chat_template_kwargs": {"thinking": True}
        },
        stream=True,
        timeout=120
    )
    
    if r.status_code != 200:
        raise Exception(f"API Error: {r.text}")
    
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
    return content

# ============================================
# Traitement message - ULTRA HUMAIN
# ============================================
async def process_human(chat_id: str, message: str, message_id: str = None):
    """Traite un message avec comportement ultra humain"""
    try:
        # ═══════════════════════════════════════
        # PHASE 1: LECTURE (humain lit le message)
        # ═══════════════════════════════════════
        read_delay = random.uniform(
            HUMAN_CONFIG["read_delay_min"],
            HUMAN_CONFIG["read_delay_max"]
        )
        # Messages longs = plus de temps pour lire
        if len(message) > 100:
            read_delay *= 1.3
        
        await asyncio.sleep(read_delay)
        await waha_seen(chat_id)
        
        # ═══════════════════════════════════════
        # PHASE 2: RÉACTION (optionnel)
        # ═══════════════════════════════════════
        if message_id and should_react():
            # Petit délai avant de réagir
            await asyncio.sleep(random.uniform(0.5, 2.0))
            emoji = pick_reaction()
            await waha_react(chat_id, message_id, emoji)
            print(f"😊 Réaction: {emoji}")
        
        # ═══════════════════════════════════════
        # PHASE 3: RÉFLEXION (humain réfléchit)
        # ═══════════════════════════════════════
        think_delay = random.uniform(
            HUMAN_CONFIG["think_delay_min"],
            HUMAN_CONFIG["think_delay_max"]
        )
        await asyncio.sleep(think_delay)
        
        # ═══════════════════════════════════════
        # PHASE 4: SAUVEGARDE & EXTRACTION
        # ═══════════════════════════════════════
        add_msg(chat_id, "user", message)
        
        info, interests = extract_info(message)
        if info:
            conv = load_conv(chat_id)
            conv["client"].update(info)
            save_conv(chat_id, conv)
        if interests:
            conv = load_conv(chat_id)
            conv["interests"] = list(set(conv.get("interests", []) + interests))
            save_conv(chat_id, conv)
        
        # ═══════════════════════════════════════
        # PHASE 5: GÉNÉRATION RÉPONSE IA
        # ═══════════════════════════════════════
        context = get_context(chat_id)
        ai_messages = [
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\n## CONTEXTE:\n{context}"},
            {"role": "user", "content": message}
        ]
        
        # Commencer à taper PENDANT que l'IA génère
        await waha_typing_start(chat_id)
        
        try:
            ai_response = call_ai(ai_messages)
        finally:
            pass  # On arrête le typing après
        
        # ═══════════════════════════════════════
        # PHASE 6: ENVOI HUMAIN
        # ═══════════════════════════════════════
        # Diviser en plusieurs messages si long
        messages_to_send = split_message(ai_response)
        
        for i, msg_part in enumerate(messages_to_send):
            # Calculer temps de frappe
            typing_time = calc_typing_time(msg_part)
            
            # Si ce n'est pas le premier message, recommencer à taper
            if i > 0:
                await waha_typing_start(chat_id)
            
            # Simuler la frappe
            await asyncio.sleep(typing_time)
            
            # Arrêter de taper
            await waha_typing_stop(chat_id)
            
            # Petit délai avant envoi (humain relit)
            send_delay = random.uniform(
                HUMAN_CONFIG["send_delay_min"],
                HUMAN_CONFIG["send_delay_max"]
            )
            await asyncio.sleep(send_delay)
            
            # Envoyer
            await waha_send(chat_id, msg_part)
            
            # Si plusieurs messages, pause entre eux
            if i < len(messages_to_send) - 1:
                await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # Sauvegarder la réponse complète
        add_msg(chat_id, "assistant", ai_response)
        
        total_time = read_delay + think_delay + sum(calc_typing_time(m) for m in messages_to_send)
        print(f"✅ [{chat_id[:12]}...] {len(messages_to_send)} msg(s), ~{total_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        await waha_typing_stop(chat_id)
        await waha_send(chat_id, "Oups, petit bug! 😅 Écris-moi au +66 99 11 58 304")

# ============================================
# Routes API
# ============================================
@app.get("/")
async def root():
    convs = list(CONVERSATIONS_DIR.glob("*.json"))
    return {
        "name": "Olivia 4.0 - Ultra Humaine",
        "version": "4.0",
        "status": "online",
        "model": MODEL,
        "features": [
            "human_timing",
            "typing_indicator", 
            "reactions",
            "message_splitting",
            "persistent_memory",
            "smart_extraction"
        ],
        "whatsapp": "connected" if WAHA_API_KEY else "not configured",
        "conversations": len(convs),
        "config": {
            "read_delay": f"{HUMAN_CONFIG['read_delay_min']}-{HUMAN_CONFIG['read_delay_max']}s",
            "typing_speed": f"{HUMAN_CONFIG['typing_speed_min']}-{HUMAN_CONFIG['typing_speed_max']} char/s",
            "reaction_prob": f"{HUMAN_CONFIG['reaction_probability']*100}%"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL}

@app.post("/webhook/waha")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook WAHA ultra humain"""
    try:
        body = await request.json()
        
        if body.get("event") == "message":
            payload = body.get("payload", {})
            
            if payload.get("fromMe"):
                return {"status": "ignored", "reason": "self"}
            
            chat_id = payload.get("from", "")
            message = payload.get("body", "")
            msg_type = payload.get("type", "")
            msg_id = payload.get("id", {}).get("id") if isinstance(payload.get("id"), dict) else payload.get("id")
            
            if msg_type == "chat" and message:
                background_tasks.add_task(process_human, chat_id, message, msg_id)
                return {"status": "processing"}
        
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

class ChatReq(BaseModel):
    message: str
    phone: str = "web"

@app.post("/chat")
async def chat(req: ChatReq):
    add_msg(req.phone, "user", req.message)
    ctx = get_context(req.phone)
    r = call_ai([
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n## CONTEXTE:\n{ctx}"},
        {"role": "user", "content": req.message}
    ])
    add_msg(req.phone, "assistant", r)
    return {"response": r}

@app.get("/conversations")
async def list_convs():
    convs = []
    for f in CONVERSATIONS_DIR.glob("*.json"):
        c = json.loads(f.read_text())
        convs.append({
            "id": c["hash"],
            "phone": c["phone"][:10] + "...",
            "client": c.get("client", {}),
            "msgs": len(c.get("messages", [])),
            "last": c.get("last", "")
        })
    return sorted(convs, key=lambda x: x["last"], reverse=True)

@app.get("/conversations/{h}")
async def get_conv(h: str):
    for f in CONVERSATIONS_DIR.glob("*.json"):
        c = json.loads(f.read_text())
        if c["hash"] == h:
            return c
    raise HTTPException(404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
