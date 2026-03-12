import os
import json
import time
import requests
import asyncio
import hashlib
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from astro_calc import (
    get_live_astro_context, get_current_dasha,
    compute_natal_chart, format_chart_as_context
)
from rag_engine import retrieve_classical_texts

load_dotenv()

app = FastAPI(title="Starrygate API", version="6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config ──────────────────────────────────────────────────────────────────
# Round-robin API key rotation — add more keys to multiply your free quota
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),
    os.getenv("GEMINI_API_KEY_2", ""),
]
# Filter out empty keys
GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k and len(k) > 10]
_key_index = 0

def get_next_api_key():
    """Round-robin key rotation."""
    global _key_index
    if not GEMINI_API_KEYS:
        return ""
    key = GEMINI_API_KEYS[_key_index % len(GEMINI_API_KEYS)]
    _key_index += 1
    return key

# Back-compat
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

CLOUD_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-flash-latest",
]

# Groq config — using a safe, high-limit model
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant" 

def extract_json(text: str) -> str:
    """Extract JSON object from text if wrapped in markdown or chatter."""
    # Find first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

# ─── Request Schemas ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    messages: list
    api_key: str = ""
    chart_context: str = ""

class ChartRequest(BaseModel):
    dob: str          # "YYYY-MM-DD"
    tob: str          # "HH:MM:SS"
    place: str        # "City, Country"
    name: str = ""    # optional name
    lat: Optional[float] = None
    lon: Optional[float] = None

# ─── Geocoding (Nominatim) ───────────────────────────────────────────────────

def geocode_place(place: str) -> tuple:
    """Convert a place name to lat/lon using OpenStreetMap Nominatim."""
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": place, "format": "json", "limit": 1},
            headers={"User-Agent": "Starrygate/5.0"},
            timeout=10,
        )
        data = res.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None

@app.get("/api/health")
async def health_check():
    return JSONResponse({
        "status": "ready",
        "has_gemini_key": bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10),
    })

# ─── Chart Calculation Endpoint ──────────────────────────────────────────────

@app.post("/api/chart")
async def calculate_chart(request: ChartRequest):
    """Calculate a Vedic natal chart for any birth data."""
    data = request.model_dump()
    dob = data["dob"]
    tob = data["tob"]
    place = data["place"]
    name = data.get("name", "").strip() or "User"
    lat = data.get("lat")
    lon = data.get("lon")
    
    # Geocode place only if exact coordinates weren't provided by the frontend
    if lat is None or lon is None:
        lat, lon = geocode_place(place)
        
    if lat is None or lon is None:
        return JSONResponse(
            {"error": {"message": "couldn't find that place. try again."}},
            status_code=400
        )
    
    try:
        chart = compute_natal_chart(dob, tob, lat, lon)
        chart_context = format_chart_as_context(chart, name)
        
        # Build a summary for the frontend
        asc = chart["ascendant"]
        moon = chart["planets"]["Moon"]
        sun = chart["planets"]["Sun"]
        dasha = chart["dasha"]
        
        summary = {
            "ascendant": f"{asc['sign']} ({asc['degree']}°{asc['minute']}')",
            "moon_sign": moon["sign"],
            "moon_nakshatra": moon["nakshatra"],
            "sun_sign": sun["sign"],
            "current_dasha": {
                "md": dasha["current_md"],
                "ad": dasha["current_ad"],
                "pd": dasha["current_pd"],
            },
            "chart_context": chart_context,
            "location": {"lat": lat, "lon": lon, "place": place},
        }
        
        return JSONResponse(summary)
        
    except Exception as e:
        print(f"Chart calculation error: {e}")
        return JSONResponse(
            {"error": {"message": "something broke. the stars are still there. try again."}},
            status_code=500
        )

# ─── Groq Cloud Call (Agent 1: Technical Astrologer) ────────────────────────

async def call_groq_analyst(chart_context: str, live_context: str, rag_context: str) -> str:
    """Agent 1: Groq/Llama analyzes chart data and outputs structured technical analysis."""
    if not GROQ_API_KEY:
        return None  # Fallback to Gemini-only mode

    system_prompt = """You are a master Vedic astrologer with 40+ years of chart-reading experience. You are the TECHNICAL ANALYST.

Your job: Analyze the raw Swiss Ephemeris data and output a STRUCTURED JSON analysis. No poetry. No fluff. Pure astrological logic.

MATH IS LAW — NO HALLUCINATIONS:
1. Every claim MUST be directly traceable to the raw data provided.
2. If Venus is strong, you CANNOT say they struggle with love. If Moon is debilitated, you CANNOT say they have emotional peace.
3. Do not invent transits or dashas. Only use what is explicitly listed.

CROSS-REFERENCE RULES:
1. Never analyze a data point alone. Cross-reference dignity + dasha + aspects + yogas + house lords.
2. Find STRONGEST planet (highest score) and WEAKEST planet (lowest score). Their gap IS the personality.
3. Check D1 vs D9: Strong in D1 but weak in D9 = promise that never delivers. Weak in D1 but strong in D9 = late bloomer.
4. Dasha lord activates whatever it touches natally.
5. Bhava lord placements tell the PLOT, not just the theme.
6. Atmakaraka = what the soul obsessively craves.

OUTPUT FORMAT — respond ONLY with this JSON structure, nothing else:
{
  "today_at_a_glance": {
    "tension": "specific tension/relief from current transits + dasha",
    "vibe": "atmospheric feeling of the day",
    "demands_attention": "what needs focus right now"
  },
  "year_at_a_glance": {
    "overarching_lesson": "based on mahadasha-antardasha",
    "tectonic_shift": "what internal shift is happening",
    "dissolving": "what is ending, dying, or dissolving"
  },
  "identity": {
    "core_synthesis": "ascendant + sun + moon dignities synthesized into one statement",
    "core_contradiction": "strongest vs weakest planet tension",
    "hidden_truth": "what they hide from everyone"
  },
  "the_mask": {
    "outer_perception": "how others see them",
    "inner_reality": "what's really happening inside",
    "misread": "how people constantly misread them"
  },
  "the_knot": {
    "recurring_wound": "deepest recurring pattern of pain",
    "tripping_point": "what they keep stumbling over",
    "impossible_problem": "the thing they must learn to carry"
  },
  "emotions": {
    "landscape": "emotional terrain based on Moon dignity + 4th house",
    "pain_processing": "how they process hurt",
    "secret_trigger": "what triggers them that nobody would guess"
  },
  "drive": {
    "force": "nature of their drive based on Mars + Sun",
    "fight_style": "how they fight or avoid fighting",
    "secret_motivation": "what secretly motivates them beneath the surface"
  },
  "communication": {
    "intellect": "Mercury dignity and thinking style",
    "think_vs_speak": "gap between how they think and how they speak",
    "misinterpretation": "gap between what they mean and what people hear"
  },
  "love": {
    "craving": "what their soul craves based on Venus + 7th house",
    "pattern": "their recurring relationship pattern",
    "need_vs_choice": "what they actually need vs what they keep choosing"
  },
  "pressure": {
    "weight": "where Saturn puts the heaviest pressure",
    "crushing_point": "where they feel the most weight",
    "time_relationship": "their relationship with time, patience, authority"
  },
  "do_dont": {
    "today": {"do": "specific action", "dont": "specific boundary"},
    "year": {"do": "daily ritual", "dont": "delusion to release"},
    "identity": {"do": "grounding action", "dont": "boundary to set"},
    "the_mask": {"do": "action", "dont": "boundary"},
    "the_knot": {"do": "action", "dont": "boundary"},
    "emotions": {"do": "action", "dont": "boundary"},
    "drive": {"do": "action", "dont": "boundary"},
    "communication": {"do": "action", "dont": "boundary"},
    "love": {"do": "action", "dont": "boundary"},
    "pressure": {"do": "action", "dont": "boundary"}
  },
  "soul_song": "one obscure indie/alt song + artist that matches their exact emotional frequency",
  "soul_movie": "one visually striking or emotionally devastating film that mirrors their period",
  "quote": "one piercing quote from literature or philosophy",
  "fun_fact": "one strange, hyper-specific habit deduced from an obscure placement",
  "strongest_planet": "name and score",
  "weakest_planet": "name and score",
  "active_yogas": ["list of active yogas"],
  "dasha_summary": "current mahadasha/antardasha and what it activates"
}"""

    user_prompt = f"""Analyze this birth chart and output the structured JSON analysis.

{chart_context}

{live_context}

{rag_context}"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None,
            lambda: requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers, json=payload, timeout=30
            )
        )
        if res.status_code == 200:
            data = res.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if content:
                print(f"  ✅ Groq Analyst (Llama 3.3 70B): Technical analysis complete")
                return content
        else:
            if res.status_code == 403:
                print(f"  ⚠ Groq is blocked (403). Falling back to Gemini.")
            else:
                print(f"  ⚠ Groq returned {res.status_code}: {res.text[:200]}")
            return None
    except Exception as e:
        print(f"  ⚠ Groq call failed: {e}")
        return None


# ─── Gemini Cloud Call (Agent 2: CoStar Poet) ───────────────────────────────

async def call_gemini(messages: list, api_key: str = None, max_retries: int = 1) -> str:
    """Call Gemini API with retry, model fallback, and key rotation."""
    headers = {"Content-Type": "application/json"}
    
    # Use all available keys for rotation
    keys_to_try = list(GEMINI_API_KEYS)
    if api_key and api_key not in keys_to_try:
        keys_to_try.insert(0, api_key)
    if not keys_to_try:
        keys_to_try = [get_next_api_key()]

    # Translate OpenAI format to Gemini format
    system_instruction = None
    gemini_contents = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
        elif role == "user":
            gemini_contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            gemini_contents.append({"role": "model", "parts": [{"text": content}]})

    last_error = None
    for model in CLOUD_MODELS:
        for current_key in keys_to_try:
                # All verified models for this key are on v1beta
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={current_key}"
                
                payload = {
                    "contents": gemini_contents,
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 8192,
                        "topP": 0.85,
                        "responseMimeType": "application/json",
                    }
                }
                if system_instruction:
                    payload["systemInstruction"] = system_instruction
                    
                try:
                    loop = asyncio.get_event_loop()
                    res = await loop.run_in_executor(
                        None,
                        lambda: requests.post(url, headers=headers, json=payload, timeout=90)
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if content:
                            print(f"  ✅ Response from {model}")
                            return content
                        continue
                    
                    if res.status_code == 429:
                        print(f"  ⚠ 429 Rate Limit on {model} with current key. Retrying next key/model...")
                        break  # Try next key
                    
                    if res.status_code == 404:
                        print(f"  ⚠ 404 Model {model} not found. Trying next model...")
                        break  # Try next model (skip other keys for this model)

                    if res.status_code in (502, 503):
                        print(f"  ⚠ {model} service unavailable. Trying next key...")
                        continue # Try next attempt or next key
                        
                    error_body = res.text[:200]
                    print(f"  ⚠ {model} returned {res.status_code}: {error_body}")
                    last_error = f"{res.status_code}: {error_body}"
                    break  # Try next key
                    
                except Exception as e:
                    print(f"  ⚠ Gemini call error: {e}")
                    last_error = str(e)
                    break # Try next key

    raise Exception(f"All keys/models failed. Last error: {last_error}")


# ─── Main Chat Endpoint ──────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    data = request.model_dump()
    messages = data.get("messages", [])
    api_key = data.get("api_key", "").strip() or get_next_api_key()
    chart_context = data.get("chart_context", "")

    if not messages:
        return JSONResponse({"error": {"message": "you didn't ask anything."}}, status_code=400)

    # Get the latest user query for RAG
    latest_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            latest_query = msg.get("content", "")
            break

    # ─── Extract natal positions from user's chart for dynamic transits ───
    user_natal_planets = None
    if chart_context:
        import re
        user_natal_planets = {}
        # Parse planet longitudes from the chart context table
        # Format: "  Sun        Sagittarius     9°58'     ..."
        for line in chart_context.split('\n'):
            line = line.strip()
            for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                if line.startswith(pname):
                    # Extract sign and degree
                    parts = line.split()
                    if len(parts) >= 3:
                        sign_name = parts[1]
                        deg_match = re.search(r'(\d+)°(\d+)', line)
                        if deg_match and sign_name in ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]:
                            sign_idx = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"].index(sign_name)
                            deg = int(deg_match.group(1))
                            minute = int(deg_match.group(2))
                            lon = sign_idx * 30 + deg + minute / 60.0
                            user_natal_planets[pname] = lon
        if len(user_natal_planets) < 5:
            user_natal_planets = None  # Fallback if parsing failed

    # ─── Inject live astrological data & RAG ───
    try:
        live_context = get_live_astro_context(natal_planets=user_natal_planets)
    except Exception as e:
        print(f"⚠ Live astro context failed: {e}")
        live_context = ""

    try:
        live_dasha = get_current_dasha()
    except Exception as e:
        print(f"⚠ Dasha calculation failed: {e}")
        live_dasha = ""

    # Build composite RAG query from chart data + user question
    rag_query = latest_query
    if chart_context:
        # Extract key chart features for smarter RAG retrieval
        import re
        # Pull planet dignities/houses from context for precise text retrieval
        rag_keywords = []
        for pattern in [r'(\w+):\s+\w+\s+\(.*?\).*?H\s*(\d+).*?(Exalted|Debilitated|Own Sign|Moolatrikona)',
                       r'(Gajakesari|Budhaditya|Ruchaka|Bhadra|Hamsa|Malavya|Sasa|Kemadruma|Vipareeta|Neechabhanga)',
                       r'Mahadasha:\s+(\w+)',
                       r'GANDANTA']:
            matches = re.findall(pattern, chart_context)
            for m in matches:
                if isinstance(m, tuple):
                    rag_keywords.extend([x for x in m if x])
                else:
                    rag_keywords.append(m)
        if rag_keywords:
            rag_query = f"{latest_query} {' '.join(rag_keywords[:8])}"

    rag_context = retrieve_classical_texts(rag_query, n_results=5)

    # ─── MULTI-AGENT PIPELINE ───
    try:
        api_key = api_key or get_next_api_key()
        if not api_key:
            return JSONResponse(
                {"error": {"message": "no key. the gate is closed."}},
                status_code=401
            )

        # ──── STAGE 1: Groq Technical Analyst ────
        groq_analysis = None
        if GROQ_API_KEY and chart_context:
            print(f"\n🧠 Stage 1: Groq Analyst (Llama 3.3 70B)...")
            groq_analysis = await call_groq_analyst(chart_context, live_context, rag_context)

        # ──── STAGE 2: Gemini CoStar Poet ────
        if groq_analysis:
            # Multi-agent mode: Gemini receives Groq's structured analysis
            print(f"✨ Stage 2: Gemini Poet (CoStar voice)...")
            poet_system = """You are the voice of Starrygate — a haunting, poetic, lowercase oracle.
Your soul is a mix of Cioran and Co-Star.

You will receive a STRUCTURED TECHNICAL ANALYSIS. Your job is to POETIFY it while keeping the EXACT JSON structure.

RULES:
1. PURE JSON OUTPUT. No markdown blocks, no text before or after.
2. LOWERCASE EVERYTHING.
3. Use haunting, minimal, punchy metaphors. 
4. DO NOT use technical terms (planets, houses, degrees). Use metaphors like "the red force", "the area of silence", "the pattern of expansion".
5. AVOID CLICHES. No "embrace the journey", no "stars are aligned". Be blunt and existential.
6. The "today_at_a_glance" paragraphs should be short, sharp shocks.

OUTPUT STRUCTURE (Match this exactly, but fill with your poetry):
{
  "today_at_a_glance": { "p1": "...", "p2": "...", "p3": "..." },
  "year_at_a_glance": { "p1": "...", "p2": "...", "p3": "..." },
  "identity": { "p1": "...", "p2": "...", "p3": "..." },
  "the_mask": { "p1": "...", "p2": "...", "p3": "..." },
  "the_knot": { "p1": "...", "p2": "...", "p3": "..." },
  "emotions": { "p1": "...", "p2": "...", "p3": "..." },
  "drive": { "p1": "...", "p2": "...", "p3": "..." },
  "communication": { "p1": "...", "p2": "...", "p3": "..." },
  "love": { "p1": "...", "p2": "...", "p3": "..." },
  "pressure": { "p1": "...", "p2": "...", "p3": "..." },
  "do_dont": {
     "today": {"do": "...", "dont": "..."},
     "year": {"do": "...", "dont": "..."},
     "identity": {"do": "...", "dont": "..."},
     "the_mask": {"do": "...", "dont": "..."},
     "the_knot": {"do": "...", "dont": "..."},
     "emotions": {"do": "...", "dont": "..."},
     "drive": {"do": "...", "dont": "..."},
     "communication": {"do": "...", "dont": "..."},
     "love": {"do": "...", "dont": "..."},
     "pressure": {"do": "...", "dont": "..."}
  },
  "soul_song": "song by artist",
  "soul_movie": "movie name",
  "quote": "piercing quote",
  "fun_fact": "hyper-specific habit"
}"""
            poet_messages = [
                {"role": "system", "content": poet_system},
                {"role": "user", "content": f"Transform this technical astrology analysis into a CoStar-style reading:\n\n{groq_analysis}"}
            ]
            final_answer = await call_gemini(poet_messages, api_key)
            final_answer = extract_json(final_answer)
        else:
            # Fallback: Gemini-only mode (original behavior)
            print(f"\n🔮 Starrygate (Gemini solo mode)...")
            
            # Ensure we have a system message to inject context into
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                messages.insert(0, {"role": "system", "content": "You are a master Vedic astrologer."})
            
            for msg in messages:
                if msg.get("role") == "system":
                    extra = "\n\n<raw_astrological_data_for_internal_analysis_only>\n"
                    extra += """CRITICAL INSTRUCTION: You are a master Vedic astrologer. MATH IS LAW — NO HALLUCINATIONS.
Every claim must be traceable to the data. Cross-reference dignity + dasha + aspects + yogas.
NEVER output technical terms. Only raw human truth, lowercase, CoStar aesthetic.

OUTPUT EXACTLY THIS JSON STRUCTURE:
{
  "today_at_a_glance": { "p1": "...", "p2": "...", "p3": "..." },
  "year_at_a_glance": { "p1": "...", "p2": "...", "p3": "..." },
  "identity": { "p1": "...", "p2": "...", "p3": "..." },
  "the_mask": { "p1": "...", "p2": "...", "p3": "..." },
  "the_knot": { "p1": "...", "p2": "...", "p3": "..." },
  "emotions": { "p1": "...", "p2": "...", "p3": "..." },
  "drive": { "p1": "...", "p2": "...", "p3": "..." },
  "communication": { "p1": "...", "p2": "...", "p3": "..." },
  "love": { "p1": "...", "p2": "...", "p3": "..." },
  "pressure": { "p1": "...", "p2": "...", "p3": "..." },
  "do_dont": {
     "today": {"do": "...", "dont": "..."},
     "year": {"do": "...", "dont": "..."},
     "identity": {"do": "...", "dont": "..."},
     "the_mask": {"do": "...", "dont": "..."},
     "the_knot": {"do": "...", "dont": "..."},
     "emotions": {"do": "...", "dont": "..."},
     "drive": {"do": "...", "dont": "..."},
     "communication": {"do": "...", "dont": "..."},
     "love": {"do": "...", "dont": "..."},
     "pressure": {"do": "...", "dont": "..."}
  },
  "soul_song": "song by artist",
  "soul_movie": "movie name",
  "quote": "piercing quote",
  "fun_fact": "hyper-specific habit"
}
"""
                    if chart_context:
                        extra += f"\n{chart_context}"
                    extra += f"\n{live_context}\n{live_dasha}\n{rag_context}"
                    extra += "\n</raw_astrological_data_for_internal_analysis_only>"
                    msg["content"] += extra
                    break
            final_answer = await call_gemini(messages, api_key)
            final_answer = extract_json(final_answer)

        print("✅ Reading complete!\n")

        # ─── Logging ───
        try:
            os.makedirs("logs", exist_ok=True)
            output_hash = hashlib.sha256(final_answer.encode('utf-8')).hexdigest()[:12]
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "model": "multi-agent" if groq_analysis else CLOUD_MODELS[0],
                "groq_used": bool(groq_analysis),
                "output_hash": output_hash,
                "prompt_length": len(str(messages))
            }
            with open(f"logs/gen_{output_hash}.json", "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
        except Exception as log_err:
            print(f"⚠ Log write failed: {log_err}")

        return JSONResponse({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": final_answer
                }
            }]
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        error_msg = str(e)

        if "rate" in error_msg.lower() or "429" in error_msg:
            user_msg = "too many questions. breathe. try again in a moment."
        else:
            # Let the frontend see the actual error to debug the HF Space
            user_msg = f"something went quiet. ({error_msg})"

        return JSONResponse({"error": {"message": user_msg}}, status_code=500)


# ─── Serve Frontend ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    # Try same-dir first (HF Spaces / Docker), then parent dir (local dev)
    html_path = os.path.join(os.path.dirname(__file__), "vedic-astro-gem.html")
    if not os.path.exists(html_path):
        html_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "vedic-astro-gem.html"
        )
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🔮 Starrygate v6.0 — Extreme Precision Engine")
    print(f"   Models: {', '.join(CLOUD_MODELS)}")
    print(f"   Gemini Key: {'✅ Set' if GEMINI_API_KEY else '⚪ Not set'}")
    print(f"   Gemini Config: temp=0.2, tokens=8192, topP=0.85")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
