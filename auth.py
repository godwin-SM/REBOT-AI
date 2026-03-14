"""
Google OAuth Authentication for REBOT AI.
Simple token verification and user management.
"""

import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# JWT Configuration (for our own tokens)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

def create_access_token(user_id: str, email: str) -> dict:
    """Create access token for authenticated user"""
    now = datetime.utcnow()
    
    payload = {
        "user_id": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": TOKEN_EXPIRY_HOURS * 3600
    }

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")

def get_user_from_token(token: str) -> Optional[str]:
    """Extract user_id from token"""
    try:
        payload = verify_token(token)
        return payload.get("user_id")
    except:
        return None

# ----------------------
# GOOGLE OAUTH VERIFICATION
# ----------------------

def verify_google_token(token: str) -> dict:
    """
    Verify Google ID token and return user info.
    Validates token signature with Google's public keys.
    """
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
        
        # Google's public cert for verification
        request = requests.Request()
        
        # Get Google's OAuth client ID from environment
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        
        if not CLIENT_ID:
            raise Exception("GOOGLE_CLIENT_ID not configured in .env")
        
        # Verify token signature with Google's public keys
        # Try with 'audience' parameter (newer versions)
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                request, 
                audience=CLIENT_ID
            )
        except TypeError:
            # Fallback for older versions that use different parameter
            idinfo = id_token.verify_oauth2_token(token, request)
            # Verify the audience manually
            if idinfo.get('aud') != CLIENT_ID:
                raise Exception(f"Token audience mismatch. Expected {CLIENT_ID}, got {idinfo.get('aud')}")
        
        print(f"[DEBUG] Google token info keys: {list(idinfo.keys())}")
        print(f"[DEBUG] Google picture field: {idinfo.get('picture', 'NOT_PROVIDED')}")
        
        return idinfo
        
    except Exception as e:
        print(f"Google token verification error: {e}")
        raise Exception(f"Invalid Google token: {str(e)}")

# ----------------------
# SUPABASE USER MANAGEMENT
# ----------------------

def get_supabase():
    """Get Supabase client"""
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
        return None

def get_or_create_google_user(google_token: str, frontend_picture: str = None) -> dict:
    """
    Verify Google token and create/get user from database.
    For first-time users, creates account automatically.
    frontend_picture: Optional picture URL from frontend's decoded JWT
    """
    try:
        # Verify token with Google
        google_info = verify_google_token(google_token)
        
        email = google_info.get("email")
        name = google_info.get("name")
        picture = frontend_picture or google_info.get("picture")  # Use frontend picture if provided
        google_id = google_info.get("sub")  # Google's unique ID
        
        print(f"[DEBUG] Google user info: email={email}, name={name}, picture={picture}")
        
        if not email:
            return {"success": False, "error": "No email in Google token"}
        
        sb = get_supabase()
        if not sb:
            return {"success": False, "error": "Database connection failed"}
        
        # Check if user exists
        result = sb.table("users").select("id, email, name").eq("email", email).execute()
        
        if result.data:
            # User exists - just update last login
            user_id = result.data[0]["id"]
            try:
                sb.table("users").update({
                    "last_login": datetime.utcnow().isoformat()
                }).eq("id", user_id).execute()
            except:
                pass  # Non-critical update
        else:
            # Create new user from Google info
            user_data = {
                "email": email,
                "name": name,
                "google_id": google_id,
                "picture": picture,
                "created_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat()
            }
            
            result = sb.table("users").insert(user_data).execute()
            
            if not result.data:
                return {"success": False, "error": "Failed to create user"}
            
            user_id = result.data[0]["id"]
        
        # Create our own JWT token
        tokens = create_access_token(user_id, email)
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "tokens": tokens
        }
    
    except Exception as e:
        print(f"Error in get_or_create_google_user: {e}")
        return {"success": False, "error": str(e)}

def get_user_by_id(user_id: str) -> dict:
    """Fetch user details by ID"""
    try:
        sb = get_supabase()
        if not sb:
            return None
        
        result = sb.table("users").select("id, email, name, picture, created_at").eq("id", user_id).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

