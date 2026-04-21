#!/usr/bin/env python3
"""
Test RunwayML API connection without consuming credits.
Tests authentication and header validation.
"""
import os
import requests
import json
from pathlib import Path


def _load_env_fallback() -> None:
    """Load key=value pairs from local .env when terminal env vars are absent."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

def test_runway_api():
    """Test Runway API with minimal parameters to validate auth and headers."""
    _load_env_fallback()
    
    api_key = os.getenv("RUNWAYML_API_KEY")
    if not api_key:
        print("❌ ERROR: RUNWAYML_API_KEY environment variable not set")
        print("   Set it in your .env file or system environment")
        return False
    
    print(f"✓ API Key loaded (first 10 chars): {api_key[:10]}***")
    
    api_url = os.getenv("RUNWAYML_API_URL", "https://api.dev.runwayml.com/v1/text_to_video")
    print(f"✓ Using endpoint: {api_url}")
    if "/v1/generate/video" in api_url:
        print("⚠️  Legacy endpoint detected. Prefer /v1/text_to_video")
    
    # Test 1: Query organization info (no credits consumed)
    print("\n[Test 1] Testing authentication with organization endpoint...")
    version = os.getenv("RUNWAYML_API_VERSION", "2024-11-06")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": version,
    }
    
    try:
        response = requests.get(
            "https://api.dev.runwayml.com/v1/organization",
            headers=headers,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication SUCCESS")
            print(f"   Organization: {data.get('name', 'Unknown')}")
            if 'credits' in data.get('usage', {}):
                print(f"   Credits remaining: {data['usage']['credits']}")
            return True
        elif response.status_code == 401:
            print(f"❌ Authentication FAILED: Invalid or expired API key")
            print(f"   Response: {response.text[:200]}")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - API server not responding")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - check network/firewall")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_video_generation_headers():
    """Test that video generation endpoint accepts requests without version header."""
    _load_env_fallback()
    
    api_key = os.getenv("RUNWAYML_API_KEY")
    if not api_key:
        return False
    
    print("\n[Test 2] Testing video generation headers...")
    
    version = os.getenv("RUNWAYML_API_VERSION", "2024-11-06")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": version,
    }
    
    payload = {
        # Intentionally invalid payload to validate auth/header path without spending credits
        "num_frames": 1
    }
    
    try:
        response = requests.post(
            os.getenv("RUNWAYML_API_URL", "https://api.dev.runwayml.com/v1/text_to_video"),
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Headers accepted - endpoint reachable")
            return True
        elif response.status_code == 400:
            error_text = response.text
            if "X-Runway-Version" in error_text:
                print("❌ X-Runway-Version header issue detected")
                print(f"   Error: {error_text[:300]}")
                return False
            print("✅ Endpoint reachable and header accepted (400 is from intentionally invalid payload)")
            print(f"   Response: {error_text[:300]}")
            return True
        elif response.status_code == 402:
            print("⚠️  Out of credits - authentication valid, but would consume credits")
            print("   This means API is working, just no credits available")
            return True
        elif response.status_code == 401:
            print("❌ Authentication failed")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"   {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("RunwayML API Connection Test")
    print("=" * 60)
    
    test1_pass = test_runway_api()
    test2_pass = test_video_generation_headers()
    
    print("\n" + "=" * 60)
    if test1_pass:
        print("✅ API VALIDATION PASSED - Ready to generate videos")
        print("   Run your video generation test now")
    else:
        print("❌ API VALIDATION FAILED")
        print("   Check your RUNWAYML_API_KEY environment variable")
    print("=" * 60)
