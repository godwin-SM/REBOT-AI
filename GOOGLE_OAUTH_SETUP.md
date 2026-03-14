# Google OAuth Setup Guide

## Quick Start

Google OAuth authentication requires minimal setup and provides a seamless login experience.

## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Go to **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Web application**
6. Add authorized redirect URIs:
   - `http://localhost:3000` (for local testing)
   - `http://localhost:8000` (for local development)
   - `https://your-domain.com` (for production)
7. Copy your **Client ID**

## Step 2: Update Frontend

In [static/script.js](static/script.js), find this line:

```javascript
client_id: "YOUR_GOOGLE_CLIENT_ID_HERE",
```

Replace with your actual Google Client ID:

```javascript
client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com",
```

## Step 3: Update Environment Variables (.env)

Add to your `.env` file:

```
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
JWT_SECRET_KEY=your-super-secret-key
OPENROUTER_API_KEY=sk-or-v1-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
```

## Step 4: Create Database Tables

Run this in your Supabase SQL editor:

```sql
-- USERS TABLE (simplified for Google OAuth)
CREATE TABLE public.users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  google_id VARCHAR(255) UNIQUE,
  picture TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CHAT HISTORY TABLE (User-specific)
CREATE TABLE public.chat_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  user_message TEXT NOT NULL,
  bot_reply TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MEMORY TABLE (User-specific embeddings)
CREATE TABLE public.memory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding VECTOR(384),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DOCUMENTS TABLE
CREATE TABLE public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  filepath VARCHAR(500),
  size INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CREATE INDEXES
CREATE INDEX idx_chat_history_user_id ON public.chat_history(user_id);
CREATE INDEX idx_memory_user_id ON public.memory(user_id);
CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_google_id ON public.users(google_id);
```

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages added:
- `google-auth` - Verify Google tokens
- `google-auth-oauthlib` - OAuth 2.0 support
- `PyJWT` - JWT token handling

## Step 6: Test Locally

```bash
python -m uvicorn app:app --reload
```

Visit `http://localhost:8000` and click "Sign in with Google"

## How It Works

### Authentication Flow

1. **User clicks "Sign in with Google"**
   - Google's JavaScript library opens secure popup
   - User signs in with their Google account
   - User consents to share email/name/picture

2. **Frontend receives Google ID Token**
   - Frontend sends ID token to `/auth/google` endpoint
   - Token is a JWT cryptographically signed by Google

3. **Backend verifies token**
   - Validates signature using Google's public keys
   - Confirms token hasn't expired
   - Extracts email, name, picture, google_id

4. **User created or retrieved**
   - If new user: creates account automatically
   - If existing user: updates last_login timestamp
   - No passwords needed - Google handles authentication

5. **Backend issues JWT token**
   - Creates our own JWT with user_id and email
   - Sent to frontend (24-hour expiry)
   - Frontend stores in localStorage
   - Used for subsequent API requests

### Benefits of Google OAuth

✅ **No passwords to manage** - Users use their Google account
✅ **Secure** - Google's infrastructure handles authentication
✅ **User data** - Email, name, profile picture available
✅ **One-click login** - Fast signup and login experience
✅ **Account recovery** - Users recover account via Google
✅ **2FA support** - Leverages Google's 2FA if enabled

## Deployment (Render)

1. Go to Render dashboard
2. Set environment variables:
   ```
   GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
   JWT_SECRET_KEY=your-super-secret-production-key
   OPENROUTER_API_KEY=sk-or-v1-...
   SUPABASE_URL=https://...supabase.co
   SUPABASE_KEY=eyJ...
   ```

3. Update `static/script.js` with your Client ID before deploying:
   ```javascript
   client_id: "YOUR_PRODUCTION_CLIENT_ID.apps.googleusercontent.com"
   ```

4. Add authorized redirect URI in Google Cloud Console:
   ```
   https://your-render-deployment-url.onrender.com
   ```

## Troubleshooting

### "GOOGLE_CLIENT_ID not configured"
- Add `GOOGLE_CLIENT_ID` to your .env file
- Restart the application

### "Invalid Google token"
- Check your Client ID is correct
- Verify token hasn't expired
- Check Google's public keys are reachable

### Google Sign-In button not showing
- Ensure `https://accounts.google.com/gsi/client` is loaded
- Check browser console for errors
- Verify `client_id` in script.js is correct

### "User from Google is signed in, but API calls fail"
- Verify JWT_SECRET_KEY is set in .env
- Check Authorization header is being sent
- Confirm token hasn't expired yet

## Security Notes

✅ Never expose Client Secret (we don't use it)
✅ Never log sensitive data
✅ Always use HTTPS in production
✅ Change JWT_SECRET_KEY regularly in production
✅ Monitor failed authentication attempts

## Multiple Environments

### Development (.env)
```
GOOGLE_CLIENT_ID=xxx-dev.apps.googleusercontent.com
JWT_SECRET_KEY=dev-secret-key
```

### Production (.env.prod)
```
GOOGLE_CLIENT_KEY=xxx-prod.apps.googleusercontent.com
JWT_SECRET_KEY=production-secret-key-change-regularly
```

Also update `static/script.js` with environment-specific Client ID.

## API Endpoint

### POST /auth/google
Authenticate user with Google ID token

**Request:**
```json
{
  "token": "eyJ...JWT token from Google..."
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "uuid",
  "email": "user@gmail.com",
  "name": "User Name",
  "picture": "https://...",
  "tokens": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid Google token: ..."
}
```

## Next Steps

- Implement logout button (done ✅)
- Add user profile page
- Implement password reset (not needed with OAuth)
- Add rate limiting
- Monitor failed auth attempts

