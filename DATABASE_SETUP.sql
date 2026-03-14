-- REBOT AI - Supabase Database Schema (Google OAuth)
-- Run these SQL commands in your Supabase SQL editor
-- Safe to run multiple times - uses IF NOT EXISTS

-- Enable pgvector extension for embeddings (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. USERS TABLE (optimized for Google OAuth)
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  google_id VARCHAR(255) UNIQUE NOT NULL,
  picture TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CHAT HISTORY TABLE (User-specific)
CREATE TABLE IF NOT EXISTS public.chat_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  user_message TEXT NOT NULL,
  bot_reply TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. MEMORY TABLE (User-specific embeddings for RAG)
CREATE TABLE IF NOT EXISTS public.memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(384),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. DOCUMENTS TABLE (Track uploaded files)
CREATE TABLE IF NOT EXISTS public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  filepath VARCHAR(500),
  size INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Handle previously created tables that may be missing user_id
ALTER TABLE IF EXISTS public.chat_history ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS public.memory ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS public.documents ADD COLUMN IF NOT EXISTS user_id UUID;

-- CREATE INDEXES for better performance (if not already created)
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON public.chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_user_id ON public.memory(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON public.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON public.users(google_id);

-- Row Level Security is not enabled since authentication is handled at the application level
-- with custom JWT tokens. Users are verified in the Python app before database operations.


