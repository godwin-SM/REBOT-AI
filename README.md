# 🤖 REBOT AI - Lightweight AI Chat Assistant

An AI-powered chat application with document upload, smart search, and user authentication. Built for efficiency with minimal memory footprint (~250MB).

## 🎯 What is REBOT AI?

A conversational AI assistant that lets users:
- Chat with an intelligent AI powered by OpenRouter API
- Upload documents (PDF, DOCX, TXT) and ask questions about them
- Get context-aware responses using recent text search
- Save chat history and documents securely

## 🚀 Key Features

- 💬 **AI Chat** - Real-time conversation with OpenRouter API
- 📄 **Document Upload** - Extract and search from PDFs, Word docs, and text files
- 🔍 **Smart Search** - Retrieve relevant document content and memory
- 🔐 **Google OAuth** - Secure user authentication
- 👥 **Multi-user Support** - Isolated sessions for each user
- 📱 **Mobile-Friendly** - Responsive design with PWA support
- ⚡ **Ultra-Lightweight** - Only ~250MB for deployment (free Render tier compatible)

## 🛠️ Tech Stack

- **Backend:** FastAPI, Uvicorn, Supabase
- **Frontend:** HTML, CSS, JavaScript (vanilla, no frameworks)
- **AI:** OpenRouter (LLM API)
- **Auth:** Google OAuth 2.0, JWT tokens
- **Cloud:** Supabase (database), Docker-ready

## 📦 Quick Setup

### 1. Install
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
```
Add to `.env`:
```env
OPENROUTER_API_KEY=your_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### 3. Run
```bash
python app.py
# Open http://localhost:8000
```

## 📁 Project Structure

```
rebot-ai/
├── app.py              # Main FastAPI application
├── auth.py            # Google OAuth & JWT
├── rag.py             # Semantic search & embeddings
├── requirements.txt   # Dependencies
├── Dockerfile         # Docker setup
├── static/
│   ├── index.html     # UI
│   ├── style.css
│   └── script.js
├── uploads/           # User uploaded files
└── vector_db/         # Local vector database
```

## 🚀 Deployment

### Docker
```bash
docker build -t rebot-ai .
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  rebot-ai
```

### Cloud (Render, Railway, etc.)
1. Push to GitHub
2. Connect to deployment platform
3. Set environment variables
4. Deploy

## 📚 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web interface |
| `/api/chat` | POST | Send chat message |
| `/api/upload` | POST | Upload document |
| `/auth/google` | POST | Google login |

## 🔐 Authentication

Uses Google OAuth 2.0 for secure login. JWT tokens are generated for API access.

## 📖 For More Details

- See `AUTHENTICATION.md` for auth setup
- See `DEPLOYMENT.md` for deployment specifics
- See `DATABASE_SETUP.sql` for Supabase schema

---

**Ready to use!** Install dependencies and run `python app.py` to get started.

## 📖 API Endpoints

### GET `/`
Returns the web interface (index.html)

### GET `/health`
Health check endpoint for monitoring
```bash
curl http://localhost:8000/health
# {"status": "ok", "message": "Server is running"}
```

### POST `/chat`
Send a chat message
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
# {"reply": "Hello! How can I assist you?"}
```

### POST `/upload`
Upload a document (PDF, DOCX, TXT)
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"
```

## ⚙️ Configuration

### Environment Variables
```env
OPENROUTER_API_KEY=your_api_key           # For AI responses
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key                 # For data storage
```

## 🔧 Architecture

```
┌─────────────────────────┐
│   Web Interface (HTML)  │
│    (static/index.html)  │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│   FastAPI Server        │
│   - Chat endpoint       │
│   - Upload endpoint     │
│   - Health check        │
└────────────┬────────────┘
             │
     ┌───────┴───────┐
     │               │
┌────▼─────┐   ┌─────▼──────┐
│ RAG Engine     │ OpenRouter │
│ (rag.py)       │ API       │
└────┬─────┘    └────────────┘
     │
  ┌──┴──────────────────┐
  │                     │
┌─▼────────┐   ┌───────▼──┐
│ChromaDB   │   │Supabase  │
│(Vector)   │   │(Backup)  │
└──────────┘    └──────────┘
```

## 📝 Features Detail

### Chat
- AI-powered conversation with memory
- Automatically retrieves relevant document context
- Integrates with OpenRouter for LLM access

### Document Upload
- Supports PDF, DOCX, TXT files
- Automatic chunking and embedding
- Semantic search for relevant context
- Max file size: 20,000 characters

### Memory System
- ChromaDB for local vector storage
- Supabase for backup and persistence
- Automatic memory retrieval during chat


**🎯 Total Size: ~450MB** | **Status: ✅ Optimized**
