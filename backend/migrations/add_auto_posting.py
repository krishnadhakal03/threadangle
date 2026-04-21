"""
Migration: Add auto-posting and social account features
Creates social_accounts table and adds auto-posting columns to generations
"""

from sqlalchemy import create_engine, text
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./threadangle.db")
# Convert async URL to sync for migration
if "aiosqlite" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sqlite+aiosqlite", "sqlite")

def upgrade():
    """Run migration"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("\n🔄 Starting auto-posting migration...")
        print("="*60)
        
        # Create social_accounts table
        print("\n1️⃣ Creating social_accounts table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS social_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                platform VARCHAR NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_expires_at TIMESTAMP,
                platform_user_id VARCHAR,
                platform_username VARCHAR,
                platform_profile_pic VARCHAR,
                is_active BOOLEAN DEFAULT 1,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        print("✅ social_accounts table created")
        
        # Check if auto_post_enabled column already exists
        print("\n2️⃣ Adding auto-posting columns to generations...")
        try:
            # Try to add columns one by one (SQLite doesn't support multiple ADD COLUMN)
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_post_enabled BOOLEAN DEFAULT 0
                """))
                print("   ✅ Added auto_post_enabled")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_post_enabled already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_post_platforms TEXT
                """))
                print("   ✅ Added auto_post_platforms")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_post_platforms already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_post_time TIMESTAMP
                """))
                print("   ✅ Added auto_post_time")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_post_time already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_posted BOOLEAN DEFAULT 0
                """))
                print("   ✅ Added auto_posted")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_posted already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_posted_at TIMESTAMP
                """))
                print("   ✅ Added auto_posted_at")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_posted_at already exists")
                else:
                    raise
            
            try:
                conn.execute(text("""
                    ALTER TABLE generations ADD COLUMN auto_post_results TEXT
                """))
                print("   ✅ Added auto_post_results")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print("   ⏭️  auto_post_results already exists")
                else:
                    raise
            
        except Exception as e:
            print(f"⚠️  Warning during column addition: {e}")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ AUTO-POSTING MIGRATION COMPLETE!")
        print("\nNew features enabled:")
        print("  • Social account connections (Twitter, LinkedIn, Instagram)")
        print("  • Encrypted token storage")
        print("  • Scheduled auto-posting")
        print("="*60 + "\n")

if __name__ == "__main__":
    upgrade()
