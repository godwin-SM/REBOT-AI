#!/usr/bin/env python
"""
Network diagnostic script to test Google OAuth connectivity
"""

import socket
import ssl
import urllib.request
import sys

print("=" * 60)
print("NETWORK DIAGNOSTICS FOR GOOGLE OAUTH")
print("=" * 60)

# Test 1: Basic DNS resolution
print("\n[1] Testing DNS Resolution...")
try:
    ip = socket.gethostbyname('oauth2.googleapis.com')
    print(f"   ✓ oauth2.googleapis.com resolves to {ip}")
except socket.gaierror as e:
    print(f"   ✗ FAILED: Cannot resolve oauth2.googleapis.com")
    print(f"   Error: {e}")
    sys.exit(1)

# Test 2: Check connectivity to Google
print("\n[2] Testing connectivity to Google OAuth endpoint...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('oauth2.googleapis.com', 443))
    s.close()
    print("   ✓ Successfully connected to oauth2.googleapis.com:443")
except Exception as e:
    print(f"   ✗ FAILED: Cannot connect to oauth2.googleapis.com:443")
    print(f"   Error: {e}")
    print("   This might be due to: firewall, proxy, or network issues")

# Test 3: HTTPS request to Google
print("\n[3] Testing HTTPS request to Google...")
try:
    url = 'https://oauth2.googleapis.com/oauth2/v3/certs'
    response = urllib.request.urlopen(url, timeout=5)
    print(f"   ✓ Successfully reached Google OAuth certs endpoint (HTTP {response.status})")
except urllib.error.HTTPError as e:
    # HTTP errors still prove DNS + TLS + outbound connectivity are working.
    print(f"   ✓ Reached Google OAuth endpoint (HTTP {e.code})")
except Exception as e:
    print(f"   ✗ FAILED: Cannot reach Google OAuth endpoint")
    print(f"   Error: {e}")
    print("\n   SOLUTIONS:")
    print("   1. Check if you have internet connection: ping google.com")
    print("   2. Check if you're behind a corporate proxy/firewall")
    print("   3. Try: ipconfig /release && ipconfig /renew (Windows)")
    print("   4. Check Windows Firewall or antivirus settings")
    sys.exit(1)

# Test 4: Check Python google-auth library
print("\n[4] Checking Python google-auth library...")
try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
    print("   ✓ google-auth library is properly installed")
except ImportError as e:
    print(f"   ✗ FAILED: google-auth library not found")
    print(f"   Error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All network diagnostics passed!")
print("=" * 60)
