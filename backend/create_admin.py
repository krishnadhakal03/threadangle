"""
create_admin.py — Create a test user and set up admin password.

Usage (from f:\\Threadforge\\backend with venv active):
  python create_admin.py

What it does:
  1. Creates (or updates) a user with plan=founder and onboarding done
  2. Ensures ADMIN_PASSWORD is set in .env
"""

import os
import sys
import sqlite3
import secrets

# ── Config ───────────────────────────────────────────────────────────────────
TEST_EMAIL    = "admin@test.com"
TEST_PASSWORD = "Admin@12345"
TEST_NAME     = "Admin Tester"
TEST_PLAN     = "founder"   # founder | solo | free

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
DB_PATH  = os.path.join(os.path.dirname(__file__), "threadangle.db")
# ─────────────────────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.dirname(__file__))

# ── 1. Hash the password using the same bcrypt the app uses ──────────────────
import bcrypt

def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

# ── 2. Ensure ADMIN_PASSWORD in .env ─────────────────────────────────────────
def read_env() -> dict:
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    return env

def write_env_key(key: str, value: str):
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

env = read_env()
admin_pw = env.get("ADMIN_PASSWORD", "")
if not admin_pw:
    admin_pw = secrets.token_urlsafe(16)
    write_env_key("ADMIN_PASSWORD", admin_pw)
    print(f"✅ ADMIN_PASSWORD written to .env  →  {admin_pw}")
else:
    print(f"✅ ADMIN_PASSWORD already set      →  {admin_pw}")

# ── 3. Upsert the test user via plain sqlite3 ─────────────────────────────────
pw_hash = hash_pw(TEST_PASSWORD)
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("SELECT id FROM users WHERE email = ?", (TEST_EMAIL,))
row = cur.fetchone()

if row:
    cur.execute(
        "UPDATE users SET password_hash=?, plan=?, name=?, onboarding_completed=1, usage_count=0 WHERE email=?",
        (pw_hash, TEST_PLAN, TEST_NAME, TEST_EMAIL),
    )
    print(f"🔄 Updated existing user: {TEST_EMAIL}")
else:
    cur.execute(
        "INSERT INTO users (email, password_hash, plan, name, usage_count, onboarding_completed) VALUES (?,?,?,?,0,1)",
        (TEST_EMAIL, pw_hash, TEST_PLAN, TEST_NAME),
    )
    print(f"🆕 Created new user: {TEST_EMAIL}")

con.commit()
con.close()

# ── 4. Summary ────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("  TEST USER  (sign in as a regular member)")
print("=" * 60)
print(f"  URL      : https://localhost:5173/login")
print(f"  Email    : {TEST_EMAIL}")
print(f"  Password : {TEST_PASSWORD}")
print(f"  Plan     : {TEST_PLAN}  (unlimited generations)")
print()
print("=" * 60)
print("  ADMIN API  (stats dashboard — no login needed)")
print("=" * 60)
print(f"  Header   : X-Admin-Password: {admin_pw}")
print()
print("  PowerShell:")
print(f'  Invoke-RestMethod -Uri "http://localhost:8000/api/admin/stats" `')
print(f'    -Headers @{{ "X-Admin-Password" = "{admin_pw}" }} | ConvertTo-Json -Depth 5')
print()
print("  curl:")
print(f'  curl -s -H "X-Admin-Password: {admin_pw}" http://localhost:8000/api/admin/stats')
print("=" * 60)
