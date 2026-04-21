"""
Run auto-posting worker
Add to Windows Task Scheduler or cron: */5 * * * * python run_auto_poster.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.auto_poster import process_auto_posts
import asyncio

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  THREADANGLE AUTO-POSTER")
    print("="*60)
    
    asyncio.run(process_auto_posts())
