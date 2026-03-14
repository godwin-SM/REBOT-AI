from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pypdf import PdfReader
from docx import Document
import requests
import os
import asyncio
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

# Load environment variables from .env (e.g., SUPABASE_URL / SUPABASE_KEY)
load_dotenv()

# Import rag functions (they are now lazy-loaded internally)
from rag import store_memory, retrieve_memory, get_model, get_collection
from auth import verify_token, get_user_from_token, get_or_create_google_user, get_user_by_id

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ---------
# LIFESPAN & EXECUTOR
# ---------
executor = ThreadPoolExecutor(max_workers=2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: App is ready immediately
    # Models will lazy-load on first request
    print("REBOT AI server starting...")
    yield
    # Shutdown: Clean up executor
    executor.shutdown(wait=True)

# -----------------------
# SUPABASE CONNECTION (Lazy Load)
# -----------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

def get_supabase():
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Warning: Could not initialize Supabase: {e}")
    return supabase

app = FastAPI(lifespan=lifespan, title="REBOT AI")

DOCUMENT_CONTEXT = ""

# ----------------------
# AUTHENTICATION HELPER
# ----------------------
def get_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract and verify user_id from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    user_id = get_user_from_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_id

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running"}

@app.get("/debug/check-db")
def debug_check_db():
    """Debug endpoint to check database connection and data"""
    sb = get_supabase()
    if not sb:
        return {"success": False, "error": "No Supabase connection"}
    
    try:
        users = sb.table("users").select("id, email").limit(5).execute()
        chat_history = sb.table("chat_history").select("*").limit(5).execute()
        
        return {
            "success": True,
            "users": users.data if users and hasattr(users, 'data') else [],
            "chat_history": chat_history.data if chat_history and hasattr(chat_history, 'data') else [],
            "user_count": len(users.data) if users and hasattr(users, 'data') else 0,
            "chat_count": len(chat_history.data) if chat_history and hasattr(chat_history, 'data') else 0
        }
    except Exception as e:
        return {"success": False, "error": str(e), "trace": __import__('traceback').format_exc()}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------
# GOOGLE OAUTH ENDPOINT
# -----------------------

@app.post("/auth/google")
async def google_auth(data: dict):
    """
    Authenticate with Google token.
    Frontend sends the Google ID token received from Sign-In.
    Backend verifies it and creates/gets user.
    Optional: Frontend can also send the picture URL from the decoded JWT.
    """
    google_token = data.get("token")
    frontend_picture = data.get("picture")  # Picture from frontend's decoded JWT
    
    if not google_token:
        return {"success": False, "error": "No Google token provided"}
    
    result = get_or_create_google_user(google_token, frontend_picture)
    return result

@app.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user info"""
    try:
        user_id = get_user_id_from_header(authorization)
        user = get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

# -----------------------
# CHAT ENDPOINT
# -----------------------
@app.post("/chat")
async def chat(data: dict, authorization: Optional[str] = Header(None)):
    """Chat endpoint - requires authentication"""
    try:
        user_id = get_user_id_from_header(authorization)
    except HTTPException as e:
        return {"success": False, "error": e.detail}

    user_message = data.get("message")

    if not user_message:
        return {"success": False, "error": "Please send a message."}

    # Retrieve document memory for this user (run in thread pool to avoid blocking)
    loop = asyncio.get_event_loop()
    try:
        context = await asyncio.wait_for(
            loop.run_in_executor(executor, retrieve_memory, user_message, user_id),
            timeout=5.0  # Reduced from 30s to 5s
        )
    except asyncio.TimeoutError:
        context = ""

    messages = [
        {"role": "system", "content": "You are REBOT AI, a helpful assistant."},
        {"role": "system", "content": f"Document content:\n{DOCUMENT_CONTEXT[:4000]}"},
        {"role": "system", "content": f"Relevant memory:\n{context}"},
        {"role": "user", "content": user_message}
    ]

    try:
        # Use httpx for async API call instead of blocking requests
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 500  # Limit tokens for faster response
                }
            )

        result = response.json()

        if "choices" not in result:
            return {"success": False, "error": f"API Error: {result}"}

        reply = result["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"Error: {str(e)}"

    # Store conversation memory for this user (non-blocking background task)
    loop.run_in_executor(executor, store_memory, user_message + " " + reply, user_id)

    # Store chat history in Supabase (non-blocking background task)
    def save_chat_to_db():
        sb = get_supabase()
        if sb:
            try:
                print(f"[DEBUG] Saving to chat_history: user_id={user_id}, user_msg={user_message[:50]}..., bot_reply={reply[:50]}...")
                insert_result = sb.table("chat_history").insert({
                    "user_id": str(user_id),
                    "user_message": user_message,
                    "bot_reply": reply
                }).execute()
                print(f"[DEBUG] Insert result: {insert_result}")
                if insert_result and hasattr(insert_result, 'data') and insert_result.data:
                    print(f"[DEBUG] Successfully saved chat to database")
                else:
                    print(f"[DEBUG] Warning: Insert result data is empty")
            except Exception as e:
                print(f"[ERROR] Failed to save chat to database: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[DEBUG] Supabase client not available, chat not saved to database")
    
    loop.run_in_executor(executor, save_chat_to_db)

    return {"success": True, "reply": reply}


# -----------------------
# CHAT HISTORY ENDPOINT
# -----------------------
@app.get("/chat-history")
async def get_chat_history(authorization: Optional[str] = Header(None)):
    """Retrieve chat history for authenticated user from Supabase"""
    try:
        user_id = get_user_id_from_header(authorization)
        print(f"[DEBUG] Retrieved user_id: {user_id}")
    except HTTPException as e:
        print(f"[DEBUG] Authorization failed: {e.detail}")
        return {"success": False, "error": e.detail}
    
    sb = get_supabase()
    print(f"[DEBUG] Supabase client: {sb}")
    if not sb:
        return {"success": False, "error": "Database connection unavailable"}
    
    try:
        print(f"[DEBUG] Querying chat history for user_id: {user_id}")
        # Query with proper sorting
        result = sb.table("chat_history").select("user_message, bot_reply").eq("user_id", str(user_id)).order("id", desc=False).execute()
        
        print(f"[DEBUG] Query result type: {type(result)}")
        print(f"[DEBUG] Query result: {result}")
        
        history = []
        if result and hasattr(result, 'data') and result.data:
            print(f"[DEBUG] Found {len(result.data)} rows")
            for row in result.data:
                print(f"[DEBUG] Row: {row}")
                history.append({"role": "user", "content": row.get("user_message", "")})
                history.append({"role": "bot", "content": row.get("bot_reply", "")})
        else:
            print(f"[DEBUG] No data in result or result is None")
        
        print(f"[DEBUG] Returning history with {len(history)} messages")
        return {"success": True, "history": history}
    except Exception as e:
        print(f"[ERROR] Error retrieving chat history: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# -----------------------
# FILE UPLOAD ENDPOINT
# -----------------------
@app.post("/upload")
async def upload(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Upload file endpoint - requires authentication"""
    try:
        user_id = get_user_id_from_header(authorization)
    except HTTPException as e:
        return {"success": False, "error": e.detail}

    global DOCUMENT_CONTEXT

    # Create user-specific upload folder
    user_upload_folder = f"{UPLOAD_FOLDER}/{user_id}"
    os.makedirs(user_upload_folder, exist_ok=True)

    filepath = f"{user_upload_folder}/{file.filename}"

    # Save file
    with open(filepath, "wb") as f:
        f.write(await file.read())

    # Process file in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    
    def process_file(filepath_arg, filename_arg):
        """Process file and extract text"""
        text = ""
        filename = filename_arg.lower()

        try:
            # TXT
            if filename.endswith(".txt"):
                with open(filepath_arg, "r", encoding="utf-8") as f:
                    text = f.read()

            # PDF
            elif filename.endswith(".pdf"):
                reader = PdfReader(filepath_arg)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            # DOCX
            elif filename.endswith(".docx"):
                doc = Document(filepath_arg)
                for para in doc.paragraphs:
                    text += para.text + "\n"

            else:
                raise ValueError("Unsupported file type.")

        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

        if text.strip() == "":
            raise Exception("No readable text found in this file.")

        return text[:20000]  # Limit to 20k characters

    try:
        text = await loop.run_in_executor(executor, process_file, filepath, file.filename)
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Store in RAG memory (non-blocking)
    chunk_size = 500
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        loop.run_in_executor(executor, store_memory, chunk, user_id)
    
    DOCUMENT_CONTEXT = text

    # Store file metadata in Supabase (non-blocking)
    def save_to_supabase():
        sb = get_supabase()
        if sb:
            try:
                sb.table("documents").insert({
                    "user_id": user_id,
                    "filename": file.filename,
                    "filepath": filepath,
                    "size": len(text)
                }).execute()
            except Exception as e:
                print("Supabase error:", e)

    loop.run_in_executor(executor, save_to_supabase)

    # Generate summary asynchronously (optional, doesn't block response)
    async def generate_summary():
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openai/gpt-4o-mini",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"Summarize this document in 2-3 sentences:\n\n{text[:5000]}"
                            }
                        ],
                        "max_tokens": 200
                    }
                )
                result = response.json()
                if "choices" in result:
                    return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Summary generation failed: {e}")
            return None

    # Don't wait for summary, it can happen in background
    summary_task = asyncio.create_task(generate_summary())

    return {
        "success": True,
        "reply": f"✅ Document '{file.filename}' uploaded successfully! The file has been added to my knowledge base.",
        "filename": file.filename,
        "size": len(text)
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)