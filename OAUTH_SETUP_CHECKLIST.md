# OAuth Setup Checklist: FacebookAgent Instagram
## Your Step-by-Step Action Plan

**Target:** Get Facebook + Instagram OAuth working locally by March 15  
**Final Deadline:** Production ready by March 19, 2026

---

## ✅ PHASE 1: DELETE & RECREATE APPS (15 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 1 & 2** (Steps 1-3)

- [ ] Step 1: Delete old Threadangle app from Meta Dashboard
- [ ] Step 2: Create new app (Business type)
- [ ] Step 3: Copy App ID + App Secret to `.env` file

**After this phase:**
- New Threadangle app created
- Credentials saved locally

---

## ✅ PHASE 2: CONFIGURE FACEBOOK (20 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 3 & 4** (Steps 4-6)

- [ ] Step 4: Add Facebook Login product
- [ ] Step 5: Set OAuth redirect URIs (localhost:8000)
- [ ] Step 6: Create test user + save Facebook Test User ID

**After this phase:**
- Facebook OAuth ready for local testing
- Test user created

---

## ✅ PHASE 3: CONFIGURE INSTAGRAM (20 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 4 & 5** (Steps 7-10)

- [ ] Step 7: Add Instagram Graph API product
- [ ] Step 8: Create test app + copy tokens
- [ ] Step 9: Get Instagram App ID
- [ ] Step 10: Configure webhook (you'll use ngrok URL in Step 14)

**After this phase:**
- Instagram app configured
- Tokens saved to `.env`

---

## ✅ PHASE 4: CREATE .ENV FILE (5 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 6** (Step 11)

- [ ] Step 11: Create/update `backend/.env` with all values from previous steps

**File location:** `backend/.env`

**Template provided in guide**

---

## ✅ PHASE 5: SETUP NGROK LOCAL TUNNEL (10 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 7** (Steps 12-14)

- [ ] Step 12: Download & install ngrok from https://ngrok.com/download
- [ ] Step 13: Run `ngrok http 8000` in PowerShell
- [ ] Step 14: Copy ngrok URL and update webhook URL in Meta Dashboard

**After this phase:**
- Your localhost:8000 is exposed to public internet via ngrok tunnel
- Webhook URL updated in Meta Dashboard

---

## ✅ PHASE 6: CREATE WEBHOOK ENDPOINT (5 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 8** (Steps 15-16)

- [ ] Step 15: FILE CREATED → `backend/routes/webhooks.py` ✅ (already done for you)
- [ ] Step 16: Update `backend/main.py` to register the webhook router

**What to add to `backend/main.py`:**
```python
from routes.webhooks import router as webhooks_router

# Inside your FastAPI app setup:
app.include_router(webhooks_router)
```

---

## ✅ PHASE 7: TEST WEBHOOK VERIFICATION (15 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 9** (Steps 17-19)

- [ ] Step 17: Start backend server (`python start_backend.py`)
- [ ] Step 18: Click "Test" in Meta Dashboard → Instagram Configuration
- [ ] Step 19: Check backend logs for "✅ Webhook verified successfully!"

**Expected in logs:**
```
✅ Webhook verified successfully!
```

---

## ✅ PHASE 8: ADD OAUTH ENDPOINTS (15 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 10 & 11** (Steps 20-21)

- [ ] Step 20: Add Facebook OAuth routes to `backend/routes/auth.py`
- [ ] Step 21: Add Instagram OAuth routes to `backend/routes/auth.py`

**OR:** Copy the code from the guide into your auth.py file

---

## ✅ PHASE 9: TEST LOCAL OAUTH FLOW (20 minutes)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 12** (Steps 22-25)

**Setup:**
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] ngrok still running

**Tests:**
- [ ] Step 23: Connect Facebook from Settings
- [ ] Step 24: Connect Instagram from Settings
- [ ] Step 25: Schedule content with auto-posting enabled

**Expected:**
- Both show "Connected ✓" with green checkmarks
- Schedule creates successfully

---

## 🚀 PHASE 10: PREPARE FOR PRODUCTION (Coming after local testing works)
Read **OAUTH_SETUP_GUIDE.md** → **PHASE 13** (Steps 26-28)

- [ ] Get SSL certificate for kriangle.com
- [ ] Update Meta Dashboard for HTTPS URLs
- [ ] Deploy backend to production
- [ ] Update `.env.production` with kriangle.com URLs

---

## 🆘 TROUBLESHOOTING QUICK REFERENCE

**Problem: Webhook won't verify**
→ Check TROUBLESHOOTING CHECKLIST in OAUTH_SETUP_GUIDE.md

**Problem: OAuth redirect not working**
→ Check redirect URIs match exactly in Meta Dashboard

**Problem: Access token invalid**
→ Verify app secret and token scope in guide

---

## 📋 QUICK COMMANDS

```powershell
# Start ngrok tunnel
ngrok http 8000

# Start backend (from backend/ folder)
python start_backend.py

# Start frontend (from frontend/ folder)
npm run dev

# View backend logs
# (Check the terminal where start_backend.py is running)
```

---

## 📌 IMPORTANT NOTES

1. **ngrok URL changes every restart** - Update Meta Dashboard webhook if you restart ngrok
2. **Test accounts are temporary** - They work for 90 days then need renewal
3. **Keep .env secret** - Never commit to Git
4. **Use https for production** - Instagram requires HTTPS on production
5. **Webhook verify token** - Must match exactly between .env and Meta Dashboard

---

## ✨ ESTIMATED TIMELINE

- **Today (Phase 1-4):** 1 hour → Apps & .env created
- **Today (Phase 5-7):** 30 minutes → Webhook tested
- **Today (Phase 8-9):** 1.5 hours → OAuth endpoints & testing
- **Remaining (Phase 10):** 1 hour → Production deployment

**Total: ~4 hours to full OAuth working**

---

## 📞 WHERE TO GET HELP

1. **Can't find something in Meta Dashboard?** → Check OAUTH_SETUP_GUIDE.md screenshots section
2. **Webhook verification failing?** → Check TROUBLESHOOTING section
3. **Code questions?** → See code examples in OAUTH_SETUP_GUIDE.md

---

**Start with Step 1 and work your way down the checklist! 🚀**
