from sentence_transformers import SentenceTransformer
from supabase import create_client
import os

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------
# CREATE EMBEDDING
# -----------------------
def create_embedding(text):
    return model.encode(text).tolist()


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
        supabase.table("documents").insert(data).execute()
    except Exception as e:
        print("Supabase error:", e)

    return embedding