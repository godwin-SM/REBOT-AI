import os
from dotenv import load_dotenv

# Load environment variables from .env (e.g., SUPABASE_URL / SUPABASE_KEY)
load_dotenv()

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
    # Use Supabase only - removed ChromaDB and embedding model to save memory
    sb = get_supabase()
    if sb:
        try:
            sb.table("memory").insert({
                "user_id": user_id,
                "content": text
            }).execute()
        except Exception as e:
            print("Supabase error:", e)


# -----------------------
# RETRIEVE MEMORY
# -----------------------
def retrieve_memory(query, user_id=None):
    # Use simple keyword search from Supabase - removed embedding lookup
    sb = get_supabase()
    if not sb:
        return ""
    
    try:
        # Simple text search - retrieve recent memory entries
        result = sb.table("memory").select("content").eq("user_id", user_id).order("id", desc=True).limit(5).execute()
        
        if result and hasattr(result, 'data') and result.data:
            # Return last 5 memory entries as context
            return "\n".join([row.get("content", "") for row in result.data])
        
        return ""
    except Exception as e:
        print(f"Memory retrieval error: {e}")
        return ""