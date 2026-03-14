# DEPLOYMENT CHECKLIST

## Pre-Deployment
- [ ] All dependencies in requirements.txt
- [ ] .env file configured with API keys
- [ ] JWT_SECRET_KEY set in .env for authentication
- [ ] .gitignore excludes `__pycache__`, `vector_db/`, `uploads/`, and `.env`
- [ ] .dockerignore configured for minimal image
- [ ] Dockerfile uses python:3.12-slim base image
- [ ] render.yaml configured with `--no-cache-dir` flag
- [ ] Test locally: `python -m uvicorn app:app --reload`
- [ ] Run size check: `python check_size.py` (should be <500MB)
- [ ] Run tests: `python test_optimized.py` (all tests pass)

## Database Setup (Supabase)
- [ ] Create new Supabase project
- [ ] Run DATABASE_SETUP.sql in Supabase SQL editor to create tables:
  - `users` - Store user accounts with hashed passwords
  - `chat_history` - User-specific chat messages
  - `memory` - User-specific embeddings for RAG
  - `documents` - Track uploaded files per user
- [ ] Enable Row Level Security (RLS) policies for data isolation
- [ ] Get SUPABASE_URL and SUPABASE_KEY from your project settings

## Environment Variables (.env)
```
OPENROUTER_API_KEY=sk-or-v1-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...
JWT_SECRET_KEY=your-secret-key-change-this-in-production
```

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
  - JWT_SECRET_KEY = your-secret-key
- [ ] Choose Python environment
- [ ] Deploy from render.yaml
- [ ] Wait for health check to pass (120s timeout)

## Post-Deployment
- [ ] Test /health endpoint
- [ ] Test /register endpoint - Create new user account
- [ ] Test /login endpoint - Authenticate user
- [ ] Test /chat endpoint with valid JWT token
- [ ] Test /upload endpoint with sample file
- [ ] Check application logs for errors
- [ ] Monitor deployment size (should be <500MB)
- [ ] Verify API responses are working
- [ ] Verify data isolation - users can only see their own data

## Monitoring
- [ ] Health check passes every 30 seconds
- [ ] No memory leaks in logs
- [ ] Response times under 5 seconds
- [ ] Model loading completes at startup
- [ ] User authentication is required for all sensitive endpoints
- [ ] Token expiration and refresh working correctly

## Authentication Features
✅ User Registration - Create new accounts with email/password
✅ User Login - Authenticate with JWT tokens
✅ Token Expiration - Access tokens expire after 24 hours
✅ Token Refresh - Refresh tokens valid for 30 days
✅ Data Isolation - Each user only sees their own data
✅ Password Hashing - SHA-256 hashing for security
✅ Private Memory - RAG embeddings isolated per user
✅ Private Documents - Uploaded files isolated per user
✅ Private Chat History - Conversation history isolated per user

## Security Checklist
- [ ] JWT_SECRET_KEY changed from default in production
- [ ] All sensitive data (API keys, passwords) in .env, not in code
- [ ] HTTPS enabled on Render (automatic)
- [ ] CORS configured appropriately (currently allows all origins)
- [ ] Password validation: minimum 6 characters
- [ ] Database Row Level Security (RLS) enabled
- [ ] No sensitive data logged in application logs

## Optimization Notes
Current optimizations implemented:
- ✅ Lightweight embedding model (multi-qa-MiniLM-L6-cos-v1 ~80MB)
- ✅ ONNX Runtime instead of PyTorch (~100MB vs 500MB)
- ✅ Python 3.12-slim base image
- ✅ pip --no-cache-dir flag during build
- ✅ Comprehensive .gitignore and .dockerignore
- ✅ Lazy loading of heavy dependencies
- ✅ Thread pool for non-blocking operations
- ✅ User-specific data folders to prevent conflicts

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

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Authenticate and get tokens
- `POST /refresh` - Refresh access token
- `GET /me` - Get current user info

### Chat & Documents (Require Authorization Header)
- `POST /chat` - Send message to AI
- `POST /upload` - Upload document for RAG

All protected endpoints require: `Authorization: Bearer <access_token>`

## Troubleshooting

### "Invalid token" error
- JWT_SECRET_KEY mismatch between frontend and backend
- Token has expired (24 hour expiry)
- Check .env file has JWT_SECRET_KEY set

### "User not found" error
- Ensure DATABASE_SETUP.sql tables were created
- Check Supabase credentials in .env

### Memory or embedding errors
- Ensure ChromaDB vector_db/ folder is writable
- Check sufficient disk space for embeddings
- Try clearing vector_db/ directory if corrupted

