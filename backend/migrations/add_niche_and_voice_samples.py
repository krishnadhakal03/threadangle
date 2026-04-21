"""
Migration: add_niche_and_voice_samples
Adds niche_tags and voice_samples_submitted columns to the users table.

Usage:
    cd backend
    python migrations/add_niche_and_voice_samples.py
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

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    columns_to_add = [
        ("niche_tags", "TEXT"),
        ("voice_samples_submitted", "BOOLEAN DEFAULT 0"),
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            print(f"  ✅ Added column: {col_name}")
        else:
            print(f"  ⏭️  Column already exists: {col_name}")

    conn.commit()
    conn.close()
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    upgrade()
