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
from typing import Optional, Any
from dotenv import load_dotenv

from astro_calc import (
    get_live_astro_context, get_current_dasha,
    compute_natal_chart, format_chart_as_context
)
from rag_engine import retrieve_classical_texts
from rag_crawler import run_background_crawler

load_dotenv()

app = FastAPI(title="Starrygate API", version="7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Starts background tasks when the server boots on Hugging Face Space."""
    print("✨ FastAPI Server started. Booting background services...")
    # Spin off the slow background crawler without blocking main thread
    asyncio.create_task(run_background_crawler())

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
# Agent 2: JSON Formatter — clean output + chat
AGENT2_MODEL = "google/gemini-2.5-flash"

# Configure generation for stability
DEFAULT_TEMP = 0.1
DEFAULT_TOP_P = 0.85

# Gemini direct API fallback (free tier: 500 req/day, 15 RPM)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_REST_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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
    messages: list[dict[str, Any]]
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
            {"error": {"message": "Could not find that location. Please try again."}},
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
            {"error": {"message": "Chart calculation failed. Please try again."}},
            status_code=500
        )

# ─── OpenRouter Call (Unified) ───────────────────────────────────────────────

async def call_openrouter(messages: list[dict[str, Any]], model: str, api_key: Optional[str] = None,
                          json_mode: bool = False, temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> str:
    """Call OpenRouter API with key rotation, retry logic, and Gemini fallback.
    
    If max_tokens is None, it won't be sent — OpenRouter won't pre-check credits.
    On 402 (payment required), automatically falls back to direct Gemini API.
    """
    temp = temperature if temperature is not None else DEFAULT_TEMP
    
    # Build list of keys to try
    keys_to_try = list(OPENROUTER_API_KEYS)
    if api_key and api_key not in keys_to_try:
        keys_to_try.insert(0, api_key)
    if not keys_to_try:
        # No OpenRouter keys, go straight to Gemini fallback
        print("  ⚠ No OpenRouter keys, using Gemini direct fallback...")
        return await call_gemini_direct(messages, json_mode=json_mode, temperature=temp)

    last_error = None
    hit_402 = False
    for current_key in keys_to_try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {current_key}",
            "HTTP-Referer": "https://starrygate.in",
            "X-Title": "Starrygate",
        }
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "top_p": DEFAULT_TOP_P,
        }
        
        # Only set max_tokens if explicitly provided
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
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
            
            if res.status_code == 402:
                print(f"  ⚠ OpenRouter 402: Insufficient credits. Will fallback to Gemini...")
                hit_402 = True
                last_error = "402 insufficient credits"
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

    # If we hit 402 on all keys, fallback to direct Gemini API (free tier)
    if hit_402 and GEMINI_API_KEY:
        print("  🔄 All OpenRouter keys exhausted. Cannot fallback to free Gemini API because it is reserved for the background RAG Crawler.")
        # We intentionally do NOT call_gemini_direct here to preserve the crawler's 1500 req/day quota.
        raise Exception(f"All OpenRouter keys failed (402 Payment Required). Free tier is reserved for RAG Crawler. Last error: {last_error}")

    raise Exception(f"All OpenRouter keys failed. Last error: {last_error}")


async def call_gemini_direct(messages: list[dict[str, Any]], json_mode: bool = False,
                             temperature: float = 0.1) -> str:
    """Direct Gemini REST API call as a free-tier fallback.
    
    Uses the same GEMINI_API_KEY used for embeddings.
    Free tier: 500 requests/day, 15 requests/minute.
    """
    if not GEMINI_API_KEY:
        raise Exception("No Gemini API key configured for fallback")
    
    # Convert OpenAI message format to Gemini format
    system_instruction = ""
    gemini_contents = []
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            system_instruction += content + "\n"
        elif role == "user":
            gemini_contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            gemini_contents.append({"role": "model", "parts": [{"text": content}]})
    
    payload: dict[str, Any] = {
        "contents": gemini_contents,
        "generationConfig": {
            "temperature": temperature,
            "topP": DEFAULT_TOP_P,
        }
    }
    
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction.strip()}]}
    
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    
    try:
        url = f"{GEMINI_REST_URL}?key={GEMINI_API_KEY}"
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(
            None,
            lambda: requests.post(url, json=payload, timeout=120)
        )
        
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "")
                    if text:
                        print(f"  ✅ Response from Gemini direct API (free tier)")
                        return text
        
        error_text = res.text[:300]
        raise Exception(f"Gemini direct API error {res.status_code}: {error_text}")
        
    except requests.exceptions.Timeout:
        raise Exception("Gemini direct API timeout")
    except Exception as e:
        if "Gemini direct" in str(e):
            raise
        raise Exception(f"Gemini direct API call failed: {e}")


# ─── Agent 1: Technical Analyst (OpenRouter) ─────────────────────────────────

async def call_analyst(chart_context: str, live_context: str, rag_context: str) -> str:
    """Agent 1: Analyzes chart data and outputs a plain-text reading."""

    from prompts import ANALYST_SYSTEM_PROMPT
    system_prompt = ANALYST_SYSTEM_PROMPT

    user_prompt = f"""Analyze this birth chart and write a clear plain-text reading.

{chart_context}

{live_context}

{rag_context}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        print(f"\n🧠 Analyst ({AGENT1_MODEL})...")
        result = await call_openrouter(
            messages, model=AGENT1_MODEL,
            api_key=get_next_openrouter_key(), json_mode=False
        )
        print(f"  ✅ Analysis complete")
        return result
    except Exception as e:
        print(f"  ⚠ Analyst failed: {e}")
        return None


# ─── OpenRouter RAG Synthesis (Contextual Compression) ───────────────────────

async def synthesize_rag_context(raw_rag: str, chart_context: str, query: str) -> str:
    """Use OpenRouter to distill raw retrieved chunks into a focused, chart-specific
    knowledge brief. This is dramatically more powerful than dumping raw chunks."""
    if not raw_rag or not chart_context:
        return raw_rag

    try:
        from prompts import RAG_SYNTHESIS_SYSTEM_PROMPT
        synth_system = RAG_SYNTHESIS_SYSTEM_PROMPT

        synth_user = f"""CHART DATA:
{chart_context}

QUERY: {query}

RAW RETRIEVED CLASSICAL TEXTS:
{raw_rag}

Extract and synthesize ONLY the rules that apply to this specific chart."""

        messages = [
            {"role": "system", "content": synth_system},
            {"role": "user", "content": synth_user}
        ]

        print(f"  📚 RAG Synthesis: Distilling classical knowledge for this chart ({AGENT1_MODEL})...")
        synthesized = await call_openrouter(
            messages, model=AGENT1_MODEL,  # Back to full Flash for guaranteed reasoning quality
            api_key=get_next_openrouter_key(),
            json_mode=False, temperature=0.05
        )
        print(f"  ✅ RAG Synthesis complete ({len(synthesized)} chars)")
        return f"=== SYNTHESIZED VEDIC KNOWLEDGE (chart-specific) ===\n{synthesized}\n=== END SYNTHESIZED KNOWLEDGE ==="

    except Exception as e:
        print(f"  ⚠ RAG Synthesis failed ({e}), using raw chunks")
        return raw_rag


# ─── Main Chat Endpoint ──────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    data = request.model_dump()
    messages = data.get("messages", [])
    chart_context = data.get("chart_context", "")

    if not messages:
        return JSONResponse({"error": {"message": "No messages provided."}}, status_code=400)

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

    # ─── Build composite RAG query ───
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
            rag_query = f"{latest_query} {' '.join(str(k) for k in rag_keywords[:8])}"

    # ─── Parallelize Live Data & RAG Embedding Retrieval for Speed ───
    loop = asyncio.get_event_loop()
    
    # Fire off simultaneous tasks
    future_context = loop.run_in_executor(None, get_live_astro_context, user_natal_planets)
    future_dasha = loop.run_in_executor(None, get_current_dasha)
    future_rag = loop.run_in_executor(None, retrieve_classical_texts, rag_query, 8) # Increased to 8 for more power
    
    results = await asyncio.gather(
        future_context, future_dasha, future_rag, return_exceptions=True
    )
    
    res_context, res_dasha, res_rag = results
    
    # Handle exceptions gracefully and type cast
    if isinstance(res_context, Exception):
        print(f"⚠ Live astro context failed: {res_context}")
        live_context: str = ""
    else:
        live_context: str = str(res_context)
        
    if isinstance(res_dasha, Exception):
        print(f"⚠ Dasha calculation failed: {res_dasha}")
        live_dasha: str = ""
    else:
        live_dasha: str = str(res_dasha)
        
    if isinstance(res_rag, Exception):
        print(f"⚠ RAG retrieval failed: {res_rag}")
        raw_rag: str = ""
    else:
        raw_rag: str = str(res_rag)

    # ─── Synthesize RAG context with OpenRouter for chart-specific focus ───
    rag_context = await synthesize_rag_context(raw_rag, chart_context, latest_query)

    # ─── MULTI-AGENT PIPELINE ───
    try:
        if not OPENROUTER_API_KEYS:
            return JSONResponse(
                {"error": {"message": "No API key configured."}},
                status_code=401
            )

        # ─── BIFURCATED LOGIC: READING vs. CHAT ───
        # Count only user messages (frontend always prepends a system message)
        user_messages = [m for m in messages if m.get("role") != "system"]
        is_initial_reading = (len(user_messages) <= 1 and latest_query.strip() == INITIAL_READING_PROMPT)
        analyst_result = None

        if is_initial_reading:
            # ──── Technical Analyst ────
            if chart_context:
                analyst_result = await call_analyst(chart_context, live_context, rag_context)

            if analyst_result:
                final_answer = analyst_result
            else:
                # Fallback: single-agent plain-text reading
                print(f"\n🔮 Starrygate (solo mode — Reading)...")
                has_system = any(msg.get("role") == "system" for msg in messages)
                if not has_system:
                    messages.insert(0, {"role": "system", "content": "You are a master Vedic astrologer."})

                for msg in messages:
                    if msg.get("role") == "system":
                        extra = "\n\n<chart_data>\n"
                        if chart_context: extra += f"\n{chart_context}"
                        extra += f"\n{live_context}\n{live_dasha}\n{rag_context}"
                        extra += "\n</chart_data>"
                        msg["content"] += extra
                        break
                final_answer = await call_openrouter(
                    messages, model=AGENT2_MODEL,
                    api_key=get_next_openrouter_key(), json_mode=False
                )
        else:
            # ──── FREE-FORM CHAT MODE ────
            print(f"💬 Chat Mode: Follow-up...")
            from prompts import CHAT_SYSTEM_PROMPT
            chat_system = CHAT_SYSTEM_PROMPT

            # Remove the frontend's reading-template system instruction so the AI doesn't repeat the full reading
            messages = [m for m in messages if m.get("role") != "system"]
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
                "model": AGENT1_MODEL if analyst_result else AGENT2_MODEL,
                "used_analyst": bool(analyst_result),
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
            user_msg = "Too many requests. Please try again in a moment."
        else:
            user_msg = f"Something went wrong. ({error_msg})"

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
    print("🔮 Starrygate v7.1 — OpenRouter + Gemini Fallback Engine")
    print(f"   Agent 1 (Analyst): {AGENT1_MODEL}")
    print(f"   Agent 2 (Poet):    {AGENT2_MODEL}")
    print(f"   OpenRouter Keys:   {len(OPENROUTER_API_KEYS)} configured")
    print(f"   Gemini Fallback:   {'✅ configured' if GEMINI_API_KEY else '❌ not configured'}")
    print(f"   Config: temp={DEFAULT_TEMP}, topP={DEFAULT_TOP_P}")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
