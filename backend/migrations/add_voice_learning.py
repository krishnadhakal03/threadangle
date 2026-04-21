"""
Migration: add_voice_learning
Adds voice profile columns to the users table.

Usage:
    cd backend
    python migrations/add_voice_learning.py
"""
import os
import sys
import sqlite3
from pathlib import Path

# Allow imports from the backend package
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_db_path():
    """Resolve the SQLite file path from DATABASE_URL."""
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./threadangle.db")
    if "sqlite" not in url:
        raise ValueError(f"This migration only supports SQLite. DATABASE_URL={url}")

    # Strip driver prefix: "sqlite+aiosqlite:///./foo.db" → "./foo.db"
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
        ("voice_profile", "TEXT"),
        ("voice_learned", "BOOLEAN DEFAULT 0"),
        ("successful_generations_count", "INTEGER DEFAULT 0"),
        ("voice_learned_at", "TIMESTAMP"),
    ]

    added = []
    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
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
