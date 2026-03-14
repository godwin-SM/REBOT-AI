import os
from dotenv import load_dotenv

load_dotenv()

# Lazy-loaded embedding model
model = None

def get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded successfully")
    return model

# Lazy-loaded supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

def get_supabase():
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


# -----------------------
# CREATE EMBEDDING
# -----------------------
def create_embedding(text):
    return get_model().encode(text).tolist()


# -----------------------
# STORE EMBEDDING
# -----------------------
def store_embedding(text):

    embedding = create_embedding(text)

    data = {
        "content": text,
        "embedding": embedding
    }

    try:
        sb = get_supabase()
        if sb:
            sb.table("documents").insert(data).execute()
    except Exception as e:
        print("Supabase error:", e)

    return embedding