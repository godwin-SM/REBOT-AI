from fastapi import FastAPI, UploadFile, File
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

# Load environment variables from .env (e.g., SUPABASE_URL / SUPABASE_KEY)
load_dotenv()

# Import rag functions (they are now lazy-loaded internally)
from rag import store_memory, retrieve_memory, get_model, get_collection

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

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Server is running"}

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
# CHAT ENDPOINT
# -----------------------
@app.post("/chat")
async def chat(data: dict):

    user_message = data.get("message")

    if not user_message:
        return {"reply": "Please send a message."}

    # Retrieve document memory (run in thread pool to avoid blocking)
    loop = asyncio.get_event_loop()
    try:
        context = await asyncio.wait_for(
            loop.run_in_executor(executor, retrieve_memory, user_message),
            timeout=30.0
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

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": messages
            }
        )

        result = response.json()

        if "choices" not in result:
            return {"reply": f"API Error: {result}"}

        reply = result["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"Error: {str(e)}"

    # Store conversation memory locally (non-blocking background task)
    loop.run_in_executor(executor, store_memory, user_message + " " + reply)

    # Store chat history in Supabase
    sb = get_supabase()
    if sb:
        try:
            sb.table("chat_history").insert({
                "user_message": user_message,
                "bot_reply": reply
            }).execute()
        except Exception as e:
            print("Supabase error:", e)

    return {"reply": reply}


# -----------------------
# FILE UPLOAD ENDPOINT
# -----------------------
@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    global DOCUMENT_CONTEXT

    filepath = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(filepath, "wb") as f:
        f.write(await file.read())

    text = ""
    
    filename = file.filename.lower()

    try:

        # TXT
        if filename.endswith(".txt"):

            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

        # PDF
        elif filename.endswith(".pdf"):

            reader = PdfReader(filepath)

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        # DOCX
        elif filename.endswith(".docx"):

            doc = Document(filepath)

            for para in doc.paragraphs:
                text += para.text + "\n"

        else:
            return {"reply": "Unsupported file type."}

    except Exception as e:
        return {"reply": f"Error reading file: {str(e)}"}

    if text.strip() == "":
        return {"reply": "No readable text found in this file."}

    # Limit large files
    text = text[:20000]

    # Store file text in RAG memory (run in thread pool)
    chunk_size = 500
    loop = asyncio.get_event_loop()

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        await loop.run_in_executor(executor, store_memory, chunk)
    
    DOCUMENT_CONTEXT = text

    # Ask AI to summarize uploaded document
    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages":[
                    {
                        "role":"user",
                        "content":f"Summarize this document:\n\n{text}"
                    }
                ]
            }
        )

        result = response.json()

        if "choices" not in result:
            return {"reply": f"API error: {result}"}

        reply = result["choices"][0]["message"]["content"]

    except Exception as e:
        reply = f"Upload succeeded but AI analysis failed: {str(e)}"

    return {"reply": reply}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)