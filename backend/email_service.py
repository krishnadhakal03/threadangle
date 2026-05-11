import os
import asyncio
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_email_config_logged = False


def _get_env(*keys, default=None):
    for key in keys:
        value = os.getenv(key)
        if value not in (None, ""):
            return value
    return default


def _parse_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_smtp_config():
    """Read SMTP settings from env, supporting production and legacy local keys."""
    port_raw = _get_env("SMTP_PORT", default="587")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587

    username = _get_env("SMTP_USER", "ZOHO_EMAIL", "SMTP_FROM_EMAIL")
    from_email = _get_env("SMTP_FROM_EMAIL", "SMTP_USER", "ZOHO_EMAIL")
    from_header = _get_env("SMTP_FROM")
    if not from_header and from_email:
        from_header = f"Threadangle <{from_email}>"

    return {
        "host": _get_env("SMTP_HOST", default="smtp.zoho.com"),
        "port": port,
        "username": username,
        "password": _get_env("SMTP_PASSWORD", "ZOHO_PASSWORD"),
        "from_header": from_header,
        "start_tls": _parse_bool(_get_env("SMTP_STARTTLS"), default=(port != 465)),
        "use_tls": _parse_bool(_get_env("SMTP_USE_TLS"), default=(port == 465)),
        "contact_to_email": _get_env("CONTACT_TO_EMAIL", default="hello@kriangle.com"),
    }


def log_email_config_status():
    global _email_config_logged
    if _email_config_logged:
        return

    config = get_smtp_config()
    logger.info(
        "Email config status: SMTP_HOST present=%s, SMTP_PORT present=%s, "
        "SMTP_USER present=%s, SMTP_PASSWORD present=%s, SMTP_FROM present=%s, "
        "SMTP_FROM_EMAIL present=%s, SMTP_STARTTLS present=%s, CONTACT_TO_EMAIL present=%s",
        "yes" if os.getenv("SMTP_HOST") else "no",
        "yes" if os.getenv("SMTP_PORT") else "no",
        "yes" if config["username"] else "no",
        "yes" if config["password"] else "no",
        "yes" if os.getenv("SMTP_FROM") else "no",
        "yes" if os.getenv("SMTP_FROM_EMAIL") else "no",
        "yes" if os.getenv("SMTP_STARTTLS") else "no",
        "yes" if os.getenv("CONTACT_TO_EMAIL") else "no",
    )
    if config["contact_to_email"]:
        logger.info("Contact form recipient configured as %s", config["contact_to_email"])
    _email_config_logged = True


def get_email_setting(key, default=""):
    try:
        db_path = os.path.join(os.path.dirname(__file__), "threadangle.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content_value FROM cms_content WHERE content_key=?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] not in (None, "") else default
    except Exception:
        return default


def render_email_body(content_key: str, fallback_body: str, replacements: dict | None = None):
    template = get_email_setting(content_key, "")
    body = template if template else fallback_body
    if replacements:
        for key, value in replacements.items():
            body = body.replace(f"{{{{{key}}}}}", str(value))
            body = body.replace(f"{{{key}}}", str(value))
    return body

# GLOBAL EMAIL WRAPPER
def get_email_wrapper(subject, body_content, unsubscribe_line=""):
    brand_name = get_email_setting("email_brand_name", "Threadangle")
    brand_tagline = get_email_setting("email_brand_tagline", "Find the angle. Go viral.")
    reply_note = get_email_setting("email_reply_note", "Questions? Reply to this email — we read every message personally.")
    footer_links_raw = get_email_setting("email_footer_links", "kriangle.com|https://kriangle.com,Contact Us|https://kriangle.com/contact,Pricing|https://kriangle.com/pricing")
    brand_credit = get_email_setting("email_brand_credit", "Threadangle is a product by Kriangle · © 2026 Kriangle. All rights reserved.")

    links_html = []
    for pair in str(footer_links_raw).split(','):
        if '|' in pair:
            label, href = pair.split('|', 1)
            links_html.append(f'<a href="{href.strip()}">{label.strip()}</a>')
    if not links_html:
        links_html = ['<a href="https://kriangle.com">kriangle.com</a>', '<a href="https://kriangle.com/contact">Contact Us</a>', '<a href="https://kriangle.com/pricing">Pricing</a>']

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{subject}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background-color: #09090B; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #FAFAFA; }}
    .wrapper {{ width: 100%; background-color: #09090B; padding: 40px 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: #111113; border: 1px solid #27272A; border-radius: 12px; overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 32px 40px; text-align: center; border-bottom: 1px solid #27272A; }}
    .logo-badge {{ display: inline-block; background-color: #3B82F6; color: #ffffff; font-size: 18px; padding: 8px 12px; border-radius: 8px; margin-bottom: 12px; }}
    .logo-text {{ font-size: 24px; font-weight: 700; color: #FAFAFA; letter-spacing: -0.5px; }}
    .logo-tagline {{ font-size: 13px; color: #A1A1AA; margin-top: 4px; }}
    .body {{ padding: 40px; }}
    .greeting {{ font-size: 20px; font-weight: 600; color: #FAFAFA; margin-bottom: 16px; }}
    p {{ font-size: 15px; color: #A1A1AA; line-height: 1.7; margin-bottom: 16px; }}
    .highlight {{ color: #FAFAFA; }}
    .cta-button {{ display: block; width: fit-content; margin: 28px auto; background-color: #3B82F6; color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 15px; font-weight: 600; text-align: center; }}
    .cta-button:hover {{ background-color: #2563EB; }}
    .steps-box {{ background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 24px; margin: 24px 0; }}
    .step-item {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }}
    .step-item:last-child {{ margin-bottom: 0; }}
    .step-number {{ background-color: #3B82F6; color: #ffffff; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; text-align: center; line-height: 24px; }}
    .step-text {{ font-size: 14px; color: #A1A1AA; line-height: 1.6; padding-top: 2px; }}
    .step-text strong {{ color: #FAFAFA; }}
    .info-box {{ background-color: #18181B; border: 1px solid #27272A; border-left: 3px solid #3B82F6; border-radius: 8px; padding: 20px 24px; margin: 24px 0; }}
    .warning-box {{ background-color: #18181B; border: 1px solid #27272A; border-left: 3px solid #F59E0B; border-radius: 8px; padding: 20px 24px; margin: 24px 0; }}
    .success-box {{ background-color: #052E16; border: 1px solid #166534; border-radius: 8px; padding: 20px 24px; margin: 24px 0; text-align: center; }}
    .divider {{ border: none; border-top: 1px solid #27272A; margin: 28px 0; }}
    .feature-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 24px 0; }}
    .feature-card {{ background-color: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 16px; text-align: center; }}
    .feature-icon {{ font-size: 24px; margin-bottom: 8px; }}
    .feature-title {{ font-size: 13px; font-weight: 600; color: #FAFAFA; }}
    .feature-desc {{ font-size: 12px; color: #71717A; margin-top: 4px; }}
    .footer {{ background-color: #09090B; border-top: 1px solid #27272A; padding: 28px 40px; text-align: center; }}
    .footer p {{ font-size: 12px; color: #52525B; margin-bottom: 6px; }}
    .footer a {{ color: #3B82F6; text-decoration: none; }}
    .footer .brand-credit {{ font-size: 11px; color: #3F3F46; margin-top: 12px; padding-top: 12px; border-top: 1px solid #1C1C1F; }}
    @media (max-width: 600px) {{
      .body {{ padding: 24px 20px; }}
      .header {{ padding: 24px 20px; }}
      .feature-grid {{ grid-template-columns: 1fr; }}
      .cta-button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">

      <!-- HEADER -->
      <div class="header">
        <div class="logo-badge">⚡</div>
        <div class="logo-text">{brand_name}</div>
        <div class="logo-tagline">{brand_tagline}</div>
      </div>

      <!-- BODY -->
      <div class="body">
        {body_content}
      </div>

      <!-- FOOTER -->
      <div class="footer">
        <p>{reply_note}</p>
        <p>{' · '.join(links_html)}</p>
        <p>{unsubscribe_line}</p>
        <div class="brand-credit">{brand_credit}</div>
      </div>

    </div>
  </div>
</body>
</html>"""

async def send_email_async(to_email, subject, html_content, reply_to=None):
    config = get_smtp_config()
    log_email_config_status()

    if not config["username"] or not config["password"]:
        logger.error("SKIPPING EMAIL TO %s: SMTP credentials missing from environment", to_email)
        return False
        
    message = MIMEMultipart("alternative")
    message["From"] = config["from_header"]
    message["To"] = to_email
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.attach(MIMEText(html_content, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=config["host"],
            port=config["port"],
            username=config["username"],
            password=config["password"],
            use_tls=config["use_tls"],
            start_tls=config["start_tls"],
            timeout=10,
        )
        logger.info(f"EMAIL SENT SUCCESSFULLY TO {to_email} AT {datetime.now()}")
        return True
    except Exception as e:
        logger.error(f"FAILED TO SEND EMAIL TO {to_email}: {e}")
        return False


async def send_admin_test_email(to_email: str):
    subject = "Threadangle test email ✅"
    body = """<p class="greeting">Test email sent successfully</p>

<p>This email was triggered from your Admin panel using the currently saved CMS email settings.</p>

<div class="info-box">
  <p style="margin: 0; font-size: 13px; color: #A1A1AA;">
    You can now edit <strong style="color: #FAFAFA;">email_subject_*</strong> and
    <strong style="color: #FAFAFA;">email_body_*</strong> fields in Admin → Settings → Email,
    then send this test again to preview changes.
  </p>
</div>

<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""

    html = get_email_wrapper(subject, body, "Internal test email from admin panel")
    return await send_email_async(to_email, subject, html)

# EMAIL 1 — WELCOME EMAIL
async def send_welcome_email(user_email):
    subject = get_email_setting("email_subject_welcome", "Your Threadangle account is ready ⚡")
    body_fallback = """<p class="greeting">Welcome to Threadangle! 🎉</p>

<p>Your account is set up and <strong class="highlight">5 free generations are waiting for you.</strong> No credit card needed — just start creating.</p>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">1</div>
    <div class="step-text"><strong>Go to your dashboard</strong><br>Log in at kriangle.com/dashboard</div>
  </div>
  <div class="step-item">
    <div class="step-number">2</div>
    <div class="step-text"><strong>Paste any blog URL or text</strong><br>Any article, blog post, or idea works</div>
  </div>
  <div class="step-item">
    <div class="step-number">3</div>
    <div class="step-text"><strong>Hit Generate ⚡</strong><br>Get a Twitter thread, LinkedIn post and TikTok script in 20 seconds</div>
  </div>
</div>

<a href="https://kriangle.com/dashboard" class="cta-button">Go to My Dashboard →</a>

<hr class="divider">

<p style="font-size: 14px; color: #71717A; margin-bottom: 12px;">WHAT YOU CAN GENERATE FROM:</p>
<div class="feature-grid">
  <div class="feature-card">
    <div class="feature-icon">📝</div>
    <div class="feature-title">Blog Posts</div>
    <div class="feature-desc">Paste any article URL</div>
  </div>
  <div class="feature-card">
    <div class="feature-icon">🎥</div>
    <div class="feature-title">YouTube Videos</div>
    <div class="feature-desc">Paste a YouTube link</div>
  </div>
  <div class="feature-card">
    <div class="feature-icon">🎙️</div>
    <div class="feature-title">Podcast Notes</div>
    <div class="feature-desc">Paste your transcript</div>
  </div>
  <div class="feature-card">
    <div class="feature-icon">💡</div>
    <div class="feature-title">Raw Ideas</div>
    <div class="feature-desc">Paste any text</div>
  </div>
</div>

<hr class="divider">

<p style="font-size: 14px;">Questions? Just reply to this email. I read every single message personally.</p>
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_welcome", body_fallback)
    unsubscribe = "You received this because you created a free account at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)

# EMAIL 2 — PASSWORD RESET EMAIL
async def send_password_reset_email(user_email, reset_token):
    reset_url = f"https://kriangle.com/reset-password?token={reset_token}"
    subject = get_email_setting("email_subject_reset", "Reset your Threadangle password")
    body_fallback = f"""<p class="greeting">Reset Your Password</p>

<p>We received a request to reset the password for your Threadangle account associated with this email address.</p>

<div class="warning-box">
  <p style="margin: 0; font-size: 14px; color: #FCD34D;">⏱ <strong style="color: #FAFAFA;">This link expires in 1 hour.</strong> If you did not request this, you can safely ignore this email.</p>
</div>

<p>Click the button below to set a new password:</p>

<a href="{reset_url}" class="cta-button">Reset My Password →</a>

<p style="font-size: 13px; color: #52525B; text-align: center;">Or copy and paste this link into your browser:</p>
<p style="font-size: 12px; color: #3B82F6; word-break: break-all; text-align: center; background: #18181B; padding: 12px; border-radius: 6px;">{reset_url}</p>

<hr class="divider">

<div class="info-box">
  <p style="margin: 0; font-size: 13px; color: #A1A1AA;">🔒 <strong style="color: #FAFAFA;">Security note:</strong> Threadangle staff will never ask for your password. If you did not request this reset, your account is safe — just ignore this email and your password will remain unchanged.</p>
</div>

<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_reset", body_fallback, {"reset_url": reset_url})
    unsubscribe = "You received this because a password reset was requested for your account at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)

# EMAIL 3 — CONTACT FORM AUTO-REPLY
async def send_contact_auto_reply(name, user_email, subject_text):
    subject = get_email_setting("email_subject_contact_auto", "We received your message — Threadangle")
    body_fallback = f"""<p class="greeting">We Got Your Message, {name}! 👋</p>

<p>Thanks for reaching out to Threadangle. We have received your message about <strong class="highlight">"{subject_text}"</strong> and will get back to you within 24 hours.</p>

<div class="success-box">
  <p style="font-size: 32px; margin-bottom: 8px;">✅</p>
  <p style="font-size: 16px; font-weight: 600; color: #4ADE80; margin: 0;">Message received successfully</p>
  <p style="font-size: 13px; color: #86EFAC; margin-top: 6px; margin-bottom: 0;">We typically reply within a few hours during business days</p>
</div>

<p>While you wait, here are a few things you can do:</p>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">→</div>
    <div class="step-text"><strong>Check our FAQ</strong> — <a href="https://kriangle.com/#faq" style="color: #3B82F6;">kriangle.com/#faq</a><br>Most common questions are answered there instantly</div>
  </div>
  <div class="step-item">
    <div class="step-number">→</div>
    <div class="step-text"><strong>Manage your subscription</strong> — <a href="https://kriangle.com/dashboard" style="color: #3B82F6;">go to Settings</a><br>Billing questions can often be resolved directly in your account</div>
  </div>
  <div class="step-item">
    <div class="step-number">→</div>
    <div class="step-text"><strong>Read our blog</strong> — <a href="https://kriangle.com/blog" style="color: #3B82F6;">kriangle.com/blog</a><br>Tips on content creation, Twitter growth, and going viral</div>
  </div>
</div>

<hr class="divider">

<p style="font-size: 14px; color: #71717A;">— The Threadangle Team<br>hello@kriangle.com · kriangle.com</p>"""
    body = render_email_body("email_body_contact_auto", body_fallback, {"name": name, "subject_text": subject_text})
    unsubscribe = "You received this because you submitted a contact form at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)

# EMAIL 4 — CONTACT NOTIFICATION TO ADMIN
async def send_admin_contact_notification(contact_data):
    name = contact_data.get('name')
    user_email = contact_data.get('email')
    subject_text = contact_data.get('subject')
    message_text = contact_data.get('message')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prefix = get_email_setting("email_subject_admin_contact_prefix", "New Threadangle Contact:")
    subject = f"{prefix} {subject_text}"
    body_fallback = f"""<p class="greeting">New Contact Form Submission</p>

<div class="info-box">
  <p style="margin: 0 0 8px 0; font-size: 13px; color: #71717A;">FROM</p>
  <p style="margin: 0; font-size: 16px; font-weight: 600; color: #FAFAFA;">{name}</p>
  <p style="margin: 4px 0 0 0; font-size: 14px; color: #3B82F6;">{user_email}</p>
</div>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">📌</div>
    <div class="step-text"><strong>Subject:</strong> {subject_text}</div>
  </div>
  <div class="step-item">
    <div class="step-number">🕐</div>
    <div class="step-text"><strong>Received:</strong> {timestamp}</div>
  </div>
</div>

<p style="font-size: 14px; color: #71717A; margin-bottom: 8px;">MESSAGE:</p>
<div style="background: #18181B; border: 1px solid #27272A; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
  <p style="font-size: 15px; color: #E4E4E7; line-height: 1.7; margin: 0; white-space: pre-wrap;">{message_text}</p>
</div>

<a href="mailto:{user_email}?subject=Re: {subject_text}" class="cta-button">Reply to {name} →</a>

<hr class="divider">
<p style="font-size: 12px; color: #52525B; text-align: center;">This is an automated notification from Threadangle contact form · kriangle.com</p>"""
    body = render_email_body("email_body_admin_contact", body_fallback, {
    "name": name,
    "user_email": user_email,
    "subject_text": subject_text,
    "message_text": message_text,
    "timestamp": timestamp,
  })
    
    html = get_email_wrapper(subject, body, "")
    return await send_email_async(get_smtp_config()["contact_to_email"], subject, html, reply_to=user_email)

# EMAIL 5 — UPGRADE CONFIRMATION EMAIL
async def send_upgrade_confirmation(user_email, plan_name, amount, next_billing_date):
    template = get_email_setting("email_subject_upgrade_template", "You are now on Threadangle {plan} ⚡")
    subject = template.replace("{plan}", str(plan_name))
    body_fallback = f"""<p class="greeting">You are on {plan_name} now! 🎉</p>

<p>Thank you for upgrading. Your payment was successful and your account has been upgraded immediately.</p>

<div class="success-box">
  <p style="font-size: 32px; margin-bottom: 8px;">⚡</p>
  <p style="font-size: 18px; font-weight: 700; color: #4ADE80; margin: 0;">Threadangle {plan_name}</p>
  <p style="font-size: 14px; color: #86EFAC; margin-top: 6px; margin-bottom: 0;">Active and ready to use right now</p>
</div>

<div class="info-box">
  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
    <span style="font-size: 14px; color: #71717A;">Plan</span>
    <span style="font-size: 14px; font-weight: 600; color: #FAFAFA;">Threadangle {plan_name}</span>
  </div>
  <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
    <span style="font-size: 14px; color: #71717A;">Amount charged</span>
    <span style="font-size: 14px; font-weight: 600; color: #FAFAFA;">${amount}/month</span>
  </div>
  <div style="display: flex; justify-content: space-between;">
    <span style="font-size: 14px; color: #71717A;">Next billing date</span>
    <span style="font-size: 14px; font-weight: 600; color: #FAFAFA;">{next_billing_date}</span>
  </div>
</div>

<p>You now have access to:</p>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Unlimited generations</strong> — no monthly limits ever</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>All platforms</strong> — Twitter, LinkedIn, and TikTok scripts</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>All tones</strong> — Professional, Casual, Viral, Educational</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Generation history</strong> — all your past content saved</div>
  </div>
</div>

<a href="https://kriangle.com/dashboard" class="cta-button">Start Creating Now →</a>

<hr class="divider">

<p style="font-size: 13px; color: #52525B;">To manage or cancel your subscription at any time, go to <a href="https://kriangle.com/dashboard" style="color: #3B82F6;">Dashboard → Settings → Manage Subscription</a>. You can also reply to this email if you have any billing questions.</p>

<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_upgrade_confirmation", body_fallback, {
    "plan_name": plan_name,
    "amount": amount,
    "next_billing_date": next_billing_date,
  })
    unsubscribe = "You received this because you upgraded your Threadangle account at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)

# EMAIL 5b — SUBSCRIPTION CONFIRMATION (called from webhook)
async def send_subscription_confirmation(to_email: str, plan_name: str, generation_limit: int):
    """Send subscription confirmation after successful payment.

    Args:
        to_email: User's email address
        plan_name: "Solo" or "Founder"
        generation_limit: 30 for Solo, 100 for Founder
    """
    plan_emoji = '⭐' if plan_name.lower() == 'founder' else '⚡'
    subject_tpl = get_email_setting("email_subject_subscription_confirmation", "🎉 You're now on Threadangle {plan}!")
    subject = subject_tpl.replace("{plan}", str(plan_name))
    body_fallback = f"""<p class="greeting">{plan_emoji} Welcome to {plan_name}!</p>

<p>Your subscription is now <strong class="highlight">active</strong>. You have
<strong class="highlight">{generation_limit} generations per month</strong> to turn
your ideas into viral content.</p>

<div class="success-box">
  <p style="font-size: 32px; margin-bottom: 8px;">{plan_emoji}</p>
  <p style="font-size: 18px; font-weight: 700; color: #4ADE80; margin: 0;">Threadangle {plan_name} — Active</p>
  <p style="font-size: 14px; color: #86EFAC; margin-top: 6px; margin-bottom: 0;">{generation_limit} generations per month</p>
</div>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">1</div>
    <div class="step-text"><strong>Paste any blog URL or text</strong><br>Any article, blog post, or idea works</div>
  </div>
  <div class="step-item">
    <div class="step-number">2</div>
    <div class="step-text"><strong>Choose your tone</strong><br>Professional, Bold, or Casual</div>
  </div>
  <div class="step-item">
    <div class="step-number">3</div>
    <div class="step-text"><strong>Hit Generate {plan_emoji}</strong><br>Get platform-ready content in 20 seconds</div>
  </div>
</div>

<a href="https://kriangle.com/dashboard" class="cta-button">Start Creating Content →</a>

<div class="info-box">
  <p style="margin: 0; font-size: 13px; color: #A1A1AA;">💡 <strong style="color: #FAFAFA;">Pro tip:</strong>
  Save article URLs throughout the week. Batch-generate all your content on Sunday evening.
  One focused hour = content for the entire week.</p>
</div>

<hr class="divider">
<p style="font-size: 14px;">Questions? Just reply to this email — we read every message personally.</p>
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_subscription_confirmation", body_fallback, {
    "plan_name": plan_name,
    "generation_limit": generation_limit,
    "plan_emoji": plan_emoji,
  })
    unsubscribe = f"You received this because you subscribed to Threadangle {plan_name} at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(to_email, subject, html)

# EMAIL 6 — SUBSCRIPTION CANCELLATION
async def send_cancellation_email(user_email, plan_name):
    subject = get_email_setting("email_subject_cancellation", "Your Threadangle subscription has been cancelled")
    body_fallback = f"""<p class="greeting">Subscription Cancelled</p>

<p>Your <strong class="highlight">Threadangle {plan_name}</strong> subscription has been cancelled.
You will retain access until the end of your current billing period.</p>

<div class="info-box">
  <p style="margin: 0; font-size: 14px; color: #A1A1AA;">
    Sorry to see you go. If you ever change your mind, you can resubscribe anytime
    from your dashboard — your history and settings will still be there.
  </p>
</div>

<a href="{os.getenv('FRONTEND_URL', 'https://kriangle.com')}/pricing"
   style="display:block;width:fit-content;margin:28px auto;background:transparent;
          color:#3B82F6;padding:14px 32px;border-radius:8px;text-decoration:none;
          font-weight:700;font-size:15px;border:1px solid #3B82F6;text-align:center;">
  Reactivate Subscription →
</a>

<hr class="divider">
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_cancellation", body_fallback, {"plan_name": plan_name})
    unsubscribe = "You received this because you cancelled your Threadangle subscription"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)


# EMAIL 7 — USAGE LIMIT WARNING
async def send_usage_limit_email(user_email, name):
    subject = get_email_setting("email_subject_usage_limit", "You've used all your free generations ⚡")
    body_fallback = f"""<p class="greeting">You've hit your free limit, {name}! ⚡</p>

<p>You have used all <strong class="highlight">3 free generations</strong>.
Upgrade to keep creating viral content without limits.</p>

<div class="info-box">
  <p style="font-weight: 700; color: #FAFAFA; margin-bottom: 16px;">Starter Plan — $12/month</p>
  <div style="color: #A1A1AA; font-size: 14px; line-height: 2;">
    ✓ Unlimited generations<br>
    ✓ All 3 platforms (Twitter, LinkedIn, TikTok)<br>
    ✓ All 4 tones<br>
    ✓ Full generation history
  </div>
</div>

<a href="{os.getenv('FRONTEND_URL', 'https://kriangle.com')}/pricing" class="cta-button">
  Upgrade Now — $12/month →
</a>

<p style="font-size: 13px; color: #52525B; text-align: center;">Cancel anytime. No contracts.</p>

<hr class="divider">
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_usage_limit", body_fallback, {"name": name})
    unsubscribe = "You received this because you reached your free generation limit at kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)



# EMAIL 8 — VOICE LEARNING NOTIFICATION
async def send_voice_learned_email(user_email: str, user_name: str):
    """Send a notification when Threadangle has finished learning a user's voice."""
    name_part = f" {user_name}" if user_name and user_name != user_email else ""
    subject = get_email_setting("email_subject_voice_learned", "🎤 Threadangle has learned your voice!")
    display_name = name_part.strip() or 'friend'
    body_fallback = f"""<p class="greeting">Your voice is learned, {display_name}! 🎤</p>

<p>After analyzing your first 3 successful generations, Threadangle now knows your unique writing style.</p>

<div class="success-box">
  <p style="font-size: 40px; margin-bottom: 8px;">🎤</p>
  <p style="font-size: 18px; font-weight: 700; color: #4ADE80; margin: 0;">Voice Profile Activated</p>
  <p style="font-size: 13px; color: #86EFAC; margin-top: 6px; margin-bottom: 0;">Future content will sound authentically like you</p>
</div>

<p>From now on, all content you generate will match <strong class="highlight">your</strong> writing style — not generic AI output.</p>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Your sentence style</strong> — length and rhythm preserved</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Your vocabulary level</strong> — casual, professional, or technical</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Your signature phrases</strong> — woven into future content</div>
  </div>
  <div class="step-item">
    <div class="step-number">✓</div>
    <div class="step-text"><strong>Your structure patterns</strong> — openings, flow, and closings</div>
  </div>
</div>

<a href="https://kriangle.com/dashboard" class="cta-button">Generate Content Now →</a>

<div class="info-box">
  <p style="margin: 0; font-size: 13px; color: #A1A1AA;">💡 <strong style="color: #FAFAFA;">Pro Tip:</strong> The more you generate, the better Threadangle understands your voice. If you'd ever like to reset your profile, just reach out.</p>
</div>

<hr class="divider">
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_voice_learned", body_fallback, {"display_name": display_name})
    unsubscribe = "You received this because your voice profile was activated on kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)


# EMAIL 7 — AUTO-POST SUCCESS NOTIFICATION
async def send_auto_post_success_email(user_email: str, user_name: str, platforms: list, content_preview: str):
    """Send notification when auto-post successfully publishes to social platforms."""
    name_part = f" {user_name}" if user_name and user_name != user_email else ""
    platform_list = ", ".join([p.title() for p in platforms])
    
    subject = get_email_setting("email_subject_auto_post_success", "✅ Your post went live!")
    body_fallback = f"""<p class="greeting">Post published{name_part}! ✨</p>

<p>Your scheduled content has been <strong class="highlight">automatically posted</strong> to {platform_list}.</p>

<div class="success-box">
  <p style="font-size: 36px; margin-bottom: 8px;">🚀</p>
  <p style="font-size: 16px; font-weight: 700; color: #4ADE80; margin: 0;">Auto-posted successfully</p>
  <p style="font-size: 13px; color: #86EFAC; margin-top: 4px; margin-bottom: 0;">On: {platform_list}</p>
</div>

<p><strong class="highlight">Your content:</strong></p>
<div class="info-box" style="border-left-color: #3B82F6;">
  <p style="margin: 0; font-size: 14px; color: #A1A1AA; line-height: 1.6;">{content_preview}</p>
</div>

<div class="steps-box">
  <div class="step-item">
    <div class="step-number">1</div>
    <div class="step-text"><strong>Check your posts</strong> — Visit each platform to see your live content</div>
  </div>
  <div class="step-item">
    <div class="step-number">2</div>
    <div class="step-text"><strong>Monitor engagement</strong> — Track likes, comments, and shares in real-time</div>
  </div>
  <div class="step-item">
    <div class="step-number">3</div>
    <div class="step-text"><strong>Schedule more posts</strong> — Use Threadangle to auto-post every day</div>
  </div>
</div>

<a href="https://kriangle.com/dashboard/history" class="cta-button">View Your Posted Content →</a>

<hr class="divider">
<p style="font-size: 14px; color: #71717A;">— The Threadangle Auto-Posting Team</p>"""
    body = render_email_body("email_body_auto_post_success", body_fallback, {
    "name_part": name_part,
    "platform_list": platform_list,
    "content_preview": content_preview,
  })
    unsubscribe = "You received this because you have auto-posting enabled on kriangle.com"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)


# EMAIL 8 — AUTO-POST FAILURE NOTIFICATION
async def send_auto_post_failure_email(user_email: str, user_name: str, failed_platforms: dict):
    """Send notification when auto-post fails to publish to one or more platforms."""
    name_part = f" {user_name}" if user_name and user_name != user_email else ""
    
    subject = get_email_setting("email_subject_auto_post_failure", "⚠️ Auto-post partially failed")
    body = f"""<p class="greeting">Auto-post issue{name_part}</p>

<p>We tried to publish your scheduled content, but encountered issues with some platforms.</p>

<div class="warning-box">
  <p style="margin: 0; font-size: 14px; color: #FCD34D;">⚠️ <strong style="color: #FAFAFA;">Action needed:</strong> Reconnect your accounts to resume auto-posting.</p>
</div>

<div class="success-box" style="background-color: #18181B; border: 1px solid #27272A; text-align: left;">
  <p style="margin: 0 0 16px 0; font-size: 14px;"><strong style="color: #FAFAFA;">Failed platforms:</strong></p>"""
    
    for platform, error_info in failed_platforms.items():
        error_msg = error_info.get('error', 'Unknown error')
        body += f"""
  <p style="margin: 8px 0; font-size: 13px; color: #FCA5A5;">
    <strong style="color: #FAFAFA;">{platform.title()}:</strong> {error_msg}
  </p>"""
    
    body += """
</div>

<p><strong class="highlight">Common reasons:</strong></p>
<div class="steps-box">
  <div class="step-item">
    <div class="step-number">🔑</div>
    <div class="step-text"><strong>Your token expired</strong> — Social platforms require periodic re-authorization</div>
  </div>
  <div class="step-item">
    <div class="step-number">📱</div>
    <div class="step-text"><strong>Account disconnected</strong> — You may have revoked our access in platform settings</div>
  </div>
  <div class="step-item">
    <div class="step-number">⚙️</div>
    <div class="step-text"><strong>Permission denied</strong> — Check platform permissions for posting rights</div>
  </div>
</div>

<p><strong class="highlight">Here's how to fix it:</strong></p>
<a href="https://kriangle.com/dashboard/settings" class="cta-button">Reconnect Your Accounts →</a>

<div class="info-box">
  <p style="margin: 0; font-size: 13px; color: #A1A1AA;">💡 <strong style="color: #FAFAFA;">Once reconnected,</strong> your next scheduled post will auto-post successfully. No need to reschedule.</p>
</div>

<hr class="divider">
<p style="font-size: 14px; color: #71717A;">Need help? Reply to this email and we'll assist you right away.</p>
<p style="font-size: 14px; color: #71717A;">— The Threadangle Team</p>"""
    body = render_email_body("email_body_auto_post_failure", body, {
    "name_part": name_part,
    "failed_platforms_html": "".join(
      [
        f"<p style=\"margin: 8px 0; font-size: 13px; color: #FCA5A5;\"><strong style=\"color: #FAFAFA;\">{platform.title()}:</strong> {error_info.get('error', 'Unknown error')}</p>"
        for platform, error_info in failed_platforms.items()
      ]
    ),
  })
    unsubscribe = "You received this because auto-posting failed on your scheduled content"
    html = get_email_wrapper(subject, body, unsubscribe)
    return await send_email_async(user_email, subject, html)


async def test_email_connection():
    config = get_smtp_config()
    if not config["username"]:
        print("EMAIL TEST FAILED: SMTP_USER/ZOHO_EMAIL not found in environment")
        return
        
    subject = "Threadangle email system working ✅"
    body = "<p class='greeting'>Success!</p><p>The Zoho SMTP connection is working perfectly. Branded emails are ready to send.</p>"
    html = get_email_wrapper(subject, body, "Internal test email")
    
    success = await send_email_async(config["username"], subject, html)
    if success:
        print(f"EMAIL TEST SUCCESSFUL: Sent to {config['username']}")
    else:
        print("EMAIL TEST FAILED: Check SMTP credentials")
        
    subject = "Threadangle email system working ✅"
    body = "<p class='greeting'>Success!</p><p>The Zoho SMTP connection is working perfectly. Branded emails are ready to send.</p>"
    html = get_email_wrapper(subject, body, "Internal test email")
    
    success = await send_email_async(config["username"], subject, html)
    if success:
        print(f"EMAIL TEST SUCCESSFUL: Sent to {config['username']}")
    else:
        print("EMAIL TEST FAILED: Check SMTP credentials")
