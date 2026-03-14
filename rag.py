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
            print("Loading embedding model...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
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
def store_memory(text):

    embedding = get_model().encode(text).tolist()

    # Store in ChromaDB
    coll = get_collection()
    coll.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(hash(text))]
    )

    # Store in Supabase
    sb = get_supabase()
    if sb:
        try:
            sb.table("memory").insert({
                "content": text,
                "embedding": embedding
            }).execute()
        except Exception as e:
            print("Supabase error:", e)


# -----------------------
# RETRIEVE MEMORY
# -----------------------
def retrieve_memory(query):

    embedding = get_model().encode(query).tolist()

    coll = get_collection()
    results = coll.query(
        query_embeddings=[embedding],
        n_results=3
    )

    if results["documents"] and len(results["documents"][0]) > 0:
        return "\n".join(results["documents"][0])

    return ""