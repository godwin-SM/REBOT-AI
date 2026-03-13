import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from supabase import create_client
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
            print("Loading embedding model...")
            model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Embedding model loaded successfully")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            raise
    return model

# -----------------------
# CHROMA VECTOR DB (Persistent)
# -----------------------
client = chromadb.Client(
    Settings(persist_directory="vector_db")
)

collection = client.get_or_create_collection("rebot_memory")

# -----------------------
# SUPABASE CONNECTION
# -----------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase only if credentials are available
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase in rag.py: {e}")


# -----------------------
# STORE MEMORY
# -----------------------
def store_memory(text):

    embedding = get_model().encode(text).tolist()

    # Store in ChromaDB
    collection.add(
        documents=[text],
        embeddings=[embedding],
        ids=[str(hash(text))]
    )

    # Store in Supabase
    if supabase:
        try:
            supabase.table("memory").insert({
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

    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )

    if results["documents"] and len(results["documents"][0]) > 0:
        return "\n".join(results["documents"][0])

    return ""