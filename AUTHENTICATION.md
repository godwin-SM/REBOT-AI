# Google OAuth Authentication Guide

## Overview

REBOT AI uses Google OAuth for simple, secure authentication. Users sign in with their Google account - no passwords to manage, all data remains private and isolated per user.

## Key Features

### Easy Google Sign-In
- One-click login with Google
- No passwords to remember
- Automatic account creation for new users
- Gmail, Google Workspace, and consumer Google accounts supported

### Secure & Fast
- Google handles all authentication security
- Cryptographically verified ID tokens
- 24-hour access tokens with auto-expiry
- User data isolated by user_id

## Quick Setup

1. **Get Google Client ID** - See [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)
2. **Create Supabase tables** - Run [DATABASE_SETUP.sql](DATABASE_SETUP.sql)
3. **Update environment variables** - Set in `.env` file
4. **Update frontend** - Put Client ID in `static/script.js`
5. **Start app** - `python -m uvicorn app:app --reload`

## Environment Variables

Required in `.env`:

```
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
JWT_SECRET_KEY=your-secret-key-change-in-production
OPENROUTER_API_KEY=sk-or-v1-...
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...
```

## User Flow

### First Time User
1. User visits app
2. Clicks "Sign in with Google"
3. Enters Google credentials (if not already signed in)
4. Approves data sharing (email, name, profile picture)
5. Automatically creates account
6. Logged in and ready to chat

### Returning User
1. User visits app
2. Clicks "Sign in with Google"
3. Google auto-logs them in (same Google session as before)
4. Logged in and ready to chat

## Database Schema

### users table
```sql
- id (UUID)         -- Unique user ID
- email (string)    -- Google account email
- name (string)     -- User's display name
- google_id (string)-- Google's unique identifier
- picture (string)  -- Profile picture URL
- created_at        -- Account creation time
- last_login        -- Last login timestamp
```

### chat_history table
Stores user-specific conversations (filtered by user_id)

### memory table
Stores user-specific RAG embeddings (filtered by user_id)

### documents table
Stores user-specific uploaded files (filtered by user_id)

## API Endpoints

### Authentication

#### POST /auth/google
Sign in or register with Google

```bash
curl -X POST http://localhost:8000/auth/google \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

**Response (Success):**
```json
{
  "success": true,
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@gmail.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid Google token: ..."
}
```

### Protected Endpoints (require Authorization header)

#### GET /me
Get current user information

```bash
curl http://localhost:8000/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@gmail.com",
    "name": "John Doe",
    "picture": "https://lh3.googleusercontent.com/...",
    "created_at": "2024-03-14T10:30:00"
  }
}
```

#### POST /chat
Send message to AI (requires auth)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{"message": "What does my document say?"}'
```

#### POST /upload
Upload documents (requires auth)

```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@document.pdf"
```

## Token Management

### Access Token
- **Duration:** 24 hours
- **Format:** JWT
- **Purpose:** Authenticate API requests
- **Stored:** Browser's localStorage
- **Usage:** `Authorization: Bearer <access_token>`

### Expiration
When access token expires:
- Frontend detects 401 response
- User is logged out
- Redirected to login page
- Must sign in again with Google

## Security Features

✅ **No password storage** - Only Google stores passwords
✅ **Cryptographic verification** - Tokens signed by Google
✅ **Data isolation** - Each user sees only their data
✅ **Token expiration** - 24-hour access token lifetime
✅ **HTTPS required** - All communications encrypted
✅ **RLS policies** - Database row-level security

## Data Privacy

### What We Store
- Google account email
- User's display name
- Profile picture URL
- Google user ID

### What We Don't Store
- Passwords (handled by Google)
- Credit card or payment info
- Users can request data deletion anytime

### Who Can Access What
- Users can only see their own data
- Conversations are private
- Uploaded documents are private
- No data shared with other users

## Troubleshooting

### "GOOGLE_CLIENT_ID not configured"
**Problem:** Missing environment variable
**Solution:** Add to `.env`:
```
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
```

### Google Sign-In button not showing
**Problem:** Google library not loaded
**Solution:** Check if `https://accounts.google.com/gsi/client` is accessible
**Fix:** Check internet connection, allow scripts in browser

### "Invalid Google token"
**Problem:** Token verification failed
**Solution:**
- Check Client ID is correct
- Verify GOOGLE_CLIENT_ID in .env matches frontend
- Ensure token hasn't expired
- Check Google's public keys are reachable

### "Unauthorized" on chat endpoint
**Problem:** Token not sent or invalid
**Solution:**
- Check Authorization header is present
- Verify token format: `Authorization: Bearer <token>`
- Check token hasn't expired
- Try logging in again

### Can't create accounts
**Problem:** Database issue
**Solution:**
- Ensure DATABASE_SETUP.sql was run in Supabase
- Check Supabase credentials in .env
- Verify `users` table exists
- Check table permissions

## Production Deployment

### Environment Variables
In your deployment (Render, Heroku, etc.):
```
GOOGLE_CLIENT_ID=prod-client-id.apps.googleusercontent.com
JWT_SECRET_KEY=your-super-secret-production-key
OPENROUTER_API_KEY=sk-or-v1-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Google OAuth Setup
1. Create production credentials in Google Cloud Console
2. Add authorized redirect URIs:
   - `https://your-domain.com`
   - `https://your-app.onrender.com` (if using Render)
3. Update `static/script.js` with production Client ID

### HTTPS Required
Always use HTTPS in production - OAuth requires secure connections

## Example: JavaScript Frontend

```javascript
// Frontend stores tokens
localStorage.setItem('accessToken', data.tokens.access_token);

// Use token in requests
const response = await fetch('/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ message: 'Hello!' })
});
```

## Example: Multi-User Scenario

### User A's Experience
```
1. Clicks "Sign in with Google"
2. Uses john@gmail.com
3. Account created automatically
4. Uploads sales_report.pdf
5. Chats: "Summarize my report"
6. Only sees their document and conversation
```

### User B's Experience
```
1. Clicks "Sign in with Google"
2. Uses jane@gmail.com
3. Account created automatically
4. Uploads budget.xlsx
5. Chats: "Analyze my budget"
6. Only sees their document and conversation
7. Cannot access User A's data
```

## Support

For setup issues, see [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)

For general auth questions, check troubleshooting section above.

For Google account issues, visit [Google Account Help](https://support.google.com/accounts)

