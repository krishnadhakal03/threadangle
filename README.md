# Threadangle — Viral Content Generator

AI-powered tool that turns any URL or text into high-performing social media content (Twitter threads, LinkedIn posts, TikTok scripts).

## 🚀 Deployment Checklist

### 1. Server Setup
- [ ] AWS EC2 Ubuntu 22.04 instance running.
- [ ] Domain `kriangle.com` pointing to EC2 Elastic IP.
- [ ] Run `backend/server-setup.sh` on the server.
- [ ] Update `.env` with production keys:
  - `ANTHROPIC_API_KEY`
  - `STRIPE_SECRET_KEY`
  - `JWT_SECRET`
  - `STRIPE_PRO_PRICE_ID`
  - etc.

### 2. Nginx & SSL
- [ ] Copy `nginx.conf` to `/etc/nginx/sites-available/threadangle`.
- [ ] Symlink to `sites-enabled`.
- [ ] Run `sudo certbot --nginx -d kriangle.com -d www.kriangle.com` for free SSL.

### 3. Stripe Webhooks
- [ ] Configure Stripe dashboard webhook to: `https://kriangle.com/api/payments/webhook`.
- [ ] Subscribe to `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`.

### 4. Post-Launch Tests
- [ ] Landing page loads over HTTPS.
- [ ] Signup/Login flow works.
- [ ] Public Hook Generator handles rate limits.
- [ ] AI generation works with a real URL.
- [ ] Sidebar usage bar correctly updates.

---
Built with FastAPI, React, Tailwind CSS, and Anthropic Claude.
