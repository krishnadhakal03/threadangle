# 🚀 AUTO-POSTING FEATURE - SETUP GUIDE

## Overview

The auto-posting feature allows users to connect their Twitter/X, LinkedIn, and Instagram accounts and automatically publish content at scheduled times. This document provides complete setup instructions.

---

## 📋 Prerequisites

Before enabling auto-posting, you need to:

1. **Twitter/X Developer Account** - Free tier available
2. **LinkedIn Developer Account** - Free
3. **Facebook Developer Account** - For Instagram integration (free)
4. **Encryption Key** - For secure token storage
5. **Python Packages** - `cryptography`, `tweepy`, `requests`

---

## 🔧 STEP 1: Database Migration

Run the migration to create required tables:

```bash
cd backend
python migrations/add_auto_posting.py
```

This creates:
- `social_accounts` table for storing OAuth connections
- Auto-posting columns in `generations` table

**Expected Output:**
```
🔄 Starting auto-posting migration...
============================================================
1️⃣ Creating social_accounts table...
✅ social_accounts table created
2️⃣ Adding auto-posting columns to generations...
   ✅ Added auto_post_enabled
   ✅ Added auto_post_platforms
   ...
✅ AUTO-POSTING MIGRATION COMPLETE!
```

---

## 🐦 STEP 2: Twitter/X Setup

### 2.1 Create Twitter Developer Account

1. Go to https://developer.twitter.com
2. Click "Sign up" and complete the application
3. Create a new Project and App

### 2.2 Configure OAuth 2.0

1. In your Twitter app dashboard:
   - Navigate to "User authentication settings"
   - Click "Set up"
   - Select **OAuth 2.0**
   - Enable: Read, Write permissions
   
2. Set Callback URLs:
   ```
   Development: http://localhost:8000/api/auth/twitter/callback
   Production: https://yourdomain.com/api/auth/twitter/callback
   ```

3. Set Website URL:
   ```
   http://localhost:5173 (dev) or https://yourdomain.com (prod)
   ```

### 2.3 Get Credentials

1. Go to "Keys and tokens" tab
2. Copy **Client ID** and **Client Secret**

### 2.4 Add to Environment Variables

Edit `backend/.env`:

```bash
# Twitter/X OAuth 2.0
TWITTER_CLIENT_ID=your_client_id_here
TWITTER_CLIENT_SECRET=your_client_secret_here
TWITTER_REDIRECT_URI=http://localhost:8000/api/auth/twitter/callback
```

**Production:**
```bash
TWITTER_REDIRECT_URI=https://yourdomain.com/api/auth/twitter/callback
```

---

## 💼 STEP 3: LinkedIn Setup

### 3.1 Create LinkedIn App

1. Go to https://www.linkedin.com/developers
2. Click "Create app"
3. Fill in:
   - App name: "Threadangle"
   - LinkedIn Page: Your company page
   - Privacy policy URL
   - App logo (optional)

### 3.2 Configure OAuth

1. Go to "Auth" tab
2. Add **Redirect URLs**:
   ```
   http://localhost:8000/api/auth/linkedin/callback
   https://yourdomain.com/api/auth/linkedin/callback
   ```

### 3.3 Request Products

1. Go to "Products" tab
2. Request access to:
   - **Sign In with LinkedIn using OpenID Connect**
   - **Share on LinkedIn**

*Note: Access may require company verification (24-48 hours)*

### 3.4 Get Credentials

1. Go to "Auth" tab
2. Copy **Client ID** and **Client Secret**

### 3.5 Add to Environment Variables

Edit `backend/.env`:

```bash
# LinkedIn OAuth 2.0
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/auth/linkedin/callback
```

---

## 📸 STEP 4: Instagram Setup

### 4.1 Requirements

Instagram posting requires:
- **Facebook Business Page** connected to Instagram Business Account
- **Instagram Business or Creator Account** (not personal)

### 4.2 Create Facebook App

1. Go to https://developers.facebook.com
2. Click "Create App"
3. Select "Business" type
4. Fill in app details

### 4.3 Add Instagram Product

1. In app dashboard, click "Add Product"
2. Add **Instagram Basic Display** or **Instagram Graph API**
3. Add **Login with Facebook**

### 4.4 Configure OAuth

1. Go to Facebook Login → Settings
2. Add **Valid OAuth Redirect URIs**:
   ```
   http://localhost:8000/api/auth/instagram/callback
   https://yourdomain.com/api/auth/instagram/callback
   ```

### 4.5 Get Credentials

1. Go to Settings → Basic
2. Copy **App ID** and **App Secret**

### 4.6 Add to Environment Variables

Edit `backend/.env`:

```bash
# Instagram (Facebook) OAuth 2.0
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/auth/instagram/callback
```

### 4.7 Important Note

⚠️ **Instagram posting limitations:**
- The API requires actual media (image/video) upload
- For MVP, we only prepare captions - users paste manually in Instagram app
- Full automation requires media hosting and container creation

---

## 🔐 STEP 5: Generate Encryption Key

Tokens must be encrypted before database storage.

### 5.1 Generate Key

```bash
cd backend
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 5.2 Add to Environment

Copy the output and add to `backend/.env`:

```bash
# Token Encryption
ENCRYPTION_KEY=your_32_byte_key_here
```

**⚠️ CRITICAL:** Never commit this key to version control!

---

## 📦 STEP 6: Install Python Dependencies

```bash
cd backend
pip install cryptography tweepy requests --break-system-packages
```

Or update `requirements.txt`:

```txt
cryptography==41.0.7
tweepy==4.14.0
requests==2.31.0
```

Then:
```bash
pip install -r requirements.txt --break-system-packages
```

---

## ⏰ STEP 7: Setup Auto-Posting Worker

The auto-posting worker checks for scheduled posts every 5 minutes.

### 7.1 Test Manually

```bash
cd backend
python run_auto_poster.py
```

**Expected Output:**
```
============================================================
  THREADANGLE AUTO-POSTER
============================================================

🤖 AUTO-POSTING CHECK: 2026-03-12 10:00:00
============================================================
Found 0 posts to publish
No posts scheduled for this time
============================================================
```

### 7.2 Setup Cron Job (Linux/Mac)

```bash
crontab -e
```

Add:
```bash
*/5 * * * * cd /path/to/backend && /path/to/.venv/bin/python run_auto_poster.py >> /var/log/auto_poster.log 2>&1
```

### 7.3 Setup Task Scheduler (Windows)

1. Open Task Scheduler
2. Create New Task:
   - **Name:** Threadangle Auto-Poster
   - **Trigger:** Every 5 minutes
   - **Action:** Start a program
     - Program: `python`
     - Arguments: `run_auto_poster.py`
     - Start in: `F:\Threadforge\backend`

---

## ✅ STEP 8: Test the Feature

### 8.1 Start Development Servers

```bash
# Terminal 1 - Backend
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 8.2 Test OAuth Flow

1. Go to http://localhost:5173/dashboard
2. Navigate to **Settings**
3. Scroll to **Connected Accounts**
4. Click **Connect** on Twitter/X
5. Authorize the app
6. Verify you're redirected back with success message

### 8.3 Test Auto-Posting

1. Generate content on Dashboard
2. Go to **History**
3. Click **Auto-Post** button on a generation
4. Select platforms and schedule time
5. Click **Schedule Post**
6. Wait for scheduled time (or manually run `python run_auto_poster.py`)
7. Verify post appears on social media

---

## 🔍 Troubleshooting

### Twitter Connection Fails

**Error:** "Invalid OAuth state"

**Fix:**
- Check `TWITTER_CLIENT_ID` and `TWITTER_CLIENT_SECRET` in `.env`
- Verify redirect URI matches exactly (no trailing slash)
- Ensure OAuth 2.0 is enabled (not OAuth 1.0a)

### LinkedIn Requires Verification

**Error:** "Application not verified"

**Fix:**
- LinkedIn may require company page verification
- Process takes 24-48 hours
- Alternative: Use Sign In with LinkedIn (no verification needed)

### Instagram Caption Not Posting

**Expected Behavior:**
- Instagram API requires media upload (complex)
- Current implementation returns caption text
- Users manually paste in Instagram app with their video

**Future Enhancement:**
- Implement media container upload workflow
- Add image/video hosting

### Encryption Key Error

**Error:** "Token decryption failed"

**Fix:**
- Regenerate `ENCRYPTION_KEY`
- All existing tokens will be invalidated
- Users must reconnect accounts

### Auto-Poster Not Running

**Checklist:**
- [ ] Migration ran successfully
- [ ] Worker script has no syntax errors: `python run_auto_poster.py`
- [ ] Cron job/Task Scheduler configured correctly
- [ ] Database connections work
- [ ] Tokens not expired

---

## 📊 Rate Limits & Costs

### Twitter Free Tier
- **1,500 tweets per month** per app
- **50 tweets per 24 hours** per user
- First 100 users = FREE

### LinkedIn
- **No explicit limits** for standard posting
- Rate limiting applies to rapid requests

### Instagram/Facebook
- **200 API calls per hour** per user
- Media uploads count as separate calls

---

## 🎯 Production Deployment

### Environment Variables

Update production `.env`:

```bash
# Frontend URL for OAuth redirects
FRONTEND_URL=https://yourdomain.com

# Update redirect URIs
TWITTER_REDIRECT_URI=https://yourdomain.com/api/auth/twitter/callback
LINKEDIN_REDIRECT_URI=https://yourdomain.com/api/auth/linkedin/callback
FACEBOOK_REDIRECT_URI=https://yourdomain.com/api/auth/instagram/callback
```

### App URLs

Update OAuth app settings in provider dashboards with production URLs.

### Worker Deployment

**Option 1: Systemd Service (Linux)**

Create `/etc/systemd/system/threadangle-autoposter.timer`:

```ini
[Unit]
Description=Threadangle Auto-Poster Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

**Option 2: Heroku Scheduler**

Add to `Procfile`:
```
worker: python backend/run_auto_poster.py
```

**Option 3: AWS Lambda**

Deploy `run_auto_poster.py` as Lambda function with CloudWatch trigger.

---

## 🎉 Success Metrics

**You'll know it works when:**

✅ Users can connect social accounts without errors  
✅ Connected accounts appear in Settings  
✅ Auto-Post button visible in History  
✅ Scheduled posts show in database with correct time  
✅ Worker logs show "Posted to: [platform]"  
✅ Content appears on social media at scheduled time  

---

## 📚 Additional Resources

- [Twitter API Docs](https://developer.twitter.com/en/docs/twitter-api)
- [LinkedIn API Docs](https://learn.microsoft.com/en-us/linkedin/)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Tweepy Documentation](https://docs.tweepy.org/)

---

## 🆘 Support

If you encounter issues:

1. Check error logs: `tail -f /var/log/auto_poster.log`
2. Verify OAuth credentials
3. Test encryption: `python backend/utils/encryption.py`
4. Check database: `SELECT * FROM social_accounts;`
5. Review API rate limits

---

**Last Updated:** March 12, 2026  
**Version:** 1.0.0
