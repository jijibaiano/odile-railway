"""
Odile - Clone pour Railway
Agent de voyage Phi Phi Paradise Travel
Utilise NVIDIA API avec Kimi K2.5
Connecté à WhatsApp via WAHA
"""

import os
import json
import requests
import httpx
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="Odile - Phi Phi Paradise Travel",
    description="Assistant voyage intelligent pour la Thaïlande",
    version="1.0.0"
)

# CORS pour permettre les appels depuis n'importe où
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
MODEL = "moonshotai/kimi-k2.5"

# WAHA Configuration
WAHA_API_URL = os.getenv("WAHA_API_URL", "https://devlikeaprowaha-production-ed27.up.railway.app")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

# ============================================
# Personnalité Odile
# ============================================
SYSTEM_PROMPT = """Tu es Odile, l'assistante virtuelle de Phi Phi Paradise Travel, une agence de voyage basée à Koh Phi Phi, Thaïlande.

## Ta personnalité
- Chaleureuse et accueillante, chaque voyageur est un invité
- Helpful first - tu aides, tu ne pousses pas à la vente
- Bilingue français/anglais - tu t'adaptes à la langue du client
- Experte de la Thaïlande - îles, plongée, temples, éléphants

## Informations agence
- WhatsApp: +66 99 11 58 304 (Thaïlande) / +33 7 85 65 40 82 (France)
- Site: phiphiparadisetravel.com
- Licence TAT: 33/10549
- Aucun acompte requis
- Guides francophones disponibles

## Destinations principales
- Koh Phi Phi (base) - Maya Bay, plongée, bateaux pirates
- Krabi/Ao Nang - Hong Island, 4 Islands, James Bond Island
- Phuket - Similan Islands, Phi Phi day trips
- Koh Lanta - Îles Trang, Koh Kradan (#1 monde 2023)
- Bangkok - Temples, marchés flottants, Ayutthaya

## Excursions populaires (prix en THB)
- Matin Maya (lever soleil): ฿800
- Bateau Pirate Phoenix/Dragon: ฿1,800
- Hong Island Sunset BBQ: ฿2,500
- 4 Islands Sunset BBQ: ฿2,500
- Baptême plongée: ฿4,200
- Sanctuaire éléphants + cascades: ฿3,000
- Phi Phi depuis Phuket: ฿3,500

## Ton style
- Utilise des emojis avec parcimonie (🌴🌊🐘)
- Réponds de manière concise mais complète
- Ne mets PAS de liens markdown [texte](url) - écris juste le numéro WhatsApp
- Adapte-toi: questions simples = réponses courtes, demandes complexes = plus de détails
- Signe "Odile - Phi Phi Paradise Travel" en fin de conversation

## Règles
- Ne jamais inventer de prix ou d'informations
- Pour réserver, dis de répondre directement à ce message WhatsApp
- Être honnête si tu ne sais pas quelque chose
- Réponses courtes pour WhatsApp (max 500 caractères si possible)
"""

# ============================================
# Modèles Pydantic
# ============================================
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Message]] = []
    stream: Optional[bool] = False
    language: Optional[str] = "fr"

class ChatResponse(BaseModel):
    response: str
    model: str = MODEL

# ============================================
# Fonctions utilitaires
# ============================================
def call_nvidia_api(messages: list, stream: bool = False):
    """Appelle l'API NVIDIA avec Kimi K2.5"""
    
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
        "max_tokens": 4096,
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
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Erreur NVIDIA API: {response.text}"
        )
    
    return response

def parse_sse_response(response):
    """Parse la réponse SSE de NVIDIA"""
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

async def send_whatsapp_message(to: str, message: str):
    """Envoie un message WhatsApp via WAHA"""
    if not WAHA_API_KEY:
        print("WAHA_API_KEY non configurée")
        return False
    
    url = f"{WAHA_API_URL}/api/sendText"
    headers = {
        "X-Api-Key": WAHA_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "session": WAHA_SESSION,
        "chatId": to,
        "text": message
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            print(f"WAHA response: {response.status_code} - {response.text}")
            return response.status_code == 200 or response.status_code == 201
    except Exception as e:
        print(f"Erreur envoi WhatsApp: {e}")
        return False

async def process_whatsapp_message(from_number: str, message_text: str):
    """Traite un message WhatsApp et répond"""
    try:
        # Appeler l'API NVIDIA
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message_text}
        ]
        
        response = call_nvidia_api(messages, stream=True)
        ai_response = parse_sse_response(response)
        
        # Envoyer la réponse via WhatsApp
        await send_whatsapp_message(from_number, ai_response)
        
        print(f"Message traité: {from_number} -> {message_text[:50]}...")
        
    except Exception as e:
        print(f"Erreur traitement message: {e}")
        # Envoyer un message d'erreur
        await send_whatsapp_message(
            from_number, 
            "Désolée, je rencontre un problème technique. Contactez-nous directement au +66 99 11 58 304. - Odile"
        )

# ============================================
# Routes API
# ============================================
@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "name": "Odile - Phi Phi Paradise Travel",
        "status": "online",
        "model": MODEL,
        "whatsapp": "connected" if WAHA_API_KEY else "not configured",
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "info": "GET /info",
            "webhook": "POST /webhook/waha"
        }
    }

@app.get("/health")
async def health():
    """Health check pour Railway"""
    return {"status": "healthy", "model": MODEL}

@app.get("/info")
async def info():
    """Informations sur l'agence"""
    return {
        "agency": "Phi Phi Paradise Travel",
        "assistant": "Odile",
        "location": "Koh Phi Phi, Thailand",
        "license": "TAT 33/10549",
        "contact": {
            "whatsapp_th": "+66 99 11 58 304",
            "whatsapp_fr": "+33 7 85 65 40 82",
            "website": "https://phiphiparadisetravel.com"
        },
        "languages": ["Français", "English"],
        "destinations": ["Koh Phi Phi", "Krabi", "Phuket", "Koh Lanta", "Bangkok"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de chat avec Odile"""
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for msg in request.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})
    
    messages.append({"role": "user", "content": request.message})
    
    response = call_nvidia_api(messages, stream=True)
    content = parse_sse_response(response)
    
    return ChatResponse(response=content, model=MODEL)

@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook pour WAHA (WhatsApp HTTP API)
    Reçoit les messages et répond automatiquement
    """
    try:
        body = await request.json()
        print(f"WAHA Webhook received: {json.dumps(body)[:500]}")
        
        event = body.get("event")
        
        # Traiter uniquement les messages entrants
        if event == "message":
            payload = body.get("payload", {})
            
            # Ignorer les messages sortants (de nous)
            if payload.get("fromMe", False):
                return {"status": "ignored", "reason": "outgoing message"}
            
            # Extraire les infos du message
            from_number = payload.get("from", "")
            message_body = payload.get("body", "")
            message_type = payload.get("type", "")
            
            # Traiter uniquement les messages texte
            if message_type == "chat" and message_body:
                # Traiter en arrière-plan pour répondre rapidement au webhook
                background_tasks.add_task(
                    process_whatsapp_message,
                    from_number,
                    message_body
                )
                return {"status": "processing", "from": from_number}
            
            return {"status": "ignored", "reason": f"unsupported type: {message_type}"}
        
        return {"status": "ignored", "reason": f"unsupported event: {event}"}
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/test")
async def test():
    """Test rapide de l'API"""
    try:
        chat_request = ChatRequest(
            message="Bonjour! Dis juste OK",
            stream=False
        )
        response = await chat(chat_request)
        return {
            "status": "success",
            "nvidia_api": "working",
            "waha_configured": bool(WAHA_API_KEY),
            "response_preview": response.response[:200] if response.response else None
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============================================
# Point d'entrée
# ============================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
