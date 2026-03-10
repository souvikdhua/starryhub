import os
import re
import chromadb
from chromadb.utils import embedding_functions

# Paths
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, 'data', 'vedic_knowledge_base.txt')
DB_PATH = os.path.join(BASE_DIR, 'chroma_db')

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=DB_PATH)

# Use a lightweight, fast, and highly effective embedding model
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get or create the collection
collection = chroma_client.get_or_create_collection(
    name="vedic_corpus",
    embedding_function=sentence_transformer_ef
)

def load_and_chunk_texts():
    """Reads the raw corpus and splits it into logical chunks."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by explicit section dividers to keep context whole
    sections = re.split(r'--- SECTION \d+:', content)
    
    chunks = []
    for s in sections:
        s = s.strip()
        if s:
            # Overlap handling or further splitting could go here if chunks are too massive,
            # but for 45KB total, section-level chunking is usually optimal for Vedic rules.
            chunks.append(s)
            
    return chunks

def initialize_db():
    """Populates the vector database if it's currently empty."""
    if collection.count() == 0:
        print("🌱 Initializing ChromaDB Vector Database with Vedic Corpus...")
        chunks = load_and_chunk_texts()
        
        # Prepare data for Chroma
        documents = []
        ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            ids.append(f"chunk_{i}")
            # Basic metadata, you could add topic tags here if desired
            metadatas.append({"source": "vedic_knowledge_base.txt", "chunk_id": i})
            
        # Add to collection (this will compute embeddings automatically)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"✅ Successfully embedded {len(chunks)} Vedic logic chunks.")

# Initialize the DB on first import
initialize_db()

def retrieve_classical_texts(query: str, n_results: int = 3):
    """
    Performs a semantic vector search using ChromaDB.
    Finds the mathematical closest rules to the meaning of the query.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return ""
            
        rag_str = "=== RETRIEVED MASTER VEDIC KNOWLEDGE CONTEXT ===\n"
        rag_str += "The following are exact rules retrieved from the Vedic Master Knowledge Base (BPHS, Jaimini, Phaladeepika) based on semantic resonance with the user's query. YOU MUST APPLY THESE RULES EXACTLY in your response and synthesize them deeply.\n\n"
        
        # Retrieve the top matched documents
        for i, doc in enumerate(results['documents'][0]):
            # Cap each block at 2500 chars to manage token windows safely
            snippet = doc[:2500] 
            rag_str += f"[KNOWLEDGE BLOCK {i+1}]\n{snippet}...\n\n"
            
        rag_str += "=== END MASTER KNOWLEDGE CONTEXT ==="
        return rag_str
        
    except Exception as e:
        print(f"Error in vector retrieval: {e}")
        return ""

if __name__ == "__main__":
    test_query = "Why am I facing delays and sorrow in my career?"
    print(f"TESTING QUERY: '{test_query}'\n")
    print(retrieve_classical_texts(test_query))

if __name__ == "__main__":
    print(retrieve_classical_texts("What happens if my sun is with ketu?"))
    print("\n----------------\n")
    print(retrieve_classical_texts("Is my debilitated mars bad for marriage?"))

