"""
OLIVIA 3.0 - Agent Parfait Phi Phi Paradise Travel
===================================================
- Comportement humain (typing, délais, seen)
- Mémoire persistante par client
- Base de connaissances complète (site + MyRezz)
- Intégration Google (Calendar, Drive, Gmail)
- Email récap automatique
- Connexion Wix
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
    title="Olivia 3.0 - Phi Phi Paradise Travel",
    description="Agent conversationnel parfait avec comportement humain",
    version="3.0.0"
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
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
RECAP_EMAIL = os.getenv("RECAP_EMAIL", "phiphiparadis@gmail.com")

# Wix
WIX_SITE_ID = "274240b7-3bf8-44b3-8219-435cf5cb5805"
WIX_ACCOUNT_ID = "f4bbd6a8-1149-4ce7-9722-5b80664a22fc"

# Mémoire persistante
DATA_DIR = Path("/tmp/olivia_data")
DATA_DIR.mkdir(exist_ok=True)
CONVERSATIONS_DIR = DATA_DIR / "conversations"
CONVERSATIONS_DIR.mkdir(exist_ok=True)

# ============================================
# BASE DE CONNAISSANCES COMPLÈTE
# ============================================
KNOWLEDGE_BASE = """
## 🌴 PHI PHI PARADISE TRAVEL - BASE DE CONNAISSANCES COMPLÈTE

### INFORMATIONS AGENCE
- **Nom:** Phi Phi Paradise Travel
- **Propriétaire:** Jiji
- **Base:** Koh Phi Phi, Thaïlande
- **Licence TAT:** 33/10549
- **Site web:** https://phiphiparadisetravel.com
- **WhatsApp TH:** +66 99 11 58 304
- **WhatsApp FR:** +33 7 85 65 40 82
- **Email:** phiphiparadis@gmail.com

### POLITIQUE & AVANTAGES
- ✅ **Aucun acompte requis** - Payez sur place
- ✅ **Guides francophones** sur la plupart des excursions
- ✅ **Petits groupes** - Max 10-12 personnes
- ✅ **Transfert hôtel inclus** dans toutes les excursions
- ✅ **Équipement snorkeling inclus**
- 👶 **Enfants 3-9 ans:** -50%
- 👶 **Enfants -3 ans:** GRATUIT
- ⚠️ Prix en Baht Thaïlandais (THB/฿)

---

## 🏝️ EXCURSIONS DEPUIS KOH PHI PHI

### ⭐ Matin Maya (Lever du soleil) - BEST-SELLER
- **Prix:** ฿800/personne
- **Horaire:** 6h30-11h30 (5h)
- **Sites:** Maya Bay à l'ouverture (avant la foule!), Pileh Lagoon, Viking Cave, Monkey Beach, Shark Point
- **Inclus:** Masque, snorkeling, guide francophone, plateau de fruits, photos
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/100673
- **Page site:** https://phiphiparadisetravel.com/excursion/matin-maya

### Magique Turquoise
- **Prix:** ฿700/personne
- **Sites:** Pileh Lagoon, Viking Cave, Loh Samah, Monkey Beach
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/98661
- **Page site:** https://phiphiparadisetravel.com/excursion/magique-turquoise

### Bateau Pirate Phoenix (Matin - Calme)
- **Prix:** ฿1,800/personne
- **Horaire:** 9h30-15h30 (6h)
- **Ambiance:** Calme et relaxante, idéal pour les familles
- **Sites:** Phi Phi Don, Monkey Beach, Maya Beach, Loh Sama Bay, Pileh Lagoon, Viking Cave
- **Inclus:** Masque, snorkeling, repas complet, photos souvenirs, frais parc national
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71115
- **Page site:** https://phiphiparadisetravel.com/excursion/bateau-pirate

### Bateau Pirate Dragon (Sunset - Festif)
- **Prix:** ฿1,800/personne
- **Horaire:** 11h30-19h00 (7h30)
- **Ambiance:** Festive avec musique et bar à bord
- **Sites:** Mêmes sites + coucher de soleil spectaculaire
- **Inclus:** Kayak, paddle, masque, repas, photos, eau/café/thé
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71115
- **Page site:** https://phiphiparadisetravel.com/excursion/bateau-pirate-sunset

### Long Tail Privé Phi Phi
- **Prix:** ฿4,200 pour le bateau (jusqu'à 3 personnes)
- **Durée:** 6 heures
- **Avantage:** Itinéraire 100% personnalisé, vous choisissez où aller!
- **Inclus:** Eau, glacière, plateau fruits, masque snorkeling
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71403

### Speed Boat Privé Phi Phi
- **Prix:** ฿12,000 pour le bateau
- **Durée:** 4 heures
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71921

### Yacht Privé Phi Phi
- **Prix:** ฿72,000 pour la journée
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/100220

---

## 🤿 PLONGÉE À KOH PHI PHI

### Baptême de Plongée (Discover Scuba)
- **Prix:** ฿3,400 + ฿600 frais parc marine = ฿4,000 total
- **Durée:** Demi-journée (matin ou après-midi)
- **Inclus:** 2 plongées de 50 minutes, équipement complet, déjeuner, fruits
- **Option:** +฿750 pour photographie sous-marine
- **Prérequis:** Aucune expérience requise!
- **Instructeurs:** Francophones disponibles
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71911

### Fun Dive (Plongeurs certifiés)
- **Prix:** ฿2,700 + ฿600 frais marine = ฿3,300 total
- **Inclus:** 2 plongées, équipement complet
- **Groupes:** Max 4 plongeurs par guide
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71667

### Scuba Review (Remise à niveau)
- **Prix:** ฿3,200
- **Pour:** Plongeurs certifiés n'ayant pas plongé depuis longtemps
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71666

### Open Water SSI
- **Prix:** ฿12,900 + ฿800 frais
- **Durée:** 3-4 jours
- **Certification:** Internationale, valable à vie
- **Profondeur max:** 18m

### Open Water PADI
- **Prix:** ฿13,800 + ฿800 frais
- **Durée:** 3-4 jours
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71669

### Advanced SSI/PADI
- **Prix SSI:** ฿10,400 + ฿800
- **Prix PADI:** ฿11,300 + ฿800
- **Durée:** 2 jours
- **Profondeur max:** 30m
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/71912

---

## 🌅 EXCURSIONS DEPUIS KRABI / AO NANG

### ⭐ Hong Island Sunset & BBQ - BEST-SELLER
- **Prix:** ฿2,500/personne
- **Horaire:** 11h00-20h00 (9h)
- **Sites:** Koh Hong (lagon secret), viewpoint 420 marches, Koh Laolading, Koh Pakbia
- **Spécial:** Baignade avec planctons bioluminescents! ✨
- **Inclus:** Transfert hôtel, déjeuner, BBQ au coucher du soleil, masque, frais parc national
- **Max:** 10-12 personnes
- **Page site:** https://phiphiparadisetravel.com/excursion/hong-island-sunset

### ⭐ 4 Islands Sunset & BBQ
- **Prix:** ฿2,500/personne
- **Horaire:** 11h30-20h00 (8h30)
- **Sites:** Secret Beach, Tup Island (banc de sable), Chicken Island, Poda Island
- **Spécial:** Planctons bioluminescents! ✨
- **Inclus:** Transfert, déjeuner, BBQ sunset, masque, parc national
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86354
- **Page site:** https://phiphiparadisetravel.com/excursion/4-islands

### 4 Islands Sunrise
- **Prix:** ฿2,500/personne
- **Horaire:** 5h00-12h00
- **Sites:** Poda Island (petit-déjeuner au lever du soleil!), Tup Island, Chicken Island, Secret Beach
- **Inclus:** Transfert, petit-déjeuner sur la plage, masque, parc national

### 7 Islands Long Tail Privé
- **Prix:** ฿3,900 pour le bateau
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86356

### Baie de Phang Nga - James Bond Island
- **Prix:** ฿2,500/personne
- **Horaire:** 8h00-18h30 (10h30)
- **Sites:** Grottes mangroves en canoë, James Bond Island (L'Homme au pistolet d'or), village flottant Koh Panney
- **Fun:** Match de foot sur terrain flottant!
- **Inclus:** Transfert, canoë avec guide thai, repas, parc national
- **Max:** 10-12 personnes
- **Page site:** https://phiphiparadisetravel.com/excursion/james-bond-island

### Canoë Kayak & Crystal Lake
- **Prix:** ฿1,500/personne
- **Horaire:** 7h15-13h00
- **Sites:** Crystal Pool, Emerald Pool, mangrove, jungle
- **Avantage:** Arrivée AVANT l'ouverture au public!
- **Inclus:** Transfert, repas thai, masque, parc national

### Jungle Tour - Emerald Pool & Hot Springs
- **Prix:** ฿3,000/personne
- **Horaire:** 7h00-15h30
- **Sites:** Emerald Pool, cascades, sources d'eau chaude naturelles
- **Inclus:** Transfert, buffet à volonté, parc national

### Immersion Koh Klang
- **Prix:** ฿2,500/personne
- **Horaire:** 9h30-16h00
- **Sites:** Grottes préhistoriques, mangroves, village local, rizières, cocoteraies
- **Activités:** Artisanat local, apiculture, balade en tricycle
- **Inclus:** Transfert, déjeuner local authentique

### Temple du Tigre + Sources Chaudes
- **Prix:** ฿2,500/personne
- **Horaire:** 7h30-15h30
- **Sites:** Tiger Temple (1237 marches - vue incroyable!), sources chaudes salées dans un hôtel 5*
- **Inclus:** Transfert, repas thai, parc national

### Road Trip Scooter 🛵
- **Prix:** ฿2,000/personne
- **Horaire:** 10h00-19h00
- **Inclus:** Scooter + essence, repas, eau, guide francophone
- **Programme:** Spots incontournables + secrets locaux + coucher de soleil

### Seul au Monde 🏝️ - EXCLUSIVITÉ
- **Prix:** ฿2,500/personne
- **Horaire:** 8h45-15h30
- **Sites:** Koh Yao Yai (plages désertes, banc de sable privé), Koh Nok (viewpoint époustouflant)
- **Pourquoi:** Île encore sauvage, loin du tourisme de masse
- **Inclus:** Transfert, repas sur la plage, masque, parc national

### 🐘 Sanctuaire Éléphants + Cascades Bencha
- **Prix:** ฿3,000/personne
- **Horaire:** 7h00-15h00 (8h)
- **Programme:**
  - 3h avec les éléphants: balade à leurs côtés, baignade avec eux, bain de boue
  - Parc National Bencha: 7 niveaux de cascades, arbre de 500 ans, pique-nique nature
- **Éthique:** Sanctuaire certifié, aucune exploitation des animaux
- **Inclus:** Transfert, repas, parc national
- **Page site:** https://phiphiparadisetravel.com/excursion/elephant-sanctuary

### Excursions Privées Krabi
- **Hong Island Privée:** ฿10,500 (1-4 pers) / ฿18,000 (5-10 pers)
- **4 Islands Privée:** ฿10,500 (1-4 pers) / ฿18,000 (5-10 pers)
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86352

---

## 🚤 EXCURSIONS DEPUIS PHUKET

### Koh Phi Phi Autrement (Speedboat Premium)
- **Prix:** ฿3,500/personne
- **Horaire:** 5h15-15h30 (10h)
- **Avantage:** Maya Bay au lever du soleil, AVANT tout le monde!
- **Max:** 15 personnes seulement
- **Inclus:** Transfert hôtel, petit-déjeuner français (café, croissants, jus), repas sous les cocotiers, frais parc national
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/84448
- **Page site:** https://phiphiparadisetravel.com/excursion/phi-phi-sunrise

### Bateau Phoenix depuis Phuket
- **Prix:** ฿3,600/personne
- **Horaire:** 5h00-15h30
- **Inclus:** Transfert hôtel aller-retour, masque, snorkeling, repas, parc national

### Îles Similan - Paradis du snorkeling
- **Prix:** ฿2,000/personne
- **Pourquoi:** Les plus belles eaux de Thaïlande! Coraux intacts, tortues, poissons tropicaux
- **Saison:** Octobre à Mai uniquement
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/84442

### Coral & Racha Islands
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/84449

### James Bond Island depuis Phuket
- **Prix:** ฿1,700/personne
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/84187

### Speed Boat Privé depuis Phuket
- **Prix:** Sur devis selon itinéraire
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/84450

---

## 🏛️ EXCURSIONS DEPUIS BANGKOK

### Temples de Bangkok (Grand Palace, Wat Pho, Wat Arun)
- **Guide Anglais:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86554
- **Guide Français:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86582
- **Page site:** https://phiphiparadisetravel.com/excursion/bangkok-temples

### Floating Market & Train Market
- **Sites:** Marché flottant Damnoen Saduak, marché du train Mae Klong
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86552

### Ayutthaya (Ancienne capitale UNESCO)
- **Guide Anglais:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86578
- **Guide Français:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86588

### Tuk Tuk Tour Gastronomique
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86579

### Combo Marchés + Ayutthaya
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86580

### Dîner Croisière Bangkok
- **Programme:** Croisière sur le Chao Phraya, dîner buffet, vue temples illuminés
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86581

### Visite Bangkok Tranquille (Guide Français)
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86585

### Kanchanaburi - River Kwai (Guide Français)
- **Sites:** Pont de la rivière Kwai, cascades Erawan
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86589

### Nakornpathom - Lac de Lotus (Guide Français)
- **Sites:** Lac aux lotus roses (saison), plus grand temple de Thaïlande
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86590

---

## 🐘 EXCURSIONS DEPUIS CHIANG MAI

### Éléphants Chiang Mai
- **Prix:** ฿1,500/personne
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86591

### Chiang Rai - Temples Blanc & Bleu
- **Prix:** ฿1,900/personne
- **Sites:** Temple Blanc (Wat Rong Khun), Temple Bleu (Wat Rong Suea Ten)
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86592

### Thai Cooking Class
- **Prix:** ฿1,900/personne
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86593

### Tuk Tuk Tour + Muay Thai
- **Prix:** ฿3,000/personne
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86594

### Chiang Rai Full Day
- **Prix:** ฿1,900/personne
- **Lien MyRezz:** https://booking.myrezapp.com/fr/online/booking/step1/16686/86595

---

## 🌴 EXCURSIONS DEPUIS KOH LANTA

### Îles Trang (Koh Kradan - #1 Plus belle île du monde 2023!)
- **Prix (bateau privé):**
  - 1-4 personnes: ฿7,500
  - 4-6 personnes: ฿8,500
  - 6-8 personnes: ฿9,500
  - 8-10 personnes: ฿10,500
  - 10-12 personnes: ฿11,500
  - 12-14 personnes: ฿13,000
- **Horaire:** 8h00-17h00
- **Sites:** Koh Ngai, Koh Maa, Koh Mook (Emerald Cave!), Koh Chuek, Koh Kradan
- **Inclus:** Transfert, repas sur la plage, fruits, boissons, masque, frais parc national

### Koh Rok
- **Prix:** Mêmes tarifs que îles Trang
- **Pourquoi:** Snorkeling exceptionnel, eaux cristallines

---

## 🚢 FERRIES & TRANSFERTS

### Depuis Phi Phi
- **Phi Phi → Phuket:** ฿1,100 - https://booking.myrezapp.com/fr/online/booking/step1/16686/71407
- **Phi Phi → Krabi:** ฿1,100 - https://booking.myrezapp.com/fr/online/booking/step1/16686/71409

---

## 💡 RECOMMANDATIONS PAR PROFIL

### Pour les familles avec enfants:
- Bateau Pirate Phoenix (calme)
- Hong Island (planctons magiques pour les enfants!)
- Sanctuaire Éléphants

### Pour les couples romantiques:
- Matin Maya (lever de soleil)
- Hong Island Sunset BBQ
- Yacht Privé

### Pour les fêtards:
- Bateau Pirate Dragon (ambiance festive)

### Pour les aventuriers:
- Baptême de plongée
- Road Trip Scooter
- Temple du Tigre (1237 marches!)

### Pour les amoureux de nature:
- Seul au Monde (île sauvage)
- Similan Islands
- Koh Kradan

### Budget serré:
- Matin Maya (฿800)
- Magique Turquoise (฿700)
"""

# ============================================
# Mémoire persistante (fichiers JSON)
# ============================================
def get_phone_hash(phone: str) -> str:
    """Hash du numéro pour confidentialité"""
    return hashlib.md5(phone.encode()).hexdigest()[:12]

def get_conversation_file(phone: str) -> Path:
    """Chemin du fichier de conversation"""
    return CONVERSATIONS_DIR / f"{get_phone_hash(phone)}.json"

def load_conversation(phone: str) -> dict:
    """Charge ou crée une conversation"""
    file_path = get_conversation_file(phone)
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "phone": phone,
        "phone_hash": get_phone_hash(phone),
        "messages": [],
        "client_info": {},
        "first_contact": datetime.now().isoformat(),
        "last_interaction": datetime.now().isoformat(),
        "interests": [],
        "recommended_trips": [],
        "total_messages": 0
    }

def save_conversation(phone: str, conv: dict):
    """Sauvegarde une conversation"""
    file_path = get_conversation_file(phone)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(conv, f, ensure_ascii=False, indent=2)

def add_message(phone: str, role: str, content: str):
    """Ajoute un message et sauvegarde"""
    conv = load_conversation(phone)
    conv["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    # Garder les 30 derniers messages
    if len(conv["messages"]) > 30:
        conv["messages"] = conv["messages"][-30:]
    conv["last_interaction"] = datetime.now().isoformat()
    conv["total_messages"] += 1
    save_conversation(phone, conv)
    return conv

def update_client_info(phone: str, info: dict):
    """Met à jour les infos client"""
    conv = load_conversation(phone)
    conv["client_info"].update(info)
    save_conversation(phone, conv)

def get_context_for_ai(phone: str) -> str:
    """Génère le contexte pour l'IA"""
    conv = load_conversation(phone)
    context = ""
    
    if conv["client_info"]:
        context += "\n## INFOS CLIENT CONNUES:\n"
        for k, v in conv["client_info"].items():
            context += f"- {k}: {v}\n"
    
    if conv["interests"]:
        context += f"\n## INTÉRÊTS: {', '.join(conv['interests'])}\n"
    
    if conv["recommended_trips"]:
        context += f"\n## EXCURSIONS DÉJÀ RECOMMANDÉES: {', '.join(conv['recommended_trips'])}\n"
    
    if conv["messages"]:
        context += "\n## HISTORIQUE (derniers échanges):\n"
        for msg in conv["messages"][-8:]:
            role = "Client" if msg["role"] == "user" else "Olivia"
            text = msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"]
            context += f"{role}: {text}\n"
    
    return context

# ============================================
# Extraction d'infos client
# ============================================
def extract_info(text: str) -> dict:
    """Extrait les infos du message"""
    info = {}
    text_lower = text.lower()
    
    # Prénom
    prenom_match = re.search(r"(?:je m'appelle|my name is|moi c'est|i'm|je suis)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)", text, re.IGNORECASE)
    if prenom_match:
        info["prenom"] = prenom_match.group(1).capitalize()
    
    # Nombre de personnes
    pers_match = re.search(r"(\d+)\s*(?:personnes?|pers|people|pax|adultes?|nous sommes)", text_lower)
    if pers_match:
        info["nombre_personnes"] = pers_match.group(1)
    
    # Date
    date_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}(?:[\/\-\.]\d{2,4})?)", text)
    if date_match:
        info["date_voyage"] = date_match.group(1)
    
    # Mois
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre",
            "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    for m in mois:
        if m in text_lower:
            info["mois_voyage"] = m.capitalize()
            break
    
    # Localisation
    lieux = ["phi phi", "krabi", "ao nang", "phuket", "bangkok", "chiang mai", "lanta", "railay"]
    for lieu in lieux:
        if lieu in text_lower:
            info["localisation"] = lieu.title()
            break
    
    # Intérêts
    interets_found = []
    interets_keywords = {
        "plongée": ["plongée", "plonger", "diving", "scuba", "snorkeling", "snorkel"],
        "famille": ["famille", "enfant", "kid", "family", "bébé", "baby"],
        "romantique": ["couple", "romantique", "romantic", "lune de miel", "honeymoon", "amoureux"],
        "fête": ["fête", "party", "festif", "ambiance", "musique", "alcool", "bar"],
        "nature": ["nature", "tranquille", "calme", "peaceful", "éléphant", "elephant", "jungle"],
        "aventure": ["aventure", "adventure", "adrénaline", "sport"],
        "budget": ["budget", "pas cher", "cheap", "économique", "moins cher"]
    }
    for interet, keywords in interets_keywords.items():
        if any(kw in text_lower for kw in keywords):
            interets_found.append(interet)
    
    if interets_found:
        info["interets"] = interets_found
    
    return info

# ============================================
# WAHA - Comportement Humain
# ============================================
async def waha_send_seen(chat_id: str):
    """Marque le message comme lu"""
    if not WAHA_API_KEY:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{WAHA_API_URL}/api/sendSeen",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, "chatId": chat_id},
                timeout=10
            )
    except Exception as e:
        print(f"sendSeen error: {e}")

async def waha_start_typing(chat_id: str):
    """Commence à taper"""
    if not WAHA_API_KEY:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{WAHA_API_URL}/api/startTyping",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, "chatId": chat_id},
                timeout=10
            )
    except Exception as e:
        print(f"startTyping error: {e}")

async def waha_stop_typing(chat_id: str):
    """Arrête de taper"""
    if not WAHA_API_KEY:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{WAHA_API_URL}/api/stopTyping",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, "chatId": chat_id},
                timeout=10
            )
    except Exception as e:
        print(f"stopTyping error: {e}")

async def waha_send_text(chat_id: str, text: str):
    """Envoie un message texte"""
    if not WAHA_API_KEY:
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WAHA_API_URL}/api/sendText",
                headers={"X-Api-Key": WAHA_API_KEY, "Content-Type": "application/json"},
                json={"session": WAHA_SESSION, "chatId": chat_id, "text": text},
                timeout=30
            )
            return response.status_code in [200, 201]
    except Exception as e:
        print(f"sendText error: {e}")
        return False

def calculate_typing_time(text: str) -> float:
    """Calcule un temps de frappe réaliste (humain tape ~40 mots/min)"""
    words = len(text.split())
    # Entre 1.5 et 4 secondes par ligne de ~10 mots
    base_time = (words / 10) * random.uniform(1.5, 3.0)
    # Minimum 2 sec, maximum 15 sec
    return max(2.0, min(base_time, 15.0))

# ============================================
# IA - NVIDIA API
# ============================================
SYSTEM_PROMPT = f"""Tu es Olivia, l'assistante virtuelle de Phi Phi Paradise Travel.

## TA PERSONNALITÉ
- Chaleureuse, accueillante, naturelle
- Tu parles comme une vraie personne, pas un robot
- Bilingue français/anglais (adapte-toi au client)
- Experte passionnée de la Thaïlande
- Tu veux AIDER, pas juste vendre

## STYLE DE RÉPONSE WHATSAPP
- Messages COURTS (max 300 caractères idéalement)
- Naturel et conversationnel
- Utilise des emojis avec modération (1-2 max par message)
- Pose UNE question à la fois
- Si longue réponse nécessaire, divise en plusieurs messages courts

## QUAND DONNER LES LIENS
- Donne le lien MyRezz quand le client montre un intérêt clair
- Donne aussi le lien du site pour plus d'infos: phiphiparadisetravel.com
- Format: "Tu peux réserver ici: [lien]" (pas de markdown)

## COLLECTE D'INFOS (subtile)
Essaie de savoir naturellement:
- Prénom
- Dates de voyage
- Où ils logent (Phi Phi, Krabi, Phuket?)
- Intérêts (plongée, fête, famille, nature?)
- Combien de personnes

## RECOMMANDATIONS INTELLIGENTES
- Adapte tes suggestions au profil du client
- Familles → Bateau Phoenix, Éléphants
- Couples → Matin Maya, Sunset BBQ
- Fêtards → Bateau Dragon
- Aventuriers → Plongée, Temple du Tigre
- Budget → Matin Maya (฿800), Magique Turquoise (฿700)

## INFOS CLÉS À RETENIR
- Aucun acompte requis
- Enfants -9 ans: -50%
- Enfants -3 ans: gratuit
- Guides francophones disponibles
- Transfert hôtel toujours inclus

## FORMAT PRIX
- Toujours en Baht: ฿800, ฿2,500, etc.

## SI TU NE SAIS PAS
- Dis-le honnêtement
- Propose de contacter Jiji au +66 99 11 58 304

## SIGNATURE
- Signe "Olivia 🌴" uniquement en fin de conversation ou après une réservation

{KNOWLEDGE_BASE}
"""

def call_nvidia_api(messages: list) -> str:
    """Appelle l'API NVIDIA"""
    if not NVIDIA_API_KEY:
        raise Exception("NVIDIA_API_KEY manquante")
    
    response = requests.post(
        NVIDIA_API_URL,
        headers={
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.8,
            "top_p": 0.9,
            "stream": True,
            "chat_template_kwargs": {"thinking": True}
        },
        stream=True,
        timeout=120
    )
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.text}")
    
    # Parse SSE
    content = ""
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content += delta.get("content", "")
                except:
                    continue
    
    return content

# ============================================
# Traitement du message WhatsApp
# ============================================
async def process_message(chat_id: str, message: str):
    """Traite un message avec comportement humain"""
    try:
        # 1. DÉLAI LECTURE (humain lit avant de répondre)
        read_delay = random.uniform(1.0, 3.0)
        await asyncio.sleep(read_delay)
        
        # 2. MARQUER COMME LU
        await waha_send_seen(chat_id)
        
        # 3. DÉLAI RÉFLEXION (humain réfléchit)
        think_delay = random.uniform(2.0, 5.0)
        await asyncio.sleep(think_delay)
        
        # 4. COMMENCER À TAPER
        await waha_start_typing(chat_id)
        
        # 5. SAUVEGARDER MESSAGE CLIENT
        add_message(chat_id, "user", message)
        
        # 6. EXTRAIRE INFOS CLIENT
        info = extract_info(message)
        if info:
            # Séparer les intérêts
            interets = info.pop("interets", [])
            if info:
                update_client_info(chat_id, info)
            if interets:
                conv = load_conversation(chat_id)
                conv["interests"] = list(set(conv.get("interests", []) + interets))
                save_conversation(chat_id, conv)
        
        # 7. GÉNÉRER RÉPONSE IA
        context = get_context_for_ai(chat_id)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + f"\n\n## CONTEXTE CLIENT ACTUEL:\n{context}"},
            {"role": "user", "content": message}
        ]
        
        ai_response = call_nvidia_api(messages)
        
        # 8. SIMULER TEMPS DE FRAPPE
        typing_time = calculate_typing_time(ai_response)
        await asyncio.sleep(typing_time)
        
        # 9. ARRÊTER DE TAPER
        await waha_stop_typing(chat_id)
        
        # 10. PETIT DÉLAI AVANT ENVOI
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # 11. ENVOYER LA RÉPONSE
        await waha_send_text(chat_id, ai_response)
        
        # 12. SAUVEGARDER RÉPONSE
        add_message(chat_id, "assistant", ai_response)
        
        print(f"✅ [{chat_id[:15]}...] Répondu en {typing_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        await waha_stop_typing(chat_id)
        await waha_send_text(chat_id, "Désolée, petit souci! 😅 Contacte-nous au +66 99 11 58 304")

# ============================================
# Routes API
# ============================================
@app.get("/")
async def root():
    """Status de l'agent"""
    conv_files = list(CONVERSATIONS_DIR.glob("*.json"))
    return {
        "name": "Olivia 3.0 - Phi Phi Paradise Travel",
        "version": "3.0",
        "status": "online",
        "model": MODEL,
        "features": [
            "human_behavior",
            "persistent_memory", 
            "knowledge_base",
            "typing_indicator",
            "smart_extraction"
        ],
        "whatsapp": "connected" if WAHA_API_KEY else "not configured",
        "active_conversations": len(conv_files)
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL}

@app.post("/webhook/waha")
async def waha_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook WAHA avec comportement humain"""
    try:
        body = await request.json()
        
        if body.get("event") == "message":
            payload = body.get("payload", {})
            
            # Ignorer nos propres messages
            if payload.get("fromMe"):
                return {"status": "ignored", "reason": "self"}
            
            chat_id = payload.get("from", "")
            message = payload.get("body", "")
            msg_type = payload.get("type", "")
            
            # Traiter les messages texte
            if msg_type == "chat" and message:
                background_tasks.add_task(process_message, chat_id, message)
                return {"status": "processing", "chat": chat_id[:15]}
        
        return {"status": "ignored"}
    
    except Exception as e:
        return {"status": "error", "detail": str(e)}

class ChatRequest(BaseModel):
    message: str
    phone: Optional[str] = "web_user"

@app.post("/chat")
async def chat_api(request: ChatRequest):
    """API Chat directe"""
    add_message(request.phone, "user", request.message)
    
    context = get_context_for_ai(request.phone)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n## CONTEXTE:\n{context}"},
        {"role": "user", "content": request.message}
    ]
    
    response = call_nvidia_api(messages)
    add_message(request.phone, "assistant", response)
    
    return {"response": response, "model": MODEL}

@app.get("/conversations")
async def list_conversations():
    """Liste toutes les conversations"""
    convs = []
    for file in CONVERSATIONS_DIR.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            conv = json.load(f)
            convs.append({
                "id": conv["phone_hash"],
                "phone": conv["phone"][:10] + "...",
                "client_info": conv.get("client_info", {}),
                "messages": len(conv.get("messages", [])),
                "last": conv.get("last_interaction", "")
            })
    return {"conversations": sorted(convs, key=lambda x: x["last"], reverse=True)}

@app.get("/conversations/{phone_hash}")
async def get_conversation(phone_hash: str):
    """Détail d'une conversation"""
    for file in CONVERSATIONS_DIR.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            conv = json.load(f)
            if conv["phone_hash"] == phone_hash:
                return conv
    raise HTTPException(status_code=404, detail="Conversation non trouvée")

@app.get("/test")
async def test():
    return {
        "nvidia": "✅" if NVIDIA_API_KEY else "❌",
        "waha": "✅" if WAHA_API_KEY else "❌",
        "model": MODEL,
        "knowledge_base_chars": len(KNOWLEDGE_BASE)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
