# REBOT AI - Size-Optimized AI Assistant

A lightweight, AI-powered chat assistant with document upload and semantic memory. **Optimized to fit within 500MB deployment limit.**

## 🚀 Features

✅ **AI-Powered Chat** - Intelligent responses via OpenRouter API  
✅ **Document Memory** - Upload PDFs, DOCX, TXT files and ask questions about them  
✅ **Semantic Search** - Uses lightweight embedding model for context retrieval  
✅ **Persistent Storage** - ChromaDB vector database + Supabase backend  
✅ **Sub-500MB Footprint** - Optimized for fast deployment and minimal resources  

## 📦 Size Optimizations

### What We Optimized
- **Replaced PyTorch** (~500MB) with **ONNX Runtime** (~100MB)
- **Smaller embedding model** - `multi-qa-MiniLM-L6-cos-v1` (~80MB) instead of `all-MiniLM-L6-v2` (~140MB)
- **Python 3.12-slim base** - Removes unnecessary system libraries
- **Removed unused dependencies** - Streamlined requirements.txt

### Deployment Size Breakdown
```
FastAPI + Uvicorn         ~50 MB
Python base dependencies  ~150 MB
Embedding model          ~80 MB (multi-qa-MiniLM-L6-cos-v1)
ONNX Runtime             ~100 MB
ChromaDB                 ~30 MB
Document parsing (pypdf) ~20 MB
Source + Static files    ~20 MB
────────────────────────────────
Total:                   ~450 MB ✅
```

## 🛠️ Installation

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys:
# - OPENROUTER_API_KEY
# - SUPABASE_URL
# - SUPABASE_KEY

# Run server
python -m uvicorn app:app --reload
```

### Docker Deployment
```bash
# Build image (optimized multi-stage build)
docker build -t rebot-ai .

# Run container
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  rebot-ai
```

### Deploy to Render
```bash
# Push to GitHub
git push origin main

# On Render.com:
1. Connect GitHub repository
2. Set environment variables:
   - OPENROUTER_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
3. Deploy using render.yaml configuration
```

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

### Performance Tuning
The app is pre-optimized, but you can adjust:

- **Model loading**: Happens at startup (configurable in `rag.py`)
- **ChromaDB persistence**: Stored in `vector_db/` directory
- **Max file size**: 20,000 characters (configurable in `app.py`)
- **Memory chunks**: 500 characters (configurable in `app.py`)

## 🧪 Testing

```bash
# Run comprehensive tests
python test_optimized.py

# Check deployment size
python check_size.py

# Direct API testing
python comprehensive_test.py
```

## 📊 Performance

- **Startup time**: ~8-12 seconds (models preload at startup)
- **Chat response time**: 1-3 seconds (depends on OpenRouter API)
- **Memory per request**: ~50MB
- **Concurrent users**: Tested up to 10 simultaneous connections

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

## 🚨 Troubleshooting

### Models taking too long to load?
- Models preload at startup (~10s first time)
- Subsequent requests use cached models
- Internet connection required for first download

### `ModuleNotFoundError: No module named 'X'`
```bash
pip install -r requirements.txt
```

### Size exceeds 500MB?
Check what's using space:
```bash
python check_size.py
```

Common issues:
- `.git` folder included (add to `.gitignore`)
- `vector_db/` data accumulated (delete and rebuild)
- `uploads/` files (delete old uploads)

## 📈 Scalability

To scale beyond current limits:
1. Use Embed Cache for embeddings (avoid recomputing)
2. Implement request queuing for concurrent chat
3. Use CDN for static files
4. Consider using Pinecone for distributed vector search

## 📄 License

MIT License - See LICENSE file

## 🙋 Support

Issues? Check:
1. `.env` file has correct API keys
2. Internet connection for model downloads
3. Supabase credentials are valid
4. Run `python check_size.py` to verify installation

---

**🎯 Total Size: ~450MB** | **Status: ✅ Optimized**
