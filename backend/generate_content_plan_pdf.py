"""
Generate the 30-Day AI Productivity Content Plan as a PDF.
Output: F:/Threadforge/backend/assets/30_Day_AI_Content_Plan.pdf
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUTPUT_PATH = Path(__file__).resolve().parent / "assets" / "30_Day_AI_Content_Plan.pdf"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Colour palette ──────────────────────────────────────────────────────────
DARK      = colors.HexColor("#0f0f0f")
ACCENT    = colors.HexColor("#7c3aed")   # purple
ACCENT2   = colors.HexColor("#10b981")   # green
LIGHT_BG  = colors.HexColor("#f5f3ff")
GRAY      = colors.HexColor("#6b7280")
WHITE     = colors.white
RED       = colors.HexColor("#ef4444")
YELLOW    = colors.HexColor("#f59e0b")

def build_styles():
    base = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return dict(
        H1 = S("H1", fontSize=22, textColor=ACCENT,    fontName="Helvetica-Bold",
                spaceAfter=6, spaceBefore=12, alignment=TA_CENTER),
        H2 = S("H2", fontSize=15, textColor=DARK,      fontName="Helvetica-Bold",
                spaceAfter=4, spaceBefore=10,
                borderPad=4, backColor=LIGHT_BG, borderRadius=4),
        H3 = S("H3", fontSize=12, textColor=ACCENT,    fontName="Helvetica-Bold",
                spaceAfter=3, spaceBefore=8),
        H4 = S("H4", fontSize=10, textColor=ACCENT2,   fontName="Helvetica-Bold",
                spaceAfter=2, spaceBefore=6),
        BODY = S("BODY", fontSize=9, textColor=DARK,   leading=14, spaceAfter=3),
        CODE = S("CODE", fontSize=8, fontName="Courier",textColor=colors.HexColor("#1e1e1e"),
                 backColor=colors.HexColor("#f3f4f6"), leading=12,
                 leftIndent=6, rightIndent=6, spaceAfter=4, spaceBefore=2),
        LABEL = S("LABEL", fontSize=8, textColor=GRAY, fontName="Helvetica-Bold",
                  spaceAfter=1, spaceBefore=4),
        COVER_TITLE = S("COVER_TITLE", fontSize=30, textColor=WHITE,
                        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6),
        COVER_SUB   = S("COVER_SUB",   fontSize=13, textColor=colors.HexColor("#c4b5fd"),
                        alignment=TA_CENTER, spaceAfter=4),
        BULLET = S("BULLET", fontSize=9, textColor=DARK, leading=14,
                   leftIndent=12, spaceAfter=2),
    )

# ── helpers ──────────────────────────────────────────────────────────────────
def hr(story):
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#e5e7eb"), spaceAfter=4))

def section(story, title, st):
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(title, st["H2"]))
    hr(story)

def sub(story, title, st):
    story.append(Paragraph(title, st["H3"]))

def label(story, text, st):
    story.append(Paragraph(text, st["LABEL"]))

def body(story, text, st):
    story.append(Paragraph(text, st["BODY"]))

def code_block(story, text, st):
    for line in text.strip().split("\n"):
        story.append(Paragraph(line or " ", st["CODE"]))

def bullet(story, items, st):
    for item in items:
        story.append(Paragraph(f"• {item}", st["BULLET"]))

def simple_table(story, headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  ACCENT),
        ("TEXTCOLOR",    (0,0), (-1,0),  WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_BG]),
        ("GRID",         (0,0), (-1,-1), 0.3, colors.HexColor("#d1d5db")),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 4*mm))


# ════════════════════════════════════════════════════════════════════════════
def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm,  bottomMargin=15*mm,
        title="30-Day AI Productivity Content Plan",
        author="Threadforge",
    )

    st = build_styles()
    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    cover_table = Table([[
        Paragraph("🚀 30-DAY AI PRODUCTIVITY", st["COVER_TITLE"]),
    ]], colWidths=[180*mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), ACCENT),
        ("ROUNDEDCORNERS", (0,0), (-1,-1), [8]),
        ("TOPPADDING",    (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(Spacer(1, 30*mm))
    story.append(cover_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("CONTENT MACHINE", ParagraphStyle(
        "CT2", parent=st["COVER_TITLE"], fontSize=24, textColor=ACCENT)))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "YouTube Shorts · TikTok · Instagram Reels", st["COVER_SUB"]))
    story.append(Paragraph(
        "Niche: AI Productivity & Workflow Automation", st["COVER_SUB"]))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph(
        "1000 Credits · 30 Videos · Full Scripts · AI Prompts · SEO Metadata",
        ParagraphStyle("CS", parent=st["COVER_SUB"], fontSize=10,
                       textColor=colors.HexColor("#9ca3af"))))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Generated by Threadforge  |  April 2026",
        ParagraphStyle("CF", parent=st["COVER_SUB"], fontSize=9,
                       textColor=GRAY)))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ───────────────────────────────────────────────────
    story.append(Paragraph("TABLE OF CONTENTS", st["H1"]))
    hr(story)
    toc_items = [
        "1.  Niche Selection & Justification",
        "2.  Content Pillars & Hook Library",
        "3.  30-Day Calendar Overview",
        "4.  Week 1 — Daily Full Blueprints (Days 1–7)",
        "5.  Week 2 — Topic Calendar (Days 8–14)",
        "6.  Week 3 — Topic Calendar (Days 15–21)",
        "7.  Week 4 — Convert to Followers (Days 22–30)",
        "8.  Credit Optimization Strategy",
        "9.  Weekly Analytics Framework",
        "10. Sunday Execution Checklist",
    ]
    bullet(story, toc_items, st)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1 — NICHE
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 1 — NICHE SELECTION", st)
    story.append(Paragraph("✅ Selected Niche: AI Productivity & Workflow Automation", st["H3"]))
    bullet(story, [
        "Algorithm: 'How-to + transformation' gets highest SAVE rates — saves = #1 ranking signal in 2026",
        "Psychology: Fear of being left behind. Urgency. Identity threat. Every professional is scared of being replaced.",
        "RPM: $12–28 (SaaS affiliates + B2B sponsorships = premium category)",
        "AI content ease: ★★★★★ — desk, code, UI, laptop footage all abundant on Pexels/Pixabay",
        "Perfect for Threadforge: your platform IS the product demo — authentic, congruent, no impostor syndrome",
        "Sub-niches to expand: AI for business · AI for creators · AI for developers · AI income strategies",
    ], st)

    story.append(Spacer(1, 3*mm))
    simple_table(story,
        ["Niche", "Virality", "RPM", "AI Ease", "Grade"],
        [
            ["AI Productivity",    "★★★★★", "$12–28", "★★★★★", "A+"],
            ["Dark Psychology",    "★★★★★", "$6–14",  "★★★★",  "A"],
            ["Quiet Wealth",       "★★★★",  "$18–40", "★★★★",  "A"],
            ["Biohacking 2.0",     "★★★★",  "$10–22", "★★★",   "B+"],
            ["Nostalgia Reframes", "★★★★★", "$5–12",  "★★★",   "B+"],
        ],
        col_widths=[65*mm, 30*mm, 25*mm, 25*mm, 20*mm]
    )
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2 — PILLARS & HOOKS
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 2 — CONTENT PILLARS & HOOK LIBRARY", st)

    sub(story, "5 Content Pillars", st)
    simple_table(story,
        ["Pillar", "Format", "Emotion Triggered"],
        [
            ["P1: REVELATION",    '"Nobody tells you that AI can..."',          "Surprise + urgency"],
            ["P2: WORKFLOW SWAP", '"I replaced X with AI. Here\'s what happened"', "Curiosity + FOMO"],
            ["P3: SPEED RUN",     '"I built [thing] in [time] using only AI"',  "Awe + aspiration"],
            ["P4: MISTAKE/WARN",  '"Stop using AI wrong. Do this instead"',     "Fear + correction"],
            ["P5: LIST BOMB",     '"7 AI tools that make you look 10x smarter"',"Validation + saves"],
        ],
        col_widths=[35*mm, 80*mm, 55*mm]
    )

    sub(story, "Hook Pattern Library (Rotate Weekly)", st)
    hooks = [
        ("H1 STAT SHOCK",    '"95% of developers still do X manually. Here\'s why that\'s insane."'),
        ("H2 IDENTITY BAIT", '"If you use AI and still feel slow, watch this."'),
        ("H3 CONTRAST",      '"Junior devs: 4 hours. AI workflow: 6 minutes. Same output."'),
        ("H4 THREAT",        '"Your competitor already uses this. You don\'t."'),
        ("H5 MYTH BUST",     '"ChatGPT alone won\'t save you. This stack will."'),
        ("H6 CONFESSION",    '"I wasted 3 months before I found this AI workflow."'),
        ("H7 CHALLENGE",     '"Try this AI workflow for 48 hours. Your output will double."'),
    ]
    for code, text in hooks:
        story.append(Paragraph(
            f'<font color="#7c3aed"><b>{code}:</b></font>  {text}', st["BODY"]))

    story.append(Spacer(1, 3*mm))
    sub(story, "Retention Mechanics (Every Video Must Have 3+)", st)
    bullet(story, [
        "Pattern interrupt at 8–10 sec (cut to different visual / zoom change)",
        "Open loop in first 3 sec — NEVER answer the hook immediately",
        "Numbered list — brain tracks progress, stays to finish",
        "Twist or reframe near end — forces rewatch",
        "Specific CTA: 'comment the ONE tool you use' beats 'comment below'",
    ], st)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3 — 30-DAY CALENDAR
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 3 — 30-DAY CALENDAR OVERVIEW", st)
    simple_table(story,
        ["Week", "Theme", "Goal"],
        [
            ["Week 1", "Hook Testing (7 different hooks/styles)",
             "Find which hook style gets >40% retention"],
            ["Week 2", "Scale top 2 hooks + introduce P2+P3 pillars",
             "2× output on winning pillars"],
            ["Week 3", "Add social proof + proof-of-result formats",
             "Drive saves + follows"],
            ["Week 4", "Series format + CTA for channel/newsletter",
             "Convert viewers to subscribers"],
        ],
        col_widths=[20*mm, 80*mm, 70*mm]
    )
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4 — WEEK 1 FULL BLUEPRINTS
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 4 — WEEK 1: DAILY FULL BLUEPRINTS", st)

    days = [
        {
            "day": 1, "pillar": "REVELATION", "hook": "STAT SHOCK",
            "topic": "The AI Code Review That Replaced 1 Hour of Work",
            "script": """\
[HOOK 0-2s]
"A senior engineer just reviewed 200 lines of code in 4 minutes.
No junior dev. No PR meeting. Just this."

[BODY 2-20s]
"Most developers still do code review the old way.
Paste your diff into Claude. Use this prompt:
'Review for security, performance, and logic errors.
Flag anything breaking — explain why in one line each.'
You get security flags, performance issues, rewrites.
Under 5 minutes. Catches 90% of what humans catch."

[CTA 20-25s]
"Save this. Use it on your next PR.
Tell me what it caught that you missed." """,
            "ai_prompt": """\
SCENE 1: Extreme close-up of code diff, green/red lines, dark editor, 9:16, cinematic
SCENE 2: Person typing at desk, AI chat + terminal visible, documentary style, vertical
SCENE 3: Screen zoom into AI response highlighting security warnings, Matrix-modern, 9:16""",
            "youtube": "AI Code Review in 4 Minutes (Senior Engineers Are Doing This)",
            "tiktok":  "This AI code review workflow saved me 6 hours this week. Save for your next PR 🧵",
            "hashtags": "#AIWorkflow #CodeReview #ProgrammingTips #AITools #DeveloperLife #Shorts",
            "thumbnail": '"200 Lines Reviewed in 4 MIN" | Sub: "This AI prompt does it" | Dark code bg + neon green',
        },
        {
            "day": 2, "pillar": "WORKFLOW SWAP", "hook": "IDENTITY BAIT",
            "topic": "I Stopped Writing Documentation. AI Does It Now.",
            "script": """\
[HOOK 0-2s]
"If you're still writing docs manually in 2026 — you're working for free."

[BODY 2-18s]
"After writing a function, run this in Cursor:
'Generate JSDoc with parameter types, return value, and one usage example.'
Done. Auto-inserted. Zero context switching.
For full module docs: give Claude your module.
'Write a README with: overview, setup, API reference, and gotchas.'
90 seconds. Reads better than most humans write."

[CTA 18-22s]
"What would you do with 3 hours a week back? Drop it below." """,
            "ai_prompt": """\
SCENE 1: Developer + blank docs page, frustration, dramatic zoom-out, vertical
SCENE 2: Code auto-completing with AI, docs appearing instantly, dark IDE, satisfying typewriter
SCENE 3: Developer leaning back, satisfied, golden hour city view, teal-orange grade""",
            "youtube": "Stop Writing Docs Manually — AI Does It Better in 90 Seconds",
            "tiktok":  "Documentation killed my productivity for years. 3 hours back every week permanently. 🔥",
            "hashtags": "#documentation #devlife #aitools #cursor #claudeai #productivity #coding",
            "thumbnail": '"I Stopped Writing Docs" | Sub: "AI writes better ones in 90 sec" | Split screen',
        },
        {
            "day": 3, "pillar": "SPEED RUN", "hook": "CONTRAST",
            "topic": "I Built a Full Chrome Extension in 45 Minutes Using AI",
            "script": """\
[HOOK 0-2s]
"45 minutes. Zero prior extension experience.
Fully working Chrome extension. Here's exactly how."

[BODY 2-22s]
"4-step AI workflow:
Step 1: Claude for architecture — file structure + each file's purpose.
Step 2: Cursor generates all files, one function at a time.
Step 3: ChatGPT for manifest + permissions — paste error, get fix, 30 sec.
Step 4: Claude writes README and store description.
Total: 45 minutes. Published next morning. 200 users now."

[CTA 22-28s]
"Save this workflow. Next time you have a problem nobody's solved — build it." """,
            "ai_prompt": """\
SCENE 1: Timer counting down, multiple browser tabs + code, fast-motion, blue tech, vertical
SCENE 2: Split screen — AI chat left / VS Code right, code appearing rapidly, startup aesthetic
SCENE 3: Chrome installing extension, 'Extension added' popup, warm celebratory light, 9:16""",
            "youtube": "I Built a Chrome Extension in 45 Min Using Only AI (Step-by-Step)",
            "tiktok":  "No experience. No tutorials. Just AI and a problem worth solving. 4-step workflow 👇🔥",
            "hashtags": "#chromextension #buildinpublic #aitools #cursor #developer #productivity",
            "thumbnail": '"45 MINUTES → Chrome Extension" | Sub: "Step-by-step AI workflow"',
        },
        {
            "day": 4, "pillar": "MISTAKE/WARNING", "hook": "THREAT",
            "topic": "The Wrong Way to Use ChatGPT for Work",
            "script": """\
[HOOK 0-2s]
"You're using ChatGPT wrong at work.
It's making you slower, not faster."

[BODY 2-19s]
"Mistake: asking it questions like Google. You get generic. Useless.
Fix: give it a ROLE, a CONSTRAINT, and a FORMAT.
Wrong: 'Help me write an email to my client.'
Right: 'You are a senior account manager.
Write a 3-sentence follow-up email after a missed deadline.
Tone: professional, owning the mistake, proposing solution. No filler.'
Same tool. Completely different output."

[CTA 19-23s]
"Try it on your next email. Tell me if the output surprises you." """,
            "ai_prompt": """\
SCENE 1: Typing generic ChatGPT prompt, bad response, frustrated reaction, vertical 9:16
SCENE 2: Same person rewriting with role+constraints, dramatically better output, relief
SCENE 3: Side-by-side two emails — one bland, one sharp, zoom into difference""",
            "youtube": "You're Using ChatGPT Wrong at Work (Do This Instead)",
            "tiktok":  "The prompt mistake wasting 20 min every time you use AI at work. Fixed in 10 seconds.",
            "hashtags": "#chatgpt #aiprompts #productivity #worksmarter #aitools #promptengineering",
            "thumbnail": '"Using AI WRONG?" | Sub: "Most people make this mistake daily" | Red alert style',
        },
        {
            "day": 5, "pillar": "LIST BOMB", "hook": "MYTH BUST",
            "topic": "5 AI Tools That Replace Full-Time Roles in Your Workflow",
            "script": """\
[HOOK 0-2s]
"These 5 AI tools together replace what used to require
3 different people on your team."

[BODY 2-23s]
"1: Cursor — replaces 80% of Googling + Stack Overflow.
2: Perplexity — real-time research with citations. No hallucinations.
3: Notion AI — records, transcribes, summarizes, assigns action items.
4: ElevenLabs — voiceover, clone, narrate, localize. Minutes.
5: Runway — AI scene generation from text prompts.
Combined: under $100/month.
What they replace: potentially $15,000/month in contractor fees."

[CTA 23-27s]
"Save this list. Which one will you try first?" """,
            "ai_prompt": """\
SCENE 1: Quick montage of 5 tool interfaces, energetic cuts, tech product aesthetic, vertical
SCENE 2: Split — 'Old Way' crowded desk vs 'New Way' one person + multiple AI windows
SCENE 3: Price comparison screen — $15K/month vs $100/month, dramatic zoom reveal""",
            "youtube": "5 AI Tools That Replace $15K/Month in Labor (2026 Stack)",
            "tiktok":  "Under $100/month. Replaces what used to take 3 people. The exact AI stack I use 👇",
            "hashtags": "#aitools #productivity #techstack #aiworkflow #cursor #notion #elevenlaabs #runway",
            "thumbnail": '"$15K/month → $100/month" | Sub: "5 AI tools doing the work"',
        },
        {
            "day": 6, "pillar": "REVELATION", "hook": "CONFESSION",
            "topic": "I Wasted 6 Months Using AI Wrong. Here's What Changed.",
            "script": """\
[HOOK 0-2s]
"I used AI every day for 6 months
and barely saved 30 minutes a week. Then I learned this."

[BODY 2-21s]
"The problem wasn't the tools. It was my system.
I was using AI reactively — one-off prompts. Copy, edit, move on.
The shift: I built a personal prompt library.
30 saved prompts for my most repeated tasks.
Morning brief. Meeting prep. Email drafts.
Code debugging. Content outlines. Client updates.
Now: open a task, hit saved prompt, paste context, done.
Average 4 minutes per task, not 20.
Across 8–10 AI tasks per day? Nearly 3 hours back. Daily."

[CTA 21-25s]
"Want my 10 daily prompts? Comment PROMPTS below." """,
            "ai_prompt": """\
SCENE 1: Person at desk looking frustrated, AI chat open, clock ticking, moody light, vertical
SCENE 2: Same desk — now organized, prompt library visible, fast efficient workflow, bright
SCENE 3: Analytics-style time saved counter, green numbers rising, satisfying reveal""",
            "youtube": "I Used AI Daily for 6 Months and Barely Saved Time — Then This Changed Everything",
            "tiktok":  "6 months. Daily AI use. Barely saved time. The fix took 2 hours and saves me 3h/day now.",
            "hashtags": "#aiprompts #productivity #chatgpt #claude #aiworkflow #timemanagement #devlife",
            "thumbnail": '"6 MONTHS WASTED" | Sub: "Until I found this system" | Timeline visual',
        },
        {
            "day": 7, "pillar": "SPEED RUN", "hook": "CHALLENGE",
            "topic": "48-Hour AI Workflow Challenge — Your Output Will Double",
            "script": """\
[HOOK 0-2s]
"48-hour challenge. This one AI workflow change
will double your output. Guaranteed."

[BODY 2-20s]
"Before starting any task, spend 60 seconds writing this:
'Task: [what you're trying to do]
Context: [relevant background]
Output format: [what done looks like]
Constraints: [what to avoid]'
Then paste into Claude or ChatGPT.
The AI stops guessing. You stop editing.
First output is usually the final output.
Most people fail at AI because they skip context. Context is everything."

[CTA 20-24s]
"Do it for 48 hours.
Come back and tell me what your best output was." """,
            "ai_prompt": """\
SCENE 1: Timer '48:00:00' on screen, challenge accepted energy, bold text overlay, vertical
SCENE 2: Quick framework text appearing: Task/Context/Format/Constraints, animated build-up
SCENE 3: Before/after: messy AI output → clean first-try perfect output, satisfying transformation""",
            "youtube": "48-Hour AI Workflow Challenge — Your Output Will Double",
            "tiktok":  "I dare you to try this for 48 hours. The people who do never go back.",
            "hashtags": "#aichallenge #productivity #chatgpt #claudeai #aiworkflow #48hourchallenge",
            "thumbnail": '"48-HOUR CHALLENGE" | Sub: "Double your output — guaranteed" | Countdown style',
        },
    ]

    for d in days:
        story.append(KeepTogether([
            Paragraph(
                f'<font color="#7c3aed">DAY {d["day"]}</font>'
                f'  ·  <font color="#10b981">{d["pillar"]}</font>'
                f'  ·  <font color="#6b7280">{d["hook"]}</font>',
                st["H3"]
            ),
            Paragraph(d["topic"], ParagraphStyle(
                "DT", parent=st["BODY"], fontSize=11,
                fontName="Helvetica-Bold", spaceAfter=4)),
        ]))

        label(story, "① VIRAL SCRIPT", st)
        code_block(story, d["script"], st)

        label(story, "② AI VIDEO GENERATION PROMPT (gen3a_turbo)", st)
        code_block(story, d["ai_prompt"], st)

        label(story, "③ YOUTUBE SHORTS TITLE", st)
        story.append(Paragraph(d["youtube"], st["BODY"]))

        label(story, "④ TIKTOK CAPTION", st)
        story.append(Paragraph(d["tiktok"], st["BODY"]))

        label(story, "⑤ HASHTAGS", st)
        story.append(Paragraph(d["hashtags"], st["CODE"]))

        label(story, "⑥ THUMBNAIL TEXT IDEA", st)
        story.append(Paragraph(d["thumbnail"], st["BODY"]))

        story.append(HRFlowable(width="100%", thickness=1,
                                color=ACCENT, spaceAfter=8, spaceBefore=6))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTIONS 5-7 — WEEKS 2-4 CALENDAR
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 5 — WEEK 2 TOPIC CALENDAR (Days 8–14)", st)
    simple_table(story,
        ["Day", "Topic", "Pillar", "Hook"],
        [
            ["8",  "Claude vs ChatGPT vs Gemini — honest breakdown",         "LIST BOMB",     "MYTH BUST"],
            ["9",  "How I prep for any meeting in 3 minutes using AI",        "WORKFLOW SWAP", "CONTRAST"],
            ["10", "AI turned my 2-hour report into a 10-min task",           "SPEED RUN",     "STAT SHOCK"],
            ["11", "The AI prompt that makes any bad feedback useful",         "REVELATION",    "IDENTITY BAIT"],
            ["12", "Stop asking AI to write. Start asking it to think",        "MISTAKE",       "THREAT"],
            ["13", "Built a personal CRM using only free AI tools",            "SPEED RUN",     "CONTRAST"],
            ["14", "AI stack that made me most valuable person in the room",   "LIST BOMB",     "IDENTITY BAIT"],
        ],
        col_widths=[12*mm, 80*mm, 35*mm, 35*mm]
    )

    section(story, "SECTION 6 — WEEK 3 TOPIC CALENDAR (Days 15–21)", st)
    simple_table(story,
        ["Day", "Topic", "Pillar", "Format"],
        [
            ["15", "My weekly AI workflow — real-time walkthrough",            "WORKFLOW SWAP", "Screen-share style"],
            ["16", "Comment said 'AI can't do X' — watch this",               "MISTAKE",       "Comment response"],
            ["17", "7 AI prompts that took me 3 months to find",               "LIST BOMB",     "Numbered list"],
            ["18", "How AI helped me close a $5K client in 2 hours",           "SPEED RUN",     "Story format"],
            ["19", "The dark side of AI productivity nobody talks about",       "REVELATION",    "Myth bust"],
            ["20", "Viewer submitted AI workflow — I tried it for a week",     "WORKFLOW SWAP", "Social proof"],
            ["21", "This AI tool went from 0 to my most used in 30 days",      "LIST BOMB",     "Transformation"],
        ],
        col_widths=[12*mm, 80*mm, 35*mm, 35*mm]
    )

    section(story, "SECTION 7 — WEEK 4 CONVERT TO FOLLOWERS (Days 22–30)", st)
    simple_table(story,
        ["Day", "Topic", "Series / CTA"],
        [
            ["22", "My full AI toolkit for 2026 (Part 1 of 3) — Discovery tools",   "Follow for parts 2+3"],
            ["23", "Full AI toolkit Part 2 — Automation tools",                       "Follow series"],
            ["24", "Full AI toolkit Part 3 — Content + writing tools",                "Subscribe"],
            ["25", "I tracked every minute saved with AI for 30 days",                "Newsletter CTA"],
            ["26", "Reader Q&A: Your biggest AI productivity questions",               "Comment mining"],
            ["27", "AI vs no AI — I ran the same week both ways",                     "High share potential"],
            ["28", "The one AI prompt I use before every important decision",          "Save + share"],
            ["29", "What I'd do if I started from scratch with AI today",             "Profile visit CTA"],
            ["30", "30 days of AI productivity — what actually worked",               "Channel subscribe"],
        ],
        col_widths=[12*mm, 105*mm, 53*mm]
    )
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 8 — CREDIT STRATEGY
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 8 — CREDIT OPTIMIZATION STRATEGY", st)
    simple_table(story,
        ["Phase", "Videos", "Model", "Duration", "Credits/Video", "Total Credits"],
        [
            ["Week 1 Testing",  "7",  "gen3a_turbo", "3 × 10s clips", "~75",  "525"],
            ["Week 2 Scale",    "7",  "gen4_turbo",  "3 × 10s clips", "~75",  "200"],
            ["Week 3 Quality",  "7",  "gen4.5",      "2 × 5s clips",  "~120", "175"],
            ["Reserve",         "—",  "—",           "—",             "—",    "100"],
            ["TOTAL",           "21 AI-hybrid", "",  "",              "",     "1000"],
        ],
        col_widths=[30*mm, 18*mm, 30*mm, 30*mm, 30*mm, 28*mm]
    )

    sub(story, "Reuse Strategy — Stretch Every Credit", st)
    bullet(story, [
        "Reuse background/ambient scenes (desk, typing, city) across multiple videos — same Runway clip, different voice = 0 extra credits",
        "Use Pexels/Pixabay (free) for all 'person thinking', 'laptop', 'coffee' B-roll — no Runway needed",
        "Reserve gen4.5 ONLY for Hero scenes (first 3 seconds) where quality matters most",
        "Batch by visual type — generate all 'dark desk + laptop' scenes in one session for consistent aesthetic",
        "Week 4 (Days 22–30): pure stock only — series format works better with screen-recording style anyway",
    ], st)

    story.append(Spacer(1, 3*mm))
    sub(story, "Model Cost Reference (per 5-second clip)", st)
    simple_table(story,
        ["Model", "Credits/sec", "5s = credits", "10s = credits", "Best For"],
        [
            ["gen3a_turbo", "5",  "25",  "50",  "Testing, bulk generation"],
            ["gen4_turbo",  "5",  "25",  "50",  "Quality testing, scale phase"],
            ["gen4.5",      "12", "60",  "120", "Final hero scenes only"],
            ["veo3",        "40", "200", "400", "AVOID during dev phase"],
        ],
        col_widths=[35*mm, 30*mm, 30*mm, 30*mm, 45*mm]
    )
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 9 — ANALYTICS
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 9 — WEEKLY ANALYTICS FRAMEWORK", st)

    sub(story, "Metrics Dashboard — Week 1", st)
    simple_table(story,
        ["Metric", "Tool", "Target", "Action if Below Target"],
        [
            ["Hook retention (0–3s)", "YT Studio",        ">65%", "Change hook style immediately"],
            ["Avg watch time",        "YT Studio",        ">40%", "Shorten or change pacing"],
            ["Completion rate",       "TikTok Analytics", ">35%", "Cut last 5 seconds"],
            ["Save rate",             "YT / IG",          ">3%",  "Make content more 'reference-worthy'"],
            ["Comment rate",          "All platforms",    ">0.5%","Adjust CTA specificity"],
            ["Follow/sub rate",       "All platforms",    ">1%",  "Add series format hook"],
        ],
        col_widths=[42*mm, 33*mm, 18*mm, 77*mm]
    )

    sub(story, "Decision Rules After Week 1", st)
    story.append(Paragraph(
        '<font color="#10b981"><b>SCALE IT</b></font> — Double down immediately if:', st["BODY"]))
    bullet(story, [
        "Any video with >50% avg watch time",
        "Any hook holding >70% at 3 seconds",
        "Any video with save rate >5%",
    ], st)

    story.append(Paragraph(
        '<font color="#f59e0b"><b>IMPROVE IT</b></font> — Tweak and retest if:', st["BODY"]))
    bullet(story, [
        "Videos with 30–50% avg watch time",
        "Good saves but low comments → add explicit CTA",
        "Good hooks but low completion → cut body length",
    ], st)

    story.append(Paragraph(
        '<font color="#ef4444"><b>KILL IT</b></font> — Stop producing, extract lesson if:', st["BODY"]))
    bullet(story, [
        "Videos with <30% avg watch time on first 100 views",
        "Hook patterns with <50% 3-second retention",
        "Any format where comments are negative or confused",
    ], st)
    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 10 — EXECUTION CHECKLIST
    # ════════════════════════════════════════════════════════════════════════
    section(story, "SECTION 10 — SUNDAY EXECUTION CHECKLIST", st)
    sub(story, "Every Sunday — Batch Production Day", st)
    checklist = [
        "Open Threadforge → generate 7 scripts using the pillar templates",
        "Generate AI scenes via Runway (3 scenes × 7 videos = 21 clips on budget)",
        "Generate ElevenLabs voiceovers for all 7 videos",
        "Assemble in video editor — add captions and render 7 videos",
        "Schedule all 7 (one per day at optimal posting time)",
        "Review prior week analytics → update decision log",
    ]
    for item in checklist:
        story.append(Paragraph(f"☐  {item}", st["BODY"]))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 4*mm))
    sub(story, "Every Monday — Analysis Day (15 minutes max)", st)
    analysis = [
        "Record: top 3 metrics for each video from prior week",
        "Identify pattern in top performer (hook style? topic type? CTA?)",
        "Set ONE experiment variable for the coming week",
        "Update prompt library if new winning prompt discovered",
    ]
    for item in analysis:
        story.append(Paragraph(f"☐  {item}", st["BODY"]))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 6*mm))
    sub(story, "Optimal Posting Schedule", st)
    simple_table(story,
        ["Platform", "Best Time", "Frequency"],
        [
            ["YouTube Shorts",    "7am or 6pm (audience local time)", "Daily"],
            ["TikTok",            "9am, 12pm, or 7pm — pick one consistent slot", "Daily"],
            ["Instagram Reels",   "6–8pm + repurpose to Stories", "Daily"],
        ],
        col_widths=[40*mm, 95*mm, 35*mm]
    )

    # ── FINAL PAGE — QUICK REFERENCE CARD
    story.append(PageBreak())
    story.append(Paragraph("QUICK REFERENCE CARD", st["H1"]))
    hr(story)

    story.append(Paragraph(
        "Generate any video with Threadforge using these params:", st["BODY"]))
    story.append(Spacer(1, 2*mm))
    code_block(story, """\
POST /api/generate/video/free
{
  "hook":             "[Your hook from the script above]",
  "body":             "[Your body from the script above]",
  "cta":              "[Your CTA from the script above]",
  "duration_seconds": 25,
  "scene_mode":       "hybrid",
  "niche":            "technology",
  "runway_model":     "gen3a_turbo"   // Week 1-2: budget testing
                      "gen4_turbo"    // Week 2-3: better quality
                      "gen4.5"        // Week 3+: hero quality
}""", st)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Plan generated by <b>Threadforge</b> — AI Productivity Video Machine  |  April 2026",
        ParagraphStyle("FOOTER", parent=st["BODY"], fontSize=8,
                       textColor=GRAY, alignment=TA_CENTER)))

    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    build_pdf()
