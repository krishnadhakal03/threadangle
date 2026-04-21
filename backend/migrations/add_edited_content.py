"""
Migration: add_edited_content
Adds edited content columns to the generations table.

Usage:
    cd backend
    python migrations/add_edited_content.py
"""
import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_path():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./threadangle.db")
    if "sqlite" not in url:
        raise ValueError(f"This migration only supports SQLite. DATABASE_URL={url}")

    raw_path = url.split("///")[-1]
    if raw_path.startswith("./"):
        raw_path = raw_path[2:]

    backend_dir = Path(__file__).parent.parent
    return str(backend_dir / raw_path)


def upgrade():
    db_path = get_db_path()
    print(f"📁 Database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(generations)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("twitter_content_edited", "TEXT"),
        ("linkedin_content_edited", "TEXT"),
        ("tiktok_content_edited", "TEXT"),
        ("has_edits", "BOOLEAN DEFAULT 0"),
        ("last_edited_at", "TIMESTAMP"),
    ]

    added = []
    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE generations ADD COLUMN {col_name} {col_def}")
            added.append(col_name)
            print(f"   ✅ Added column: {col_name}")
        else:
            print(f"   ⏭  Already exists: {col_name}")

    conn.commit()
    conn.close()

    if added:
        print(f"\n✅ Migration complete — added: {', '.join(added)}")
    else:
        print("\n✅ Nothing to do — all columns already present")


if __name__ == "__main__":
    upgrade()
