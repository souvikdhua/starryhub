import os
import sys
import time
import requests
import asyncio
import urllib.parse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from rag_engine import inject_dynamic_knowledge

load_dotenv()

# Configure Gemini 2.5 Flash using the modern SDK
# User explicitly requested latest Gemini 2.5 Flash
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

# Outputting to /tmp/ to bypass macOS "Operation Not Permitted" on the live repo
KNOWLEDGE_BASE_PATH = "/tmp/scraped_vedic_knowledge.txt"
os.makedirs(os.path.dirname(KNOWLEDGE_BASE_PATH), exist_ok=True)

EXTRACTION_PROMPT = """
You are a master Vedic Astrologer and Data Extraction AI. 
I am going to provide you with raw HTML scraped from an astrology website.

Your task is to extract ONLY the pure, hard, classical Vedic Astrology rules, planetary combinations, and predictive wisdom from this text.

FORMAT INSTRUCTIONS:
1. Ignore all website navigation, ads, fluff, author bios, and irrelevant text.
2. Format the extracted knowledge into clean, readable sub-sections.
3. Use this exact heading format for the document:
--- SECTION X: [TOPIC NAME] ---
4. Use `X.Y [SUBTOPIC]` for individual rules (e.g., `1.1 SUN IN 1ST HOUSE`).
5. Write the rules clearly and authoritatively.

Raw Scraped Text:
{text}
"""

QUALITY_CHECK_PROMPT = """
You are a strict, orthodox Vedic Astrology (Jyotish) Editor.
Review the following extracted text.

Your job is to REJECT this text if it contains:
1. Modern Western Astrology (Pluto, Neptune, Uranus are heavily featured).
2. Generic sun-sign horoscope fluff (e.g., "Taurus, you will have a good day").
3. Irrelevant website garbage, ads, or non-astrological content.
4. Low information density (just rambling without specific planetary rules).

Only ACCEPT if it contains hard, classical Vedic rules (Parasara, Jaimini, Yogas, Dashas, Nakshatras, Bhavas, etc.).

Respond EXCLUSIVELY with a JSON object in this exact format:
{
  "is_valid": true or false,
  "reason": "Brief explanation of why it passed or failed."
}

Text to review:
{text}
"""

def fetch_url(url: str) -> tuple[str, list[str]]:
    """Fetches the raw HTML content, returning text and astrology-related links."""
    print(f"🌐 Crawling URL with AnyAPI: {url}")
    try:
        api_url = "https://anyapi.io/api/v1/scrape"
        params = {
            "apiKey": "cn440hemi0oupjldt3hueps0d5eav3foenkbtchn9oqq167d2rsko",
            "url": url,
        }
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        # AnyAPI returns a JSON object where 'content' is the HTML
        data = response.json()
        html = data.get('content', '') if isinstance(data, dict) else response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- Autonomous Link Discovery ---
        new_links = []
        keywords = ['astrology', 'jyotish', 'vedic', 'planet', 'zodiac', 'dasha', 'nakshatra', 'bhava', 'rashi', 'yoga', 'horoscope', 'navagraha']
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('#'): continue
            
            full_url = urllib.parse.urljoin(url, href)
            if not full_url.startswith('http'): continue
            
            url_lower = full_url.lower()
            text_lower = a.get_text().lower()
            
            # Simple keyword matching to ensure the spider stays in the niche
            if 'wikipedia.org' in url_lower:
                if any(k in url_lower for k in keywords):
                    new_links.append(full_url)
            else:
                if any(k in url_lower or k in text_lower for k in keywords):
                    new_links.append(full_url)
                    
        new_links = list(set(new_links))
        print(f"🔗 Discovered {len(new_links)} contextually relevant links.")
        
        # --- Clean Content Extraction ---
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        return text, new_links
    except Exception as e:
        print(f"❌ Failed to fetch {url} via AnyAPI: {e}")
        return "", []

def extract_knowledge_with_gemini(raw_text: str) -> str:
    """Uses Gemini 2.5 Flash to parse and format the raw text into Vedic rules."""
    if not raw_text or len(raw_text) < 100:
        return ""
    
    print("🧠 Processing with Gemini 2.5 Flash...")
    try:
        # Gemini can handle huge context, but we truncate just in case
        prompt = EXTRACTION_PROMPT.format(text=raw_text[:60000]) 
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"❌ Gemini Extraction failed: {e}")
        return ""

def validate_vedic_quality(extracted_text: str) -> bool:
    """Uses a secondary Gemini pass to strictly grade the knowledge quality."""
    if not extracted_text:
        return False
        
    print("🕵️  Running QA: Validating Vedic authenticity...")
    try:
        from google.genai import types
        prompt = QUALITY_CHECK_PROMPT.format(text=extracted_text[:20000])
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        # Parse the JSON validation
        import json
        result = json.loads(response.text)
        is_valid = result.get("is_valid", False)
        reason = result.get("reason", "No reason provided.")
        
        if is_valid:
            print(f"   ✅ QA PASSED: {reason}")
        else:
            print(f"   🚫 QA REJECTED: {reason}")
            
        return is_valid
    except Exception as e:
        print(f"   ⚠ QA Failed to parse JSON, defaulting to reject: {e}")
        return False

def append_to_knowledge_base(formatted_text: str, source_url: str):
    """Appends the formatted knowledge to the master corpus."""
    if not formatted_text:
        return
        
    print(f"💾 Appending new knowledge to corpus...")
    
    # Simple logic to find the next SECTION number
    section_num = 1
    if os.path.exists(KNOWLEDGE_BASE_PATH):
        with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            import re
            matches = re.findall(r'--- SECTION (\d+)', content)
            if matches:
                section_num = max(int(m) for m in matches) + 1
    
    # Replace placeholder X with actual number
    formatted_text = formatted_text.replace("SECTION X", f"SECTION {section_num}")
    
    with open(KNOWLEDGE_BASE_PATH, 'a', encoding='utf-8') as f:
        f.write(f"\n\n\n=== SOURCE: {source_url} ===\n")
        f.write(formatted_text)
    
    print(f"✅ Knowledge added! (Section {section_num})")

TARGET_URLS = [
    "https://en.wikipedia.org/wiki/Hindu_astrology",
    "https://en.wikipedia.org/wiki/Navagraha",
    "https://en.wikipedia.org/wiki/Nakshatra",
    "https://en.wikipedia.org/wiki/Dasha_(astrology)",
    "https://en.wikipedia.org/wiki/Yoga_(astrology)",
    "https://en.wikipedia.org/wiki/Bhava",
    "https://en.wikipedia.org/wiki/Panchanga",
    "https://en.wikipedia.org/wiki/Muhurta",
]

async def run_background_crawler():
    """
    Autonomous Spider Loop for Hugging Face Space.
    Extracts Vedic knowledge, dynamically discovers new links, and sleeps between operations to safely respect free tiers forever.
    """
    print("🚀 Starting Autonomous Background RAG Spider...")
    await asyncio.sleep(30) # Let the FastAPI boot fully first
    
    visited_urls = set()
    urls_to_queue = list(TARGET_URLS)
    
    while True: # Infinite crawling
        if not urls_to_queue:
            print("🕸️ Spider queue exhausted! Restarting from seed URLs in 2 hours.")
            urls_to_queue = list(TARGET_URLS)
            visited_urls.clear()
            await asyncio.sleep(7200)
            continue
            
        url = urls_to_queue.pop(0)
        
        if url in visited_urls:
            continue
            
        visited_urls.add(url)
        
        try:
            print(f"\n⏳ SPIDER WAKING: {url}")
            print(f"   [Dynamic Queue: {len(urls_to_queue)} | Visited: {len(visited_urls)}]")
            
            # 1. Fetch & Discover
            text, new_links = await asyncio.to_thread(fetch_url, url)
            
            # Append new relevant links to queue (cap at 5000 to prevent HF memory bloat)
            for link in new_links:
                if link not in visited_urls and link not in urls_to_queue and len(urls_to_queue) < 5000:
                    urls_to_queue.append(link)
                    
            if not text:
                await asyncio.sleep(300)
                continue
                
            # 2. Extract using Gemini 2.5 Flash
            clean_knowledge = await asyncio.to_thread(extract_knowledge_with_gemini, text)
            
            # 3. Strict Autonomous QA Quality Check
            is_high_quality = await asyncio.to_thread(validate_vedic_quality, clean_knowledge)
            
            if clean_knowledge and is_high_quality:
                # 4. Store to disk (for backups)
                await asyncio.to_thread(append_to_knowledge_base, clean_knowledge, url)
                # 5. Hot-load into live Server RAG engine
                await asyncio.to_thread(inject_dynamic_knowledge, clean_knowledge, url)
            else:
                print(f"🗑️ Discarding Extracted Knowledge from {url} (Failed QA or Empty)")
            
            print(f"💤 Spider sleeping for 3 minutes to maximize free daily limits (targeting ~450 pages/day)...")
            await asyncio.sleep(180) # 20 reqs/hr = ~480/day. (Gemini free tier is 1500/day. This stays safely within limits).
            
        except Exception as e:
            print(f"❌ Background Spider Error on {url}: {e}")
            await asyncio.sleep(300)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rag_crawler.py <URL1> <URL2> ...")
        print("Example: python rag_crawler.py https://example.com/bphs_chapter_1")
        sys.exit(1)
        
    urls_to_scrape = sys.argv[1:]
    
    print("="*60)
    print("🕸️  Starrygate Gemini RAG Crawler Engine")
    print("="*60)
    print(f"Targeting {len(urls_to_scrape)} URLs...")
    
    for url in urls_to_scrape:
        raw_content, discovered_links = fetch_url(url)
        clean_knowledge = extract_knowledge_with_gemini(raw_content)
        append_to_knowledge_base(clean_knowledge, url)
        time.sleep(2) # rate limit protection
        
    print("\n🎉 Crawl complete! Run `python rag_engine.py` to rebuild the embedding cache.")
