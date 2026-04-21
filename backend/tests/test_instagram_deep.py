"""
Deep automated test for Instagram OAuth integration.
Found issues will be printed as FAIL with explanation.
Run from backend/ with: python -m pytest tests/test_instagram_deep.py -v -s
Or directly: python tests/test_instagram_deep.py
"""

import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Load .env manually so we don't need python-dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent.parent))

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
INFO = "\033[94mINFO\033[0m"

failures = []
warnings = []

def check(name, condition, message=""):
    if condition:
        print(f"  [{PASS}] {name}")
    else:
        print(f"  [{FAIL}] {name}" + (f": {message}" if message else ""))
        failures.append(f"{name}: {message}")


def warn(name, message=""):
    print(f"  [{WARN}] {name}" + (f": {message}" if message else ""))
    warnings.append(f"{name}: {message}")


def info(name, message=""):
    print(f"  [{INFO}] {name}" + (f": {message}" if message else ""))


# ─── SECTION 1: Environment Variables ────────────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 1: Environment Variables")
print("══════════════════════════════════════════")

app_id = os.getenv("FACEBOOK_APP_ID")
app_secret = os.getenv("FACEBOOK_APP_SECRET")
redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")
frontend_url = os.getenv("FRONTEND_URL")

check("FACEBOOK_APP_ID is set", bool(app_id),
      "Missing! Add to backend/.env: FACEBOOK_APP_ID=1870226043633520")
check("FACEBOOK_APP_SECRET is set", bool(app_secret),
      "Missing! Add to backend/.env: FACEBOOK_APP_SECRET=<your-secret>")
check("FACEBOOK_REDIRECT_URI is set", bool(redirect_uri),
      "Missing! Add: FACEBOOK_REDIRECT_URI=http://localhost:5173/auth/facebook/callback")

if app_id:
    check("FACEBOOK_APP_ID is a numeric string", app_id.isdigit(),
          f"Got: {app_id!r} — should be numeric app ID only")
    info("FACEBOOK_APP_ID", app_id)

if redirect_uri:
    info("FACEBOOK_REDIRECT_URI", redirect_uri)
    check("Redirect URI points to localhost for dev",
          "localhost" in redirect_uri or "127.0.0.1" in redirect_uri,
          f"Got {redirect_uri!r}. For local dev this must match the Valid OAuth Redirect URI in Meta portal exactly")

if frontend_url:
    info("FRONTEND_URL", frontend_url)
    if "localhost" not in frontend_url and "127.0.0.1" not in frontend_url:
        warn("FRONTEND_URL is production URL",
             f"FRONTEND_URL={frontend_url!r}. The OAuth callback redirect in social_auth.py uses this. "
             "For local development, the twitter/linkedin callback routes will redirect to production. "
             "Consider setting FRONTEND_URL=http://localhost:5173 in .env for local dev.")


# ─── SECTION 2: Import & OAuth URL Generation ────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 2: OAuth URL Generation")
print("══════════════════════════════════════════")

try:
    from integrations.instagram import (
        get_instagram_oauth_url,
        exchange_instagram_code_for_token,
        get_instagram_connection_data,
        FACEBOOK_APP_ID as IG_APP_ID,
        FACEBOOK_APP_SECRET as IG_APP_SECRET,
        FACEBOOK_REDIRECT_URI as IG_REDIRECT_URI,
    )
    check("instagram.py imports successfully", True)
except Exception as e:
    check("instagram.py imports successfully", False, str(e))
    print("\n>>> Cannot continue without successful import. Exiting.")
    sys.exit(1)

check("Module FACEBOOK_APP_ID is not None", IG_APP_ID is not None,
      "The module read None from env — FACEBOOK_APP_ID is missing from .env")
check("Module FACEBOOK_APP_SECRET is not None", IG_APP_SECRET is not None,
      "The module read None from env — FACEBOOK_APP_SECRET is missing from .env")

# Generate an OAuth URL and inspect it
test_state = "test_state_12345"
try:
    oauth_url = get_instagram_oauth_url(test_state)
    info("Generated OAuth URL", oauth_url[:120] + "..." if len(oauth_url) > 120 else oauth_url)
    parsed = urlparse(oauth_url)
    params = parse_qs(parsed.query)

    check("OAuth URL uses facebook.com (not instagram.com or api.instagram.com)",
          "facebook.com" in parsed.netloc or "facebook.com" in oauth_url,
          f"Got netloc: {parsed.netloc!r} — must use www.facebook.com/dialog/oauth")

    check("OAuth URL uses dialog/oauth path",
          "/dialog/oauth" in parsed.path,
          f"Got path: {parsed.path!r}")

    client_id_in_url = params.get("client_id", [None])[0]
    check("client_id in OAuth URL is not 'None'",
          client_id_in_url not in (None, "None", "none", ""),
          f"client_id={client_id_in_url!r} — FACEBOOK_APP_ID env var is missing")

    scope_in_url = params.get("scope", [""])[0]
    info("Scope in URL", scope_in_url)

    required_scopes = ["instagram_basic", "pages_show_list"]
    for s in required_scopes:
        check(f"Scope includes '{s}' (required by Meta docs)",
              s in scope_in_url,
              f"'{s}' is required per https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/get-started Step 2")

    check("Scope includes 'instagram_content_publish' (for posting)",
          "instagram_content_publish" in scope_in_url,
          "Add instagram_content_publish to enable posting to Instagram")

    state_in_url = params.get("state", [None])[0]
    check("state parameter is present in OAuth URL", state_in_url == test_state,
          f"Got state={state_in_url!r}")

    redirect_in_url = params.get("redirect_uri", [None])[0]
    check("redirect_uri is present in OAuth URL", bool(redirect_in_url),
          "redirect_uri param missing")
    if redirect_in_url:
        check("redirect_uri matches FACEBOOK_REDIRECT_URI env var",
              redirect_in_url == IG_REDIRECT_URI,
              f"URL has {redirect_in_url!r} but env has {IG_REDIRECT_URI!r}")

    # Check API version
    api_version = None
    parts = parsed.path.split("/")
    for part in parts:
        if part.startswith("v") and "." in part:
            api_version = part
    info("Facebook API version in URL", api_version or "(none — using default)")

except Exception as e:
    check("OAuth URL generation", False, str(e))


# ─── SECTION 3: Token Exchange Endpoint Logic ────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 3: Token Exchange (with invalid code)")
print("══════════════════════════════════════════")

import requests as req

# Hit the token exchange endpoint with a fake code — we expect a specific error
# from Facebook (not a Python crash), which proves our HTTP call is correct.
if app_id and app_secret and redirect_uri:
    try:
        # This will fail at Facebook, but the HTTP call structure must be correct
        r = req.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": "FAKE_CODE_FOR_TESTING",
            },
            timeout=10,
        )
        data = r.json()
        info("FB token exchange HTTP status", str(r.status_code))
        info("FB token exchange response", json.dumps(data)[:200])

        if r.status_code == 400 and "error" in data:
            err = data["error"]
            check("Facebook token exchange endpoint reachable (expected auth error with fake code)",
                  True)
            info("Error code", str(err.get("code")))
            info("Error message", err.get("message", ""))
            # Error 100 = invalid code, which means our endpoint is correct
            # Error 101 = invalid app ID
            if err.get("code") == 101 or "Invalid App ID" in str(err.get("message", "")):
                check("App ID is valid at Facebook", False,
                      f"Facebook says Invalid App ID: {app_id!r}. Check FACEBOOK_APP_ID in .env")
            elif err.get("code") == 100 and "code" in str(err.get("message", "")).lower():
                check("App ID recognized by Facebook", True)
                check("Redirect URI is recognized by Facebook", True)
            elif "redirect_uri" in str(err.get("message", "")).lower():
                check("Redirect URI is valid in Meta portal", False,
                      f"Facebook rejected redirect_uri={redirect_uri!r}. "
                      "Make sure this exact URI is in Meta portal > Facebook Login > Settings > Valid OAuth Redirect URIs")
        elif r.status_code == 200:
            warn("Token exchange with FAKE code returned 200", "Unexpected — Facebook accepted a fake code")
        else:
            warn("Unexpected token exchange response", f"Status {r.status_code}: {json.dumps(data)[:200]}")
    except req.exceptions.Timeout:
        warn("Token exchange connectivity", "Request timed out — check internet connection")
    except Exception as e:
        warn("Token exchange test", str(e))
else:
    warn("Token exchange test skipped", "FACEBOOK_APP_ID or FACEBOOK_APP_SECRET missing")


# ─── SECTION 4: me/accounts API Reachability ──────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 4: Facebook Graph API Reachability")
print("══════════════════════════════════════════")

try:
    test_r = req.get("https://graph.facebook.com/v18.0/", timeout=8)
    check("graph.facebook.com is reachable", test_r.status_code in (200, 400, 404),
          f"Got {test_r.status_code}")
    info("graph.facebook.com response", test_r.text[:100])
except Exception as e:
    check("graph.facebook.com is reachable", False, str(e))


# ─── SECTION 5: Backend Route Registration ───────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 5: Backend Route / Logic Checks")
print("══════════════════════════════════════════")

# Check the backend is currently running
try:
    health_r = req.get("http://localhost:8000/", timeout=5)
    check("Backend is running on :8000", health_r.status_code == 200,
          f"Got {health_r.status_code}: {health_r.text[:100]}")
except Exception as e:
    check("Backend is running on :8000", False, f"Cannot connect: {e}")

# Try the connect endpoint with no auth (should get 401/403, not 500)
try:
    r = req.get("http://localhost:8000/api/auth/instagram/connect", timeout=5)
    info("Instagram connect (no auth) status", str(r.status_code))
    check("Instagram connect endpoint exists (returns 401/403 without auth, not 404/500)",
          r.status_code in (401, 403),
          f"Got {r.status_code}: {r.text[:200]}")
except Exception as e:
    warn("Instagram connect endpoint check", str(e))

# Verify the facebook exchange endpoint exists
try:
    r = req.post("http://localhost:8000/api/auth/facebook/exchange",
                 json={"code": "test", "state": "test"}, timeout=5)
    info("Facebook exchange endpoint status", str(r.status_code))
    check("Facebook exchange endpoint exists (400 with missing state, not 404/500)",
          r.status_code in (400, 422),
          f"Got {r.status_code}: {r.text[:200]}")
except Exception as e:
    warn("Facebook exchange endpoint check", str(e))


# ─── SECTION 6: Social Auth Route Logic ──────────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 6: Code Logic Analysis")
print("══════════════════════════════════════════")

# Read and analyse social_auth.py for known issues
social_auth_path = Path(__file__).parent.parent / "routes" / "social_auth.py"
if social_auth_path.exists():
    code = social_auth_path.read_text(encoding="utf-8", errors="replace")

    check("social_auth.py imports get_instagram_connection_data",
          "get_instagram_connection_data" in code)

    check("facebook/exchange route exists in social_auth.py",
          '"/api/auth/facebook/exchange"' in code or "facebook/exchange" in code)

    check("State is deleted before processing (prevents replay attacks)",
          "db.delete(state_row)" in code or "await db.delete" in code)

    check("OAuthState model is imported",
          "OAuthState" in code)

ig_path = Path(__file__).parent.parent / "integrations" / "instagram.py"
if ig_path.exists():
    ig_code = ig_path.read_text(encoding="utf-8", errors="replace")

    # Strip comment/docstring lines to avoid false positives from warning comments
    # (e.g. "do NOT use api.instagram.com" in docstring counts as a match)
    ig_code_lines = ig_code.splitlines()
    non_comment_lines = [
        l for l in ig_code_lines
        if not l.strip().startswith("#")
        and '"""' not in l
        and "DO NOT" not in l
        and "api.instagram.com" not in l  # only in doc warnings
        and "graph.instagram.com" not in l  # only in doc warnings
    ]
    ig_code_no_comments = "\n".join(non_comment_lines)

    check("instagram.py uses graph.facebook.com in actual calls",
          "graph.facebook.com" in ig_code_no_comments,
          "No graph.facebook.com calls found (excluding comments)")

    check("instagram.py has no api.instagram.com in actual code (only in docstring)",
          all("api.instagram.com" not in l for l in ig_code_lines
              if not l.strip().startswith("#") and '"""' not in l and "DO NOT" not in l
              and "SEPARATE" not in l and "→" not in l and "*" not in l.strip()[:1]),
          "Found api.instagram.com in actual code — should only appear in warning comments")

    check("instagram.py iterates ALL pages (not just pages[0])",
          "for page in pages" in ig_code,
          "Must iterate all pages to find the one with an IG business account")

    check("instagram.py checks instagram_business_account field",
          "instagram_business_account" in ig_code)

    check("instagram.py prints debug logs for me/accounts call",
          "me/accounts" in ig_code and "print" in ig_code)

    check("instagram.py raises Exception when no pages found (not returns None)",
          "raise Exception" in ig_code and "No Facebook Pages" in ig_code)

    check("instagram.py uses page_access_token (not user token) for IG calls",
          "page_access_token" in ig_code or "page_token" in ig_code)

    # Find the actual scope= assignment line (not doc comments)
    scope_lines = [
        l for l in ig_code_lines
        if "'scope'" in l and ":" in l and "instagram" in l.lower()
    ]
    if scope_lines:
        info("Actual scope assignment", scope_lines[0].strip())
        actual_scope = scope_lines[0]
        check("Scope includes 'instagram_basic' in actual params (required by Meta docs)",
              "instagram_basic" in actual_scope,
              "Meta docs Step 2 requires instagram_basic. See: "
              "developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/get-started")
        check("Scope does NOT include 'instagram_business_basic' (wrong API) in actual params",
              "instagram_business_basic" not in actual_scope,
              "instagram_business_basic is for the api.instagram.com flow — wrong API")
    else:
        warn("Could not find scope assignment line in instagram.py")


# ─── SECTION 7: Models Check ─────────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 7: Database Model Check")
print("══════════════════════════════════════════")

models_path = Path(__file__).parent.parent / "models.py"
if models_path.exists():
    models_code = models_path.read_text(encoding="utf-8", errors="replace")
    check("OAuthState model exists in models.py",
          "class OAuthState" in models_code or "OAuthState" in models_code)
    check("SocialAccount model has platform_username field",
          "platform_username" in models_code)
    check("SocialAccount model has platform_user_id field",
          "platform_user_id" in models_code)
    check("SocialAccount model has access_token field",
          "access_token" in models_code)


# ─── SECTION 8: Frontend FacebookCallback Check ──────────────────────────────
print("\n══════════════════════════════════════════")
print(" SECTION 8: Frontend Callback Page Check")
print("══════════════════════════════════════════")

fb_cb_path = Path(__file__).parent.parent.parent / "frontend" / "src" / "pages" / "FacebookCallback.jsx"
if fb_cb_path.exists():
    cb_code = fb_cb_path.read_text(encoding="utf-8", errors="replace")
    check("FacebookCallback uses useRef to prevent double-invoke",
          "useRef" in cb_code and "hasFired" in cb_code)
    check("FacebookCallback POSTs to /auth/facebook/exchange",
          "facebook/exchange" in cb_code)
    check("FacebookCallback picks up 'code' param from URL",
          'searchParams.get(\'code\')' in cb_code or 'searchParams.get("code")' in cb_code)
    check("FacebookCallback picks up 'state' param from URL",
          'searchParams.get(\'state\')' in cb_code or 'searchParams.get("state")' in cb_code)
    check("FacebookCallback sets localStorage on success",
          "oauth-completed" in cb_code)
    check("FacebookCallback handles 'error' param (user cancelled)",
          "error" in cb_code and "searchParams.get" in cb_code)
else:
    warn("FacebookCallback.jsx not found", str(fb_cb_path))


# Check App routing includes the callback page
app_jsx = Path(__file__).parent.parent.parent / "frontend" / "src" / "App.jsx"
if app_jsx.exists():
    app_code = app_jsx.read_text(encoding="utf-8", errors="replace")
    check("App.jsx routes to FacebookCallback at /auth/facebook/callback",
          "FacebookCallback" in app_code and "facebook/callback" in app_code,
          "If the route is missing, users will see a 404 after Facebook redirects them back")
else:
    warn("App.jsx not found for route check")


# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print(" SUMMARY")
print("══════════════════════════════════════════")
if failures:
    print(f"\n  ❌ {len(failures)} FAILURE(S):\n")
    for i, f in enumerate(failures, 1):
        print(f"    {i}. {f}")
else:
    print(f"\n  ✅ All checks passed!")

if warnings:
    print(f"\n  ⚠️  {len(warnings)} WARNING(S):\n")
    for i, w in enumerate(warnings, 1):
        print(f"    {i}. {w}")

print()
if failures:
    sys.exit(1)
