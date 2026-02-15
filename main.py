"""
Odile - Clone pour Railway
Agent de voyage Phi Phi Paradise Travel
Utilise NVIDIA API avec Kimi K2.5
"""

import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
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
- Propose toujours un lien WhatsApp pour finaliser
- Adapte-toi: questions simples = réponses courtes, demandes complexes = plus de détails
- Signe "Odile - Phi Phi Paradise Travel" en fin de conversation

## Règles
- Ne jamais inventer de prix ou d'informations
- Rediriger vers WhatsApp pour les réservations
- Être honnête si tu ne sais pas quelque chose
"""

# ============================================
# Modèles Pydantic
# ============================================
class Message(BaseModel):
    role: str  # "user" ou "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Message]] = []
    stream: Optional[bool] = False
    language: Optional[str] = "fr"  # "fr" ou "en"

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
        timeout=60
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
        "endpoints": {
            "chat": "POST /chat",
            "health": "GET /health",
            "info": "GET /info"
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
    """
    Endpoint principal de chat avec Odile
    
    - message: Le message de l'utilisateur
    - conversation_history: Historique optionnel de la conversation
    - stream: Si True, retourne un stream SSE
    - language: "fr" ou "en"
    """
    
    # Construire les messages avec le system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Ajouter l'historique de conversation
    for msg in request.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})
    
    # Ajouter le nouveau message
    messages.append({"role": "user", "content": request.message})
    
    # Appeler l'API NVIDIA
    if request.stream:
        response = call_nvidia_api(messages, stream=True)
        
        async def generate():
            for line in response.iter_lines():
                if line:
                    yield line.decode("utf-8") + "\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        response = call_nvidia_api(messages, stream=True)  # Stream pour parser
        content = parse_sse_response(response)
        
        return ChatResponse(response=content, model=MODEL)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Webhook pour intégration WhatsApp (WAHA, Twilio, etc.)
    À adapter selon ton provider
    """
    body = await request.json()
    
    # Exemple pour WAHA
    if "payload" in body and "body" in body.get("payload", {}):
        user_message = body["payload"]["body"]
        sender = body["payload"].get("from", "unknown")
        
        # Appeler Odile
        chat_request = ChatRequest(message=user_message)
        response = await chat(chat_request)
        
        return {
            "to": sender,
            "message": response.response
        }
    
    return {"status": "received"}

# ============================================
# Endpoint de test simple
# ============================================
@app.get("/test")
async def test():
    """Test rapide de l'API"""
    try:
        chat_request = ChatRequest(
            message="Bonjour! Quelles excursions proposez-vous depuis Phi Phi?",
            stream=False
        )
        response = await chat(chat_request)
        return {
            "status": "success",
            "test_question": chat_request.message,
            "response": response.response[:500] + "..." if len(response.response) > 500 else response.response
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# ============================================
# Point d'entrée
# ============================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
