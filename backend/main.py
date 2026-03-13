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

app = FastAPI(title="Starrygate API", version="7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config ──────────────────────────────────────────────────────────────────
# OpenRouter API keys — round-robin rotation for quota multiplication
OPENROUTER_API_KEYS = [
    os.getenv("OPENROUTER_API_KEY", ""),
    os.getenv("OPENROUTER_API_KEY_2", ""),
]
OPENROUTER_API_KEYS = [k for k in OPENROUTER_API_KEYS if k and len(k) > 10]
_key_index = 0

def get_next_openrouter_key():
    """Round-robin key rotation for OpenRouter."""
    global _key_index
    if not OPENROUTER_API_KEYS:
        return ""
    key = OPENROUTER_API_KEYS[_key_index % len(OPENROUTER_API_KEYS)]
    _key_index += 1
    return key

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Agent 1: Technical Analyst — structured JSON output
AGENT1_MODEL = "google/gemini-2.5-flash"
# Agent 2: CoStar Poet — poetic transformation + chat
AGENT2_MODEL = "google/gemini-2.5-flash"

# Configure generation for stability
DEFAULT_TEMP = 0.1
DEFAULT_TOKENS = 8192    # Keep within OpenRouter credit budget
DEFAULT_TOP_P = 0.85

def extract_json(text: str) -> str:
    """Extract JSON object from text if wrapped in markdown or chatter."""
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

INITIAL_READING_PROMPT = "Generate my full chart reading exactly in the requested format. Follow the system instructions precisely."

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
            headers={"User-Agent": "Starrygate/7.0"},
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
        "has_openrouter_key": bool(OPENROUTER_API_KEYS),
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

# ─── OpenRouter Call (Unified) ───────────────────────────────────────────────

async def call_openrouter(messages: list, model: str, api_key: str = None,
                          json_mode: bool = False, temperature: float = None) -> str:
    """Call OpenRouter API with key rotation and retry logic.
    
    OpenRouter uses the OpenAI-compatible chat/completions format.
    """
    temp = temperature if temperature is not None else DEFAULT_TEMP
    
    # Build list of keys to try
    keys_to_try = list(OPENROUTER_API_KEYS)
    if api_key and api_key not in keys_to_try:
        keys_to_try.insert(0, api_key)
    if not keys_to_try:
        raise Exception("no OpenRouter API keys configured")

    last_error = None
    for current_key in keys_to_try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {current_key}",
            "HTTP-Referer": "https://starrygate.in",
            "X-Title": "Starrygate",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": DEFAULT_TOKENS,
            "top_p": DEFAULT_TOP_P,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    OPENROUTER_URL, headers=headers, json=payload, timeout=120
                )
            )
            
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    if content:
                        used_model = data.get("model", model)
                        print(f"  ✅ Response from {used_model} via OpenRouter")
                        return content
                continue
            
            if res.status_code == 429:
                print(f"  ⚠ 429 Rate Limit on {model}. Trying next key...")
                last_error = "429 rate limit"
                continue
            
            if res.status_code in (502, 503):
                print(f"  ⚠ {model} upstream unavailable ({res.status_code}). Trying next key...")
                last_error = f"{res.status_code} upstream error"
                continue
            
            error_body = res.text[:300]
            print(f"  ⚠ OpenRouter returned {res.status_code}: {error_body}")
            last_error = f"{res.status_code}: {error_body}"
            continue
            
        except Exception as e:
            print(f"  ⚠ OpenRouter call error: {e}")
            last_error = str(e)
            continue

    raise Exception(f"All OpenRouter keys failed. Last error: {last_error}")


# ─── Agent 1: Technical Analyst (OpenRouter) ─────────────────────────────────

async def call_analyst(chart_context: str, live_context: str, rag_context: str) -> str:
    """Agent 1: Analyzes chart data and outputs structured technical JSON analysis."""

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

OUTPUT FORMAT — respond ONLY with this JSON structure. Keep all values under 15 words. Lowercase only. Blunt tone. No jargon. No formatting. NOTHING ELSE but the JSON.
{
  "today_at_a_glance": {"tension": "...", "vibe": "...", "demands_attention": "..."},
  "year_at_a_glance": {"overarching_lesson": "...", "tectonic_shift": "...", "dissolving": "..."},
  "identity": {"core_synthesis": "...", "core_contradiction": "...", "hidden_truth": "..."},
  "the_mask": {"outer_perception": "...", "inner_reality": "...", "misread": "..."},
  "the_knot": {"recurring_wound": "...", "tripping_point": "...", "impossible_problem": "..."},
  "emotions": {"landscape": "...", "pain_processing": "...", "secret_trigger": "..."},
  "drive": {"force": "...", "fight_style": "...", "secret_motivation": "..."},
  "communication": {"intellect": "...", "think_vs_speak": "...", "misinterpretation": "..."},
  "love": {"craving": "...", "pattern": "...", "need_vs_choice": "..."},
  "pressure": {"weight": "...", "crushing_point": "...", "time_relationship": "..."},
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
  "soul_movie": "movie title",
  "quote": "piercing quote",
  "fun_fact": "specific habit",
  "strongest_planet": "name and score",
  "weakest_planet": "name and score",
  "active_yogas": ["name"],
  "dasha_summary": "mahadasha/antardasha effect"
}"""

    user_prompt = f"""Analyze this birth chart and output the structured JSON analysis.

{chart_context}

{live_context}

{rag_context}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        print(f"\n🧠 Stage 1: Technical Analyst ({AGENT1_MODEL})...")
        result = await call_openrouter(
            messages, model=AGENT1_MODEL,
            api_key=get_next_openrouter_key(), json_mode=True
        )
        print(f"  ✅ Agent 1: Technical analysis complete")
        return result
    except Exception as e:
        print(f"  ⚠ Agent 1 failed: {e}")
        return None


# ─── Main Chat Endpoint ──────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    data = request.model_dump()
    messages = data.get("messages", [])
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
        for line in chart_context.split('\n'):
            line = line.strip()
            for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                if line.startswith(pname):
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
            user_natal_planets = None

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

    # Build composite RAG query
    rag_query = latest_query
    if chart_context:
        import re
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
        if not OPENROUTER_API_KEYS:
            return JSONResponse(
                {"error": {"message": "no key. the gate is closed."}},
                status_code=401
            )

        # ─── BIFURCATED LOGIC: READING vs. CHAT ───
        is_initial_reading = (latest_query.strip() == INITIAL_READING_PROMPT)
        analyst_result = None

        if is_initial_reading:
            # ──── STAGE 1: Technical Analyst (Agent 1) ────
            if chart_context:
                analyst_result = await call_analyst(chart_context, live_context, rag_context)

            # ──── STAGE 2: CoStar Poet (Agent 2) ────
            if analyst_result:
                # Multi-agent mode: Poet receives Analyst's structured output
                print(f"✨ Stage 2: CoStar Poet ({AGENT2_MODEL})...")
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

OUTPUT STRUCTURE:
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
                    {"role": "user", "content": f"Transform this technical astrology analysis into a CoStar-style reading:\n\n{analyst_result}"}
                ]
                final_answer = await call_openrouter(
                    poet_messages, model=AGENT2_MODEL,
                    api_key=get_next_openrouter_key(), json_mode=True
                )
                final_answer = extract_json(final_answer)
            else:
                # Fallback: Single-agent mode for Initial Reading
                print(f"\n🔮 Starrygate (solo mode — Reading)...")
                has_system = any(msg.get("role") == "system" for msg in messages)
                if not has_system:
                    messages.insert(0, {"role": "system", "content": "You are a master Vedic astrologer."})
                
                for msg in messages:
                    if msg.get("role") == "system":
                        extra = "\n\n<raw_astrological_data_for_internal_analysis_only>\n"
                        extra += "OUTPUT EXACTLY THE 10-SECTION JSON STRUCTURE. LOWERCASE. POETIC.\n"
                        if chart_context: extra += f"\n{chart_context}"
                        extra += f"\n{live_context}\n{live_dasha}\n{rag_context}"
                        extra += "\n</raw_astrological_data_for_internal_analysis_only>"
                        msg["content"] += extra
                        break
                final_answer = await call_openrouter(
                    messages, model=AGENT2_MODEL,
                    api_key=get_next_openrouter_key(), json_mode=True
                )
                final_answer = extract_json(final_answer)
        else:
            # ──── FREE-FORM CHAT MODE ────
            print(f"💬 Chat Mode: Poetic follow-up...")
            chat_system = """You are the personal oracle of Starrygate. You are speaking to the user in a chat window.
VOICE: Poetic, lowercase, blunt, existential.
STYLE: No JSON. No markdown headers. Just short, haunting paragraphs.
DATA: You have access to their exact Vedic chart math. Use it to answer their questions specifically, but never mention 'houses' or 'degrees'. Use metaphors ('the area of silence', 'the heavy pattern').

If they ask 'hi' or generic things, be cryptic but welcoming.
If they ask about a specific planet or life area, use the provided math to give a punchy, devastatingly accurate answer."""

            messages.insert(0, {"role": "system", "content": chat_system})
            if chart_context:
                messages[0]["content"] += f"\n\nUSER CHART DATA:\n{chart_context}\n{live_context}\n{live_dasha}\n{rag_context}"
            
            final_answer = await call_openrouter(
                messages, model=AGENT2_MODEL,
                api_key=get_next_openrouter_key(), json_mode=False
            )

        print("✅ Response complete!\n")

        # ─── Logging ───
        try:
            os.makedirs("logs", exist_ok=True)
            output_hash = hashlib.sha256(final_answer.encode('utf-8')).hexdigest()[:12]
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "model": f"multi-agent ({AGENT1_MODEL} → {AGENT2_MODEL})" if analyst_result else AGENT2_MODEL,
                "multi_agent": bool(analyst_result),
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
            user_msg = f"something went quiet. ({error_msg})"

        return JSONResponse({"error": {"message": user_msg}}, status_code=500)


# ─── Serve Frontend ──────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
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
    print("🔮 Starrygate v7.0 — OpenRouter Multi-Agent Engine")
    print(f"   Agent 1 (Analyst): {AGENT1_MODEL}")
    print(f"   Agent 2 (Poet):    {AGENT2_MODEL}")
    print(f"   OpenRouter Keys:   {len(OPENROUTER_API_KEYS)} configured")
    print(f"   Config: temp={DEFAULT_TEMP}, tokens={DEFAULT_TOKENS}, topP={DEFAULT_TOP_P}")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
