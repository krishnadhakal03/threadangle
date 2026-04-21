"""Migration: add custom_limit column to users table"""
import sqlite3
import os


def run():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'threadangle.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN custom_limit INTEGER")
        conn.commit()
        print("✅ Added custom_limit column to users table")
    except Exception as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  Column custom_limit already exists — skipping")
        else:
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
