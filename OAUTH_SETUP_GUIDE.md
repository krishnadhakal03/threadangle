# Complete OAuth Setup Guide: Facebook + Instagram
## For Threadangle (Local & Production)

**Timeline:** March 12 - March 19, 2026 (Before Launch)  
**Platforms:** Facebook OAuth 2.0 + Instagram Graph API  
**Environments:** Local (localhost:8000) → Production (kriangle.com)

---

## PHASE 1: DELETE OLD APPS & START FRESH (5 minutes)

### Step 1: Delete Existing Apps in Meta Dashboard
1. Go to **https://developers.facebook.com**
2. Click **My Apps** → Select your Threadangle app
3. Click **⚙️ Settings** (bottom left)
4. Scroll to **Delete App** button
5. Click **Delete App** and confirm

---

## PHASE 2: CREATE NEW FACEBOOK APP (10 minutes)

### Step 2: Create a New App
1. Go to **https://developers.facebook.com**
2. Click **My Apps** button (top right)
3. Click **Create App**
4. Choose app type: **Business** (for OAuth)
5. Fill in:
   - **App Name:** `Threadangle`
   - **App Contact Email:** your@email.com
   - **App Purpose:** `Manage and publish content to social media`
6. Click **Create App**

### Step 3: Get Your App Credentials
1. In the new app, go to **Settings** → **Basic**
2. **Copy these and save them:**
   - **App ID** → save to `.env` as `FACEBOOK_APP_ID`
   - **App Secret** → save to `.env` as `FACEBOOK_APP_SECRET`

---

## PHASE 3: CONFIGURE FACEBOOK LOGIN (10 minutes)

### Step 4: Add Facebook Login Product
1. Click **+ Add Product** button
2. Search for **Facebook Login**
3. Click **Set Up**
4. Choose platform: **Web**
5. Click **Continue**

### Step 5: Configure Facebook Login Settings
1. Go to **Products** → **Facebook Login** → **Settings**
2. Under **Valid OAuth Redirect URIs**, add:
   ```
   http://localhost:8000/api/auth/facebook/callback
   ```
   (For production: `https://kriangle.com/api/auth/facebook/callback`)

3. Under **Valid OAuth Redirect Domains**, add:
   ```
   localhost:8000
   ```
   (For production: `kriangle.com`)

4. Click **Save Changes**

### Step 6: Get Facebook Test Account
1. Go to **Settings** → **Users and Roles** → **Test Users**
2. Click **Create Test User**
3. Fill in:
   - **Name:** `Test User Facebook`
   - **Email:** anything@test.com
   - **Role:** Tester
4. Click **Create Test User**
5. Click the test user → **Copy the Facebook ID** → Save to `.env` as `FACEBOOK_TEST_USER_ID`

---

## PHASE 4: CONFIGURE INSTAGRAM (15 minutes)

### Step 7: Add Instagram Graph API Product
1. Back to **My App** → Click **+ Add Product**
2. Search for **Instagram Graph API**
3. Click **Set Up**
4. Click **Continue**

### Step 8: Create Instagram Business Account (Test)
1. Go to **Products** → **Instagram Graph API** → **Tools**
2. Under "Get started", click **Create Test App**
3. This creates a test Instagram Business Account
4. **Copy and save:**
   - **Page Access Token** → `.env` as `INSTAGRAM_TEST_TOKEN`
   - **Business Account ID** → `.env` as `INSTAGRAM_BUSINESS_ACCOUNT_ID`

### Step 9: Get Instagram App ID
1. Go to **Settings** → **Basic**
2. **Copy App ID** → save to `.env` as `INSTAGRAM_APP_ID`

---

## PHASE 5: CONFIGURE WEBHOOKS (10 minutes)

### Step 10: Add Webhook URL for Webhook Verification
1. Go to **Products** → **Instagram Graph API** → **Configuration**
2. Under **Webhooks for Instagram**, click **Add Subscription**
3. Enter:
   - **Callback URL:** `http://localhost:8000/api/webhooks/instagram` (for local testing with ngrok, use ngrok URL)
   - **Verify Token:** `threadangle_webhook_verify_token_2026` (save this to `.env` as `INSTAGRAM_WEBHOOK_VERIFY_TOKEN`)
4. **Subscribe to these fields:**
   - ✅ `feed` (for posts)
   - ✅ `story` (for stories)
   - ✅ `comments` (for comments)
   - ✅ `mentions` (for mentions)
5. Click **Save**

---

## PHASE 6: CREATE .ENV FILE (5 minutes)

### Step 11: Update Backend .env
Create or update `backend/.env` with:

```env
# ===== FACEBOOK OAUTH =====
FACEBOOK_APP_ID=YOUR_APP_ID
FACEBOOK_APP_SECRET=YOUR_APP_SECRET
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/auth/facebook/callback
FACEBOOK_TEST_USER_ID=YOUR_TEST_USER_ID

# ===== INSTAGRAM OAUTH =====
INSTAGRAM_APP_ID=YOUR_APP_ID
INSTAGRAM_BUSINESS_ACCOUNT_ID=YOUR_BUSINESS_ACCOUNT_ID
INSTAGRAM_TEST_TOKEN=YOUR_TEST_TOKEN
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=threadangle_webhook_verify_token_2026

# ===== ENCRYPTION (for storing user tokens) =====
ENCRYPTION_KEY=your-32-character-encryption-key-here

# ===== DATABASE =====
DATABASE_URL=sqlite:///./threadforge.db

# ===== JWT =====
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ===== FRONTEND =====
FRONTEND_URL=http://localhost:3000
```

**⚠️ IMPORTANT:** 
- Replace all `YOUR_*` placeholders with actual values from Meta Dashboard
- Keep this file secret (never commit to Git)
- For production, use different credentials and URLs

---

## PHASE 7: SETUP LOCAL TESTING WITH NGROK (15 minutes)

### Step 12: Install ngrok
1. Download from **https://ngrok.com/download**
2. Extract and add to PATH, or run from extracted folder

### Step 13: Start ngrok Tunnel
1. Open PowerShell in `F:\Threadforge`
2. Run:
   ```powershell
   ngrok http 8000
   ```
3. You'll see:
   ```
   Forwarding     https://abc123def456.ngrok.io -> http://localhost:8000
   ```
4. **Copy the `https://abc123def456.ngrok.io` URL** → Keep it handy

### Step 14: Update Webhook URL for ngrok
1. Back to Meta Dashboard → **Instagram Graph API** → **Configuration**
2. Click **Edit** next to your webhook
3. Change **Callback URL** to:
   ```
   https://abc123def456.ngrok.io/api/webhooks/instagram
   ```
   (Use YOUR ngrok URL from Step 13)
4. Click **Save**

---

## PHASE 8: CREATE BACKEND WEBHOOK ENDPOINT (15 minutes)

### Step 15: Create Webhooks Route
Create file: `backend/routes/webhooks.py`

```python
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

INSTAGRAM_WEBHOOK_VERIFY_TOKEN = os.getenv("INSTAGRAM_WEBHOOK_VERIFY_TOKEN", "threadangle_webhook_verify_token_2026")

@router.get("/instagram")
async def verify_instagram_webhook(request: Request):
    """
    Webhook verification endpoint for Instagram
    Meta will call this with hub.challenge to verify the webhook
    """
    try:
        hub_mode = request.query_params.get("hub.mode")
        hub_challenge = request.query_params.get("hub.challenge")
        hub_verify_token = request.query_params.get("hub.verify_token")

        # Verify the webhook
        if hub_mode != "subscribe":
            logger.warning(f"Invalid webhook mode: {hub_mode}")
            raise HTTPException(status_code=403, detail="Invalid mode")

        if hub_verify_token != INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
            logger.warning(f"Invalid verify token: {hub_verify_token}")
            raise HTTPException(status_code=403, detail="Invalid verify token")

        logger.info("✅ Webhook verified successfully!")
        return JSONResponse(content=hub_challenge)

    except Exception as e:
        logger.error(f"❌ Webhook verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instagram")
async def handle_instagram_webhook(request: Request):
    """
    Handle incoming Instagram webhook events
    """
    try:
        body = await request.json()
        
        logger.info(f"📨 Received webhook event: {body}")
        
        # Extract events from webhook
        if "entry" in body:
            for entry in body["entry"]:
                logger.info(f"📮 Processing entry: {entry.get('id')}")
                
                # Handle changes (posts, stories, comments, mentions)
                if "changes" in entry:
                    for change in entry["changes"]:
                        field = change.get("field")
                        value = change.get("value", {})
                        
                        logger.info(f"📝 Field: {field}")
                        logger.info(f"📍 Value: {value}")
                        
                        # TODO: Process based on field type
                        # - feed: new posts
                        # - story: new stories
                        # - comments: new comments
                        # - mentions: new mentions

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
```

### Step 16: Register Webhooks Router in Main App
In `backend/main.py`, add:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ... other imports ...
from routes.webhooks import router as webhooks_router

app = FastAPI(title="Threadangle API")

# ... existing CORS setup ...

# Include routers
# ... existing routers ...
app.include_router(webhooks_router)

# ... rest of your app ...
```

---

## PHASE 9: TEST WEBHOOK VERIFICATION (10 minutes)

### Step 17: Start Backend Server
1. Open PowerShell in `backend/` folder
2. Run:
   ```powershell
   python start_backend.py
   ```
   (or `python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`)

### Step 18: Verify Webhook in Meta Dashboard
1. Go to **Instagram Graph API** → **Configuration**
2. Click **Test** or **Verify** next to your webhook
3. You should see: **✅ Webhook verified**
4. If it fails, check:
   - ngrok tunnel is running
   - Webhook URL matches ngrok URL
   - `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` matches in `.env`
   - Backend is running and logs show the verification attempt

### Step 19: Check Backend Logs
In your backend terminal, you should see:
```
INFO:     GET /api/webhooks/instagram?hub.mode=subscribe&hub.challenge=...&hub.verify_token=...
✅ Webhook verified successfully!
```

---

## PHASE 10: CREATE FACEBOOK OAUTH ENDPOINT (15 minutes)

### Step 20: Create Facebook OAuth Routes
In `backend/routes/auth.py`, add:

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/api/auth/facebook/callback")

@router.get("/facebook/connect")
async def facebook_connect_url():
    """
    Generate Facebook OAuth URL for user authentication
    """
    try:
        auth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={FACEBOOK_APP_ID}"
            f"&redirect_uri={FACEBOOK_REDIRECT_URI}"
            f"&scope=instagram_basic,instagram_graph_user_profile,pages_read_user_content"
            f"&response_type=code"
        )
        return JSONResponse(content={"auth_url": auth_url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/facebook/callback")
async def facebook_callback(code: str = None, error: str = None):
    """
    Handle Facebook OAuth callback
    """
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"Facebook error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code provided")
        
        # Exchange code for access token
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        payload = {
            "client_id": FACEBOOK_APP_ID,
            "client_secret": FACEBOOK_APP_SECRET,
            "code": code,
            "redirect_uri": FACEBOOK_REDIRECT_URI
        }
        
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # TODO: Store access_token in database for authenticated user
        # db.save_social_connection("facebook", access_token, user_id)
        
        # Redirect back to frontend with success (or use localStorage bridge)
        return JSONResponse(content={"status": "success", "platform": "facebook"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PHASE 11: CREATE INSTAGRAM OAUTH ENDPOINT (15 minutes)

### Step 21: Add Instagram OAuth Routes
In `backend/routes/auth.py`, add:

```python
INSTAGRAM_APP_ID = os.getenv("INSTAGRAM_APP_ID")
INSTAGRAM_APP_SECRET = os.getenv("INSTAGRAM_APP_SECRET")
INSTAGRAM_REDIRECT_URI = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:8000/api/auth/instagram/callback")

@router.get("/instagram/connect")
async def instagram_connect_url():
    """
    Generate Instagram OAuth URL (uses Facebook OAuth flow)
    """
    try:
        auth_url = (
            f"https://api.instagram.com/oauth/authorize?"
            f"client_id={INSTAGRAM_APP_ID}"
            f"&redirect_uri={INSTAGRAM_REDIRECT_URI}"
            f"&scope=user_profile,user_media"
            f"&response_type=code"
        )
        return JSONResponse(content={"auth_url": auth_url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instagram/callback")
async def instagram_callback(code: str = None, error: str = None):
    """
    Handle Instagram OAuth callback
    """
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"Instagram error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code provided")
        
        # Exchange code for access token
        token_url = "https://graph.instagram.com/v18.0/access_token"
        payload = {
            "client_id": INSTAGRAM_APP_ID,
            "client_secret": INSTAGRAM_APP_SECRET,
            "code": code,
            "redirect_uri": INSTAGRAM_REDIRECT_URI
        }
        
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # TODO: Store access_token in database for authenticated user
        # db.save_social_connection("instagram", access_token, user_id)
        
        return JSONResponse(content={"status": "success", "platform": "instagram"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## PHASE 12: TEST LOCAL OAUTH FLOW (20 minutes)

### Step 22: Update Frontend OAuth Hook
Your `useConnectedAccounts.js` hook is already set up. Just verify it calls:
- `GET /api/auth/facebook/connect` → Get OAuth URL
- `GET /api/auth/instagram/connect` → Get OAuth URL

### Step 23: Test Facebook OAuth Locally
1. Make sure backend is running on `http://localhost:8000`
2. Frontend is running on `http://localhost:3000`
3. Go to **Settings** → **Social Connections**
4. Click **Connect Facebook**
5. You should get redirected to Facebook login (use your test account)
6. After login, you should see "Connected ✓"

### Step 24: Test Instagram OAuth Locally
1. Click **Connect Instagram** in Settings
2. You should get redirected to Instagram login
3. Use test Instagram account credentials
4. After login, you should see "Connected ✓"

### Step 25: Test Scheduling with Auto-Posting
1. Go to **History**
2. Select a generated content piece
3. Click **📅 Schedule**
4. Toggle "⚡ Auto-Posting"
5. Select Facebook and Instagram checkboxes
6. Set date/time
7. Click **Schedule & Auto-Post**
8. Check logs for successful schedule creation

---

## PHASE 13: PRODUCTION SETUP FOR KRIANGLE.COM (Coming Later)

### Step 26: Get SSL Certificate
When deploying to `kriangle.com`:
1. Use Let's Encrypt (free) or your hosting provider's SSL
2. Ensure HTTPS is enabled

### Step 27: Update Meta Dashboard for Production
1. Go back to Meta Dashboard
2. Under **Facebook Login** → **Settings**, add:
   ```
   https://kriangle.com/api/auth/facebook/callback
   ```
3. Under **Instagram Graph API** → **Configuration**, update webhook URL to:
   ```
   https://kriangle.com/api/webhooks/instagram
   ```

### Step 28: Update .env for Production
Create `.env.production`:
```env
FACEBOOK_REDIRECT_URI=https://kriangle.com/api/auth/facebook/callback
INSTAGRAM_REDIRECT_URI=https://kriangle.com/api/auth/instagram/callback
FRONTEND_URL=https://kriangle.com
```

---

## TROUBLESHOOTING CHECKLIST

### ❌ Webhook Won't Verify
- [ ] ngrok tunnel is running (`ngrok http 8000`)
- [ ] Webhook URL matches ngrok URL (check for typos)
- [ ] Verify token matches in `.env`
- [ ] Backend is running (port 8000)
- [ ] Check backend logs for the verification request

### ❌ OAuth Redirect Not Working
- [ ] Redirect URI in Meta Dashboard matches exactly
- [ ] OAuth URL is being generated correctly (check browser network tab)
- [ ] Backend `.env` has correct `FACEBOOK_APP_ID` and `INSTAGRAM_APP_ID`
- [ ] Frontend and backend are on correct ports (3000, 8000)

### ❌ Access Token Invalid
- [ ] App is published (or at least in development)
- [ ] App secret is correct (copy-paste carefully from Meta Dashboard)
- [ ] Token scope matches what you requested
- [ ] Test account has correct role assigned (Tester or above)

---

## NEXT STEPS (After All Steps Complete)
1. ✅ Verify webhook works (Step 19)
2. ✅ Test local OAuth flow (Steps 23-25)
3. ✅ Run full FRONTEND_AUTO_POSTING_TESTS.md test suite
4. 🚀 Deploy to production (kriangle.com)
5. 🎉 Launch on March 19, 2026

---

## QUICK REFERENCE: .ENV TEMPLATE
```env
FACEBOOK_APP_ID=YOUR_VALUE_HERE
FACEBOOK_APP_SECRET=YOUR_VALUE_HERE
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/auth/facebook/callback
FACEBOOK_TEST_USER_ID=YOUR_VALUE_HERE

INSTAGRAM_APP_ID=YOUR_VALUE_HERE
INSTAGRAM_BUSINESS_ACCOUNT_ID=YOUR_VALUE_HERE
INSTAGRAM_TEST_TOKEN=YOUR_VALUE_HERE
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=threadangle_webhook_verify_token_2026

ENCRYPTION_KEY=your-32-character-key-1234567890ab
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

DATABASE_URL=sqlite:///./threadforge.db
FRONTEND_URL=http://localhost:3000
```

---

**Questions? Let me know which step you're on!** 🚀
