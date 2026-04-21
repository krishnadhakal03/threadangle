"""
Threadangle-Ready Viral Scripts PDF Generator
Run: python generate_threadangle_scripts_pdf.py
Output: F:\Threadforge\Threadangle_Viral_Scripts_2026.pdf

Converts the 10 viral scripts from the Claude PDF into production-ready
GenerateVideoRequest payloads for the Threadangle platform.
"""
import json, textwrap
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "Threadangle_Viral_Scripts_2026.pdf"

# ── Colors ─────────────────────────────────────────────────────────────────
C_PURPLE   = colors.HexColor("#7C3AED")
C_GOLD     = colors.HexColor("#F59E0B")
C_GREEN    = colors.HexColor("#10B981")
C_RED      = colors.HexColor("#EF4444")
C_TEXT     = colors.HexColor("#1F2937")
C_GREY     = colors.HexColor("#6B7280")
C_LIGHT    = colors.HexColor("#F3F4F6")
C_INDIGO   = colors.HexColor("#1E1B4B")
C_BLUE     = colors.HexColor("#1E40AF")
C_LBLUE    = colors.HexColor("#EFF6FF")
C_TEAL     = colors.HexColor("#0D9488")
C_TEAL_L   = colors.HexColor("#F0FDFA")
C_AMBER    = colors.HexColor("#92400E")
C_AMBER_L  = colors.HexColor("#FFFBEB")
C_ORANGE   = colors.HexColor("#EA580C")
C_BLACK    = colors.HexColor("#111827")
C_WHITE    = colors.white

def hex_rgb(c):
    return '%02x%02x%02x' % (int(c.red*255), int(c.green*255), int(c.blue*255))

# ── Styles ──────────────────────────────────────────────────────────────────
def SP(name, **kw):
    return ParagraphStyle(name, **kw)

sTitle = SP("Title", fontName="Helvetica-Bold", fontSize=28, textColor=C_INDIGO,
            spaceAfter=6, leading=34, alignment=TA_CENTER)
sSub   = SP("Sub",   fontName="Helvetica",      fontSize=13, textColor=C_GREY,
            spaceAfter=4, leading=18, alignment=TA_CENTER)
sH1    = SP("H1",    fontName="Helvetica-Bold", fontSize=16, textColor=C_INDIGO,
            spaceBefore=10, spaceAfter=4, leading=20)
sH2    = SP("H2",    fontName="Helvetica-Bold", fontSize=12, textColor=C_BLUE,
            spaceBefore=6, spaceAfter=3, leading=16)
sH3    = SP("H3",    fontName="Helvetica-Bold", fontSize=10, textColor=C_BLACK,
            spaceBefore=4, spaceAfter=2, leading=14)
sBody  = SP("Body",  fontName="Helvetica",      fontSize=9,  textColor=C_TEXT,
            spaceAfter=3, leading=14)
sNote  = SP("Note",  fontName="Helvetica-Oblique", fontSize=8, textColor=C_GREY,
            spaceAfter=2, leading=12)
sCode  = SP("Code",  fontName="Courier",        fontSize=7.5, textColor=C_BLUE,
            backColor=C_LBLUE, leftIndent=4, rightIndent=4,
            spaceAfter=2, leading=12, borderPad=4)
sSmall = SP("Small", fontName="Helvetica",      fontSize=8,  textColor=C_GREY,
            spaceAfter=2, leading=11)
sTableH= SP("TH",    fontName="Helvetica-Bold", fontSize=8,  textColor=C_WHITE,
            alignment=TA_CENTER, leading=11)
sTableB= SP("TB",    fontName="Helvetica",      fontSize=8,  textColor=C_TEXT,
            alignment=TA_LEFT, leading=11)
sTableC= SP("TC",    fontName="Helvetica",      fontSize=8,  textColor=C_TEXT,
            alignment=TA_CENTER, leading=11)
sHook  = SP("Hook",  fontName="Helvetica-BoldOblique", fontSize=10, textColor=C_INDIGO,
            backColor=colors.HexColor("#EEF2FF"), leftIndent=6, rightIndent=6,
            borderPad=5, spaceAfter=4, leading=16)
sScore = SP("Score", fontName="Helvetica-Bold", fontSize=22, textColor=C_WHITE,
            alignment=TA_CENTER, leading=28)

def sp(n): return Spacer(1, n)
def hr(c=C_PURPLE, w=1): return HRFlowable(width="100%", thickness=w, color=c, spaceAfter=4)

def score_color(s):
    if s >= 9: return C_GREEN
    if s >= 7: return C_GOLD
    return C_RED

def score_label(s):
    if s >= 9.5: return "MEGA VIRAL"
    if s >= 9:   return "VERY HIGH"
    if s >= 8:   return "HIGH"
    if s >= 7:   return "SOLID"
    return "MODERATE"

def viral_bar(score):
    filled = round(score)
    bar = ("█" * filled) + ("░" * (10 - filled))
    c_hex = hex_rgb(score_color(score))
    return f'<font color="#{c_hex}"><b>{bar} {score}/10</b></font>'

def tag_para(label, bg_hex, text_hex="#FFFFFF"):
    return Paragraph(
        f'<font color="#{text_hex}"><b> {label} </b></font>',
        SP(f"tag_{label}", fontName="Helvetica-Bold", fontSize=7.5,
           backColor=colors.HexColor(bg_hex), leftIndent=2, rightIndent=2,
           borderPad=3, spaceAfter=2, leading=12, alignment=TA_CENTER)
    )

# ── Script data ─────────────────────────────────────────────────────────────
SCRIPTS = [
    {
        "num": 1,
        "title": "THE SIBERIAN ANOMALY",
        "platform": "TikTok",
        "duration": 15,
        "viral_score": 9.0,
        "est_views": "2M – 5M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 72,

        "hook": (
            "This crystal was found 3 miles underground in Siberia. "
            "When scientists touched it, their fingerprints stayed glowing for 6 hours. "
            "The CIA classified this. You were never supposed to see it."
        ),
        "body": (
            "Scene 1 (0-4s): Extreme close-up of luminescent crystal pulsing with cold blue light, cave walls glistening. "
            "Caption: '3 MILES UNDERGROUND'. "
            "Scene 2 (4-9s): Scientist removes glove — fingers glow electric blue in dark lab. "
            "Caption: '6 HOURS LATER... STILL GLOWING'. "
            "Scene 3 (9-13s): Classified documents stamped CIA flicker on screen, then black. "
            "Caption: 'THIS FILE WAS DELETED'."
        ),
        "cta": (
            "Drop '🔵' if you believe this is real. "
            "Drop '❌' if you think it's fake. "
            "Scientists are still debating — part 2 tomorrow."
        ),

        "why_it_works": [
            "CIA classified angle bypasses skepticism — forbidden = real",
            "3 miles + 6 hours: specific numbers create credibility",
            "15s forces 100% watch time — TikTok algo boost on Day 1",
            "'Part 2 tomorrow' = follow trigger without asking for follow",
        ],
        "risks": ["Could be flagged as misinformation — frame as 'unexplained phenomena'"],
        "runway_prompts": [
            "Extreme macro of bioluminescent crystal cave underground, cold blue glow, photorealistic, cinematic",
            "Close-up scientist's gloved hand touching glowing crystal, blue light radiating from contact point, dark lab, hyper-realistic",
            "Classified government document stamped CIA, redacted text, flickering overhead fluorescent light, dark room",
        ],
        "thr_payload": {
            "hook": "This crystal was found 3 miles underground in Siberia. When scientists touched it, their fingerprints stayed glowing for 6 hours. The CIA classified this. You were never supposed to see it.",
            "body": "Scene 1 (0s): Extreme close-up of luminescent crystal pulsing with cold blue light. Caption: 3 MILES UNDERGROUND. Scene 2 (4s): Scientist removes glove — fingers glow electric blue in dark lab. Caption: 6 HOURS LATER... STILL GLOWING. Scene 3 (9s): Classified documents stamped CIA flicker on screen then vanish. Caption: THIS FILE WAS DELETED.",
            "cta": "Drop blue circle if you believe this. Drop X if fake. Part 2 tomorrow.",
            "duration_seconds": 15,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 2,
        "title": "MEMORY DETECTIVE — TOKYO 2088",
        "platform": "TikTok",
        "duration": 30,
        "viral_score": 8.5,
        "est_views": "1.5M – 4M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 144,

        "hook": (
            "POV: You wake up in Tokyo 2088. "
            "The sun hasn't risen in 40 years. "
            "This is your first day as a Memory Detective. "
            "Your case: Find who killed the sun."
        ),
        "body": (
            "Scene 1 (0-5s): Wake up POV — holographic alarm, rain on window, neon Tokyo skyline with no sun. "
            "Caption: 'TOKYO 2088 — DAY 14,600 WITHOUT SUNLIGHT'. "
            "Scene 2 (5-12s): Detective badge materializes in hand, file drops: photo of a black sphere in the sky where the sun was. "
            "Caption: 'THE SUN DIDN\\'T SET. IT WAS STOLEN.' "
            "Scene 3 (12-20s): Walking rain-soaked streets, holographic wanted posters, civilians in gas masks. "
            "Caption: '40 YEARS. NO ANSWERS.' "
            "Scene 4 (20-28s): Desk with memory extraction device. Tap on a glowing orb — a memory plays. Someone planned this. "
            "Caption: 'I KNOW WHO DID IT.' Screen cuts to black."
        ),
        "cta": (
            "Comment 'DETECTIVE' if you want Part 2. "
            "Comment 'SKIP' if you think the government did it. "
            "Follow — the answer drops in 24 hours."
        ),

        "why_it_works": [
            "POV format = algorithm favourite, 2x comment rate vs third-person",
            "Murder mystery in a sci-fi world = impossible to look away",
            "Day count (14,600) makes it viscerally real",
            "'SKIP' option reverse-psychologies engagement",
        ],
        "risks": ["30s needs strong pacing — no dead seconds in body"],
        "runway_prompts": [
            "POV first-person waking up in futuristic Tokyo apartment 2088, rain on glass, neon signs glowing red and cyan outside, holographic alarm display, no sunlight, cinematic, photorealistic",
            "Rain-soaked neo-Tokyo street at permanent night, 2088, holographic wanted posters floating in air, civilians in black gas masks, sci-fi noir",
            "Futuristic detective desk in dark office, glowing memory orb hovering, holographic case files, rainy city visible through window, cinematic",
        ],
        "thr_payload": {
            "hook": "POV: You wake up in Tokyo 2088. The sun hasn't risen in 40 years. This is your first day as a Memory Detective. Your case: Find who killed the sun.",
            "body": "Scene 1: Wake up POV - holographic alarm, rain on window, neon Tokyo skyline with no sun. Caption: TOKYO 2088 - DAY 14,600 WITHOUT SUNLIGHT. Scene 2: Detective badge materialises, file photo of black sphere where sun was. Caption: THE SUN DIDN'T SET. IT WAS STOLEN. Scene 3: Rain-soaked streets, holographic wanted posters, gas mask civilians. Caption: 40 YEARS. NO ANSWERS. Scene 4: Memory extraction device on desk, glowing orb tap - memory plays. Caption: I KNOW WHO DID IT. Screen cuts black.",
            "cta": "Comment DETECTIVE for Part 2. Comment SKIP if you think the government did it. Follow — answer drops in 24 hours.",
            "duration_seconds": 30,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 3,
        "title": "7-DAY AI TAKEOVER",
        "platform": "TikTok",
        "duration": 45,
        "viral_score": 7.0,
        "est_views": "300K – 1.5M",
        "niche": "Tech & AI",
        "scene_mode": "hybrid",
        "runway_model": "gen4_turbo",
        "credit_est": 96,

        "hook": (
            "I let AI control 100% of my decisions for 7 days. "
            "Day 1: It deleted 90% of my apps. "
            "Day 7: I'm $12,000 richer. "
            "Here's every decision it made — and one you should never let it make."
        ),
        "body": (
            "Scene 1 (0-6s): Phone screen — AI deletes app after app (YouTube, Instagram, Netflix). "
            "Caption: 'DAY 1: DELETED EVERYTHING THAT MADE ME FEEL GOOD BUT DO NOTHING'. "
            "Scene 2 (6-16s): Person at desk 5am, cold coffee, laptop open — following AI schedule. "
            "Caption: 'DAY 2: IT WOKE ME UP AT 4:47AM. THE EXACT TIME MOST MILLIONAIRES START.' "
            "Scene 3 (16-28s): Screen shows AI-suggested trades / freelance work completed. "
            "Caption: 'DAY 5: $3,800 IN. ON AI\\'S ORDERS.' "
            "Scene 4 (28-38s): Phone notification — message from a contact. AI says: DO NOT REPLY. "
            "Caption: 'THE ONE DECISION I REFUSED TO FOLLOW.' "
            "Scene 5 (38-44s): Day 7 bank app: +$12,000. But no friends messaged back. "
            "Caption: 'WAS IT WORTH IT?'"
        ),
        "cta": (
            "Comment 'WORTH IT' or 'NOT WORTH IT'. "
            "I'll post the AI's exact 7-day schedule if this hits 10K likes."
        ),

        "why_it_works": [
            "AI autonomy anxiety is 2026's #1 tech fear — this weaponises it",
            "'One decision you should never let it make' creates dread-scroll",
            "Personal cost angle (friendships) adds emotional stakes",
            "Conditional CTA (10K likes) gamifies sharing",
        ],
        "risks": [
            "$12,000 claim is oversaturated — consider $3,800 for credibility",
            "Similar to script #9 — avoid posting same week",
        ],
        "runway_prompts": [
            "Extreme close-up smartphone screen, apps being deleted one by one, red delete animations, high saturation, cinematic",
            "Person at minimalist desk at 4:47am, single lamp on, laptop glowing, coffee steam, dark room, photorealistic",
            "Bank app notification on phone screen showing 12000 dollar gain, dramatic lighting, shallow depth of field",
        ],
        "thr_payload": {
            "hook": "I let AI control 100% of my decisions for 7 days. Day 1: It deleted 90% of my apps. Day 7: I'm $12,000 richer. Here's every decision it made — and one you should never let it make.",
            "body": "Scene 1: Phone screen - AI deletes YouTube, Instagram, Netflix. Caption: DAY 1: DELETED EVERYTHING THAT MADE ME FEEL GOOD BUT DO NOTHING. Scene 2: Person at desk at 4:47am, cold coffee, laptop. Caption: DAY 2: IT WOKE ME AT 4:47AM - THE EXACT TIME MOST MILLIONAIRES START. Scene 3: AI-suggested tasks completed, earnings screen. Caption: DAY 5: $3,800 IN. ON AI'S ORDERS. Scene 4: Phone message - AI says DO NOT REPLY. Caption: THE ONE DECISION I REFUSED TO FOLLOW. Scene 5: Bank app +$12,000 but empty message inbox. Caption: WAS IT WORTH IT?",
            "cta": "Comment WORTH IT or NOT WORTH IT. I'll post the AI's exact 7-day schedule if this hits 10K likes.",
            "duration_seconds": 45,
            "scene_mode": "hybrid",
            "niche": "Tech & AI",
            "runway_model": "gen4_turbo",
        },
    },
    {
        "num": 4,
        "title": "AURELIUS FINAL MESSAGE",
        "platform": "YouTube Shorts",
        "duration": 45,
        "viral_score": 9.5,
        "est_views": "3M – 10M",
        "niche": "Self-Improvement",
        "scene_mode": "hybrid",
        "runway_model": "gen4.5",
        "credit_est": 120,

        "hook": (
            "Marcus Aurelius wrote this on the battlefield the night before he died. "
            "Truth #1 will end every excuse you've ever made. "
            "Truth #3 is illegal to teach in 4 countries. "
            "Most people never hear any of them."
        ),
        "body": (
            "Scene 1 (0-7s): Roman battlefield at dusk, tent candlelight, quill writing on parchment. "
            "Caption: '167 AD. THE NIGHT MARCUS AURELIUS WROTE HIS FINAL WORDS.' "
            "Scene 2 (7-17s): Cut to modern person reading, phone drops — text appears: Truth #1. "
            "Caption: 'TRUTH #1: You already have everything you need. The suffering is optional.' "
            "Scene 3 (17-27s): Archive scrolls and modern courtroom imagery. "
            "Caption: 'TRUTH #2: Every man you admire was terrified the first time. Every. Single. One.' "
            "Scene 4 (27-37s): Red 'CLASSIFIED' stamp over scroll. "
            "Caption: 'TRUTH #3: [This one got banned in 4 countries. Dropping in comments.]' "
            "Scene 5 (37-44s): Return to battlefield — tent light extinguishes. "
            "Caption: 'HE DIED BEFORE MORNING. BUT HE LEFT THIS FOR YOU.'"
        ),
        "cta": (
            "Save this if Truth #1 hit you. "
            "Drop 🔥 if you want Truth #3 — I'll put it in the comments."
        ),

        "why_it_works": [
            "Stoicism is #1 self-improvement subgenre on YouTube 2026",
            "'Illegal to teach in 4 countries' — curiosity gap that forces full watch",
            "Truth #3 in comments = comment count exploit (YouTube Shorts metric)",
            "Historical credibility anchor (real person, real date) = trustworthy",
            "Save rate on this format: 15-25% (YouTube saves = 5x algorithm weight)",
        ],
        "risks": ["'Illegal in 4 countries' must be framed as 'governments suppress'"],
        "runway_prompts": [
            "Roman battlefield at dusk, commander's tent glowing with candlelight, leather parchment, quill pen, ancient Rome, cinematic, photorealistic",
            "Ancient scroll with Latin text, red wax seal, dramatic single candle lighting, dark background, macro lens, cinematic",
            "Roman battlefield dawn, armored soldiers silhouette, fog, dramatic backlight, Gen 4.5 quality",
        ],
        "thr_payload": {
            "hook": "Marcus Aurelius wrote this on the battlefield the night before he died. Truth #1 will end every excuse you've ever made. Truth #3 is illegal to teach in 4 countries. Most people never hear any of them.",
            "body": "Scene 1: Roman battlefield at dusk, tent candlelight, quill writing on parchment. Caption: 167 AD - THE NIGHT MARCUS AURELIUS WROTE HIS FINAL WORDS. Scene 2: Cut to modern person reading, phone drops - Truth #1 appears. Caption: TRUTH 1: You already have everything you need. The suffering is optional. Scene 3: Archive scrolls and courtroom. Caption: TRUTH 2: Every man you admire was terrified the first time. Scene 4: Red CLASSIFIED stamp over scroll. Caption: TRUTH 3: Banned in 4 countries - dropping in comments. Scene 5: Battlefield tent light extinguishes. Caption: HE DIED BEFORE MORNING. BUT HE LEFT THIS FOR YOU.",
            "cta": "Save this if Truth #1 hit you. Drop fire emoji if you want Truth #3 — I'll put it in the comments.",
            "duration_seconds": 45,
            "scene_mode": "hybrid",
            "niche": "Self-Improvement",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 5,
        "title": "COSMIC GUARDIANS 2157",
        "platform": "TikTok",
        "duration": 15,
        "viral_score": 7.5,
        "est_views": "1M – 3M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 72,

        "hook": (
            "In 2157, humans discovered we're not alone. "
            "The aliens aren't invaders. "
            "They're 300-foot tall lions in crystalline armour. "
            "And they've been protecting us from something far worse."
        ),
        "body": (
            "Scene 1 (0-5s): Deep space — massive crystalline lion-shaped silhouette eclipses a star. "
            "Caption: '2157: FIRST CONTACT'. "
            "Scene 2 (5-10s): Lion's eye opens — pupil is a galaxy. Armour refracts light like diamonds. "
            "Caption: 'THEY AREN\\'T THE THREAT.' "
            "Scene 3 (10-14s): Behind them in the dark — something vast moves. Blackness with red eyes. "
            "Caption: 'THEY\\'RE WHAT STANDS BETWEEN US AND THAT.'"
        ),
        "cta": (
            "Comment 'GUARDIAN' for the full story. "
            "What\\'s scarier — the thing they\\'re protecting us from, or the fact we didn\\'t know?"
        ),

        "why_it_works": [
            "Plot twist in 15s — aliens as protectors inverts expectation",
            "Visual concept is Runway Gen-4.5's strongest category: cosmic/epic",
            "The unseen monster is scarier than showing it — rewatch trigger",
            "15s = near 100% completion rate on TikTok",
        ],
        "risks": ["Strong AI visuals critical — if Runway quality dips, concept falls flat"],
        "runway_prompts": [
            "Massive crystalline lion silhouette 300 feet tall in deep space, armour refracting starlight like prisms, photorealistic, cinematic, epic scale",
            "Extreme close-up of enormous cosmic lion eye, pupil containing galaxy swirl, crystalline scales catching light, dark space background",
            "Deep space darkness, massive moving shadow with glowing red eyes visible in darkness behind cosmic lion guardian, photorealistic horror",
        ],
        "thr_payload": {
            "hook": "In 2157, humans discovered we're not alone. The aliens aren't invaders. They're 300-foot tall lions in crystalline armour. And they've been protecting us from something far worse.",
            "body": "Scene 1: Deep space - massive crystalline lion silhouette eclipses a star. Caption: 2157: FIRST CONTACT. Scene 2: Lion's eye opens - pupil is a galaxy, armour refracts light. Caption: THEY AREN'T THE THREAT. Scene 3: Behind them in the dark - vast darkness with red eyes moves. Caption: THEY'RE WHAT STANDS BETWEEN US AND THAT.",
            "cta": "Comment GUARDIAN for the full story. What's scarier — the thing they're protecting us from, or the fact we didn't know?",
            "duration_seconds": 15,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 6,
        "title": "GOVERNMENT AI TOOL LEAKED",
        "platform": "TikTok",
        "duration": 30,
        "viral_score": 6.5,
        "est_views": "400K – 1.5M",
        "niche": "Tech & AI",
        "scene_mode": "hybrid",
        "runway_model": "gen4_turbo",
        "credit_est": 80,

        "hook": (
            "I found the AI tool that government contractors use internally. "
            "It's publicly accessible. "
            "It's free to use right now. "
            "And in 72 hours it helped me close $8,000 in work."
        ),
        "body": (
            "Scene 1 (0-5s): Government building exterior, suited person walking in, classified briefcase. "
            "Caption: 'GOVERNMENT CONTRACTORS HAVE HAD THIS SINCE 2024.' "
            "Scene 2 (5-14s): Screen recording — tool interface shown (blurred/stylised), commands being typed. "
            "Caption: 'IT DOES IN 12 MINUTES WHAT JUNIOR ANALYSTS DO IN 8 HOURS.' "
            "Scene 3 (14-22s): Freelance invoice on screen: $8,000 closed within 72 hours. "
            "Caption: 'THIS IS NOT AN AD. THIS IS NOT AFFILIATE.' "
            "Scene 4 (22-28s): URL shown briefly then blurred. "
            "Caption: 'COMMENT \"TOOL\" AND I\\'LL DM IT DIRECTLY. FREE. NO CATCH.'"
        ),
        "cta": (
            "Comment 'TOOL' for the DM. "
            "Or tell me why you think I'm lying — I read every comment."
        ),

        "why_it_works": [
            "'Comment TOOL for DM' = comment section explosion (algo fuel)",
            "Government angle gives free tool extra credibility vs generic 'found an AI'",
            "Conspiracy framing + practical use = shareable to 2 audiences",
        ],
        "risks": [
            "Income claim fatigue — 2026 audiences are desensitised to $X in Y days",
            "Ensure tool is legitimate to avoid platform removal",
            "Do not imply classified/stolen government data",
        ],
        "runway_prompts": [
            "Government building exterior Washington DC style, suited professional walking through doors, cinematic colour grade, photorealistic",
            "Person at desk with multiple screens showing data dashboards and AI interfaces, blue light from screens, dark office, photorealistic",
        ],
        "thr_payload": {
            "hook": "I found the AI tool that government contractors use internally. It's publicly accessible. It's free to use right now. And in 72 hours it helped me close $8,000 in work.",
            "body": "Scene 1: Government building exterior, suited person entering with briefcase. Caption: GOVERNMENT CONTRACTORS HAVE HAD THIS SINCE 2024. Scene 2: Screen recording of tool interface, commands typed. Caption: IT DOES IN 12 MINUTES WHAT JUNIOR ANALYSTS DO IN 8 HOURS. Scene 3: Freelance invoice screen - $8,000 closed in 72 hours. Caption: NOT AN AD. NOT AFFILIATE. Scene 4: URL briefly shown then blurred. Caption: COMMENT TOOL AND I'LL DM IT. FREE. NO CATCH.",
            "cta": "Comment TOOL for the DM. Or tell me why you think I'm lying — I read every comment.",
            "duration_seconds": 30,
            "scene_mode": "hybrid",
            "niche": "Tech & AI",
            "runway_model": "gen4_turbo",
        },
    },
    {
        "num": 7,
        "title": "THE BANNED AI FILM",
        "platform": "Instagram Reels",
        "duration": 45,
        "viral_score": 8.0,
        "est_views": "1.5M – 4M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 144,

        "hook": (
            "This AI-generated film was banned by OpenAI, Google, and three government agencies. "
            "It predicted 3 events before they happened. "
            "The director disappeared 11 days after release. "
            "I found the original cut."
        ),
        "body": (
            "Scene 1 (0-7s): Grainy found-footage style — city skyline at night, cryptic symbol appears in sky. "
            "Caption: 'SCENE 1: RELEASED MARCH 2025.' "
            "Scene 2 (7-17s): News archive-style footage: '3 EVENTS PREDICTED — ALL OCCURRED WITHIN 60 DAYS.' "
            "Caption: 'EVENT #1: ████████ (REDACTED BY REQUEST)' "
            "Scene 3 (17-27s): Empty director's chair, name on door, office abandoned. Personal items left. "
            "Caption: 'HE LEFT EVERYTHING BEHIND. NO MESSAGE.' "
            "Scene 4 (27-37s): Film clip plays — shows impossible geometry, equations on walls. "
            "Caption: 'EVENT #3 HASN\\'T HAPPENED YET.' "
            "Scene 5 (37-44s): Static, then text on black: 'IF THIS GETS TAKEN DOWN, YOU\\'LL KNOW WHY.'"
        ),
        "cta": (
            "Save this before it disappears. "
            "Drop '🎬' if you've seen a film that got banned. "
            "I'll post Event #3 if this stays up until tomorrow."
        ),

        "why_it_works": [
            "Save CTA + 'disappears' creates genuine urgency = high save rate",
            "Redacted text makes viewer lean forward (fill in the blank psychology)",
            "'Disappears' creates self-fulfilling virality loop — sharing = protecting it",
            "Reels save weight is highest of all interactions (5x)",
        ],
        "risks": [
            "Ensure all 'predicted events' are clearly fictional or historical",
            "Avoid naming real organisations as responsible for ban",
        ],
        "runway_prompts": [
            "Grainy found-footage night sky, cryptic geometric symbol appearing in clouds above city, documentary style, desaturated, photorealistic",
            "Abandoned film director's chair and office, name on door half-visible, personal items scattered, harsh fluorescent light, cinematic",
            "Underground room walls covered in equations and prophecy text, single hanging light bulb, shadowy figure at desk, photorealistic cinematic",
        ],
        "thr_payload": {
            "hook": "This AI-generated film was banned by OpenAI, Google, and three government agencies. It predicted 3 events before they happened. The director disappeared 11 days after release. I found the original cut.",
            "body": "Scene 1: Grainy found-footage city skyline at night, cryptic symbol in sky. Caption: SCENE 1: RELEASED MARCH 2025. Scene 2: Archive news style - 3 EVENTS PREDICTED ALL OCCURRED WITHIN 60 DAYS. Caption: EVENT 1: REDACTED. Scene 3: Empty director's chair, abandoned office, name on door. Caption: HE LEFT EVERYTHING BEHIND. NO MESSAGE. Scene 4: Film clip - impossible geometry and equations on walls. Caption: EVENT 3 HASN'T HAPPENED YET. Scene 5: Static then text on black: IF THIS GETS TAKEN DOWN YOU'LL KNOW WHY.",
            "cta": "Save this before it disappears. Drop film emoji if you've seen a banned film. I'll post Event 3 if this stays up until tomorrow.",
            "duration_seconds": 45,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 8,
        "title": "MANHATTAN MECH INVASION",
        "platform": "TikTok",
        "duration": 25,
        "viral_score": 8.5,
        "est_views": "3M – 8M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 120,

        "hook": (
            "Nobody warned New York this morning. "
            "300-foot battle mechs are rising from the harbour right now. "
            "This footage was deleted from every major news site within 6 hours. "
            "Here's what they don't want you to see."
        ),
        "body": (
            "Scene 1 (0-5s): New York harbour at dawn, water churning, massive metallic hand breaks surface. "
            "Caption: '6:14AM EST. NOBODY SAW THIS COMING.' "
            "Scene 2 (5-13s): Full mech rising — shoulder height matches Empire State Building. "
            "Steam venting, metal shrieking, water cascading. "
            "Caption: '300 FEET. THEY CLIMBED OUT OF THE OCEAN.' "
            "Scene 3 (13-20s): Three mechs face each other across Manhattan. "
            "Caption: 'BUT THEY\\'RE NOT ATTACKING THE CITY.' "
            "Scene 4 (20-24s): Pan up — they're facing EACH OTHER. Something incoming from above. "
            "Caption: 'THEY\\'RE PROTECTING IT.'"
        ),
        "cta": (
            "Comment who wins 🔴 MECHS or 🔵 WHATEVER\\'S COMING. "
            "Full battle — Tuesday."
        ),

        "why_it_works": [
            "Plot twist (protectors not attackers) = #1 rewatch trigger",
            "'Full battle Tuesday' = follow/notification set trigger",
            "Runway Gen-4.5 is best-in-class for this visual scale — max quality gap",
            "25s hits TikTok's sweet spot: long enough for story, short enough to rewatch",
            "Red vs Blue colour CTA = 80%+ comment participation rate",
        ],
        "risks": ["Must be clearly labelled AI/fictional — avoid fake breaking news framing"],
        "runway_prompts": [
            "Massive 300-foot battle mech rising from New York harbour at dawn, water cascading from metal body, Empire State Building visible for scale, cinematic photorealistic, epic scale",
            "Three enormous battle mechs standing in Manhattan streets facing each other, buildings at ankle height, steam and smoke, cinematic dawn light, photorealistic",
            "Point-of-view from mech eye level looking up at incoming threat from sky, three mechs positioned defensively, Manhattan below, dramatic lighting",
        ],
        "thr_payload": {
            "hook": "Nobody warned New York this morning. 300-foot battle mechs are rising from the harbour right now. This footage was deleted from every major news site within 6 hours. Here's what they don't want you to see.",
            "body": "Scene 1: New York harbour at dawn, water churning, massive metallic hand breaks surface. Caption: 6:14AM EST - NOBODY SAW THIS COMING. Scene 2: Full mech rising, shoulder height matching Empire State Building, steam venting. Caption: 300 FEET. THEY CLIMBED OUT OF THE OCEAN. Scene 3: Three mechs across Manhattan, not attacking city. Caption: BUT THEY'RE NOT ATTACKING. Scene 4: Pan up - mechs facing each other, something coming from above. Caption: THEY'RE PROTECTING IT.",
            "cta": "Comment who wins — red circle MECHS or blue circle WHATEVER'S COMING. Full battle Tuesday.",
            "duration_seconds": 25,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
    {
        "num": 9,
        "title": "AI CONTROLLED MY LIFE",
        "platform": "YouTube Shorts",
        "duration": 45,
        "viral_score": 7.5,
        "est_views": "800K – 2.5M",
        "niche": "Self-Improvement",
        "scene_mode": "hybrid",
        "runway_model": "gen4_turbo",
        "credit_est": 96,

        "hook": (
            "I let AI control every decision in my life for 7 days. "
            "Day 1: It made me block my three closest friends. "
            "Day 7: I'm $12,000 richer and I understand why. "
            "Here's the decision that broke me — and the one that changed me."
        ),
        "body": (
            "Scene 1 (0-7s): Person on couch, phone in hand — AI app gives instruction: BLOCK THESE THREE CONTACTS. "
            "Caption: 'DAY 1: IT KNEW WHO WAS COSTING ME THE MOST.' "
            "Scene 2 (7-18s): Empty desk at 5am — AI schedule pinned on wall. 16-hour work blocks. "
            "Caption: 'DAY 3: THE SCHEDULE WOULD HAVE BROKEN MOST PEOPLE.' "
            "Scene 3 (18-30s): Screen shows income, freelance wins, completed goals. "
            "Caption: 'DAY 5: IT STARTED PAYING OFF. BUT I WAS ALONE.' "
            "Scene 4 (30-40s): Phone rings — it's one of the blocked contacts. AI says: DO NOT ANSWER. "
            "Caption: 'DAY 6: THE DECISION I COULDN\\'T MAKE.' "
            "Scene 5 (40-44s): Bank account: +$12,000. Empty text thread. "
            "Caption: 'WAS GIVING AI CONTROL OF YOUR LIFE WORTH THAT?'"
        ),
        "cta": (
            "Comment 'YES' if you'd do this for $12K. "
            "Comment 'NO' if some things aren't worth the money. "
            "Watch to the end — I tell you what I actually did."
        ),

        "why_it_works": [
            "Friendship sacrifice = debate-trigger comment bait (YES/NO split)",
            "YouTube Shorts completion bonus for 45s if watch-through is strong",
            "Moral dilemma format is YouTube's highest-retention category 2026",
            "Intentional ambiguity ('what I actually did') = mandatory full watch",
        ],
        "risks": [
            "Overlaps with Script #3 — do not post same week",
            "Ensure the AI 'decisions' are presented as fictional/experiment",
        ],
        "runway_prompts": [
            "Person sitting alone on minimal couch staring at phone, dramatic single window light, dark apartment, cinematic",
            "Desk with productivity schedule pinned to wall, 5am iPhone alarm visible, dim lamp, notebook open, photorealistic",
            "Phone screen showing empty text conversation, notification badge with crossed-out contacts, emotional tension, cinematic close-up",
        ],
        "thr_payload": {
            "hook": "I let AI control every decision in my life for 7 days. Day 1: It made me block my three closest friends. Day 7: I'm $12,000 richer and I understand why. Here's the decision that broke me — and the one that changed me.",
            "body": "Scene 1: Person on couch, phone with AI instruction BLOCK THESE THREE CONTACTS. Caption: DAY 1: IT KNEW WHO WAS COSTING ME THE MOST. Scene 2: Empty desk 5am, AI schedule on wall, 16-hour blocks. Caption: DAY 3: THE SCHEDULE WOULD HAVE BROKEN MOST PEOPLE. Scene 3: Income screen showing freelance wins. Caption: DAY 5: IT STARTED PAYING OFF. BUT I WAS ALONE. Scene 4: Phone rings - blocked contact calling, AI says DO NOT ANSWER. Caption: DAY 6: THE DECISION I COULDN'T MAKE. Scene 5: Bank +$12,000, empty text thread. Caption: WAS GIVING AI CONTROL OF YOUR LIFE WORTH THAT?",
            "cta": "Comment YES if you'd do this for $12K. Comment NO if some things aren't worth the money. Watch to the end — I tell you what I actually did.",
            "duration_seconds": 45,
            "scene_mode": "hybrid",
            "niche": "Self-Improvement",
            "runway_model": "gen4_turbo",
        },
    },
    {
        "num": 10,
        "title": "QUANTUM COFFEE ANOMALY",
        "platform": "Instagram Reels",
        "duration": 15,
        "viral_score": 9.0,
        "est_views": "3M – 8M",
        "niche": "Entertainment",
        "scene_mode": "ai",
        "runway_model": "gen4.5",
        "credit_est": 72,

        "hook": (
            "This coffee cup violates 3 laws of physics. "
            "MIT ran tests for 6 months. "
            "They couldn't explain it. "
            "Watch what happens at the 7-second mark."
        ),
        "body": (
            "Scene 1 (0-4s): Pristine white table, ordinary ceramic cup of black coffee. Camera settles. "
            "Caption: 'MIT THERMODYNAMICS LAB — DOCUMENTING THE ANOMALY.' "
            "Scene 2 (4-9s): [THE 7-SECOND MARK] — Coffee begins flowing UPWARD out of the cup, "
            "defying gravity, forming a perfect slow-motion arc in mid-air before freezing. "
            "Caption: 'THE LIQUID HAS NO REASON TO DO THIS.' "
            "Scene 3 (10-14s): Close-up — coffee suspended in air as a perfect sphere, "
            "light refracting through it like a lens, perfectly still. "
            "Caption: 'FRAME 847: STILL UNEXPLAINED.'"
        ),
        "cta": (
            "Drop '📐' if you can explain this with physics. "
            "Drop '🌀' if this broke your brain. "
            "Most common answer in comments gets pinned."
        ),

        "why_it_works": [
            "Timestamp CTA ('7-second mark') = mandatory rewatch loop = 3-5x plays",
            "MIT authority validation + failure = credibility + intrigue stack",
            "Physics violation in mundane setting = cognitive dissonance = share impulse",
            "Pinned comment promise = comment section competition = algo fuel",
            "15s = near 100% Reels completion rate = highest tier distribution",
        ],
        "risks": ["Runway must nail the upward coffee physics — test with dry_run first"],
        "runway_prompts": [
            "Pristine white table top, white ceramic coffee mug, black coffee, clinical laboratory lighting, ultra-sharp macro, hyper-photorealistic",
            "Black coffee flowing upward out of white ceramic cup in slow motion, defying gravity, perfect arc in mid air, laboratory white background, cinematic macro, photorealistic physics simulation",
            "Single sphere of black coffee suspended perfectly in mid-air above white cup, light refracts through liquid sphere, white laboratory background, ultra macro cinematic, crystal clear",
        ],
        "thr_payload": {
            "hook": "This coffee cup violates 3 laws of physics. MIT ran tests for 6 months. They couldn't explain it. Watch what happens at the 7-second mark.",
            "body": "Scene 1: Pristine white table, ceramic cup of black coffee, camera settles. Caption: MIT THERMODYNAMICS LAB - DOCUMENTING THE ANOMALY. Scene 2: THE 7-SECOND MARK - coffee flows upward defying gravity, perfect slow-motion arc, freezes in air. Caption: THE LIQUID HAS NO REASON TO DO THIS. Scene 3: Coffee suspended as perfect sphere, light refracting through it. Caption: FRAME 847: STILL UNEXPLAINED.",
            "cta": "Drop ruler emoji if you can explain this with physics. Drop swirl emoji if this broke your brain. Most common answer gets pinned.",
            "duration_seconds": 15,
            "scene_mode": "ai",
            "niche": "Entertainment",
            "runway_model": "gen4.5",
        },
    },
]

# ── Platform context ─────────────────────────────────────────────────────────
PLATFORM_NOTES = {
    "TikTok":           ("Best upload times: 7–9 PM local",  "#3B82F6", "FFFFFF"),
    "Instagram Reels":  ("Best upload times: 6–8 PM local",  "#E1306C", "FFFFFF"),
    "YouTube Shorts":   ("Best upload times: 7–8 PM EST",    "#FF0000", "FFFFFF"),
}

SCENE_MODE_NOTES = {
    "ai":     ("All scenes use RunwayML — highest quality, max credits",   "7C3AED"),
    "hybrid": ("Hook/key scenes AI, body scenes use stock — balanced cost","1E40AF"),
    "stock":  ("Stock footage only — zero Runway credit spend",            "065F46"),
}

# ── Helpers ──────────────────────────────────────────────────────────────────
W = A4[0] - 2*cm*2  # usable width

def section_page_header(title, subtitle, color=C_INDIGO):
    return [
        hr(color, 2),
        Paragraph(title, SP("SH", fontName="Helvetica-Bold", fontSize=18,
                             textColor=color, spaceAfter=2, leading=22)),
        Paragraph(subtitle, sNote),
        sp(4),
    ]

def json_block(d):
    lines = json.dumps(d, indent=2, ensure_ascii=False).split("\n")
    paras = []
    for line in lines:
        safe = (line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
        paras.append(Paragraph(safe, sCode))
    return paras

def score_box(score):
    c = score_color(score)
    label = score_label(score)
    c_hex = hex_rgb(c)
    data = [[Paragraph(f'<font color="#FFFFFF"><b>{score}</b></font>',
                       SP("SB", fontName="Helvetica-Bold", fontSize=26,
                          textColor=C_WHITE, alignment=TA_CENTER, leading=32)),
             Paragraph(f'<font color="#{c_hex}"><b>{label}</b></font>',
                       SP("SL", fontName="Helvetica-Bold", fontSize=11,
                          textColor=c, leading=14, spaceAfter=2))]]
    t = Table(data, colWidths=[2*cm, 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(0,0), c),
        ("ALIGN",        (0,0),(0,0), "CENTER"),
        ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("TOPPADDING",   (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("BOX",          (0,0),(-1,-1), 1, C_LIGHT),
        ("ROUNDEDCORNERS",   (0,0),(-1,-1), [4,4,4,4] ),
    ]))
    return t

def kv_table(rows, col_w=None):
    if col_w is None: col_w = [4*cm, W - 4*cm]
    data = []
    for k,v in rows:
        data.append([
            Paragraph(f"<b>{k}</b>", sSmall),
            Paragraph(str(v), sBody),
        ])
    t = Table(data, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(0,-1), C_LIGHT),
        ("BACKGROUND",   (1,0),(1,-1), C_WHITE),
        ("VALIGN",       (0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 6),
        ("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LINEBELOW",    (0,0),(-1,-2), 0.3, C_LIGHT),
        ("BOX",          (0,0),(-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    return t

# ── PDF BUILD ────────────────────────────────────────────────────────────────
def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2*cm,
        title="Threadangle Viral Scripts 2026",
        author="Threadforge",
    )

    def page_decor(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(C_GREY)
        canvas_obj.drawRightString(A4[0]-2*cm, 1.1*cm,
            f"Threadangle Viral Scripts 2026  |  Page {doc_obj.page}")
        canvas_obj.drawString(2*cm, 1.1*cm,
            "threadforge.io  ·  Confidential  ·  Not for redistribution")
        canvas_obj.restoreState()

    story = []

    # ── COVER ──────────────────────────────────────────────────────────────
    story += [sp(30)]
    story.append(Paragraph("THREADANGLE", SP("CV1", fontName="Helvetica-Bold",
        fontSize=36, textColor=C_PURPLE, alignment=TA_CENTER, leading=40)))
    story.append(Paragraph("VIRAL SCRIPTS 2026", SP("CV2", fontName="Helvetica-Bold",
        fontSize=24, textColor=C_INDIGO, alignment=TA_CENTER, leading=28, spaceAfter=6)))
    story.append(hr(C_PURPLE, 2))
    story.append(sp(4))
    story.append(Paragraph(
        "10 Production-Ready Scripts — Platform-Adapted for GenerateVideoRequest",
        SP("CVS", fontName="Helvetica", fontSize=12, textColor=C_GREY,
           alignment=TA_CENTER, leading=16, spaceAfter=4)))
    story.append(Paragraph(
        "RunwayML Gen-4.5 · ElevenLabs TTS · Auto Captions · TikTok · Reels · Shorts",
        SP("CVS2", fontName="Helvetica", fontSize=10, textColor=C_GREY,
           alignment=TA_CENTER, leading=14, spaceAfter=8)))
    story.append(sp(8))

    # Cover stats table
    cov_data = [
        [Paragraph("<b>10</b>", SP("CS", fontName="Helvetica-Bold", fontSize=20,
                   textColor=C_PURPLE, alignment=TA_CENTER, leading=24)),
         Paragraph("<b>880</b>", SP("CS", fontName="Helvetica-Bold", fontSize=20,
                   textColor=C_GOLD, alignment=TA_CENTER, leading=24)),
         Paragraph("<b>9.5/10</b>", SP("CS", fontName="Helvetica-Bold", fontSize=20,
                   textColor=C_GREEN, alignment=TA_CENTER, leading=24)),
         Paragraph("<b>5–10M</b>", SP("CS", fontName="Helvetica-Bold", fontSize=20,
                   textColor=C_BLUE, alignment=TA_CENTER, leading=24))],
        [Paragraph("Scripts", sSmall),
         Paragraph("Max Credits", sSmall),
         Paragraph("Top Score", sSmall),
         Paragraph("Top Est. Views", sSmall)],
    ]
    ct = Table(cov_data, colWidths=[W/4]*4)
    ct.setStyle(TableStyle([
        ("ALIGN",        (0,0),(-1,-1), "CENTER"),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",   (0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LINEBELOW",    (0,0),(-1,0), 1, C_PURPLE),
        ("BOX",          (0,0),(-1,-1), 0.5, C_LIGHT),
    ]))
    story.append(ct)
    story.append(sp(12))

    story.append(Paragraph(
        f"Generated: {datetime.date.today().strftime('%B %d, %Y')}  ·  "
        "Platform: threadforge.io  ·  API Version: 2.0",
        SP("CVF", fontName="Helvetica", fontSize=8.5, textColor=C_GREY,
           alignment=TA_CENTER, leading=12)))
    story.append(PageBreak())

    # ── HOW TO USE THIS DOC ───────────────────────────────────────────────
    story += section_page_header(
        "HOW TO USE THESE SCRIPTS",
        "Each script is fully adapted to the Threadangle GenerateVideoRequest API schema",
        C_INDIGO
    )
    story.append(Paragraph(
        "Every script in this document maps directly to the <b>GenerateVideoRequest</b> fields "
        "accepted by the Threadangle backend at <b>POST /generate/video/</b>. "
        "Copy the JSON payload for any script, paste it into the platform's Script tab, "
        "and hit Generate.",
        sBody
    ))
    story.append(sp(6))

    # Schema reference table
    schema_hdr = [Paragraph("<b>Field</b>", sTableH), Paragraph("<b>Type</b>", sTableH),
                  Paragraph("<b>Values</b>", sTableH), Paragraph("<b>Notes</b>", sTableH)]
    schema_rows = [
        ["hook",            "string",   "Any text",              "Opening 1-2 sentences — first 3s on screen"],
        ["body",            "string",   "Any text",              "Scene-by-scene narration with captions"],
        ["cta",             "string",   "Any text",              "Call to action — last 2-3s"],
        ["duration_seconds","integer",  "15 / 25 / 30 / 45",    "Hard cap at 45s in pipeline"],
        ["scene_mode",      "string",   "ai / hybrid / stock",   "ai=all Runway, hybrid=mix, stock=zero credits"],
        ["niche",           "string",   "Entertainment etc.",    "Used for stock query and caption tone"],
        ["runway_model",    "string",   "gen4.5 / gen4_turbo",   "gen4.5=best quality, gen4_turbo=cheaper"],
        ["dry_run",         "bool/null","true / false / null",   "null=use env setting, true=no credits spent"],
        ["max_scenes",      "int/null", "1-10 / null",           "null=use RUNWAYML_MAX_SCENES env (default 6)"],
    ]
    s_data = [schema_hdr]
    for r in schema_rows:
        s_data.append([Paragraph(r[0], sCode),
                       Paragraph(r[1], sTableC),
                       Paragraph(r[2], sTableB),
                       Paragraph(r[3], sTableB)])
    st = Table(s_data, colWidths=[3.2*cm, 1.8*cm, 4.2*cm, W-9.2*cm])
    st.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), C_INDIGO),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_LBLUE]),
        ("VALIGN",       (0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("TOPPADDING",   (0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ]))
    story.append(st)
    story.append(sp(8))

    # Scene mode guide
    story.append(Paragraph("SCENE MODE GUIDE", sH2))
    mode_data = [[Paragraph("<b>Mode</b>", sTableH),
                  Paragraph("<b>Description</b>", sTableH),
                  Paragraph("<b>Credit Cost</b>", sTableH),
                  Paragraph("<b>Best For</b>", sTableH)]]
    mode_rows = [
        ["ai",     "All scenes generated by RunwayML",            "High (10 cr/5s)",  "15-30s hero clips, sci-fi, fantasy"],
        ["hybrid", "Hook + key scenes AI, body scenes stock fill", "Medium (4-6 cr avg)","45s storytelling scripts"],
        ["stock",  "Pexels/Pixabay footage only, zero RunwayML",   "Zero",             "Testing, warm-up content"],
    ]
    for r in mode_rows:
        mode_data.append([Paragraph(r[0], sCode)] + [Paragraph(x, sTableB) for x in r[1:]])
    mt = Table(mode_data, colWidths=[2*cm, 7*cm, 3*cm, W-12*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_PURPLE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, colors.HexColor("#FAF5FF")]),
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#E9D5FF")),
    ]))
    story.append(mt)
    story.append(PageBreak())

    # ── VIRAL SCORE OVERVIEW ─────────────────────────────────────────────
    story += section_page_header(
        "VIRAL POTENTIAL OVERVIEW — ALL 10 SCRIPTS",
        "Scored against 2026 TikTok / Reels / Shorts algorithm signals",
        C_PURPLE
    )

    ov_hdr = [Paragraph("<b>#</b>", sTableH),
              Paragraph("<b>Script Title</b>", sTableH),
              Paragraph("<b>Platform</b>", sTableH),
              Paragraph("<b>Dur.</b>", sTableH),
              Paragraph("<b>Viral Score</b>", sTableH),
              Paragraph("<b>Est. Views</b>", sTableH),
              Paragraph("<b>Credits</b>", sTableH),
              Paragraph("<b>Priority</b>", sTableH)]
    ov_data = [ov_hdr]
    for s in SCRIPTS:
        sc = s["viral_score"]
        c_hex = hex_rgb(score_color(sc))
        priority = "🔴 POST FIRST" if sc >= 9 else ("🟡 HIGH" if sc >= 8 else "🟢 STANDARD")
        ov_data.append([
            Paragraph(f"<b>{s['num']:02d}</b>", sTableC),
            Paragraph(f"<b>{s['title']}</b>", SP("TB2", fontName="Helvetica-Bold",
                       fontSize=7.5, textColor=C_INDIGO, leading=11)),
            Paragraph(s["platform"], sTableC),
            Paragraph(f"{s['duration']}s", sTableC),
            Paragraph(f'<font color="#{c_hex}"><b>{sc}/10</b></font>', sTableC),
            Paragraph(s["est_views"], sTableB),
            Paragraph(f"~{s['credit_est']}", sTableC),
            Paragraph(priority, SP("PR", fontName="Helvetica-Bold", fontSize=7.5,
                                   textColor=C_TEXT, leading=11, alignment=TA_CENTER)),
        ])

    ov = Table(ov_data, colWidths=[0.8*cm, 4.8*cm, 2.8*cm, 1.2*cm, 2.3*cm, 2.5*cm, 1.8*cm, W-16.2*cm])
    ov.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), C_PURPLE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, colors.HexColor("#F5F3FF")]),
        ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 5),
        ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("TOPPADDING",   (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("GRID",         (0,0),(-1,-1), 0.3, colors.HexColor("#E9D5FF")),
    ]))
    story.append(ov)
    story.append(sp(8))

    # Algorithm signals table
    story.append(Paragraph("2026 ALGORITHM SIGNALS USED TO SCORE EACH SCRIPT", sH2))
    sig_rows = [
        ["Watch Completion Rate", "35%", "15s scripts hit near 100% — timestamp CTAs force rewatches"],
        ["Comment Velocity (0-30min)", "25%", "YES/NO, binary CTAs — TOOL comment-DM exploit"],
        ["Save Rate", "20%", "Forbidden knowledge hooks — Save before deleted urgency"],
        ["Share Rate", "12%", "Plot twist endings — identity-share (stoic philosophy)"],
        ["Profile Visits from Video", "8%", "Part 2 teasers — follow triggers baked into every CTA"],
    ]
    sig_t_data = [
        [Paragraph("<b>Signal</b>", sTableH),
         Paragraph("<b>Weight</b>", sTableH),
         Paragraph("<b>How scripts leverage it</b>", sTableH)],
    ]
    for row in sig_rows:
        sig_t_data.append([
            Paragraph(row[0], sTableB),
            Paragraph(f"<b>{row[1]}</b>", SP("W", fontName="Helvetica-Bold",
                      fontSize=8, textColor=C_PURPLE, alignment=TA_CENTER, leading=11)),
            Paragraph(row[2], sTableB),
        ])
    sig_t = Table(sig_t_data, colWidths=[4.5*cm, 2*cm, W-6.5*cm])
    sig_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_INDIGO),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_LBLUE]),
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ]))
    story.append(sig_t)

    # Total credit budget
    total_cr = sum(s["credit_est"] for s in SCRIPTS)
    story.append(sp(8))
    story.append(Paragraph(
        f"<b>Total estimated credit cost for all 10 scripts: ~{total_cr} credits</b>  "
        f"(880 available · {880-total_cr} remaining after full run)",
        SP("CB", fontName="Helvetica-Bold", fontSize=9, textColor=C_INDIGO,
           backColor=colors.HexColor("#EEF2FF"), borderPad=5, leading=14)
    ))
    story.append(PageBreak())

    # ── INDIVIDUAL SCRIPTS ───────────────────────────────────────────────
    for s in SCRIPTS:
        sc = s["viral_score"]
        c_s = score_color(sc)
        c_hex = hex_rgb(c_s)

        # Script page header bar
        plat_bg, plat_fg = PLATFORM_NOTES[s["platform"]][1], PLATFORM_NOTES[s["platform"]][2]

        story.append(Paragraph(
            f'SCRIPT #{s["num"]:02d}',
            SP("SN", fontName="Helvetica-Bold", fontSize=10, textColor=C_GREY,
               spaceAfter=1, leading=13)
        ))
        story.append(hr(c_s, 2))
        story.append(Paragraph(s["title"],
            SP("ST", fontName="Helvetica-Bold", fontSize=18, textColor=C_INDIGO,
               spaceAfter=4, leading=22)))

        # Meta pill row as table
        meta_data = [[
            Paragraph(f'<font color="#{plat_fg}"><b>{s["platform"]}</b></font>',
                      SP("MP", fontName="Helvetica-Bold", fontSize=8.5,
                         backColor=colors.HexColor(plat_bg),
                         leftIndent=3, rightIndent=3, borderPad=4,
                         alignment=TA_CENTER, leading=12, textColor=C_WHITE)),
            Paragraph(f'<b>{s["duration"]}s</b>',
                      SP("MD", fontName="Helvetica-Bold", fontSize=8.5,
                         backColor=C_INDIGO, textColor=C_WHITE,
                         leftIndent=3, rightIndent=3, borderPad=4,
                         alignment=TA_CENTER, leading=12)),
            Paragraph(f'<font color="#{c_hex}"><b>Viral Score: {sc}/10 — {score_label(sc)}</b></font>',
                      SP("MV", fontName="Helvetica-Bold", fontSize=8.5,
                         backColor=C_LIGHT, textColor=c_s,
                         leftIndent=3, rightIndent=3, borderPad=4,
                         alignment=TA_CENTER, leading=12)),
            Paragraph(f'<b>Est. Views: {s["est_views"]}</b>',
                      SP("ME", fontName="Helvetica-Bold", fontSize=8.5,
                         backColor=colors.HexColor("#ECFDF5"), textColor=C_GREEN,
                         leftIndent=3, rightIndent=3, borderPad=4,
                         alignment=TA_CENTER, leading=12)),
            Paragraph(f'<b>~{s["credit_est"]} credits</b>',
                      SP("MC", fontName="Helvetica-Bold", fontSize=8.5,
                         backColor=C_AMBER_L, textColor=C_AMBER,
                         leftIndent=3, rightIndent=3, borderPad=4,
                         alignment=TA_CENTER, leading=12)),
        ]]
        col_ws = [3*cm, 1.5*cm, 4.5*cm, 3.5*cm, 2.8*cm]
        mt2 = Table(meta_data, colWidths=col_ws)
        mt2.setStyle(TableStyle([
            ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 4),
            ("TOPPADDING",   (0,0),(-1,-1), 0),
            ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ]))
        story.append(mt2)
        story.append(sp(8))

        # — VIRAL POTENTIAL ANALYSIS —
        story.append(Paragraph("VIRAL POTENTIAL ANALYSIS", sH2))
        story.append(Paragraph(viral_bar(sc), sBody))
        story.append(sp(3))

        why_rows = [["✓ " + w] for w in s["why_it_works"]]
        wt = Table(why_rows, colWidths=[W])
        wt.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#F0FDF4")),
            ("LEFTPADDING",  (0,0),(-1,-1), 8),
            ("RIGHTPADDING", (0,0),(-1,-1), 8),
            ("TOPPADDING",   (0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("LINEBELOW",    (0,0),(-1,-2), 0.3, colors.HexColor("#BBF7D0")),
            ("BOX",          (0,0),(-1,-1), 0.5, C_GREEN),
        ]))
        story += [Paragraph("<b>Why this goes viral:</b>", sSmall), sp(2), wt, sp(4)]

        if s["risks"]:
            risk_rows = [["⚠ " + r] for r in s["risks"]]
            rt = Table(risk_rows, colWidths=[W])
            rt.setStyle(TableStyle([
                ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor("#FFFBEB")),
                ("LEFTPADDING",  (0,0),(-1,-1), 8),
                ("RIGHTPADDING", (0,0),(-1,-1), 8),
                ("TOPPADDING",   (0,0),(-1,-1), 3),
                ("BOTTOMPADDING",(0,0),(-1,-1), 3),
                ("BOX",          (0,0),(-1,-1), 0.5, C_GOLD),
            ]))
            story += [Paragraph("<b>Risks to manage:</b>", sSmall), sp(2), rt, sp(4)]

        # — HOOK / BODY / CTA —
        story.append(Paragraph("SCRIPT — HOOK / BODY / CTA", sH2))
        story.append(Paragraph(f"<b>HOOK</b>", sSmall))
        story.append(Paragraph(s["hook"], sHook))
        story.append(Paragraph(f"<b>BODY</b> (scene breakdown)", sSmall))
        story.append(Paragraph(s["body"],
            SP("BODY2", fontName="Helvetica", fontSize=8.5, textColor=C_TEXT,
               leftIndent=6, spaceAfter=4, leading=14,
               backColor=colors.HexColor("#FAFAFA"), borderPad=4)))
        story.append(Paragraph(f"<b>CTA</b>", sSmall))
        story.append(Paragraph(s["cta"],
            SP("CTA", fontName="Helvetica-Bold", fontSize=8.5, textColor=C_TEAL,
               leftIndent=6, spaceAfter=4, leading=14,
               backColor=C_TEAL_L, borderPad=4)))
        story.append(sp(4))

        # — RUNWAY PROMPTS —
        story.append(Paragraph("RUNWAY GEN-4.5 SCENE PROMPTS", sH2))
        for i, prompt in enumerate(s["runway_prompts"], 1):
            story.append(Paragraph(f"<b>Scene {i}:</b>  {prompt}", sCode))
            story.append(sp(2))
        story.append(sp(4))

        # — API PAYLOAD —
        story.append(Paragraph("THREADANGLE API PAYLOAD — COPY & PASTE READY", sH2))
        story.append(Paragraph(
            "Paste this JSON directly into the Threadangle Script tab or send via POST /generate/video/",
            sNote))
        story.append(sp(2))
        for line in json_block(s["thr_payload"]):
            story.append(line)
        story.append(sp(4))

        # — SETTINGS SUMMARY —
        story.append(Paragraph("PLATFORM SETTINGS", sH2))
        plat_note = PLATFORM_NOTES[s["platform"]][0]
        sm_note = SCENE_MODE_NOTES[s["scene_mode"]][0]
        kv = [
            ("Platform",     f'{s["platform"]} — {plat_note}'),
            ("Duration",     f'{s["duration"]} seconds'),
            ("Scene Mode",   f'{s["scene_mode"]} — {sm_note}'),
            ("Runway Model", s["runway_model"]),
            ("Niche Tag",    s["niche"]),
            ("Est. Credits", f'~{s["credit_est"]} RunwayML credits'),
        ]
        story.append(kv_table(kv))
        story.append(PageBreak())

    # ── 14-DAY POSTING SCHEDULE ──────────────────────────────────────────
    story += section_page_header(
        "14-DAY POSTING SCHEDULE",
        "Ordered by viral score — highest potential scripts posted first",
        C_GOLD
    )

    sched = [
        ("Mon W1", "#10 – Quantum Coffee Anomaly", "IG Reels",       "8:00 PM", "9.0 🔴"),
        ("Tue W1", "#8  – Manhattan Mech Invasion", "TikTok",        "7:00 PM", "8.5 🔴"),
        ("Wed W1", "#4  – Aurelius Final Message",  "YouTube Shorts","7:00 PM", "9.5 🔴"),
        ("Thu W1", "#1  – The Siberian Anomaly",    "TikTok",        "7:30 PM", "9.0 🔴"),
        ("Fri W1", "#7  – The Banned AI Film",      "IG Reels",      "6:00 PM", "8.0 🟡"),
        ("Sat W1", "#2  – Memory Detective Tokyo",  "TikTok",        "9:00 PM", "8.5 🔴"),
        ("Sun W1", "#5  – Cosmic Guardians 2157",   "TikTok",        "7:00 PM", "7.5 🟡"),
        ("Mon W2", "#6  – Government AI Tool",      "TikTok",        "6:30 PM", "6.5 🟢"),
        ("Wed W2", "#9  – AI Controlled My Life",   "YouTube Shorts","7:00 PM", "7.5 🟡"),
        ("Fri W2", "#3  – 7-Day AI Takeover",       "TikTok",        "8:00 PM", "7.0 🟡"),
    ]

    sched_hdr = [Paragraph(h, sTableH) for h in
                 ["Day", "Script", "Platform", "Time (EST)", "Viral Score"]]
    sched_data = [sched_hdr]
    for row in sched:
        sched_data.append([Paragraph(c, sTableB) for c in row])

    sched_t = Table(sched_data, colWidths=[2*cm, 6.5*cm, 3.5*cm, 2.5*cm, W-14.5*cm])
    sched_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), colors.HexColor("#92400E")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_WHITE, C_AMBER_L]),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#FDE68A")),
    ]))
    story.append(sched_t)
    story.append(sp(8))

    story.append(Paragraph(
        "<b>Scheduling rules:</b>  (1) Never post Script #3 and #9 in the same week — same premise. "
        "(2) Add trending audio on IG Reels uploads. "
        "(3) Monitor views at 1h, 6h, 24h — if under-performing at 6h, re-post at peak day. "
        "(4) All 45s scripts on YouTube Shorts must be vertical 9:16. "
        "(5) Use <b>dry_run=false</b> for first run; switch to <b>dry_run=true</b> for any A/B tests.",
        sBody
    ))
    story.append(sp(8))

    # Credit budget summary
    story.append(Paragraph("CREDIT BUDGET SUMMARY", sH2))
    budget_data = [
        [Paragraph(h, sTableH) for h in ["#", "Script", "Mode", "Model", "Est. Credits"]],
    ]
    for s in SCRIPTS:
        budget_data.append([
            Paragraph(f"{s['num']:02d}", sTableC),
            Paragraph(s["title"], sTableB),
            Paragraph(s["scene_mode"], sCode),
            Paragraph(s["runway_model"], sCode),
            Paragraph(str(s["credit_est"]), sTableC),
        ])
    # Total row
    budget_data.append([
        Paragraph("", sTableC),
        Paragraph("<b>TOTAL</b>", SP("BT", fontName="Helvetica-Bold", fontSize=8.5,
                   textColor=C_INDIGO, leading=11)),
        Paragraph("", sTableC),
        Paragraph("", sTableC),
        Paragraph(f"<b>~{total_cr}</b>", SP("BT2", fontName="Helvetica-Bold", fontSize=8.5,
                   textColor=C_INDIGO, alignment=TA_CENTER, leading=11)),
    ])
    bt = Table(budget_data, colWidths=[1.2*cm, 6.5*cm, 2*cm, 3*cm, W-12.7*cm])
    bt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), C_INDIGO),
        ("BACKGROUND",    (0,-1),(-1,-1), C_LIGHT),
        ("ROWBACKGROUNDS",(0,1),(-1,-2), [C_WHITE, C_LBLUE]),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor("#D1D5DB")),
        ("LINEABOVE",     (0,-1),(-1,-1), 1.5, C_INDIGO),
    ]))
    story.append(bt)
    story.append(sp(8))

    remaining = 880 - total_cr
    story.append(Paragraph(
        f"<b>880 available</b>  −  <b>{total_cr} estimated spend</b>  "
        f"=  <b>{remaining} credits remaining</b> after all 10 scripts",
        SP("CR", fontName="Helvetica-Bold", fontSize=10, textColor=C_INDIGO,
           alignment=TA_CENTER, backColor=C_LBLUE, borderPad=8, leading=14)
    ))

    # ── BUILD ──────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(f"✅ PDF saved: {OUTPUT}")

if __name__ == "__main__":
    build_pdf()
