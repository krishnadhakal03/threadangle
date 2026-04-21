import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import get_db
from models import Contact
from email_service import send_admin_contact_notification, send_contact_auto_reply
from auth import get_current_user
from models import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class ContactReq(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: constr(min_length=20)

@router.post("")
@limiter.limit("3/hour")
async def create_contact(request: Request, contact_req: ContactReq, db: AsyncSession = Depends(get_db)):
    # Save to database
    new_contact = Contact(
        name=contact_req.name,
        email=contact_req.email,
        subject=contact_req.subject,
        message=contact_req.message
    )
    db.add(new_contact)
    await db.commit()
    await db.refresh(new_contact)
    
    # Send emails (non-blocking)
    try:
        import asyncio
        contact_data = {
            "name": contact_req.name,
            "email": contact_req.email,
            "subject": contact_req.subject,
            "message": contact_req.message
        }
        asyncio.create_task(send_admin_contact_notification(contact_data))
        asyncio.create_task(send_contact_auto_reply(contact_req.name, contact_req.email))
    except Exception:
        pass
        
    return {"message": "Thanks! We will get back to you within 24 hours."}


class BugReportReq(BaseModel):
    category: str
    description: constr(min_length=10)
    steps: Optional[str] = ""
    severity: str
    user_email: Optional[str] = ""
    user_plan: Optional[str] = ""

@router.post("/bug-report")
@limiter.limit("5/hour")
async def submit_bug_report(request: Request, bug_req: BugReportReq, db: AsyncSession = Depends(get_db)):
    valid_categories = {"UI/Display Issue", "Content Generation Bug", "Scheduling Issue", "Account/Billing", "Performance", "Feature Request", "Other"}
    valid_severities = {"low", "medium", "high"}
    if bug_req.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")
    if bug_req.severity not in valid_severities:
        raise HTTPException(status_code=400, detail="Invalid severity")

    # Send bug report email (non-blocking)
    try:
        import asyncio
        bug_data = {
            "category": bug_req.category,
            "description": bug_req.description,
            "steps": bug_req.steps or "Not provided",
            "severity": bug_req.severity.upper(),
            "user_email": bug_req.user_email or "Anonymous",
            "user_plan": bug_req.user_plan or "Unknown",
            "submitted_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
        asyncio.create_task(_send_bug_report_email(bug_data))
    except Exception:
        pass

    return {"message": "Bug report submitted. We will investigate within 24 hours."}


async def _send_bug_report_email(data: dict):
    """Send a formatted bug report email to the bugs inbox."""
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_user = os.getenv("ZOHO_EMAIL")
        smtp_pass = os.getenv("ZOHO_PASSWORD")
        if not smtp_user or not smtp_pass:
            return

        severity_emoji = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴"}.get(data["severity"], "⚪")

        body = f"""
<h2>🐛 Bug Report — {data['category']}</h2>

<p><strong>Severity:</strong> {severity_emoji} {data['severity']}</p>
<p><strong>Reporter:</strong> {data['user_email']} ({data['user_plan']} plan)</p>
<p><strong>Submitted:</strong> {data['submitted_at']}</p>

<h3>Description</h3>
<p>{data['description']}</p>

<h3>Steps to Reproduce</h3>
<p>{data['steps']}</p>
"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[BUG] [{data['severity']}] {data['category']} — {data['user_email']}"
        msg["From"] = smtp_user
        msg["To"] = "bugs@kriangle.com"
        msg.attach(MIMEText(body, "html"))

        await aiosmtplib.send(
            msg,
            hostname="smtp.zoho.com",
            port=587,
            start_tls=True,
            username=smtp_user,
            password=smtp_pass,
        )
    except Exception as e:
        print(f"[bug-report] Email send failed: {e}")
