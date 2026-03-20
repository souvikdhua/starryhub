# Starrygate — The Poetic Oracle of Vedic Astrology

## 🌌 The Vision

Starrygate is a reimagining of astrological insight—a haunting, poetic, lowercase oracle. It is the antithesis of generic, upbeat AI horoscopes: blunt, modern, minimalist, and existential.

It delivers hyper-personalized psychological depth by translating rigorous Vedic mathematical precision into a Co-Star-inspired aesthetic. It doesn't just tell you your sign; it uncovers the **Knot** (karmic struggle) and the **Mask** (social self) through a voice that feels human, ancient, and slightly devastating.

---

## 📁 Project Structure

```
starryhub/
├── DOCUMENTATION.md
├── backend/
│   ├── main.py              # FastAPI app — routing, multi-agent orchestration
│   ├── astro_calc.py        # Swiss Ephemeris Vedic chart engine
│   ├── rag_engine.py        # Gemini embedding-based vector store + hybrid retrieval
│   ├── rag_crawler.py       # Autonomous background spider for live Vedic knowledge
│   ├── prompts.py           # System prompts for all agents
│   ├── Dockerfile           # Container definition (Python 3.11-slim)
│   ├── render.yaml          # Render.com deployment config
│   ├── requirements.txt     # Python dependencies
│   ├── test_bifurcation.py  # Integration tests for reading vs. chat modes
│   └── data/
│       └── vedic_knowledge_base.txt   # Seeded classical Vedic corpus
├── financial-dashboard/     # Separate sub-project
├── newtown-3d-map/          # Separate sub-project
└── vedic-astro-gem.html     # Standalone frontend (served by the FastAPI app)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/) (free tier: 1,500 req/day)
- At least one [OpenRouter API key](https://openrouter.ai/) with credits for `google/gemini-2.5-flash`

### Local Setup

```bash
# 1. Clone and enter the backend
git clone https://github.com/souvikdhua/starryhub.git
cd starryhub/backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env   # then edit with your keys
# Required:  GEMINI_API_KEY
# Optional:  OPENROUTER_API_KEY, OPENROUTER_API_KEY_2

# 4. Start the server
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000` to use the UI, or hit `http://localhost:8000/api/health` to confirm the service is live.

### Docker

```bash
cd backend
docker build -t starrygate .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=<your_key> \
  -e OPENROUTER_API_KEY=<your_key> \
  starrygate
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Powers embeddings (RAG) and the Gemini direct-API fallback. Free tier: 1,500 req/day, 15 RPM. |
| `OPENROUTER_API_KEY` | ✅ (recommended) | Primary LLM key for `google/gemini-2.5-flash` via OpenRouter. |
| `OPENROUTER_API_KEY_2` | ✖ (optional) | Second key for round-robin rotation to multiply effective quota. |

> **Note:** The system degrades gracefully. If OpenRouter credits are exhausted (HTTP 402), the generation pipeline raises an error rather than silently burning the Gemini free-tier quota, which is reserved for the background RAG crawler.

---

## ⚙️ Technical Architecture

### 1. Multi-Agent Pipeline

Every initial chart reading passes through two sequential LLM agents, both using `google/gemini-2.5-flash` via OpenRouter:

| Stage | Agent | Role | Output |
|---|---|---|---|
| 1 | **Technical Analyst** | Ingests raw chart data + RAG context; produces a dense, structured JSON report covering planetary dignities, Dashas, Navamsha (D9), Dasamsa (D10), Arudha Lagna, and Gandanta | Strict JSON (`AstroReading` schema) |
| 2 | **Co-Star Poet** | Receives the Analyst's JSON; rewrites every field into the signature Starrygate voice—lowercase, punchy, existential | Same JSON keys, poetic values |

A Pydantic schema (`AstroReading`) validates both agents' outputs before the response is sent to the client.

### 2. Bifurcated Interaction Design

The backend detects the interaction mode from the conversation state:

- **Initial Reading** (`is_initial_reading = True`): Triggers the full two-agent pipeline and returns structured JSON powering the UI sections (Identity, Emotions, The Mask, The Knot, etc.).
- **Conversational Chat**: Strips JSON overhead and returns short, haunting plain-text paragraphs via the Co-Star Poet directly. No JSON, no jargon.

### 3. Vedic Calculation Layer (`astro_calc.py`)

Built on [Swiss Ephemeris](https://www.astro.com/swisseph/) (`pyswisseph`):

- Precise geocentric longitudes for Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, and Ketu
- Planetary dignity classification (Exaltation, Debilitation, Own Sign, Moolatrikona)
- Divisional charts: Navamsha (D9), Dasamsa (D10)
- Vimsottari Dasha periods (Mahadasha → Antardasha → Pratyantardasha)
- Ashtakavarga strength, Arudha Lagna, Gandanta detection
- Timezone-aware birth time via `timezonefinder` + `pytz`

### 4. RAG Engine (`rag_engine.py`)

An in-memory vector store powered by Gemini embeddings (`gemini-embedding-2-preview`):

- **Hybrid retrieval**: 75 % semantic cosine similarity + 25 % keyword overlap
- **Disk cache**: Embeddings are saved to `gemini_embeddings_cache.npz` and reloaded on startup (invalidated automatically when the corpus changes)
- **Hot-loading**: The background crawler injects new knowledge directly into RAM without a server restart

### 5. Autonomous Background Crawler (`rag_crawler.py`)

An async spider that continuously enriches the RAG corpus at runtime:

1. Fetches Vedic astrology pages from a seed list (Wikipedia, jyotish sites) and discovers new links autonomously (up to 5,000 in queue)
2. Extracts structured knowledge via Gemini 2.5 Flash (`EXTRACTION_PROMPT`)
3. Validates quality via a secondary Gemini pass (`QUALITY_CHECK_PROMPT`) — rejects Western astrology, horoscope fluff, and low-density content
4. Hot-loads accepted knowledge into the live RAG engine and saves a backup to disk
5. Sleeps 3 minutes between pages (~480 pages/day, well within Gemini's 1,500 req/day free limit)

### 6. API Key Fallback Chain

```
Request arrives
  → Try OPENROUTER_API_KEY (round-robin with KEY_2)
      → 200 OK ✅
      → 429 Rate Limit → try next key
      → 402 Payment Required → raise error (preserve Gemini quota for RAG)
      → 502/503 Upstream → try next key
  → All OpenRouter keys exhausted → Exception returned to client
```

---

## 🌐 API Reference

### `GET /api/health`
Returns service status and key configuration.

**Response**
```json
{ "status": "ready", "has_openrouter_key": true }
```

---

### `POST /api/chart`
Computes a full Vedic natal chart from birth data.

**Request body**
```json
{
  "dob": "1990-06-15",
  "tob": "14:30:00",
  "place": "Mumbai, India",
  "name": "Arjun",
  "lat": null,
  "lon": null
}
```
`lat`/`lon` are optional — omit them and the server will geocode `place` via [Nominatim](https://nominatim.openstreetmap.org/).

**Response**
```json
{
  "ascendant": "Libra (12°34')",
  "moon_sign": "Taurus",
  "moon_nakshatra": "Rohini",
  "sun_sign": "Gemini",
  "current_dasha": { "md": "Venus", "ad": "Mercury", "pd": "Ketu" },
  "chart_context": "...",
  "location": { "lat": 19.076, "lon": 72.877, "place": "Mumbai, India" }
}
```

---

### `POST /api/chat`
Runs the multi-agent pipeline (Initial Reading) or the conversational oracle (Chat).

**Request body**
```json
{
  "messages": [
    { "role": "user", "content": "Generate my full chart reading exactly in the requested format. Follow the system instructions precisely." }
  ],
  "chart_context": "<string returned by /api/chart>",
  "api_key": ""
}
```

The `api_key` field accepts an optional user-supplied OpenRouter key inserted at the front of the rotation.

**Initial Reading response** (structured JSON)
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "{\"today_at_a_glance\": {\"p1\": \"...\", \"p2\": \"...\", \"p3\": \"...\"}, ...}"
    }
  }]
}
```

**Chat response** (plain text)
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "the moon in taurus does not forget. it holds everything you've ever loved..."
    }
  }]
}
```

---

## 🧪 Testing

```bash
# Start the server first (see Quick Start above), then:
cd backend
python test_bifurcation.py
```

`test_bifurcation.py` verifies the two interaction modes:
- **Initial Reading**: asserts that the response is valid JSON containing `today_at_a_glance`
- **Conversational Chat**: asserts that the response is plain text, not JSON

---

## ☁️ Deployment

### Render.com (Recommended)

The repository includes a `render.yaml` for one-click Docker deployment to Render's free web service tier:

```yaml
services:
  - type: web
    name: starrygate
    runtime: docker
    plan: free
    envVars:
      - key: GEMINI_API_KEY
        sync: false
    healthCheckPath: /api/health
```

Add `OPENROUTER_API_KEY` (and optionally `OPENROUTER_API_KEY_2`) as secret environment variables in the Render dashboard after deploying.

---

## ✨ Current Capabilities

- **Dynamic Transit Engine**: Natal-to-transit analysis using the user's actual birth chart.
- **Jargon Sanitizer**: Technical terms (e.g., "12th House Saturn") are replaced by evocative metaphors (e.g., "the area of silence") in all LLM prompts.
- **Divisional Depth**: Navamsha (D9, soul/marriage) and Dasamsa (D10, career/power) charts included in every analysis.
- **Aesthetic UI**: Cinematic dark-mode frontend served directly by the FastAPI app at `/`.

---

## 🔮 The Horizon (Future Vision)

### Enhanced Psychological Modules
- **Full "The Mask" Module**: Deeper persona vs. true-self exploration.
- **Full "The Knot" Module**: Detailed karmic mapping of repeating life patterns.
- **"The Shadow"**: Repressed traits and subconscious drives.

### Multimodal Insights
- **Generative Media**: Dynamic "Your Song" and "Your Film" suggestions tied to specific transit data.
- **Karmic Alerts**: Push notifications for significant planetary shifts aligned with natal Knots.

### Production Excellence
- Ultra-low latency through optimized agent handoffs and response streaming.
- Expanded RAG corpus with proprietary translations of rare Sanskrit manuscripts.
- Sub-minute birth-time precision with global timezone and daylight-savings handling.

---

> "the air feels heavy with unspoken truths. the stars don't care about your plans, but they remember your pattern." — *Starrygate*
