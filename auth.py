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
TOKEN_EXPIRY_HOURS = 720  # 30 days (was 24 hours

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
        print(f"[DEBUG] Token successfully verified. User ID: {payload.get('user_id')}")
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"[DEBUG] Token has expired: {e}")
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"[DEBUG] Invalid token error: {e}")
        raise Exception(f"Invalid token: {str(e)}")
    except Exception as e:
        print(f"[DEBUG] Unexpected error verifying token: {e}")
        raise

def get_user_from_token(token: str) -> Optional[str]:
    """Extract user_id from token"""
    try:
        payload = verify_token(token)
        return payload.get("user_id")
    except Exception as e:
        print(f"[DEBUG] Token verification failed: {str(e)}")
        print(f"[DEBUG] Token (first 50 chars): {token[:50] if token else 'EMPTY'}")
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
        import socket
        import time
        
        # Create request object for Google verification
        request = requests.Request()
        
        # Get Google's OAuth client ID from environment
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        
        if not CLIENT_ID:
            raise Exception("GOOGLE_CLIENT_ID not configured in .env")

        cert_urls = [
            "https://www.googleapis.com/oauth2/v1/certs",
            "https://www.googleapis.com/oauth2/v3/certs"
        ]

        last_error = None
        idinfo = None

        # Retry with alternate cert endpoints to handle transient DNS issues.
        for cert_url in cert_urls:
            for attempt in range(2):
                try:
                    idinfo = id_token.verify_token(
                        token,
                        request,
                        audience=CLIENT_ID,
                        certs_url=cert_url
                    )
                    break
                except Exception as e:
                    last_error = e
                    if attempt == 0:
                        time.sleep(0.8)
            if idinfo:
                break

        if not idinfo:
            # Backward-compatible fallback for older google-auth APIs.
            try:
                idinfo = id_token.verify_oauth2_token(token, request, audience=CLIENT_ID)
            except TypeError:
                idinfo = id_token.verify_oauth2_token(token, request)

        # Verify required Google claims after signature validation.
        if idinfo.get("aud") != CLIENT_ID:
            raise Exception(f"Token audience mismatch. Expected {CLIENT_ID}, got {idinfo.get('aud')}")

        issuer = idinfo.get("iss")
        if issuer not in ["accounts.google.com", "https://accounts.google.com"]:
            raise Exception(f"Invalid token issuer: {issuer}")

        if last_error and not idinfo:
            raise last_error
        
        print(f"[DEBUG] Google token info keys: {list(idinfo.keys())}")
        print(f"[DEBUG] Google picture field: {idinfo.get('picture', 'NOT_PROVIDED')}")
        
        return idinfo
        
    except socket.gaierror as e:
        error_msg = f"Network error: Cannot reach Google's servers. Check your internet connection and firewall settings. Details: {str(e)}"
        print(f"Google token verification error: {error_msg}")
        raise Exception(error_msg)
    except TimeoutError as e:
        error_msg = f"Network timeout: Google's servers took too long to respond. Check your internet connection."
        print(f"Google token verification error: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        print(f"Google token verification error: {e}")
        raise Exception(f"Invalid Google token: {str(e)}")

# ----------------------
# SUPABASE USER MANAGEMENT
# ----------------------

def get_supabase():
    """Get Supabase client"""
    from supabase import create_client
    SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
    SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()
    
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
        error_text = str(e)
        if "getaddrinfo failed" in error_text:
            sb_url = (os.getenv("SUPABASE_URL") or "").strip()
            error_text = (
                "Supabase host could not be resolved (DNS error). "
                f"Check SUPABASE_URL in .env and confirm the project still exists: {sb_url}"
            )
        print(f"Error in get_or_create_google_user: {error_text}")
        return {"success": False, "error": error_text}

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

