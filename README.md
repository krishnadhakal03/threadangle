# Threadangle — Viral Content Generator

AI-powered tool that turns any URL or text into high-performing social media content (Twitter threads, LinkedIn posts, TikTok scripts).

## HMR / Threadforge Product Roadmap Snapshot

Current product focus: turn the Hybrid Motion Renderer (HMR) breakthrough into a repeatable daily short-form video production system.

### Overall progress estimate

- **Usable production engine roadmap:** about **45–55% complete**.
- **Bigger full automation/product roadmap:** about **20–30% complete**.

### Roadmap status by area

| Roadmap Area | Status | Estimated Completion |
| --- | --- | ---: |
| Basic script → video pipeline | Mostly working | 80–90% |
| HMR rendering engine | Strong progress | 70–80% |
| Captions, audio sync, QA, review package | Strong progress | 75–85% |
| Visual realism / mixed media | Breakthrough achieved, still stabilizing | 55–65% |
| Scene intelligence architecture | Active hardening | 35–45% |
| Daily production workflow | Partially working | 40–50% |
| Analytics feedback loop | Early/manual | 15–25% |
| Autoposting / platform upload | Mostly not started | 5–15% |
| Product UI / reusable workflow | Early/prototype | 15–25% |
| AI animation / Colab GPU experiments | Backlog | 0–5% |

### Milestone view

- **Can we post decent daily videos?** About **65–70% there**.
- **Can we reliably generate postable videos without emergency engineering?** About **50–55% there**.
- **Can we run a semi-automated faceless channel system?** About **35–45% there**.
- **Can this become a reusable product/SaaS?** About **20–30% there**.

### What is already working

- Script to scenes.
- gTTS narration.
- Caption generation and semantic caption chunking.
- Audio-duration alignment.
- HMR rendering at 1080x1920.
- QA and postability reports.
- Human review packages with contact sheets.
- GitHub/Codex/TPM operating loop.
- Stock footage for hook/reveal scenes.
- Playwright proof-motion / capture for AI comparison and payoff scenes.
- Post-ready grocery candidate with technical PASS and postability STRONG_PASS.

### Main risk has changed

Earlier risk:

> Can we even make a video that looks postable?

Current risk:

> Can we make the system repeatable without turning into one-off engineering?

That means the near-term roadmap should prioritize engine stabilization, artifact safety, and analytics feedback before adding more automation complexity.

### Current priority stack

1. Finish architecture hardening, especially normalized resolved scene assets and stock/local adapter extraction.
2. Add post-ready artifact convention and manifest files.
3. Post the current grocery candidate and collect analytics.
4. Use analytics to decide the next content direction.
5. Resume Day 9 bill-leak production after engine stabilization.
6. Later: autoposting, scheduling, platform metadata automation, and product UI.

### Active / recent GitHub roadmap issues

- **#1 Hook Retention Sprint 1** — completed.
- **#2 Visual Realism Sprint 1** — superseded by Scene Intelligence work.
- **#3 Scene Intelligence Sprint 1** — active mixed-media and proof-motion work.
- **#5 Day 9 Bill Leak Money-Saving Short** — queued content production.
- **#6 Roadmap Sprint — HMR Production Stabilization** — production safety and roadmap docs.
- **#7 ResolvedSceneSpec Slice 1 — Playwright Adapter Extraction** — completed.
- **#8 ResolvedSceneSpec Slice 2 — Stock/Local Asset Adapter Extraction** — active next architecture task.

### Backlog

- Analytics tracker and performance feedback loop.
- Autoposting and scheduling.
- Platform-specific metadata generation.
- Scene override / proof clip injection.
- Local asset pack workflow.
- Colab/GPU AI animation experiments comparable to Kling, Seedance, or Runway-style generated video.

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
