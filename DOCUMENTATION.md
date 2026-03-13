# Starrygate — The Poetic Oracle of Vedic Astrology

## 🌌 The Vision
Starrygate is a reimagining of astrological insight—a "haunting, poetic, lowercase oracle." It is designed as the antithesis of generic, upbeat AI horoscopes. It is blunt, modern, minimalist, and existential.

The product aims to provide hyper-personalized psychological depth by translating rigorous Vedic mathematical precision into a curated, "Co-Star" inspired aesthetic. It doesn't just tell you your sign; it uncovers the "Knot" (karmic struggle) and the "Mask" (social self) through a voice that feels human, ancient, and slightly devastating.

---

## ⚙️ The Engine (Technical Architecture)

Starrygate employs a sophisticated **Multi-Agent Pipeline** to ensure both mathematical accuracy and aesthetic consistency.

### 1. The Multi-Agent Pipeline
- **Agent 1: The Technical Analyst (Gemini 2.5 Flash via OpenRouter)**
  - Handles the complex Vedic calculations.
  - Generates a structured, technical report covering planetary dignities, dashas, Navamsha (D9), and special points like Arudha Lagna and Gandanta.
- **Agent 2: The Co-Star Poet (Gemini 2.5 Flash via OpenRouter)**
  - Receives the technical report and transforms it into the signature Starrygate voice.
  - Enforces a strict lowercase, metaphor-rich, and blunt stylistic output.

### 2. Vedic Precision & RAG
- **Calculation Layer**: Computes precise longitudes, divisional charts (D9, D10), strength (Ashtakavarga), and temporal periods (Vimsottari Dasha).
- **RAG (Retrieval-Augmented Generation)**: Uses Gemini embeddings with hybrid retrieval (semantic + keyword) to link current celestial patterns to specific verses from classical texts like *Brihat Parasara Hora Shastra* and *Phaladeepika*, ensuring the insights are rooted in thousands of years of tradition.

### 3. Bifurcated Interaction Design
The backend intelligently distinguishes between two modes of interaction:
- **The Initial Reading**: A high-density, structured JSON response that powers the main UI sections (Identity, Emotions, The Mask, etc.).
- **Conversational Chat**: A free-form, plain-text mode for follow-up questions, providing poetic and specific answers without technical jargon or JSON overhead.

---

## ✨ Current Capabilities
- **Dynamic Transit Engine**: Natal-to-Transit analysis using the user's actual birth chart data.
- **Jargon Sanitizer**: Automatically translates technical terms (e.g., "12th House Saturn") into evocative metaphors (e.g., "the area of silence").
- **Divisional Depth**: Includes Navamsha (soul/marriage) and Dasamsa (career/power) charts.
- **Aesthetic UI**: A cinematic, dark-mode experience with fluid transitions and typography-first design.

---

## 🔮 The Horizon (Future Vision)
The goal is for Starrygate to become the most accurate and emotionally resonant astrology tool in existence.

### 1. Enhanced Psychological Modules
- **Full "The Mask" Module**: Deeper exploration of the persona vs. the true self.
- **Full "The Knot" Module**: Detailed karmic mapping of repeating life patterns.
- **"The Shadow"**: Exploration of repressed traits and subconscious drives.

### 2. Multimodal Insights
- **Generative Media**: Dynamic generation of "Your Song" and "Your Film" based on specific transit data, potentially including synthesized audio or visual moods.
- **Karmic Alerts**: Subtle notifications for significant planetary shifts based on natal "Knots".

### 3. Production Excellence
- Ultra-low latency through optimized agent handoffs.
- Expanded RAG database with proprietary translations of rare Sanskrit manuscripts.
- Global timezone and daylight savings precision for sub-minute accuracy.

---

> "the air feels heavy with unspoken truths. the stars don't care about your plans, but they remember your pattern." — *Starrygate*
