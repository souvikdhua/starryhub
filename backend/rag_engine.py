import os
import re
import json
import hashlib
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ─── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, 'data', 'vedic_knowledge_base.txt')
CACHE_PATH = os.path.join(BASE_DIR, 'gemini_embeddings_cache.npz')
EMBEDDING_MODEL = "gemini-embedding-2-preview"

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))

# ─── In-memory vector store ──────────────────────────────────────────────────
_chunks: list[str] = []
_embeddings: np.ndarray | None = None


def load_and_chunk_texts() -> list[str]:
    """Reads the raw corpus and splits it into logical chunks."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by section dividers (=== SECTION or --- SECTION)
    sections = re.split(r'(?:===|---)\s*SECTION\s*\d+', content)

    chunks = []
    for s in sections:
        s = s.strip()
        if s and len(s) > 50:  # Skip empty or trivial fragments
            chunks.append(s)

    return chunks


def _compute_content_hash(chunks: list[str]) -> str:
    """Hash of all chunk content to detect corpus changes."""
    combined = "\n".join(chunks)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def _embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> np.ndarray:
    """Embed a list of texts using Gemini embedding model."""
    # Gemini embedding API accepts batches of content
    # Process in batches of 100 to stay within limits
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
            ),
        )
        for emb in result.embeddings:
            all_embeddings.append(emb.values)

    return np.array(all_embeddings, dtype=np.float32)


def _cosine_similarity(query_vec: np.ndarray, corpus_vecs: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a query vector and corpus matrix."""
    # Normalize
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    corpus_norms = corpus_vecs / (np.linalg.norm(corpus_vecs, axis=1, keepdims=True) + 1e-10)
    return corpus_norms @ query_norm


def initialize_db():
    """Populates the in-memory vector store, using disk cache when possible."""
    global _chunks, _embeddings

    _chunks = load_and_chunk_texts()
    content_hash = _compute_content_hash(_chunks)

    # Try to load cached embeddings
    if os.path.exists(CACHE_PATH):
        try:
            cache = np.load(CACHE_PATH, allow_pickle=True)
            if str(cache.get('hash', '')) == content_hash:
                _embeddings = cache['embeddings']
                print(f"✅ Loaded {len(_chunks)} cached Gemini embeddings from disk.")
                return
            else:
                print("🔄 Corpus changed — re-embedding with Gemini...")
        except Exception as e:
            print(f"⚠ Cache load failed ({e}), re-embedding...")

    # Compute fresh embeddings
    print(f"🌱 Embedding {len(_chunks)} Vedic corpus chunks with {EMBEDDING_MODEL}...")
    _embeddings = _embed_texts(_chunks, task_type="RETRIEVAL_DOCUMENT")

    # Cache to disk
    np.savez(CACHE_PATH, embeddings=_embeddings, hash=np.array(content_hash))
    print(f"✅ Embedded and cached {len(_chunks)} chunks with Gemini.")


# Initialize on import
initialize_db()


def retrieve_classical_texts(query: str, n_results: int = 3) -> str:
    """
    Performs semantic vector search using Gemini embeddings.
    Finds the closest Vedic knowledge chunks to the query.
    """
    global _embeddings, _chunks

    if _embeddings is None or len(_chunks) == 0:
        return ""

    try:
        # Embed the query
        query_embedding = _embed_texts([query], task_type="RETRIEVAL_QUERY")[0]

        # Compute similarities
        similarities = _cosine_similarity(query_embedding, _embeddings)

        # Get top-N indices
        top_indices = np.argsort(similarities)[::-1][:n_results]

        rag_str = "=== RETRIEVED MASTER VEDIC KNOWLEDGE CONTEXT ===\n"
        rag_str += "The following are exact rules retrieved from the Vedic Master Knowledge Base (BPHS, Jaimini, Phaladeepika) based on semantic resonance with the user's query. YOU MUST APPLY THESE RULES EXACTLY in your response and synthesize them deeply.\n\n"

        for i, idx in enumerate(top_indices):
            snippet = _chunks[idx][:2500]
            score = similarities[idx]
            rag_str += f"[KNOWLEDGE BLOCK {i + 1}] (relevance: {score:.3f})\n{snippet}...\n\n"

        rag_str += "=== END MASTER KNOWLEDGE CONTEXT ==="
        return rag_str

    except Exception as e:
        print(f"Error in vector retrieval: {e}")
        return ""


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(f"🔮 Gemini RAG Engine — {EMBEDDING_MODEL}")
    print(f"   Corpus chunks: {len(_chunks)}")
    print(f"   Embedding dims: {_embeddings.shape[1] if _embeddings is not None else 'N/A'}")
    print("=" * 60)

    print("\n--- Test Query 1 ---")
    print(retrieve_classical_texts("What happens if my sun is with ketu?"))

    print("\n--- Test Query 2 ---")
    print(retrieve_classical_texts("Is my debilitated mars bad for marriage?"))
