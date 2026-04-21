"""
Run daily reminders script
Execute this via cron job at 9:00 AM every day

Windows Task Scheduler example:
- Program: python
- Arguments: F:\Threadforge\backend\run_daily_reminders.py
- Start in: F:\Threadforge\backend
- Trigger: Daily at 9:00 AM

Linux/macOS cron entry:
0 9 * * * cd /path/to/backend && python run_daily_reminders.py >> /var/log/threadangle_reminders.log 2>&1
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set working directory to backend folder
os.chdir(Path(__file__).parent)

from utils.daily_reminders import send_daily_reminders

if __name__ == "__main__":
    print("🚀 Starting daily reminders job...")
    asyncio.run(send_daily_reminders())
    print("✅ Daily reminders job completed")
