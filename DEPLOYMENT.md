# DEPLOYMENT CHECKLIST

## Pre-Deployment
- [ ] All dependencies in requirements.txt
- [ ] .env file configured with API keys
- [ ] .gitignore excludes `__pycache__`, `vector_db/`, `uploads/`, and `.env`
- [ ] .dockerignore configured for minimal image
- [ ] Dockerfile uses python:3.12-slim base image
- [ ] render.yaml configured with `--no-cache-dir` flag
- [ ] Test locally: `python -m uvicorn app:app --reload`
- [ ] Run size check: `python check_size.py` (should be <500MB)
- [ ] Run tests: `python test_optimized.py` (all tests pass)

## GitHub repository
- [ ] Initialize git: `git init`
- [ ] Add all files: `git add .`
- [ ] Commit: `git commit -m "Initial commit"`
- [ ] Push to GitHub: `git push -u origin main`

## Render.com Deployment
- [ ] Create new Web Service on Render.com
- [ ] Connect GitHub repository
- [ ] Set environment variables:
  - OPENROUTER_API_KEY = sk-or-v1-...
  - SUPABASE_URL = https://...supabase.co
  - SUPABASE_KEY = eyJ...
- [ ] Choose Python environment
- [ ] Deploy from render.yaml
- [ ] Wait for health check to pass (120s timeout)

## Post-Deployment
- [ ] Test /health endpoint
- [ ] Test /chat endpoint
- [ ] Test /upload endpoint with sample file
- [ ] Check application logs for errors
- [ ] Monitor deployment size (should be <500MB)
- [ ] Verify API responses are working

## Monitoring
- [ ] Health check passes every 30 seconds
- [ ] No memory leaks in logs
- [ ] Response times under 5 seconds
- [ ] Model loading completes at startup

## Optimization Notes
Current optimizations implemented:
- ✅ Lightweight embedding model (multi-qa-MiniLM-L6-cos-v1 ~80MB)
- ✅ ONNX Runtime instead of PyTorch (~100MB vs 500MB)
- ✅ Python 3.12-slim base image
- ✅ pip --no-cache-dir flag during build
- ✅ Comprehensive .gitignore and .dockerignore
- ✅ Lazy loading of heavy dependencies
- ✅ Thread pool for non-blocking operations

## Size Breakdown
```
Expected deployment breakdown:
- FastAPI + Uvicorn:       ~50 MB
- Python dependencies:     ~150 MB
- Embedding model:         ~80 MB
- ONNX Runtime:            ~100 MB
- ChromaDB:                ~30 MB
- pypdf + python-docx:     ~20 MB
- Application code:        ~20 MB
────────────────────────────────
TOTAL:                    ~450 MB ✅
```

If deployment size exceeds 500MB:
1. Check `vector_db/` directory size (delete if needed)
2. Check `uploads/` directory size (clear old files)
3. Verify .gitignore is excluding cache directories
4. Run: `pip cache purge` before deployment
