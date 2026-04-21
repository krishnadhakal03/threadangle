# Stripe CLI — Local Webhook Setup

Stripe cannot deliver webhooks to `localhost` directly. The Stripe CLI acts as a proxy that
forwards Stripe events to your local backend.

---

## 1. Install Stripe CLI (Windows)

1. Download the latest Windows binary from: https://github.com/stripe/stripe-cli/releases/latest
   - Choose `stripe_X.X.X_windows_x86_64.zip`
2. Extract `stripe.exe` to a permanent folder (e.g., `C:\stripe\`)
3. Add `C:\stripe` to your **System PATH**:
   - Search "Environment Variables" in Start Menu
   - Edit **Path** under System Variables → Add `C:\stripe`
4. Verify in a new PowerShell window:
   ```powershell
   stripe --version
   ```

---

## 2. Authenticate with Your Stripe Account

```powershell
stripe login
```

- A browser window opens asking you to confirm a pairing code
- Log in with your Stripe account and click **Allow access**
- You'll see `Done! The Stripe CLI is configured for your-account@example.com`

---

## 3. Start Webhook Forwarding

Open a **dedicated PowerShell terminal** (keep it running while developing):

```powershell
stripe listen --forward-to http://localhost:8000/api/payments/webhook
```

You'll see output like:
```
> Ready! Your webhook signing secret is whsec_abc123def456... (^C to quit)
```

**Copy the `whsec_...` value** — this is your local webhook secret.

---

## 4. Update `.env` with the Local Webhook Secret

Open `F:\Threadforge\backend\.env` and set:

```env
STRIPE_WEBHOOK_SECRET=whsec_abc123def456...
```

> ⚠️ **Important:** This is a *different* secret from the production webhook secret.
> The Stripe CLI generates a temporary local secret each time `stripe listen` starts.
> Your production Stripe Dashboard uses a permanent secret — keep them separate.

---

## 5. Restart the Backend

```powershell
# In F:\Threadforge\backend with venv activated:
uvicorn main:app --reload --port 8000
```

The backend must reload after changing `.env` to pick up the new webhook secret.

---

## 6. Test the Full Payment Flow

1. Ensure three terminals are running:
   - **Terminal A**: `uvicorn main:app --reload --port 8000` (backend)
   - **Terminal B**: `stripe listen --forward-to http://localhost:8000/api/payments/webhook` (Stripe CLI)
   - **Terminal C**: `npm run dev` in `frontend/` (Vite dev server)

2. Complete a test payment using Stripe's test card:
   - Card: `4242 4242 4242 4242`
   - Expiry: any future date (e.g., `12/28`)
   - CVC: any 3 digits (e.g., `123`)

3. Watch **Terminal B** for forwarded events:
   ```
   --> checkout.session.completed [evt_xxx]
   <-- [200] POST http://localhost:8000/api/payments/webhook [evt_xxx]
   ```

4. Watch **Terminal A** for webhook processing logs:
   ```
   ================================================================================
   🔔 STRIPE WEBHOOK RECEIVED
   ✅ Webhook signature verified successfully
   📋 Event type: checkout.session.completed
   💰 Processing successful payment...
   ✅ DATABASE UPDATED: Plan: SOLO | Generations: 0/30
   🎉 PAYMENT PROCESSING COMPLETE
   ```

---

## 7. Production Webhook Setup

In production (`kriangle.com`), webhooks are configured directly in the Stripe Dashboard:

1. Go to **Stripe Dashboard → Developers → Webhooks**
2. Click **Add endpoint**
3. URL: `https://kriangle.com/api/payments/webhook`
4. Events to listen to: `checkout.session.completed`, `customer.subscription.deleted`
5. Copy the **Signing secret** shown and set it as `STRIPE_WEBHOOK_SECRET` in your production `.env`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `❌ STRIPE_WEBHOOK_SECRET not found` | Check `.env` has `STRIPE_WEBHOOK_SECRET=whsec_...` and restart backend |
| `❌ Signature verification failed` | The secret in `.env` doesn't match the one `stripe listen` printed — update it |
| No events in Stripe CLI | Make sure backend is running on port 8000 and the URL is correct |
| `[400]` response in Stripe CLI | Check backend terminal for the specific error (usually signature mismatch) |
| User plan not updating | Check backend logs for `❌ User not found` — email in Stripe must match signup email |
