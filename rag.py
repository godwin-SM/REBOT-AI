import os
from dotenv import load_dotenv

# Load environment variables from .env (e.g., SUPABASE_URL / SUPABASE_KEY)
load_dotenv()

# -----------------------
# EMBEDDING MODEL (Lazy Load)
# -----------------------
model = None

def get_model():
    global model
    if model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading lightweight embedding model...")
            # Use smaller model: ~80MB instead of 140MB
            # This model is optimized for speed and size while maintaining quality
            model = SentenceTransformer(
                "multi-qa-MiniLM-L6-cos-v1",
                device="cpu"
            )
            print("Embedding model loaded successfully")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise
    return model

# -----------------------
# CHROMA VECTOR DB (Lazy Load - Persistent)
# -----------------------
client = None
collection = None

def get_collection():
    global client, collection
    if client is None:
        try:
            import chromadb
            from chromadb.config import Settings
            print("Initializing ChromaDB...")
            client = chromadb.Client(
                Settings(persist_directory="vector_db")
            )
            collection = client.get_or_create_collection("rebot_memory")
            print("ChromaDB initialized successfully")
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise
    return collection

# -----------------------
# SUPABASE CONNECTION
# -----------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase only if credentials are available (Lazy Load)
supabase = None

def get_supabase():
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize Supabase in rag.py: {e}")
    return supabase


# -----------------------
# STORE MEMORY
# -----------------------
def store_memory(text, user_id=None):

    embedding = get_model().encode(text).tolist()

    # Store in ChromaDB
    coll = get_collection()
    doc_id = f"{user_id}_{hash(text)}" if user_id else str(hash(text))
    coll.add(
        documents=[text],
        embeddings=[embedding],
        ids=[doc_id],
        metadatas=[{"user_id": user_id}] if user_id else [{}]
    )

    # Store in Supabase
    sb = get_supabase()
    if sb:
        try:
            sb.table("memory").insert({
                "user_id": user_id,
                "content": text,
                "embedding": embedding
            }).execute()
        except Exception as e:
            print("Supabase error:", e)


# -----------------------
# RETRIEVE MEMORY
# -----------------------
def retrieve_memory(query, user_id=None):

    embedding = get_model().encode(query).tolist()

    coll = get_collection()
    
    # Query ChromaDB with user filter
    if user_id:
        results = coll.query(
            query_embeddings=[embedding],
            n_results=3,
            where={"user_id": user_id}
        )
    else:
        results = coll.query(
            query_embeddings=[embedding],
            n_results=3
        )

    if results["documents"] and len(results["documents"][0]) > 0:
        return "\n".join(results["documents"][0])

    return ""