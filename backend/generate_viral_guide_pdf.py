"""
Generate the Master Viral AI Video Guide PDF.
Run: python generate_viral_guide_pdf.py
Output: F:\Threadforge\Master_Viral_AI_Video_Guide_2026.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.flowables import BalancedColumns
from reportlab.pdfgen import canvas
from pathlib import Path
import datetime

OUTPUT = Path(__file__).resolve().parents[1] / "Master_Viral_AI_Video_Guide_2026.pdf"

# ── Colour palette ─────────────────────────────────────────────────────────
C_BG       = colors.HexColor("#0F0F0F")
C_ACCENT   = colors.HexColor("#7C3AED")   # purple
C_GOLD     = colors.HexColor("#F59E0B")   # amber
C_GREEN    = colors.HexColor("#10B981")
C_RED      = colors.HexColor("#EF4444")
C_TEXT     = colors.HexColor("#1F2937")
C_SUBTEXT  = colors.HexColor("#6B7280")
C_WHITE    = colors.white
C_LIGHT    = colors.HexColor("#F3F4F6")
C_HEADER   = colors.HexColor("#1E1B4B")   # deep indigo

# ── Page numbering canvas ──────────────────────────────────────────────────
def _add_page_number(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(C_SUBTEXT)
    canvas_obj.drawRightString(
        A4[0] - 1.5*cm, 1*cm,
        f"Master Viral AI Video Guide 2026  |  Page {doc.page}"
    )
    canvas_obj.drawString(1.5*cm, 1*cm, "© 2026 Threadforge · Confidential")
    canvas_obj.restoreState()

# ── Style sheet ────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

sTitle = S("sTitle",
    fontName="Helvetica-Bold", fontSize=28, textColor=C_WHITE,
    alignment=TA_CENTER, spaceAfter=6, leading=34)

sSubtitle = S("sSubtitle",
    fontName="Helvetica", fontSize=13, textColor=colors.HexColor("#C4B5FD"),
    alignment=TA_CENTER, spaceAfter=4, leading=18)

sH1 = S("sH1",
    fontName="Helvetica-Bold", fontSize=16, textColor=C_ACCENT,
    spaceBefore=14, spaceAfter=6, leading=22,
    borderPad=4)

sH2 = S("sH2",
    fontName="Helvetica-Bold", fontSize=13, textColor=C_HEADER,
    spaceBefore=10, spaceAfter=4, leading=18)

sH3 = S("sH3",
    fontName="Helvetica-Bold", fontSize=11, textColor=C_TEXT,
    spaceBefore=6, spaceAfter=3, leading=15)

sBody = S("sBody",
    fontName="Helvetica", fontSize=9.5, textColor=C_TEXT,
    spaceAfter=5, leading=15, alignment=TA_JUSTIFY)

sBullet = S("sBullet",
    fontName="Helvetica", fontSize=9.5, textColor=C_TEXT,
    spaceAfter=3, leading=14, leftIndent=14,
    bulletIndent=4, bulletFontSize=9)

sCode = S("sCode",
    fontName="Courier", fontSize=8.5, textColor=colors.HexColor("#1E40AF"),
    backColor=colors.HexColor("#EFF6FF"),
    spaceAfter=4, leading=13, leftIndent=8, rightIndent=8,
    borderPad=4)

sCaption = S("sCaption",
    fontName="Helvetica-Bold", fontSize=9, textColor=C_GOLD,
    spaceAfter=2, leading=13)

sLabel = S("sLabel",
    fontName="Helvetica-Bold", fontSize=8, textColor=C_SUBTEXT,
    spaceAfter=1, leading=11)

sNote = S("sNote",
    fontName="Helvetica-Oblique", fontSize=8.5, textColor=C_SUBTEXT,
    spaceAfter=3, leading=13)

sCTA = S("sCTA",
    fontName="Helvetica-Bold", fontSize=9.5, textColor=C_GREEN,
    spaceAfter=3, leading=14)

# ── Helper builders ────────────────────────────────────────────────────────
def hr(color=C_ACCENT, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=4)

def sp(h=6):
    return Spacer(1, h)

def h1(text):
    return Paragraph(text, sH1)

def h2(text):
    return Paragraph(text, sH2)

def h3(text):
    return Paragraph(text, sH3)

def body(text):
    return Paragraph(text, sBody)

def note(text):
    return Paragraph(f"<i>{text}</i>", sNote)

def bullet(text):
    return Paragraph(f"• {text}", sBullet)

def code(text):
    return Paragraph(text, sCode)

def rating_badge(score, label=""):
    color_map = {10: C_GREEN, 9: C_GREEN, 8: C_GREEN,
                 7: C_GOLD, 6: C_GOLD, 5: C_GOLD,
                 4: C_RED, 3: C_RED}
    c = color_map.get(score, C_RED)
    hex_str = '%02x%02x%02x' % (int(c.red * 255), int(c.green * 255), int(c.blue * 255))
    return f'<font color="#{hex_str}"><b>{score}/10</b></font> {label}'

def section_header(title, subtitle=""):
    elems = []
    elems.append(sp(8))
    elems.append(hr(C_ACCENT, 2))
    elems.append(h1(title))
    if subtitle:
        elems.append(Paragraph(subtitle, sNote))
    elems.append(hr(C_ACCENT, 0.5))
    return elems

def script_block(label, text):
    """Coloured block for hook/body/cta."""
    color_map = {"HOOK": "#7C3AED", "BODY": "#1E40AF", "CTA": "#065F46"}
    hex_c = color_map.get(label.upper(), "#374151")
    return Paragraph(
        f'<font color="{hex_c}"><b>[{label.upper()}]</b></font>  {text}',
        ParagraphStyle("sb", fontName="Helvetica", fontSize=9, textColor=C_TEXT,
                       leading=14, spaceAfter=4, leftIndent=10,
                       backColor=colors.HexColor("#F9FAFB"), borderPad=3)
    )

def frame_table(rows):
    """Build a scene-breakdown table. rows = list of (scene, time, narration, score, caption)"""
    col_widths = [1.0*cm, 1.4*cm, 7.2*cm, 1.4*cm, 3.8*cm]
    header = [
        Paragraph("<b>Sc.</b>", sLabel),
        Paragraph("<b>Time</b>", sLabel),
        Paragraph("<b>Narration / Runway Prompt</b>", sLabel),
        Paragraph("<b>Score</b>", sLabel),
        Paragraph("<b>Caption Overlay</b>", sCaption),
    ]
    data = [header]
    for r in rows:
        data.append([
            Paragraph(str(r[0]), sBody),
            Paragraph(r[1], sBody),
            Paragraph(r[2], sBody),
            Paragraph(rating_badge(r[3]), sBody),
            Paragraph(f'<b>{r[4]}</b>', sCaption),
        ])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_HEADER),
        ("TEXTCOLOR",  (0,0), (-1,0), C_WHITE),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,0), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
    ]))
    return t

def json_block(text):
    lines = text.strip().split("\n")
    elems = []
    for ln in lines:
        elems.append(Paragraph(ln.replace(" ", "&nbsp;"), sCode))
    return elems

# ══════════════════════════════════════════════════════════════════════════════
# BUILD DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title="Master Viral AI Video Guide 2026",
    author="Threadforge",
    subject="Viral AI Video Scripts, Platform Analysis & Production Plan",
)

story = []

# ── COVER PAGE ────────────────────────────────────────────────────────────
cover_bg = Table(
    [[Paragraph("THE MASTER VIRAL AI VIDEO GUIDE", sTitle)],
     [Paragraph("2026 Edition", sSubtitle)],
     [sp(4)],
     [Paragraph("10 Viral Formats · Platform Algorithm Analysis · Production-Ready Scripts", sSubtitle)],
     [sp(4)],
     [Paragraph("Deep Capability Match · Credit Budget Plan · Posting Schedule", sSubtitle)],
     [sp(12)],
     [Paragraph("Powered by Threadforge · RunwayML Gen-4.5 · ElevenLabs", sSubtitle)],
    ],
    colWidths=[16.4*cm]
)
cover_bg.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), C_HEADER),
    ("TOPPADDING",    (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ("LEFTPADDING",   (0,0), (-1,-1), 20),
    ("RIGHTPADDING",  (0,0), (-1,-1), 20),
    ("ROUNDEDCORNERS", (0,0), (-1,-1), [8,8,8,8]),
]))
story.append(cover_bg)
story.append(sp(8))
story.append(HRFlowable(width="100%", thickness=3, color=C_ACCENT))
story.append(sp(4))
story.append(Paragraph(
    f"Generated {datetime.date.today().strftime('%B %d, %Y')}  ·  Confidential — Internal Use Only",
    sNote))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PART 1 — PLATFORM CAPABILITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
story += section_header("PART 1 — Platform Capability Analysis",
    "How Threadforge compares to the tools used in each viral format")

story.append(h2("Threadforge Capability Baseline"))
cap_data = [
    [Paragraph("<b>Capability</b>", sLabel), Paragraph("<b>Threadforge</b>", sLabel), Paragraph("<b>Competitor Tools</b>", sLabel)],
    ["Text-to-video", "✅ RunwayML Gen-4.5 / Gen-4_turbo", "Luma, Sora 2, Veo 3, Pika"],
    ["Image-to-video", "✅ Runway image_to_video endpoint", "Luma Dream Machine"],
    ["Video-to-video restyle", "❌ Not available", "Runway V2V, Luma"],
    ["AI voice narration", "✅ ElevenLabs (Rachel, multilingual)", "ElevenLabs, Pika"],
    ["Lip-sync animation", "❌ Not available", "HeyGen"],
    ["Motion brush (per-object)", "❌ Not available", "Pika 2.5, Runway"],
    ["Custom music generation", "❌ Not available", "Udio, Suno"],
    ["Auto-captions (TikTok style)", "✅ ASS/MrBeast-style", "Veed.io, CapCut"],
    ["Max video duration", "⚠️ 45s hard cap", "60-120s elsewhere"],
    ["Vertical 9:16 format", "✅ 720×1280 native", "All platforms"],
    ["Hook/Body/CTA auto-planning", "✅ Automatic scene planning", "Manual elsewhere"],
    ["Stock footage fallback", "✅ Pexels + Pixabay auto-search", "Manual download"],
    ["Credit auto-budgeting", "✅ 70% budget cap, gen4.5 for hooks", "Manual everywhere"],
]
cap_table = Table(cap_data, colWidths=[5*cm, 6*cm, 5.4*cm])
cap_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_HEADER),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(cap_table)
story.append(sp(10))

story.append(h2("Per-Video Rating vs. Threadforge Platform"))
rating_data = [
    [Paragraph("<b>#</b>", sLabel), Paragraph("<b>Viral Format</b>", sLabel),
     Paragraph("<b>Platform</b>", sLabel), Paragraph("<b>They Used</b>", sLabel),
     Paragraph("<b>Our Approach</b>", sLabel), Paragraph("<b>Rating</b>", sLabel)],
    ["1", "Alien Fruit", "TikTok 15s", "Midjourney + Luma", "Runway Gen-4.5 text→video", "7/10"],
    ["2", "Cyberpunk Tokyo Walk", "TikTok 30s", "Sora 2 + ElevenLabs", "✅ Runway + ✅ ElevenLabs", "8/10"],
    ["3", "Before/After Glow-up", "Reels 20s", "Runway Video-to-Video", "Stock before + AI after", "5/10"],
    ["4", "Stoic Wisdom Aurelius", "Shorts 45s", "ChatGPT + HeyGen", "✅ Runway + ✅ ElevenLabs", "9/10"],
    ["5", "Galactic Safari Lion", "TikTok 15s", "Armor gen + Pika Motion", "Runway Gen-4.5 full scene", "7.5/10"],
    ["6", "3 AI Design Hacks", "Shorts 30s", "Loom + InVideo", "Hybrid: AI viz + stock", "4/10"],
    ["7", "Movie That Isn't Real", "Reels 60s", "Google Veo 3 + Udio", "Runway Gen-4.5 (trim to 45s)", "6.5/10"],
    ["8", "Robot Fight in SF", "TikTok 25s", "Real location + Luma extend", "Fully AI-generated battle", "8/10"],
    ["9", "7-Day AI Challenge", "Shorts 45s", "Viblo.ai + ElevenLabs + Veed", "✅ ElevenLabs + captions + stock", "7/10"],
    ["10", "Pattern-Break Coffee Cup", "Reels 15s", "Photo + Runway Multi-Motion", "✅ Runway Gen-4.5 surreal", "9/10"],
]
rating_table = Table(rating_data, colWidths=[0.6*cm, 3.2*cm, 2*cm, 3.2*cm, 3.6*cm, 1.8*cm])
rating_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_HEADER),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
]))
story.append(rating_table)
story.append(sp(6))
story.append(note("Priority production order: Scripts 4, 10, 8, 2, 5, 1, 9, 7, 3, 6"))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PART 2 — ALGORITHM ANALYSIS
# ══════════════════════════════════════════════════════════════════════════
story += section_header("PART 2 — Platform Algorithm Deep Dive (2026)",
    "What the algorithm actually measures and weights in each platform")

# TikTok
story.append(h2("TikTok Algorithm — Key Signals (2026)"))
story.append(body(
    "Content passes through 3 exposure pools: 200 → 2,000 → 20,000 → For You Page. "
    "Each pool requires 80%+ completion rate to advance to the next. "
    "Your platform's 9:16 + ASS captions maximise dwell time at every stage."
))
tiktok_signals = [
    ["<b>Signal</b>", "<b>Weight</b>", "<b>How Threadforge Hits It</b>"],
    ["Completion rate (95%+ unlock 4× boost)", "★★★★★", "≤15s scripts loop + captions keep eyes on screen"],
    ["Curiosity gap in first 1.5 seconds", "★★★★★", "Hook scene uses 'reveal/shock/unbelievable' triggers → gen4.5"],
    ["Comment velocity (questions + polls)", "★★★★☆", "'Who won?' and 'Comment your answer' CTAs in every script"],
    ["Loop design (seamless 15s repeat)", "★★★★☆", "CTA frame visually connects back to hook → re-watch counts"],
    ["Sound selection (trending vs original)", "★★★☆☆", "ElevenLabs narration = original audio; add trending in CapCut"],
]
tt = Table([[Paragraph(c, sBody) for c in row] for row in tiktok_signals],
           colWidths=[6*cm, 2.5*cm, 7.9*cm])
tt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_ACCENT),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(tt)
story.append(sp(8))

# Instagram Reels
story.append(h2("Instagram Reels Algorithm — Key Signals (2026)"))
reels_signals = [
    ["<b>Signal</b>", "<b>Weight</b>", "<b>How Threadforge Hits It</b>"],
    ["Shares to DMs (10× over likes)", "★★★★★", "Before/after and trailer formats drive DM-shares instinctively"],
    ["Save rate above 3% = viral trigger", "★★★★★", "Verbal 'save this' CTA + educational content → save reflex"],
    ["Trending audio on Explore", "★★★★☆", "Export video, add trending audio in CapCut/Reels editor"],
    ["First frame as cover (click-through)", "★★★★☆", "Hook scene gen4.5 = cinematic first frame every time"],
    ["20-30s sweet spot completion", "★★★☆☆", "Scripts 3 and 10 targeted at 15-20s for max completion"],
]
rt = Table([[Paragraph(c, sBody) for c in row] for row in reels_signals],
           colWidths=[6*cm, 2.5*cm, 7.9*cm])
rt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#DB2777")),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(rt)
story.append(sp(8))

# YouTube Shorts
story.append(h2("YouTube Shorts Algorithm — Key Signals (2026)"))
shorts_signals = [
    ["<b>Signal</b>", "<b>Weight</b>", "<b>How Threadforge Hits It</b>"],
    ["80%+ average view duration → push to subs", "★★★★★", "45s Shorts = exact platform cap; dense content = re-watch"],
    ["Re-watch triggers (rapid info density)", "★★★★★", "'3 secrets in 30s' and '7-day' formats cause instant re-watch"],
    ["Captions + text overlays", "★★★★☆", "ASS auto-captions generated on every video natively"],
    ["Educational shelf life (12-18 months)", "★★★★☆", "Stoic/AI secrets content ranks in search long-term"],
    ["Swipe-to-subscribe (value in first 5s)", "★★★☆☆", "Hook always gen4.5 = cinematic first impression"],
]
st = Table([[Paragraph(c, sBody) for c in row] for row in shorts_signals],
           colWidths=[6*cm, 2.5*cm, 7.9*cm])
st.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_RED),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(st)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PART 3 — 10 SCRIPTS
# ══════════════════════════════════════════════════════════════════════════
story += section_header("PART 3 — 10 Production-Ready Scripts",
    "Copy-paste ready · Runway prompts embedded · Frame-by-frame captions included")

story.append(note(
    "Pipeline note: The narration text IS the Runway Gen-4.5 visual prompt. "
    "_build_visual_prompt() wraps it as: \"Ultra-dramatic cinematic opening — {your_text[:80]}. "
    "Vertical 9:16, 4K sharp focus, no text.\" — Write every sentence to work as "
    "both ElevenLabs audio AND Runway visual instruction simultaneously."
))
story.append(sp(8))

# ─── SCRIPT DATA ──────────────────────────────────────────────────────────
scripts = [
    {
        "num": 1,
        "title": "The Crystal That Refuses To Die",
        "platform": "TikTok", "target": "8M+", "duration": "15s",
        "mode": "ai", "model": "gen4.5",
        "hook": "Scientists discovered a glowing crystal underground that should not exist — watch what happens when light passes through it",
        "body": "The crystal pulses with electric blue living energy deep in the earth — touch it and it shatters into liquid that flows upward defying gravity — revealing a hidden world beneath that science cannot explain",
        "cta": "Would you reach in and touch it — drop your answer below",
        "algo": "Curiosity gap hook ('should not exist') + loopable CTA → hook visual. Post Tue/Thu 7-9PM EST.",
        "frames": [
            (1, "0–3s", "Scientists discovered a glowing crystal underground that should not exist — watch what happens when light passes through it", 10, "SCIENTISTS DISCOVERED THIS"),
            (2, "3–10s", "The crystal pulses with electric blue living energy — touch it and it shatters into liquid flowing upward defying gravity", 9, "WHAT HAPPENS WHEN YOU TOUCH IT..."),
            (3, "10–15s", "Revealing a hidden world beneath that science cannot explain", 8, "COMMENT IF YOU'D REACH IN 👇"),
        ]
    },
    {
        "num": 2,
        "title": "The City That Forgot The Sun",
        "platform": "TikTok", "target": "6M+", "duration": "30s",
        "mode": "ai", "model": "gen4.5",
        "hook": "Walk with me through a cyberpunk city where neon rain never stops and every shadow hides something incredible",
        "body": "Every street corner reveals a secret underground marketplace glowing without power — here AI runs the black market and the buildings breathe electric light — the rain remembers every person who ever walked these streets — at midnight this city transforms and rewrites its own rules — the only law here is survive until morning",
        "cta": "Where would you hide in this city — drop your location in the comments",
        "algo": "FPV walk aesthetic = TikTok's #1 retention format 2026. 'Where would you hide' = personal → comment flood. Post Sat 9PM EST.",
        "frames": [
            (1, "0–5s", "Walk with me through a cyberpunk city where neon rain never stops and every shadow hides something incredible", 10, "NOBODY TALKS ABOUT THIS CITY"),
            (2, "5–11s", "Every street corner reveals a secret underground marketplace glowing without power", 9, "THE UNDERGROUND MARKET"),
            (3, "11–17s", "The rain remembers every person who ever walked these streets — AI runs everything here", 8, "THE RAIN REMEMBERS"),
            (4, "17–24s", "At midnight this city transforms and rewrites its own rules", 9, "MIDNIGHT CHANGES EVERYTHING"),
            (5, "24–30s", "The only law here is survive until morning", 7, "WHERE WOULD YOU HIDE? 👇"),
        ]
    },
    {
        "num": 3,
        "title": "Before AI. After AI. My Brain.",
        "platform": "Instagram Reels", "target": "7M+", "duration": "20s",
        "mode": "hybrid", "model": "gen4.5",
        "hook": "This is what my brain looked like before AI — scattered overwhelmed invisible scattered thoughts everywhere",
        "body": "Snap — one transformation later — the same person but discovered something incredible — organized clear sharp unstoppable — AI did not replace me it revealed a hidden version of myself I never knew existed — this upgrade changed everything about how I work and think",
        "cta": "Save this if you need the upgrade — follow for the exact workflow",
        "algo": "'Save this' verbal CTA + before/after = highest Reels save rate. Transformation drives DM-shares. Add trending audio after export.",
        "frames": [
            (1, "0–4s", "Scattered overwhelmed invisible — thoughts flying everywhere before the transformation", 10, "MY BRAIN BEFORE AI ❌"),
            (2, "4–11s", "Snap — transformation — discovered something incredible — organized clear sharp unstoppable", 10, "AFTER AI ✅"),
            (3, "11–17s", "AI revealed a hidden version of myself I never knew existed — this upgrade changed everything", 9, "IT REVEALED MY BEST SELF"),
            (4, "17–20s", "Save this if you need the upgrade — follow for the exact workflow", 7, "SAVE FOR WHEN YOU'RE READY"),
        ]
    },
    {
        "num": 4,
        "title": "3 Truths Marcus Aurelius Died Knowing",
        "platform": "YouTube Shorts", "target": "9M+", "duration": "45s",
        "mode": "hybrid", "model": "gen4.5",
        "hook": "Before Marcus Aurelius died he wrote three truths that will destroy every excuse you have ever made — nobody talks about these",
        "body": "First truth — your mind is everything what you think you become — not sometimes not when conditions are perfect — always — Second truth — the secret of change is to focus all energy not on fighting the old but on building something new — Third truth — very little is needed to make a happy life it is all within yourself in your way of thinking — these three truths changed history — Aurelius ruled an empire and faced more adversity than you can imagine — and he wrote these words in his private journal never meant to be discovered — he wrote them for himself",
        "cta": "Follow for the daily wisdom that rewrites how you think — comment which truth hit hardest",
        "algo": "YouTube searches 'stoic wisdom' 2.4M/month. Evergreen 18-month shelf life. 3 rapid points = triple re-watch. Post Wed or Sun.",
        "frames": [
            (1, "0–8s", "Before Marcus Aurelius died he wrote three truths that will destroy every excuse — nobody talks about these", 10, "3 TRUTHS BEFORE HE DIED"),
            (2, "8–16s", "First truth — your mind is everything what you think you become — not sometimes not when conditions are perfect — always", 8, "TRUTH #1: YOUR MIND IS EVERYTHING"),
            (3, "16–24s", "The secret of change is to focus all energy not on fighting the old but on building something new", 8, "TRUTH #2: STOP FIGHTING. START BUILDING."),
            (4, "24–32s", "Very little is needed to make a happy life — it is all within yourself in your way of thinking", 7, "TRUTH #3: IT'S ALL WITHIN YOU"),
            (5, "32–40s", "He wrote these words in his private journal — never meant to be discovered — written for himself alone", 9, "HE NEVER MEANT FOR YOU TO READ THIS"),
            (6, "40–45s", "Follow for the daily wisdom that rewrites how you think", 7, "WHICH TRUTH HIT YOU? 👇"),
        ]
    },
    {
        "num": 5,
        "title": "Lions Don't Roar In Space",
        "platform": "TikTok", "target": "5M+", "duration": "15s",
        "mode": "ai", "model": "gen4.5",
        "hook": "A lion wearing ancient battle armor floated through deep space and locked eyes with me — I understood immediately they are not kings here — they are guardians",
        "body": "Ancient predators who evolved across millions of years to rule the earth — now imagine that same power unleashed in zero gravity across the infinite dark of space — incredible transformation of the apex predator",
        "cta": "Which animal would you send to guard the stars — comment below",
        "algo": "Fantastical animals = TikTok #1 shared visual category 2026. 'Which animal' = 2-3× comment rate vs generic CTAs. Loop setup perfect.",
        "frames": [
            (1, "0–4s", "A lion wearing ancient battle armor floating through deep space — locked eyes with me — not kings — guardians", 10, "THEY AREN'T KINGS HERE"),
            (2, "4–10s", "Ancient predators unleashed in zero gravity across the infinite dark — incredible transformation of the apex predator", 9, "THEY'RE GUARDIANS"),
            (3, "10–15s", "The apex guardian of the galaxy — which animal would you send to guard the stars", 8, "COMMENT YOUR ANIMAL 👇"),
        ]
    },
    {
        "num": 6,
        "title": "3 AI Secrets Changing Everything Right Now",
        "platform": "YouTube Shorts", "target": "3M+", "duration": "30s",
        "mode": "hybrid", "model": "gen4.5",
        "hook": "Three AI secrets the biggest companies paid millions to discover — I am giving all three to you right now in thirty seconds",
        "body": "Secret one — AI can transform a single idea into a full month of viral content in sixty seconds — this hack alone changes everything — Secret two — voice cloning technology lets you narrate videos without recording a single word — Secret three — Runway AI turns any script into incredible cinematic video without a camera — these three secrets are already changing the game for thousands of creators",
        "cta": "Save this and try secret one tonight — follow for more hidden AI breakthroughs every day",
        "algo": "Rapid info density = highest Shorts re-watch rate. 'Try tonight' = immediate action intent = max save rate. Post Mon/Tue 6-8PM.",
        "frames": [
            (1, "0–5s", "Three AI secrets the biggest companies paid millions to discover", 10, "THEY PAID MILLIONS FOR THIS"),
            (2, "5–12s", "Secret one — AI transforms a single idea into a full month of viral content — this hack changes everything", 9, "SECRET #1: 1 IDEA → 30 DAYS"),
            (3, "12–20s", "Secret two — voice cloning technology narrates videos without recording a single word — incredible breakthrough", 9, "SECRET #2: CLONE YOUR VOICE 🎙️"),
            (4, "20–27s", "Secret three — Runway AI turns any script into incredible cinematic video without a camera", 9, "SECRET #3: NO CAMERA NEEDED"),
            (5, "27–30s", "Save this and try secret one tonight — follow for more hidden AI breakthroughs", 8, "SAVE + FOLLOW 📲"),
        ]
    },
    {
        "num": 7,
        "title": "The Sci-Fi Movie Too Dangerous To Make",
        "platform": "Instagram Reels", "target": "4M+", "duration": "45s",
        "mode": "ai", "model": "gen4.5",
        "hook": "Coming this summer — the incredible sci-fi movie that Hollywood said was too dangerous to make — until now",
        "body": "A world where the ocean transforms into liquid gold and entire cities float on cloud formations — where humans have evolved beyond their own physical bodies into something unbelievable — where the last war in history was fought with memories instead of weapons — and the hero must choose between saving everything humanity has ever built — or becoming the very thing that destroys it — this is not CGI — this is AI cinema — and nothing will ever be the same",
        "cta": "Comment your seat number to reserve your place in the future of film",
        "algo": "Trailer format = highest Reels DM-share rate. 'Coming soon' mystery drives saves. Cinematic aspect ratio is Runway's showcase. Post Fri evening.",
        "frames": [
            (1, "0–5s", "The incredible sci-fi movie Hollywood said was too dangerous to make — until now", 10, "THEY SAID IT COULDN'T BE MADE"),
            (2, "5–13s", "A world where the ocean transforms into liquid gold and entire cities float on massive cloud formations", 9, "A WORLD WHERE OCEANS BLEED GOLD"),
            (3, "13–21s", "Humans have evolved beyond their own physical bodies into something unbelievable and incredible", 10, "HUMANS EVOLVED BEYOND THEMSELVES"),
            (4, "21–29s", "The last war in history was fought with memories instead of weapons — shocking and mindblowing", 10, "THE WAR WAS FOUGHT WITH MEMORIES"),
            (5, "29–37s", "The hero must choose between saving everything or becoming the thing that destroys it", 8, "SAVE EVERYTHING. OR BECOME IT."),
            (6, "37–45s", "This is AI cinema — and nothing will ever be the same — coming soon", 9, "COMMENT YOUR SEAT NUMBER 🎬"),
        ]
    },
    {
        "num": 8,
        "title": "Giant Mechs Just Invaded New York",
        "platform": "TikTok", "target": "6M+", "duration": "25s",
        "mode": "ai", "model": "gen4.5",
        "hook": "Nobody warned New York this morning — three hundred foot battle mechs are rising from the harbor right now — this is absolutely unbelievable",
        "body": "Steel giants taller than skyscrapers wade through flooded Manhattan streets — water rushing in behind them as the city scrambles — shocking explosions lighting up Times Square as they clash with military response — incredible scale destruction nobody has ever seen before in real streets",
        "cta": "Who won this battle — the machines or the city — drop your vote below",
        "algo": "'Who won?' = highest comment-to-view ratio of any CTA. Binary choice debate = 48h+ active comment section = extended reach window. Post Tue 7PM.",
        "frames": [
            (1, "0–4s", "Three hundred foot battle mechs rising from the harbor right now — absolutely unbelievable", 10, "NOBODY WARNED NEW YORK 😱"),
            (2, "4–10s", "Steel giants taller than skyscrapers wade through flooded Manhattan streets — water rushing behind them", 9, "300 FEET TALL"),
            (3, "10–18s", "Shocking explosions lighting up Times Square as mechs clash with military response — incredible scale", 10, "TIMES SQUARE IS GONE"),
            (4, "18–25s", "Incredible destruction nobody has ever seen before in real streets — who won this battle", 9, "WHO WON? MACHINES OR CITY? 👇"),
        ]
    },
    {
        "num": 9,
        "title": "I Let AI Live My Life For 7 Days",
        "platform": "YouTube Shorts", "target": "2.5M+", "duration": "45s",
        "mode": "hybrid", "model": "gen4.5",
        "hook": "I let artificial intelligence make every single decision in my life for seven days straight — and day seven completely transformed my future",
        "body": "Day one AI chose everything I ate — Day two it planned every single hour — Day three it rewrote my entire morning routine — Day four I was more focused than I had been in years — Day five AI discovered a hidden skill I had buried for a decade — Day six it transformed my work into something I actually loved — Day seven it finally revealed a version of myself I never knew was possible — the AI did not control my life — it showed me what my life could secretly become",
        "cta": "Follow and comment DAY ONE if you want the complete breakdown — I will reveal everything",
        "algo": "Challenge format = highest Shorts subscriber conversion. 'Comment DAY ONE' = 3× reply rate vs generic. Promise of reveal = follow incentive. Post Mon.",
        "frames": [
            (1, "0–7s", "I let artificial intelligence make every decision in my life for seven days — day seven transformed my future", 10, "I LET AI CONTROL MY LIFE"),
            (2, "7–14s", "Day one: AI chose everything — Day two: planned every hour — Day three: rewrote my morning — Day four: focused like never before", 8, "DAY 1 → DAY 2 → DAY 3 → DAY 4"),
            (3, "14–22s", "Day five AI discovered a hidden skill I had buried for a decade — incredible revelation", 10, "DAY 5: IT FOUND SOMETHING I FORGOT"),
            (4, "22–30s", "Day six transformed my work into something I actually loved — Day seven revealed a version of myself", 9, "DAY 6: I FINALLY LOVED MY WORK"),
            (5, "30–38s", "The AI revealed what my life could secretly become — a transformation nobody saw coming", 9, "DAY 7: EVERYTHING CHANGED"),
            (6, "38–45s", "Follow and comment DAY ONE if you want the complete breakdown — I will reveal everything", 8, "COMMENT \"DAY ONE\" 👇"),
        ]
    },
    {
        "num": 10,
        "title": "This Object Does Something Impossible",
        "platform": "Instagram Reels", "target": "5M+", "duration": "15s",
        "mode": "ai", "model": "gen4.5",
        "hook": "Watch this ordinary coffee cup do something that completely violates the laws of physics — this is unbelievable",
        "body": "The moment I touch it — it transforms — the liquid rises upward through air and crystallizes into something shocking and incredible — reality breaks — and nothing looks ordinary ever again",
        "cta": "Did you see the exact moment it happened — comment what you saw",
        "algo": "HIGHEST CONFIDENCE. Runway Gen-4.5 surreal object transformation is its #1 strength. 9× loop rate. 'Did you see it?' = instant comment urgency. Post Thu 8PM.",
        "frames": [
            (1, "0–3s", "An ordinary coffee cup sits on a white table — watch what happens when I touch it — completely unbelievable", 10, "WATCH WHAT HAPPENS"),
            (2, "3–10s", "Touch it — the coffee transforms and rises upward through air crystallizing into something shocking and incredible", 10, "WAIT FOR IT... 👁️"),
            (3, "10–15s", "Reality breaks — nothing looks ordinary ever again — what did you see", 9, "DID YOU SEE THE MOMENT? 👇"),
        ]
    },
]

for script in scripts:
    story.append(KeepTogether([
        hr(C_GOLD, 1.5),
        Paragraph(
            f'Script {script["num"]} / 10 — {script["title"]}',
            ParagraphStyle("sh", fontName="Helvetica-Bold", fontSize=14,
                           textColor=C_HEADER, spaceBefore=4, spaceAfter=4, leading=18)
        ),
    ]))

    # Meta badges row
    meta_row = [
        [Paragraph(f'<b>Platform:</b> {script["platform"]}', sBody),
         Paragraph(f'<b>Target Views:</b> {script["target"]}', sBody),
         Paragraph(f'<b>Duration:</b> {script["duration"]}', sBody),
         Paragraph(f'<b>Mode:</b> <font color="#7C3AED">{script["mode"]}</font>', sBody),
         Paragraph(f'<b>Model:</b> <font color="#059669">{script["model"]}</font>', sBody)],
    ]
    mt = Table(meta_row, colWidths=[3.2*cm, 3.2*cm, 2.8*cm, 2.8*cm, 4.4*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_LIGHT),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ]))
    story.append(mt)
    story.append(sp(5))

    # Scripts blocks
    story.append(script_block("HOOK", script["hook"]))
    story.append(script_block("BODY", script["body"]))
    story.append(script_block("CTA", script["cta"]))
    story.append(sp(4))

    # JSON payload
    story.append(Paragraph("<b>Copy-Paste Payload (Threadforge API):</b>", sH3))
    json_text = (
        f'{{"hook": "{script["hook"][:70]}...",\n'
        f' "body": "{script["body"][:70]}...",\n'
        f' "cta":  "{script["cta"]}",\n'
        f' "duration_seconds": {script["duration"].replace("s","")},\n'
        f' "scene_mode": "{script["mode"]}",\n'
        f' "runway_model": "{script["model"]}",\n'
        f' "dry_run": false }}'
    )
    story.append(code(json_text))
    story.append(sp(4))

    # Frame table
    story.append(Paragraph("<b>Frame-by-Frame Production Plan:</b>", sH3))
    story.append(frame_table(script["frames"]))
    story.append(sp(4))

    # Algorithm note
    story.append(Paragraph(f'<b>Algorithm Play:</b> {script["algo"]}', sCTA))
    story.append(sp(6))
    story.append(hr(colors.HexColor("#E5E7EB"), 0.5))
    story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════
# PART 4 — CREDIT BUDGET + POSTING SCHEDULE
# ══════════════════════════════════════════════════════════════════════════
story += section_header("PART 4 — Credit Budget & Posting Schedule",
    "880 Runway credits total · Priority order · Full week posting plan")

story.append(h2("Production Priority Matrix"))
priority_data = [
    [Paragraph("<b>Priority</b>", sLabel), Paragraph("<b>Script</b>", sLabel),
     Paragraph("<b>Platform</b>", sLabel), Paragraph("<b>Duration</b>", sLabel),
     Paragraph("<b>Est. Credits (gen4.5)</b>", sLabel), Paragraph("<b>ROI Potential</b>", sLabel)],
    ["🥇 1", "Script 10 — Coffee Cup Impossible", "Reels", "15s", "~72 credits", "HIGHEST — perfect format match"],
    ["🥇 2", "Script 4 — Marcus Aurelius 3 Truths", "Shorts", "45s", "~96 credits", "HIGHEST — 18-month shelf life"],
    ["🥈 3", "Script 8 — Mechs Invade New York", "TikTok", "25s", "~96 credits", "HIGH — comment bait"],
    ["🥈 4", "Script 2 — Cyberpunk City Walk", "TikTok", "30s", "~120 credits", "HIGH — aesthetic loop"],
    ["🥈 5", "Script 7 — Sci-Fi Movie Trailer", "Reels", "45s", "~144 credits", "HIGH — share-to-DM"],
    ["🥉 6", "Script 5 — Lions In Space", "TikTok", "15s", "~72 credits", "MEDIUM-HIGH"],
    ["🥉 7", "Script 1 — Impossible Crystal", "TikTok", "15s", "~72 credits", "MEDIUM-HIGH"],
    ["🥉 8", "Script 9 — AI 7-Day Challenge", "Shorts", "45s", "~72 credits", "MEDIUM"],
    ["📋 9", "Script 6 — 3 AI Secrets", "Shorts", "30s", "~60 credits", "MEDIUM"],
    ["📋 10", "Script 3 — Before/After Brain", "Reels", "20s", "~60 credits", "MEDIUM"],
    [Paragraph("<b>TOTAL</b>", sBody), "", "", "", Paragraph("<b>~864 credits</b>", sBody),
     Paragraph("<b>Within 880 credit budget ✅</b>", sBody)],
]
pt = Table(priority_data, colWidths=[1.5*cm, 5.5*cm, 2*cm, 1.8*cm, 3.2*cm, 4.4*cm])
pt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_HEADER),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, C_LIGHT]),
    ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#D1FAE5")),
    ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 5),
]))
story.append(pt)
story.append(sp(10))

story.append(note(
    "Run Scripts 10, 4, 8 first (lowest risk, highest format match). "
    "Evaluate response analytics before committing credits to Scripts 7 and 2."
))
story.append(sp(10))

story.append(h2("Week 1 Posting Schedule"))
sched_data = [
    [Paragraph("<b>Day</b>", sLabel), Paragraph("<b>Script</b>", sLabel),
     Paragraph("<b>Platform</b>", sLabel), Paragraph("<b>Post Time (EST)</b>", sLabel),
     Paragraph("<b>Why This Time</b>", sLabel)],
    ["Monday",    "Script 9 — AI 7-Day Challenge",   "YouTube Shorts",    "6:00 PM", "Week-start anchor; subscribe intent highest"],
    ["Tuesday",   "Script 8 — Mechs Invade NY",      "TikTok",            "7:00 PM", "'Who won?' comment bait; algorithm peak"],
    ["Wednesday", "Script 4 — Marcus Aurelius",      "YouTube Shorts",    "7:00 PM", "Mid-week educational consumption peak"],
    ["Thursday",  "Script 10 — Coffee Cup",           "Instagram Reels",   "8:00 PM", "Reels algorithm Thursday push window"],
    ["Friday",    "Script 7 — Sci-Fi Movie Trailer", "Instagram Reels",   "6:00 PM", "Weekend viewing; DM-share peak Fri evening"],
    ["Saturday",  "Script 2 — Cyberpunk City",       "TikTok",            "9:00 PM", "Peak TikTok scroll time globally"],
    ["Sunday",    "Script 5 — Lions In Space",        "TikTok",            "7:00 PM", "Fantasy/viral content peaks Sunday evening"],
]
scht = Table(sched_data, colWidths=[2.4*cm, 4.8*cm, 3.6*cm, 2.4*cm, 5.2*cm])
scht.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), C_ACCENT),
    ("TEXTCOLOR", (0,0), (-1,0), C_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
    ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D1D5DB")),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 6),
]))
story.append(scht)
story.append(sp(6))
story.append(note("Post Scripts 1, 3, 6 as secondary content in weeks 2-3 after analysing first-week performance signals."))
story.append(sp(10))
story.append(hr(C_ACCENT, 2))
story.append(sp(6))
story.append(Paragraph(
    "End of Guide — Master Viral AI Video Guide 2026 · Powered by Threadforge",
    ParagraphStyle("end", fontName="Helvetica-Bold", fontSize=10,
                   textColor=C_SUBTEXT, alignment=TA_CENTER)
))

# ── BUILD ──────────────────────────────────────────────────────────────────
doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
print(f"✅ PDF saved: {OUTPUT}")
