import { useState } from "react";

const SESSIONS = [
  {
    id: "setup", label: "01 · Setup", icon: "⚙️",
    title: "Project Scaffold", subtitle: "Run this first. Creates the entire project structure.",
    duration: "~30 min", difficulty: "Easy",
    prompt: `You are a senior full-stack developer. Build me a complete project called Threadangle.

TECH STACK:
- Backend: Python FastAPI
- Frontend: React 18 + Tailwind CSS
- Database: SQLite (single file, no external DB needed)
- AI: Anthropic Claude API (claude-haiku-4-5-20251001)
- Auth: JWT tokens (python-jose)
- Payments: Stripe

CREATE THIS EXACT FOLDER STRUCTURE:
threadangle/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── generate.py
│   │   └── payments.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── pages/
│   │   │   ├── Landing.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Pricing.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ThreadOutput.jsx
│   │   │   └── UsageBar.jsx
│   │   └── utils/
│   │       └── api.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── index.html
├── .gitignore
└── README.md

DATABASE TABLES (SQLite):
1. users: id, email, password_hash, plan (free/starter/pro), usage_count, usage_reset_date, stripe_customer_id, created_at
2. generations: id, user_id, input_type, input_content, twitter_output, linkedin_output, tiktok_output, hashtags, created_at
3. subscriptions: id, user_id, stripe_subscription_id, plan, status, current_period_end

RULES:
- Use SQLite with aiosqlite for async
- All API routes prefixed with /api
- CORS enabled for localhost:3000 and production domain
- Load all config from .env file, never hardcode keys
- Add error handling on every endpoint
- Pin all dependency versions in requirements.txt

Create all files with working boilerplate code now.`
  },
  {
    id: "core-ai", label: "02 · AI Core", icon: "🧠",
    title: "Thread Generation Engine", subtitle: "The heart of Threadangle — AI turns any URL or text into social content.",
    duration: "~1 hour", difficulty: "Medium",
    prompt: `In backend/routes/generate.py, build the complete content generation endpoint.

ENDPOINT: POST /api/generate
AUTH: Required (JWT Bearer token)

REQUEST BODY:
{
  "input_type": "url" or "text",
  "content": "https://blog-url.com or plain text",
  "platforms": ["twitter", "linkedin", "tiktok"],
  "tone": "professional" or "casual" or "viral" or "educational"
}

STEP 1 — CONTENT EXTRACTION:
If input_type is "url":
  - Fetch URL with httpx
  - Parse with BeautifulSoup, extract main article text
  - Strip nav, footer, ads, HTML tags
  - Truncate to 3000 characters max
If input_type is "text":
  - Use directly, truncate to 3000 chars

STEP 2 — CALL ANTHROPIC API:
Model: claude-haiku-4-5-20251001
Max tokens: 2000

System prompt:
"You are an expert social media content strategist. Transform content into platform-perfect posts. Output valid JSON only. No markdown, no explanation."

User prompt:
"Transform this content into social posts.
Tone: {tone}
Content: {extracted_content}

Return JSON (include only requested platforms):
{
  'twitter': {
    'hook': 'Opening tweet max 280 chars',
    'thread': ['Tweet 1','Tweet 2','Tweet 3','Tweet 4','Tweet 5','Tweet 6','Tweet 7','Tweet 8 with CTA'],
    'hashtags': ['tag1','tag2','tag3','tag4','tag5']
  },
  'linkedin': {
    'title': 'Attention-grabbing first line',
    'body': '200-300 word post, professional, ends with question',
    'hashtags': ['tag1','tag2','tag3']
  },
  'tiktok': {
    'hook_line': 'First 3 seconds spoken text',
    'script': {
      'hook': '0-3s text',
      'problem': '3-15s text',
      'solution': '15-40s text',
      'cta': '40-45s text'
    },
    'on_screen_text': ['Overlay 1','Overlay 2','Overlay 3'],
    'caption': 'Under 150 chars',
    'hashtags': ['tag1','tag2','tag3','tag4','tag5']
  }
}"

STEP 3 — USAGE LIMITS:
Before generating:
- free plan: max 3 per month → return 403 if hit
- starter/pro: unlimited
After success: increment user.usage_count in DB
Reset usage_count monthly when date > usage_reset_date

STEP 4 — SAVE TO DB:
Save full generation to generations table.

STEP 5 — RETURN:
{
  "success": true,
  "data": { ...ai output },
  "usage": { "used": 2, "limit": 3, "plan": "free", "resets_on": "2026-04-01" }
}

ERRORS:
- URL fetch fails → 400 "Could not read content from this URL"
- AI fails → 500 "Generation failed, please try again"  
- Bad JSON from AI → retry once then 500

Install packages: anthropic httpx beautifulsoup4 aiosqlite`
  },
  {
    id: "auth", label: "03 · Auth", icon: "🔐",
    title: "Authentication System", subtitle: "Signup, login, JWT tokens, and protected route middleware.",
    duration: "~45 min", difficulty: "Easy",
    prompt: `Build the full authentication system for Threadangle.

BACKEND — backend/routes/auth.py:

POST /api/auth/signup
Body: { "email": "...", "password": "..." }
- Validate email format
- Return 409 if email already registered
- Hash password with bcrypt (12 rounds)
- Create user: plan="free", usage_count=0, usage_reset_date=1st of next month
- Return: { "token": "jwt...", "user": { "email", "plan", "usage_count" } }

POST /api/auth/login
Body: { "email": "...", "password": "..." }
- Return 401 if user not found
- Verify bcrypt hash
- Return: { "token": "jwt...", "user": { "email", "plan", "usage_count" } }

GET /api/auth/me
Auth: Required
Return: { "email", "plan", "usage_count", "usage_limit", "resets_on" }

JWT CONFIG:
- Secret: JWT_SECRET env var
- Algorithm: HS256
- Expiry: 30 days
- Payload: { "user_id": 1, "email": "...", "exp": timestamp }

DEPENDENCY — get_current_user:
- Extract from Authorization: Bearer <token>
- Decode and validate JWT
- Fetch user from DB
- Raise HTTP 401 if missing, invalid, or expired

FRONTEND — src/utils/api.js:
- Store JWT in React context state (NOT localStorage)
- Auto-attach token to every request header
- Redirect to /login on any 401 response
- Export: signup(), login(), logout(), getMe()

AUTHCONTEXT — src/context/AuthContext.jsx:
- Wraps entire app
- Holds current user state
- Exposes login/logout functions
- Redirects unauthenticated users away from /dashboard

Password rule: minimum 8 characters. Always return specific error messages.`
  },
  {
    id: "frontend", label: "04 · Frontend", icon: "🎨",
    title: "Complete UI", subtitle: "Landing page, dashboard, and all screens built with React + Tailwind.",
    duration: "~2 hours", difficulty: "Medium",
    prompt: `Build the complete React frontend for Threadangle.

DESIGN SYSTEM:
- Dark theme: bg #0F0F0F, cards #1A1A1A, borders #2A2A2A
- Accent blue: #3B82F6
- Success green: #10B981
- Error red: #EF4444
- Font: Google Fonts "Plus Jakarta Sans"
- Style: clean modern SaaS, professional not flashy

--- LANDING PAGE (src/pages/Landing.jsx) ---

HERO:
- H1: "Turn Any Content Into Viral Social Posts — In Seconds"
- Subtitle: "Paste a URL or text. Get a Twitter thread, LinkedIn post, and TikTok script instantly. No writing required."
- Button: "Start Free — No Credit Card" → /signup
- Social proof text: "Join 1,200+ creators saving 5+ hours per week"

HOW IT WORKS (3 columns):
1. Paste — Drop in your blog URL or any text
2. Choose — Select platforms and tone
3. Create — Get ready-to-post content in 20 seconds

PLATFORMS SECTION: Icons for Twitter/X, LinkedIn, TikTok, Instagram Reels

PRICING PREVIEW: Free / $12 Starter / $19 Pro

BOTTOM CTA: "Create My Free Account" → /signup

--- DASHBOARD (src/pages/Dashboard.jsx) ---

LAYOUT: Left sidebar 200px + main content area

SIDEBAR:
- Threadangle logo
- Nav links: Generate, History, Settings
- Upgrade button (highlighted yellow if free plan)
- Bottom: plan badge + usage bar "2 of 3 uses this month"

MAIN — INPUT CARD:
- Tab toggle: URL | Text
- URL mode: single input field
- Text mode: large textarea
- Platform checkboxes: Twitter/X Thread, LinkedIn Post, TikTok Script (Pro badge if free)
- Tone radio: Professional, Casual, Viral, Educational (each with short description)
- "Generate Content ⚡" full-width blue button
- Loading state: spinner + "Generating your content..."

MAIN — OUTPUT SECTION (tabs per platform):
Twitter tab:
- Each tweet as its own numbered card (Tweet 1/8, 2/8...)
- Copy button on each tweet
- "Copy All" button at top
- Hashtags as blue pill chips

LinkedIn tab:
- Formatted post with line breaks preserved
- "Copy Post" button
- Hashtags as chips

TikTok tab:
- 4 color-coded blocks:
  Hook = red bg, Problem = orange bg, Solution = blue bg, CTA = green bg
- Duration label on each block
- "Copy Full Script" button

All output tabs: "Regenerate ↺" button

USAGE BAR COMPONENT:
- "X of 3 free uses this month"
- Colored progress bar (green→yellow→red)
- "Resets on April 1" text
- If limit hit: red banner "Upgrade to continue generating"

--- PRICING PAGE (src/pages/Pricing.jsx) ---
3 cards. Pro marked "Most Popular".
Free: 3 gens/month, 2 platforms → "Get Started Free"
Starter $12: Unlimited, all platforms → "Upgrade Now"  
Pro $19: Everything + TikTok scripts + Priority → "Upgrade Now"

--- LOGIN/SIGNUP ---
Centered form, dark card, email + password fields.
Inline red error messages. Toggle between login/signup.

RULES:
- All API calls show loading spinner while waiting
- Copy buttons show "Copied ✓" for 2 seconds
- Fully mobile responsive
- Empty dashboard state: "Paste a URL above to get started ↑"
- All page transitions: 100ms ease fade`
  },
  {
    id: "payments", label: "05 · Payments", icon: "💳",
    title: "Stripe Integration", subtitle: "Subscriptions, checkout, webhooks, and customer portal.",
    duration: "~1 hour", difficulty: "Medium",
    prompt: `Integrate Stripe into Threadangle for subscription payments.

BACKEND — backend/routes/payments.py:

POST /api/payments/create-checkout
Auth: Required
Body: { "plan": "starter" or "pro" }
- Get or create Stripe customer for this user
- Create Stripe Checkout Session:
  starter → STRIPE_STARTER_PRICE_ID ($12/mo)
  pro → STRIPE_PRO_PRICE_ID ($19/mo)
  success_url: http://localhost:3000/dashboard?upgraded=true
  cancel_url: http://localhost:3000/pricing
  metadata: { "user_id": user.id, "plan": plan }
- Return: { "checkout_url": "https://checkout.stripe.com/..." }

POST /api/payments/webhook
No auth. Verify Stripe-Signature header.
Use STRIPE_WEBHOOK_SECRET from .env.
Return 400 if signature invalid.

Events to handle:
1. checkout.session.completed
   → Update user.plan in DB
   → Save stripe_customer_id
   → Create subscription record
   → Reset usage_count to 0

2. customer.subscription.deleted
   → Downgrade user.plan to "free"
   → Update subscription status to cancelled

3. invoice.payment_failed
   → Log only. No immediate downgrade.

GET /api/payments/portal
Auth: Required
→ Create Stripe Customer Portal session
→ Return { "portal_url": "..." }

FRONTEND:
Pricing page "Upgrade Now":
1. Call POST /api/payments/create-checkout
2. Receive checkout_url
3. window.location.href = checkout_url (Stripe takes over)

After redirect back with ?upgraded=true:
- Show green banner: "You're now on Pro! Enjoy unlimited generations."
- Re-fetch user data to show new plan

Settings page:
- "Manage Subscription" button → calls /api/payments/portal → redirect

MANUAL SETUP STEPS (do these in Stripe dashboard first):
1. Create product "Threadangle Starter" — $12/month recurring
2. Create product "Threadangle Pro" — $19/month recurring  
3. Copy both Price IDs to .env
4. Test card: 4242 4242 4242 4242 | any future date | any CVC
5. Test webhooks locally: stripe listen --forward-to localhost:8000/api/payments/webhook`
  },
  {
    id: "tiktok", label: "06 · TikTok", icon: "🎬",
    title: "TikTok & Reels Scripts", subtitle: "Enhanced Pro-only video script generator with full breakdown.",
    duration: "~30 min", difficulty: "Easy",
    prompt: `Enhance the TikTok feature in Threadangle. Pro users only.

UPDATE the TikTok section of the AI prompt in generate.py:

Replace tiktok output with this enhanced structure:
{
  "tiktok": {
    "hook_line": "Single sentence for first 3 seconds. Must create pattern interrupt. Examples: 'Nobody tells you this about X', 'I wasted 3 years until I learned this', 'This one thing changed everything'",
    
    "full_script": "Complete word-for-word spoken script, 45-60 seconds at normal pace",
    
    "script_breakdown": {
      "hook":     { "duration": "0-3 seconds",   "text": "exact words to say" },
      "problem":  { "duration": "3-15 seconds",  "text": "exact words to say" },
      "solution": { "duration": "15-40 seconds", "text": "exact words to say" },
      "cta":      { "duration": "40-50 seconds", "text": "exact words to say" }
    },
    
    "on_screen_text": [
      { "timing": "0-3s",  "text": "Bold overlay for hook",   "style": "large centered" },
      { "timing": "5-10s", "text": "Key stat or claim",       "style": "bottom third" },
      { "timing": "15s+",  "text": "Main insight highlighted","style": "large centered" },
      { "timing": "40s+",  "text": "CTA with arrow emoji",    "style": "bottom" }
    ],
    
    "b_roll_suggestions": [
      "What to show during hook section",
      "What to show during problem",
      "What to show during solution"
    ],
    
    "caption": "Under 150 chars with hook element",
    "hashtags": ["niche","trending","topic","audience","viral"],
    "thumbnail_text": "Text for thumbnail to maximize clicks"
  }
}

FRONTEND — TikTok tab update:

Show script_breakdown as 4 color blocks:
- Hook block: bg #7F1D1D (dark red)
- Problem block: bg #7C2D12 (dark orange)  
- Solution block: bg #1E3A5F (dark blue)
- CTA block: bg #14532D (dark green)
Each block shows: duration badge + exact script text (large, readable)

Show full_script in single copyable textarea

Show on_screen_text as list:
[timing] | "text" | style note

Show b_roll_suggestions as numbered list with 🎥 prefix

PRO GATE for free users:
- TikTok checkbox grayed out with gold "Pro" badge
- If free user clicks TikTok: show blurred content overlay
- Center modal: "Unlock TikTok & Reels Scripts — Upgrade to Pro $19/mo"
- "Upgrade Now" button → /pricing`
  },
  {
    id: "seo", label: "07 · SEO Tool", icon: "🔍",
    title: "Free Hook Generator", subtitle: "No-login public tool page to drive Google SEO traffic.",
    duration: "~45 min", difficulty: "Easy",
    prompt: `Create a free public tool page for SEO. No login required at all.

PAGE: src/pages/FreeHookGenerator.jsx
ROUTE: /free-hook-generator
PURPOSE: Ranks on Google for "twitter hook generator free". Users try it free then sign up.

THE TOOL UI:
- Textarea: "What is your post about?"
  Placeholder: "e.g. How I grew Twitter from 0 to 10k followers in 6 months"
- Dropdown: Category
  Options: Marketing, Business, Personal Development, Tech, Finance, Health, Other
- Big button: "Generate 5 Free Hooks ⚡"
- No login wall. Works immediately.

BACKEND: POST /api/free/generate-hooks
No authentication required.
Rate limit: 3 requests per IP per hour (use slowapi library)
Body: { "topic": "...", "category": "..." }

Anthropic prompt:
"Generate 5 viral Twitter hook lines about: {topic}
Category: {category}

Each hook must use a different psychological trigger.
Return JSON only, no explanation:
{
  'hooks': [
    {'type': 'Curiosity Gap',  'text': '...', 'why_it_works': 'one sentence'},
    {'type': 'Bold Claim',     'text': '...', 'why_it_works': 'one sentence'},
    {'type': 'Personal Story', 'text': '...', 'why_it_works': 'one sentence'},
    {'type': 'Number/Stat',    'text': '...', 'why_it_works': 'one sentence'},
    {'type': 'Pain Point',     'text': '...', 'why_it_works': 'one sentence'}
  ]
}"

OUTPUT DISPLAY:
Each hook as a card:
- Colored type badge (different color per type)
- Hook text large and prominent
- "Why it works" in small gray text below
- "Copy" button (shows "Copied ✓" for 2s)

AFTER RESULTS — show upgrade callout box:
Text: "Want the full thread? Threadangle turns this hook into a complete Twitter thread + LinkedIn post + TikTok script in 20 seconds."
Button: "Try Threadangle Free — No Credit Card Required" → /signup

SEO TAGS (add to page <head>):
Title: "Free Twitter Hook Generator — Create Viral Hooks Instantly"
Description: "Generate 5 viral Twitter hook variations for any topic instantly. Free, no signup required. AI-powered."

H1 on page: "Free Twitter Hook Generator"
Keep the tool visible above the fold.
Add "Free Tools" link to main navbar and footer.`
  },
  {
    id: "deploy", label: "08 · Deploy", icon: "🚀",
    title: "Deploy to EC2", subtitle: "Get Threadangle live on kriangle.com on your existing Ubuntu server.",
    duration: "~1 hour", difficulty: "Medium",
    prompt: `Create deployment scripts for my AWS EC2 Ubuntu server.

MY SETUP:
- Ubuntu 22.04 EC2 t3.micro (single server, everything runs here)
- SQLite database stored locally on the server
- SSH access via key pair
- Domain: kriangle.com already pointing to this server IP

CREATE FILE 1 — server-setup.sh (run ONCE on a fresh server):
#!/bin/bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip git nginx -y
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
sudo npm install -g pm2
mkdir -p /var/www/threadangle

git clone https://github.com/YOUR_USERNAME/threadangle.git /home/ubuntu/threadangle

cd /home/ubuntu/threadangle/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env — fill in values manually after this script
cat > .env << 'EOF'
ANTHROPIC_API_KEY=paste_your_key_here
STRIPE_SECRET_KEY=paste_your_stripe_key
STRIPE_WEBHOOK_SECRET=paste_webhook_secret
STRIPE_STARTER_PRICE_ID=price_paste_here
STRIPE_PRO_PRICE_ID=price_paste_here
JWT_SECRET=paste_long_random_string_here
DATABASE_URL=./threadangle.db
ENVIRONMENT=production
EOF

pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name threadangle-api
pm2 save && pm2 startup

cd /home/ubuntu/threadangle/frontend
npm install && npm run build
sudo cp -r dist/* /var/www/threadangle/
echo "Server setup complete! Edit .env file now."

CREATE FILE 2 — deploy.sh (run from your LOCAL machine to push updates):
#!/bin/bash
SERVER="ubuntu@YOUR_EC2_IP_HERE"
echo "Pushing code..."
git add -A && git commit -m "Deploy $(date +%Y-%m-%d)" && git push origin main
echo "Deploying on server..."
ssh $SERVER << 'DONE'
  cd /home/ubuntu/threadangle
  git pull origin main
  cd backend && source venv/bin/activate && pip install -r requirements.txt
  pm2 restart threadangle-api
  cd ../frontend && npm install && npm run build
  sudo cp -r dist/* /var/www/threadangle/
  echo "Deployed successfully!"
DONE

CREATE FILE 3 — nginx config (save to /etc/nginx/sites-available/threadangle):
server {
    listen 80;
    server_name kriangle.com www.kriangle.com;

    # Serve React frontend
    location / {
        root /var/www/threadangle;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API to FastAPI backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}

AFTER NGINX SETUP — enable and get free SSL:
sudo ln -s /etc/nginx/sites-available/threadangle /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d kriangle.com -d www.kriangle.com

LAUNCH CHECKLIST (add to README.md):
[ ] kriangle.com loads the landing page
[ ] /signup creates account successfully  
[ ] Generation works with a real blog URL
[ ] Stripe webhook URL set to: kriangle.com/api/payments/webhook
[ ] HTTPS green lock shows in browser
[ ] pm2 status shows threadangle-api as "online"
[ ] Tested on a mobile phone`
  },
  {
    id: "launch", label: "09 · Launch", icon: "📣",
    title: "Launch & Marketing", subtitle: "Use these prompts with Claude/ChatGPT to generate all launch content.",
    duration: "~1 hour", difficulty: "Easy",
    prompt: `Use each prompt below with Claude or ChatGPT to generate your launch content.

════════════════════════════════════
PROMPT 1 — Reddit r/SideProject Post
════════════════════════════════════
Write a Reddit post for r/SideProject announcing my tool Threadangle.

Facts:
- I am a solo developer, built this in [X] weeks
- It turns any blog URL into a Twitter thread + LinkedIn post + TikTok script in 20 seconds
- Powered by Claude AI
- Free tier: 3 generations/month, no credit card required
- Paid plans: $12–19/month for unlimited
- Live at: kriangle.com

Requirements:
- First person voice, genuine builder tone
- NOT marketing language — Reddit hates that
- Include: what I built, why I built it, what's different, honest limitations
- End with a question that invites comments
- Length: 300–400 words maximum

════════════════════════════════════
PROMPT 2 — Product Hunt Launch
════════════════════════════════════
Write a Product Hunt launch page for Threadangle.
- Tagline: 60 characters max
- Description: 200–300 words
- Tone: genuinely excited but honest
- Must include: the core problem, the solution, 3 key features, free tier mention
- End with what feedback I'm looking for
- Should make a creator or solopreneur think "I need this right now"

════════════════════════════════════
PROMPT 3 — TikTok Promo Video Script
════════════════════════════════════
Write a 45-second TikTok video script to show off Threadangle.
Screen recording only. No face required.

Structure:
0-3s: Show a long blog post on screen
3-15s: Voiceover "Every week I spend hours turning my content into social posts"
15-35s: Show the tool in action — URL goes in, full thread comes out in real time
35-42s: Show the polished finished output
42-45s: Text on screen: "Link in bio — first 3 are free"

Provide: on-screen text for each segment, full caption, and hashtags.

════════════════════════════════════
PROMPT 4 — Twitter/X Launch Thread
════════════════════════════════════
Write my 10-tweet launch thread for Threadangle.

Tweet 1: Surprising hook — stat about how long creators spend on content distribution
Tweets 2–3: The problem I personally experienced
Tweets 4–5: What I built and how it works
Tweet 6: A before/after example (long blog → clean thread)
Tweet 7: The free tier and how to try it
Tweet 8: The paid plans
Tweet 9: Link to kriangle.com
Tweet 10: Ask creators to retweet if they'd use this

Tone: developer sharing a side project, not a company announcement.

════════════════════════════════════
PROMPT 5 — Cold Email to Micro-Creators
════════════════════════════════════
Write a cold email offering free Pro access to Threadangle to creators with 5,000–50,000 followers.

Requirements:
- Subject: under 50 characters, sparks curiosity
- Body: under 150 words total
- Include placeholders: [CREATOR NAME] and [THEIR NICHE]
- No pressure, no fake urgency, no guaranteed results
- Clear ask: try it free, share if you love it, zero obligation
- My name as founder in signature

════════════════════════════════════
PROMPT 6 — SEO Blog Article
════════════════════════════════════
Write a 1,500-word SEO article:
Title: "How to Turn a Blog Post Into a Twitter Thread (Fast Way in 2026)"

Target keyword: blog post to twitter thread
Secondary keywords: twitter thread generator, content repurposing, AI writing tool

Structure:
- Intro: Manual repurposing takes too long
- H2: Why threads outperform single tweets (use real stats)
- H2: The manual step-by-step method (genuine value, no tool mention)
- H2: How to do it with AI in 30 seconds (mention Threadangle naturally here, not as an ad)
- H2: Writing hooks that actually get clicks
- Conclusion: soft CTA to try the free tier

Rule: Threadangle mention should be 20% of the article or less. Write genuinely useful content first.`
  }
];

const STACK = [
  { name: "FastAPI", role: "Backend API server", cost: "Free", color: "#10B981" },
  { name: "React 18", role: "Frontend UI", cost: "Free", color: "#3B82F6" },
  { name: "SQLite", role: "Database (local file on server)", cost: "Free", color: "#8B5CF6" },
  { name: "Claude Haiku 4.5", role: "AI content generation", cost: "~$0.006 per generation", color: "#F59E0B" },
  { name: "Stripe", role: "Subscriptions & payments", cost: "2.9% + $0.30 per charge", color: "#6366F1" },
  { name: "Tailwind CSS", role: "UI styling", cost: "Free", color: "#06B6D4" },
  { name: "JWT / python-jose", role: "User auth tokens", cost: "Free", color: "#EC4899" },
  { name: "Nginx", role: "Web server & reverse proxy", cost: "Free", color: "#84CC16" },
  { name: "PM2", role: "Keep backend running 24/7", cost: "Free", color: "#F97316" },
  { name: "Let's Encrypt", role: "Free HTTPS / SSL certificate", cost: "Free", color: "#14B8A6" },
];

const TIMELINE = [
  { day: "Day 1",    task: "Run Session 01. Verify all folders created and backend starts on localhost:8000.", session: "01 Setup" },
  { day: "Day 2",    task: "Run Session 02. Test URL → thread generation works via Postman or curl.", session: "02 AI Core" },
  { day: "Day 3",    task: "Run Session 03. Test signup and login in browser. Check JWT token returned.", session: "03 Auth" },
  { day: "Day 4–5",  task: "Run Session 04. Click every page. Check mobile. Fix anything visually broken.", session: "04 Frontend" },
  { day: "Day 6",    task: "Create Stripe products manually. Run Session 05. Test with card 4242 4242 4242 4242.", session: "05 Payments" },
  { day: "Day 7",    task: "Run Session 06. Test TikTok output. Verify free users see Pro upgrade prompt.", session: "06 TikTok" },
  { day: "Day 8",    task: "Run Session 07. Test hook generator without login. Check IP rate limiting works.", session: "07 SEO Tool" },
  { day: "Day 9–10", task: "Use every feature yourself aggressively. Copy errors, paste back to AI to fix.", session: "Polish" },
  { day: "Day 11",   task: "Run Session 08. SSH into EC2, run server-setup.sh, verify kriangle.com loads.", session: "08 Deploy" },
  { day: "Day 12",   task: "Test everything on live server. SSL, payments, generation. Fix any prod bugs.", session: "Verify" },
  { day: "Day 13",   task: "Use Session 09 prompts to generate Reddit post, TikTok script, Twitter thread.", session: "09 Content" },
  { day: "Day 14",   task: "🚀 LAUNCH — Post Reddit, record TikTok, post Twitter thread, submit Product Hunt.", session: "Go Live" },
  { day: "Week 3–4", task: "Reply to every comment. Fix every bug users report. Ship one new small feature.", session: "Iterate" },
  { day: "Month 2",  task: "Publish first 2 SEO articles. Post 3x/week on TikTok. Aim for 10 paid users.", session: "Grow" },
];

export default function App() {
  const [session, setSession] = useState("setup");
  const [mainTab, setMainTab] = useState("prompts");
  const [copied, setCopied] = useState(false);

  const cur = SESSIONS.find(s => s.id === session);

  const copy = () => {
    navigator.clipboard.writeText(cur.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const diffColor = d => ({ Easy: "#10B981", Medium: "#F59E0B", Hard: "#EF4444" }[d] || "#888");

  const styles = {
    app: { fontFamily: "system-ui,-apple-system,sans-serif", background: "#09090B", minHeight: "100vh", color: "#E4E4E7", display: "flex", flexDirection: "column", fontSize: 13 },
    topbar: { background: "#111113", borderBottom: "1px solid #27272A", padding: "0 16px", height: 48, display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 },
    logo: { display: "flex", alignItems: "center", gap: 8 },
    logoBadge: { background: "#3B82F6", borderRadius: 6, width: 24, height: 24, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12 },
    logoText: { fontWeight: 700, color: "#FAFAFA", fontSize: 14 },
    tag: { background: "#18181B", border: "1px solid #3F3F46", color: "#71717A", fontSize: 10, padding: "2px 6px", borderRadius: 4 },
    tabs: { display: "flex", gap: 3 },
    body: { display: "flex", flex: 1, overflow: "hidden" },
    sidebar: { width: 190, background: "#111113", borderRight: "1px solid #27272A", overflowY: "auto", flexShrink: 0 },
    sideLabel: { padding: "10px 12px 5px", fontSize: 9, color: "#52525B", letterSpacing: 2, fontWeight: 600 },
    main: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" },
    header: { padding: "14px 18px", borderBottom: "1px solid #18181B", background: "#0D0D0F", flexShrink: 0 },
    headerRow: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 },
    titleRow: { display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" },
    h2: { fontSize: 15, fontWeight: 700, color: "#FAFAFA" },
    subtitle: { fontSize: 12, color: "#71717A" },
    copyBtn: { border: "none", color: "#fff", padding: "7px 13px", borderRadius: 7, fontSize: 12, cursor: "pointer", fontFamily: "inherit", fontWeight: 600, flexShrink: 0 },
    tip: { marginTop: 10, background: "#18181B", border: "1px solid #27272A", borderRadius: 7, padding: "8px 12px", display: "flex", gap: 8, alignItems: "flex-start" },
    tipText: { fontSize: 11, color: "#A1A1AA", lineHeight: 1.6 },
    promptArea: { flex: 1, padding: "14px 18px" },
    promptHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 },
    promptLabel: { fontSize: 10, color: "#52525B", letterSpacing: 1.5, fontWeight: 600 },
    promptBox: { background: "#0D0D0F", border: "1px solid #27272A", borderRadius: 8, padding: "13px 15px" },
    pre: { fontSize: 12, color: "#D4D4D8", whiteSpace: "pre-wrap", wordBreak: "break-word", lineHeight: 1.75, fontFamily: "Consolas,'Courier New',monospace" },
    scrollPad: { flex: 1, overflowY: "auto", padding: "18px 20px" },
    card: { background: "#111113", border: "1px solid #27272A", borderRadius: 8, padding: "12px 14px" },
  };

  const TabBtn = ({ id, label }) => (
    <button onClick={() => setMainTab(id)} style={{
      background: mainTab === id ? "#27272A" : "transparent",
      border: `1px solid ${mainTab === id ? "#3F3F46" : "transparent"}`,
      color: mainTab === id ? "#FAFAFA" : "#71717A",
      padding: "4px 11px", borderRadius: 6, fontSize: 12,
      cursor: "pointer", fontFamily: "inherit", fontWeight: 500,
    }}>{label}</button>
  );

  const SideBtn = ({ s }) => (
    <button onClick={() => setSession(s.id)} style={{
      width: "100%", background: session === s.id ? "#18181B" : "transparent",
      border: "none", borderLeft: `2px solid ${session === s.id ? "#3B82F6" : "transparent"}`,
      padding: "8px 11px", textAlign: "left", cursor: "pointer",
      display: "flex", alignItems: "center", gap: 8,
    }}>
      <span style={{ fontSize: 14 }}>{s.icon}</span>
      <div>
        <div style={{ fontSize: 11, fontWeight: 600, color: session === s.id ? "#FAFAFA" : "#A1A1AA" }}>{s.label}</div>
        <div style={{ fontSize: 10, color: "#52525B" }}>{s.duration}</div>
      </div>
    </button>
  );

  return (
    <div style={styles.app}>
      {/* Topbar */}
      <div style={styles.topbar}>
        <div style={styles.logo}>
          <div style={styles.logoBadge}>⚡</div>
          <span style={styles.logoText}>Threadangle</span>
          <span style={styles.tag}>Build Guide</span>
        </div>
        <div style={styles.tabs}>
          <TabBtn id="prompts" label="🗂 Prompts" />
          <TabBtn id="stack"   label="⚙️ Stack" />
          <TabBtn id="timeline" label="📅 Timeline" />
        </div>
      </div>

      {/* PROMPTS */}
      {mainTab === "prompts" && (
        <div style={styles.body}>
          <div style={styles.sidebar}>
            <div style={styles.sideLabel}>SESSIONS</div>
            {SESSIONS.map(s => <SideBtn key={s.id} s={s} />)}
          </div>
          <div style={styles.main}>
            <div style={styles.header}>
              <div style={styles.headerRow}>
                <div style={{ flex: 1 }}>
                  <div style={styles.titleRow}>
                    <span style={{ fontSize: 18 }}>{cur.icon}</span>
                    <h2 style={styles.h2}>{cur.title}</h2>
                    <span style={{ background: "#18181B", border: `1px solid ${diffColor(cur.difficulty)}55`, color: diffColor(cur.difficulty), fontSize: 10, padding: "2px 7px", borderRadius: 4 }}>{cur.difficulty}</span>
                    <span style={{ color: "#52525B", fontSize: 11 }}>⏱ {cur.duration}</span>
                  </div>
                  <p style={styles.subtitle}>{cur.subtitle}</p>
                </div>
                <button onClick={copy} style={{ ...styles.copyBtn, background: copied ? "#065F46" : "#2563EB" }}>
                  {copied ? "✓ Copied!" : "⎘ Copy Prompt"}
                </button>
              </div>
              <div style={styles.tip}>
                <span style={{ fontSize: 12 }}>💡</span>
                <p style={styles.tipText}>
                  <strong style={{ color: "#FAFAFA" }}>How to use:</strong> Click "Copy Prompt" above → open your terminal → type{" "}
                  <code style={{ background: "#09090B", padding: "1px 5px", borderRadius: 3, color: "#60A5FA", fontSize: 11 }}>claude</code>
                  {" "}→ paste and press Enter → wait for it to build → come back for the next session.
                </p>
              </div>
            </div>
            <div style={styles.promptArea}>
              <div style={styles.promptHeader}>
                <span style={styles.promptLabel}>PROMPT — COPY & PASTE INTO YOUR AI ASSISTANT</span>
                <span style={{ fontSize: 10, color: "#3F3F46" }}>{cur.prompt.length.toLocaleString()} chars</span>
              </div>
              <div style={styles.promptBox}>
                <pre style={styles.pre}>{cur.prompt}</pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STACK */}
      {mainTab === "stack" && (
        <div style={{ ...styles.scrollPad, maxWidth: 800, margin: "0 auto", width: "100%" }}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#FAFAFA", marginBottom: 4 }}>Technology Stack</h2>
          <p style={{ fontSize: 12, color: "#71717A", marginBottom: 16 }}>Every tool Threadangle uses and exactly what it costs you per month.</p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 18 }}>
            {STACK.map((item, i) => (
              <div key={i} style={{ ...styles.card, display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: item.color, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: "#FAFAFA" }}>{item.name}</span>
                    <span style={{ fontSize: 11, color: item.cost === "Free" ? "#10B981" : "#F59E0B", fontWeight: 600 }}>{item.cost}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#71717A", marginTop: 2 }}>{item.role}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ ...styles.card, marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#FAFAFA", marginBottom: 12, letterSpacing: 0.5 }}>YOUR MONTHLY BILL AT EACH STAGE</div>
            {[
              ["0 users (worst case)", "$10.00", "EC2 $7.59 + EBS $2.40. Nothing else."],
              ["10 free users only",   "$10.00", "AI cost ~$0.18 total — negligible."],
              ["50 paid users @ $19",  "$11.50", "AI $0.15 + Stripe ~$4 + infra $10."],
              ["200 paid @ avg $17",   "$16.00", "AI $0.60 + Stripe ~$16 + infra $10."],
              ["500 paid — upgrade EC2","$25.00", "Switch to t3.small ($15). Stripe ~$35."],
              ["$10K MRR (~600 paid)", "$60–80", "Add Redis. Infra still under 1% of revenue."],
            ].map(([stage, cost, note], i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: i < 5 ? "1px solid #18181B" : "none" }}>
                <div>
                  <span style={{ color: "#A1A1AA" }}>{stage}</span>
                  <span style={{ color: "#3F3F46", marginLeft: 10, fontSize: 11 }}>{note}</span>
                </div>
                <span style={{ fontWeight: 700, color: "#FAFAFA" }}>{cost}</span>
              </div>
            ))}
          </div>

          <div style={{ background: "#052E16", border: "1px solid #166534", borderRadius: 8, padding: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#4ADE80", marginBottom: 5 }}>⚠️ Your AWS Free Tier Ends This Month</div>
            <p style={{ fontSize: 12, color: "#86EFAC", lineHeight: 1.7 }}>
              Since you run SQLite locally (no RDS), your only new bill is <strong>EC2 t3.micro at $7.59/month</strong> plus EBS storage at $2.40. Total: <strong>~$10/month</strong>. No Supabase, no RDS, no extra services needed. Just accept the $10 bill and keep building.
            </p>
          </div>
        </div>
      )}

      {/* TIMELINE */}
      {mainTab === "timeline" && (
        <div style={{ ...styles.scrollPad, maxWidth: 800, margin: "0 auto", width: "100%" }}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: "#FAFAFA", marginBottom: 4 }}>30-Day Build Timeline</h2>
          <p style={{ fontSize: 12, color: "#71717A", marginBottom: 16 }}>About 2 hours per day. Each day depends on the previous — do not skip ahead.</p>

          <div style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 14 }}>
            {TIMELINE.map((item, i) => (
              <div key={i} style={{ ...styles.card, display: "grid", gridTemplateColumns: "75px 1fr 85px", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "#3B82F6", fontFamily: "monospace" }}>{item.day}</span>
                <span style={{ fontSize: 12, color: "#A1A1AA", lineHeight: 1.5 }}>{item.task}</span>
                <span style={{ fontSize: 10, color: "#52525B", background: "#18181B", padding: "3px 7px", borderRadius: 4, textAlign: "center" }}>{item.session}</span>
              </div>
            ))}
          </div>

          <div style={{ background: "#0C1A2E", border: "1px solid #1E3A5F", borderRadius: 8, padding: 14 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#60A5FA", marginBottom: 5 }}>When AI Generates Buggy Code (It Will Happen)</div>
            <p style={{ fontSize: 12, color: "#93C5FD", lineHeight: 1.7 }}>
              This is completely normal. When something breaks, copy the exact error message and paste it back to your AI with: <strong style={{ color: "#DBEAFE" }}>"I got this error. Fix it."</strong> Do not move to the next session until the current one is working. Every session builds on the previous one.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}