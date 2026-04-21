import os
import sqlite3

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'threadangle.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)
    conn.commit()
    return conn


class SubscribeRequest(BaseModel):
    email: str


@router.post("/newsletter/subscribe")
async def subscribe(request: SubscribeRequest):
    email = request.email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Valid email required")

    conn = _get_conn()
    try:
        conn.execute("INSERT INTO newsletter_subscribers (email) VALUES (?)", (email,))
        conn.commit()
        return {"success": True, "message": "Subscribed successfully"}
    except sqlite3.IntegrityError:
        return {"success": True, "message": "Already subscribed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/admin/newsletter/count")
async def get_subscriber_count(x_admin_password: str = Header(None)):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    conn = _get_conn()
    count = conn.execute(
        "SELECT COUNT(*) FROM newsletter_subscribers WHERE status='active'"
    ).fetchone()[0]
    conn.close()
    return {"count": count}
