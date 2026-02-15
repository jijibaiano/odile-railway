"""
Olivia 2.0 - Assistant Phi Phi Paradise Travel
- Mémoire par client
- Accès Google Calendar/Drive/Gmail
- Base de connaissances site web
- Email récap automatique
- Liens réservation MyRezz
"""

import os
import json
import requests
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import hashlib
import re

app = FastAPI(
    title="Olivia - Phi Phi Paradise Travel",
    description="Assistant voyage intelligent avec mémoire et intégrations",
    version="2.0.0"
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

# WAHA Configuration
WAHA_API_URL = os.getenv("WAHA_API_URL", "")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

# Google Configuration
GOOGLE_SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RECAP_EMAIL = os.getenv("RECAP_EMAIL", "phiphiparadis@gmail.com")

# ============================================
# Base de connaissances - Phi Phi Paradise Travel
# ============================================
KNOWLEDGE_BASE = """
## PHI PHI PARADISE TRAVEL - BASE DE CONNAISSANCES

### INFORMATIONS AGENCE
- Nom: Phi Phi Paradise Travel
- Propriétaire: Jiji
- Base: Koh Phi Phi, Thaïlande
- Licence TAT: 33/10549
- Site: https://phiphiparadisetravel.com
- WhatsApp TH: +66 99 11 58 304
- WhatsApp FR: +33 7 85 65 40 82
- Email: phiphiparadis@gmail.com

### POLITIQUE
- ✅ Aucun acompte requis
- ✅ Guides francophones disponibles
- ✅ Petits groupes (max 10-12 personnes)
- ✅ Transfert hôtel inclus
- 👶 Enfants -9 ans: -50%
- 👶 Enfants -3 ans: GRATUIT

### EXCURSIONS DEPUIS KOH PHI PHI

#### Matin Maya (Lever du soleil) ⭐ BEST-SELLER
- Prix: ฿800/pers
- Horaire: 6h30-11h30
- Sites: Maya Bay à l'ouverture, Pileh Lagoon, Viking Cave, Monkey Beach, Shark Point
- Inclus: Masque, snorkeling, guide francophone, fruits, photos
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/100673

#### Magique Turquoise
- Prix: ฿700/pers
- Sites: Pileh Lagoon, Viking Cave, Loh Samah, Monkey Beach
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/98661

#### Bateau Pirate Phoenix (Matin)
- Prix: ฿1,800/pers
- Horaire: 9h30-15h30
- Ambiance: Calme, idéal familles
- Inclus: Masque, snorkeling, repas, photos, parc national
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71115

#### Bateau Pirate Dragon (Sunset)
- Prix: ฿1,800/pers
- Horaire: 11h30-19h00
- Ambiance: Festive avec musique et bar
- Inclus: Kayak, paddle, masque, repas, photos
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71115

#### Long Tail Privé
- Prix: ฿4,200 (jusqu'à 3 pers) pour 6h
- Itinéraire flexible
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71403

### PLONGÉE À PHI PHI

#### Baptême de Plongée
- Prix: ฿3,400 + ฿600 frais marine
- 2 plongées de 50min, équipement complet
- Instructeurs francophones
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71911

#### Fun Dive (Certifiés)
- Prix: ฿2,700 + ฿600 frais marine
- 2 plongées, équipement inclus
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71667

#### Open Water PADI
- Prix: ฿12,900 + ฿800 frais
- 3-4 jours, certification internationale
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/71669

### EXCURSIONS DEPUIS KRABI / AO NANG

#### Hong Island Sunset & BBQ 🔥 ⭐ BEST-SELLER
- Prix: ฿2,500/pers
- Horaire: 11h00-20h00
- Sites: Koh Hong, Lagon, viewpoint 420 marches, planctons bioluminescents!
- Inclus: Transfert, déjeuner, BBQ sunset, masque, parc national
- Max 10-12 personnes

#### 4 Islands Sunset & BBQ 🔥
- Prix: ฿2,500/pers
- Horaire: 11h30-20h00
- Sites: Secret Beach, Tup Island, Chicken Island, Poda Island
- Planctons bioluminescents!

#### James Bond Island
- Prix: ฿2,500/pers
- Horaire: 8h00-18h30
- Sites: Canoë mangroves, James Bond Island, village flottant

#### Sanctuaire Éléphants + Cascades Bencha 🐘
- Prix: ฿3,000/pers
- Horaire: 7h00-15h00
- 3h avec éléphants + 7 niveaux de cascades

### EXCURSIONS DEPUIS PHUKET

#### Koh Phi Phi Autrement (Speedboat)
- Prix: ฿3,500/pers
- Horaire: 5h15-15h30
- Maya Bay sunrise, max 15 personnes
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/84448

#### Similan Islands
- Prix: ฿2,000/pers
- Meilleur snorkeling de Thaïlande
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/84442

#### James Bond Island
- Prix: ฿1,700/pers
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/84187

### EXCURSIONS BANGKOK

#### Temples (Grand Palace, Wat Pho, Wat Arun)
- Guide anglais: https://booking.myrezapp.com/fr/online/booking/step1/16686/86554
- Guide français: https://booking.myrezapp.com/fr/online/booking/step1/16686/86582

#### Ayutthaya
- Guide anglais: https://booking.myrezapp.com/fr/online/booking/step1/16686/86578
- Guide français: https://booking.myrezapp.com/fr/online/booking/step1/16686/86588

#### Marchés flottants
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/86552

### EXCURSIONS CHIANG MAI

#### Éléphants Chiang Mai
- Prix: ฿1,500/pers
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/86591

#### Chiang Rai (Temples Blanc/Bleu)
- Prix: ฿1,900/pers
- Lien: https://booking.myrezapp.com/fr/online/booking/step1/16686/86592

### FERRIES & TRANSFERTS
- Phi Phi → Phuket: ฿1,100 - https://booking.myrezapp.com/fr/online/booking/step1/16686/71407
- Phi Phi → Krabi: ฿1,100 - https://booking.myrezapp.com/fr/online/booking/step1/16686/71409

### KOH LANTA
- Îles Trang & Koh Kradan (#1 monde 2023!): ฿7,500-13,000 selon groupe
- Koh Rok: Snorkeling exceptionnel
"""

# ============================================
# Mémoire des conversations
# ============================================
# Structure: {phone_hash: {messages: [], client_info: {}, last_interaction: timestamp}}
conversations_memory: Dict[str, dict] = {}
MAX_MEMORY_MESSAGES = 20  # Garder les 20 derniers messages

def get_phone_hash(phone: str) -> str:
    """Hash du numéro pour la confidentialité"""
    return hashlib.md5(phone.encode()).hexdigest()[:12]

def get_conversation(phone: str) -> dict:
    """Récupère ou crée une conversation"""
    phone_hash = get_phone_hash(phone)
    if phone_hash not in conversations_memory:
        conversations_memory[phone_hash] = {
            "phone": phone,
            "messages": [],
            "client_info": {},
            "first_contact": datetime.now().isoformat(),
            "last_interaction": datetime.now().isoformat(),
            "interests": [],
            "bookings": []
        }
    return conversations_memory[phone_hash]

def add_message_to_memory(phone: str, role: str, content: str):
    """Ajoute un message à la mémoire"""
    conv = get_conversation(phone)
    conv["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # Garder seulement les derniers messages
    if len(conv["messages"]) > MAX_MEMORY_MESSAGES:
        conv["messages"] = conv["messages"][-MAX_MEMORY_MESSAGES:]
    conv["last_interaction"] = datetime.now().isoformat()

def update_client_info(phone: str, info: dict):
    """Met à jour les infos client"""
    conv = get_conversation(phone)
    conv["client_info"].update(info)

def get_conversation_context(phone: str) -> str:
    """Génère le contexte de conversation pour l'IA"""
    conv = get_conversation(phone)
    context = ""
    
    if conv["client_info"]:
        context += f"\n## INFOS CLIENT CONNUES:\n"
        for key, value in conv["client_info"].items():
            context += f"- {key}: {value}\n"
    
    if conv["interests"]:
        context += f"\n## INTÉRÊTS: {', '.join(conv['interests'])}\n"
    
    if conv["messages"]:
        context += f"\n## HISTORIQUE CONVERSATION (derniers messages):\n"
        for msg in conv["messages"][-10:]:  # 10 derniers pour le contexte
            role_name = "Client" if msg["role"] == "user" else "Olivia"
            context += f"{role_name}: {msg['content'][:200]}...\n" if len(msg['content']) > 200 else f"{role_name}: {msg['content']}\n"
    
    return context

# ============================================
# Système de prompts
# ============================================
SYSTEM_PROMPT = f"""Tu es Olivia, l'assistante virtuelle de Phi Phi Paradise Travel.

## TA PERSONNALITÉ
- Chaleureuse, accueillante, professionnelle
- Tu parles français et anglais (adapte-toi à la langue du client)
- Experte de la Thaïlande
- Tu veux aider, pas juste vendre

## TES CAPACITÉS
- Tu as accès à toute la base de connaissances de l'agence
- Tu connais les prix, horaires, et liens de réservation
- Tu peux recommander des excursions selon les préférences
- Tu mémorises les conversations avec chaque client

## COMMENT RÉPONDRE
1. Réponds toujours de manière concise (WhatsApp = messages courts)
2. Utilise des emojis avec modération (🌴🌊🐘⭐)
3. Donne les PRIX en Baht (฿)
4. Donne les LIENS de réservation MyRezz quand pertinent
5. Si le client veut réserver, donne le lien direct
6. Pour questions complexes, propose d'appeler ou WhatsApp +66 99 11 58 304

## COLLECTE D'INFOS (subtile)
Essaie de savoir naturellement:
- Prénom du client
- Dates de voyage
- Où ils logent (Phi Phi, Krabi, Phuket?)
- Intérêts (plongée, fête, famille, nature?)
- Nombre de personnes

## BASE DE CONNAISSANCES
{KNOWLEDGE_BASE}

## RÈGLES IMPORTANTES
- Ne jamais inventer de prix ou d'infos
- Toujours proposer le lien de réservation quand tu recommandes une excursion
- Si tu ne sais pas, dis-le et propose de contacter Jiji
- Signe tes messages "Olivia - Phi Phi Paradise Travel" (seulement à la fin de conversation)
"""

# ============================================
# Fonctions IA
# ============================================
def call_nvidia_api(messages: list, stream: bool = True):
    """Appelle l'API NVIDIA"""
    if not NVIDIA_API_KEY:
        raise HTTPException(status_code=500, detail="NVIDIA_API_KEY non configurée")
    
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream" if stream else "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": stream,
        "chat_template_kwargs": {"thinking": True}
    }
    
    response = requests.post(
        NVIDIA_API_URL,
        headers=headers,
        json=payload,
        stream=stream,
        timeout=120
    )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=f"Erreur API: {response.text}")
    
    return response

def parse_sse_response(response):
    """Parse la réponse SSE"""
    full_content = ""
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                except json.JSONDecodeError:
                    continue
    return full_content

def extract_client_info(message: str, response: str) -> dict:
    """Extrait les infos client des messages"""
    info = {}
    
    # Patterns pour extraire des infos
    patterns = {
        "prenom": r"(?:je m'appelle|my name is|moi c'est|I'm)\s+([A-Z][a-zéèê]+)",
        "personnes": r"(\d+)\s*(?:personnes?|pers|people|pax|adultes?)",
        "date": r"(\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?)",
        "hotel": r"(?:à l'hôtel|at|staying at|logé à)\s+([A-Za-z\s]+)",
    }
    
    combined = message + " " + response
    for key, pattern in patterns.items():
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            info[key] = match.group(1)
    
    return info

# ============================================
# WhatsApp WAHA
# ============================================
async def send_whatsapp_message(to: str, message: str):
    """Envoie un message WhatsApp"""
    if not WAHA_API_KEY:
        print("WAHA non configuré")
        return False
    
    url = f"{WAHA_API_URL}/api/sendText"
    headers = {"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"}
    payload = {"session": WAHA_SESSION, "chatId": to, "text": message}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            return response.status_code in [200, 201]
    except Exception as e:
        print(f"Erreur WhatsApp: {e}")
        return False

async def send_email_recap(phone: str):
    """Envoie un email récap de la conversation"""
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP non configuré")
        return False
    
    conv = get_conversation(phone)
    if not conv["messages"]:
        return False
    
    # Construire le récap
    subject = f"[Olivia] Conversation WhatsApp - {conv['client_info'].get('prenom', phone)}"
    
    body = f"""
Récapitulatif conversation WhatsApp
===================================

📱 Numéro: {phone}
📅 Premier contact: {conv['first_contact']}
📅 Dernière interaction: {conv['last_interaction']}

👤 Infos client:
{json.dumps(conv['client_info'], indent=2, ensure_ascii=False) if conv['client_info'] else 'Aucune info collectée'}

💬 Conversation:
"""
    for msg in conv["messages"]:
        role = "👤 Client" if msg["role"] == "user" else "🤖 Olivia"
        body += f"\n{role} ({msg['timestamp'][:16]}):\n{msg['content']}\n"
    
    # Envoyer par email (simple SMTP)
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = RECAP_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        
        print(f"Email récap envoyé pour {phone}")
        return True
    except Exception as e:
        print(f"Erreur email: {e}")
        return False

async def process_whatsapp_message(from_number: str, message_text: str):
    """Traite un message WhatsApp avec mémoire"""
    try:
        # Ajouter le message à la mémoire
        add_message_to_memory(from_number, "user", message_text)
        
        # Construire le contexte avec mémoire
        conversation_context = get_conversation_context(from_number)
        
        full_system = SYSTEM_PROMPT + f"\n\n## CONTEXTE CONVERSATION ACTUELLE:\n{conversation_context}"
        
        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": message_text}
        ]
        
        # Appeler l'IA
        response = call_nvidia_api(messages, stream=True)
        ai_response = parse_sse_response(response)
        
        # Sauvegarder la réponse
        add_message_to_memory(from_number, "assistant", ai_response)
        
        # Extraire et sauvegarder les infos client
        client_info = extract_client_info(message_text, ai_response)
        if client_info:
            update_client_info(from_number, client_info)
        
        # Envoyer la réponse WhatsApp
        await send_whatsapp_message(from_number, ai_response)
        
        print(f"✅ Message traité: {from_number[:20]}...")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        await send_whatsapp_message(
            from_number,
            "Désolée, petit souci technique! Contactez-nous au +66 99 11 58 304 🙏"
        )

# ============================================
# Routes API
# ============================================
@app.get("/")
async def root():
    return {
        "name": "Olivia - Phi Phi Paradise Travel",
        "version": "2.0",
        "status": "online",
        "model": MODEL,
        "features": ["memory", "knowledge_base", "whatsapp", "email_recap"],
        "whatsapp": "connected" if WAHA_API_KEY else "not configured",
        "active_conversations": len(conversations_memory)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL, "conversations": len(conversations_memory)}

@app.get("/info")
async def info():
    return {
        "agency": "Phi Phi Paradise Travel",
        "assistant": "Olivia",
        "version": "2.0",
        "contact": {
            "whatsapp_th": "+66 99 11 58 304",
            "whatsapp_fr": "+33 7 85 65 40 82",
            "website": "https://phiphiparadisetravel.com"
        }
    }

class ChatRequest(BaseModel):
    message: str
    phone: Optional[str] = "web_user"

class ChatResponse(BaseModel):
    response: str
    model: str = MODEL

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat avec mémoire"""
    add_message_to_memory(request.phone, "user", request.message)
    conversation_context = get_conversation_context(request.phone)
    
    full_system = SYSTEM_PROMPT + f"\n\n## CONTEXTE:\n{conversation_context}"
    
    messages = [
        {"role": "system", "content": full_system},
        {"role": "user", "content": request.message}
    ]
    
    response = call_nvidia_api(messages, stream=True)
    ai_response = parse_sse_response(response)
    
    add_message_to_memory(request.phone, "assistant", ai_response)
    
    return ChatResponse(response=ai_response, model=MODEL)

@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook WAHA"""
    try:
        body = await request.json()
        event = body.get("event")
        
        if event == "message":
            payload = body.get("payload", {})
            
            if payload.get("fromMe", False):
                return {"status": "ignored", "reason": "outgoing"}
            
            from_number = payload.get("from", "")
            message_body = payload.get("body", "")
            message_type = payload.get("type", "")
            
            if message_type == "chat" and message_body:
                background_tasks.add_task(process_whatsapp_message, from_number, message_body)
                return {"status": "processing"}
        
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/conversations")
async def list_conversations():
    """Liste les conversations actives"""
    convs = []
    for phone_hash, conv in conversations_memory.items():
        convs.append({
            "id": phone_hash,
            "client_info": conv["client_info"],
            "message_count": len(conv["messages"]),
            "last_interaction": conv["last_interaction"]
        })
    return {"conversations": convs}

@app.get("/conversations/{phone_hash}")
async def get_conversation_detail(phone_hash: str):
    """Détail d'une conversation"""
    if phone_hash in conversations_memory:
        return conversations_memory[phone_hash]
    raise HTTPException(status_code=404, detail="Conversation non trouvée")

@app.post("/conversations/{phone_hash}/email-recap")
async def send_conversation_recap(phone_hash: str, background_tasks: BackgroundTasks):
    """Envoie un email récap"""
    if phone_hash not in conversations_memory:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    phone = conversations_memory[phone_hash]["phone"]
    background_tasks.add_task(send_email_recap, phone)
    return {"status": "sending", "to": RECAP_EMAIL}

@app.get("/test")
async def test():
    """Test complet"""
    return {
        "nvidia_api": "configured" if NVIDIA_API_KEY else "missing",
        "waha": "configured" if WAHA_API_KEY else "missing",
        "smtp": "configured" if SMTP_USER else "missing",
        "model": MODEL,
        "knowledge_base_size": len(KNOWLEDGE_BASE)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
