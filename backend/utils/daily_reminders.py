"""
Daily reminder system for scheduled posts
Sends email to users with posts scheduled for today
Run this daily at 9:00 AM via cron job
"""
import asyncio
import json
from datetime import date, datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import models and email service
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import User, Generation
from email_service import send_email_async

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./threadangle.db")
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def send_scheduled_posts_email(user, scheduled_posts):
    """
    Send email to user with their scheduled posts for today
    """
    
    subject = f"📅 You have {len(scheduled_posts)} post{'s' if len(scheduled_posts) != 1 else ''} scheduled for today"
    
    # Build posts list HTML
    posts_html = ""
    for i, post in enumerate(scheduled_posts, 1):
        time_str = post.scheduled_time.strftime("%I:%M %p") if post.scheduled_time else "No time set"
        
        # Get platforms
        platforms = json.loads(post.scheduled_platforms) if post.scheduled_platforms else ["all"]
        platform_icons = []
        if "all" in platforms or "twitter" in platforms:
            platform_icons.append("🐦 Twitter")
        if "all" in platforms or "linkedin" in platforms:
            platform_icons.append("💼 LinkedIn")
        if "all" in platforms or "tiktok" in platforms:
            platform_icons.append("🎵 TikTok")
        
        # Get content preview
        preview = ""
        if post.twitter_content_edited:
            preview = post.twitter_content_edited[:150]
        elif post.twitter_output:
            try:
                content = post.twitter_output if isinstance(post.twitter_output, str) else json.dumps(post.twitter_output)
                preview = content[:150]
            except:
                preview = "Twitter content"
        elif post.linkedin_content_edited:
            preview = post.linkedin_content_edited[:150]
        elif post.linkedin_output:
            try:
                content = post.linkedin_output if isinstance(post.linkedin_output, str) else json.dumps(post.linkedin_output)
                preview = content[:150]
            except:
                preview = "LinkedIn content"
        elif post.tiktok_content_edited:
            preview = post.tiktok_content_edited[:150]
        elif post.tiktok_output:
            try:
                content = post.tiktok_output if isinstance(post.tiktok_output, str) else json.dumps(post.tiktok_output)
                preview = content[:150]
            except:
                preview = "TikTok content"
        else:
            preview = "Content preview unavailable"
        
        posts_html += f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 16px; border-left: 4px solid #3b82f6;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <div style="color: #3b82f6; font-weight: 700; font-size: 16px;">
                    ⏰ {time_str}
                </div>
                <div style="color: #64748b; font-size: 13px;">
                    {' • '.join(platform_icons)}
                </div>
            </div>
            
            <div style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 12px;">
                {preview}{'...' if len(preview) >= 150 else ''}
            </div>
            
            <div style="display: flex; gap: 12px; margin-top: 16px;">
                <a href="https://kriangle.com/dashboard" 
                   style="display: inline-block; background: #3b82f6; color: white; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600;">
                    View in Calendar →
                </a>
            </div>
        </div>
        """
    
    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #000000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
        
        <div style="max-width: 600px; margin: 40px auto; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 16px; overflow: hidden; border: 1px solid #334155;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 32px 24px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">📅</div>
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">Time to Post!</h1>
                <p style="color: #bfdbfe; margin: 8px 0 0; font-size: 15px;">
                    You have {len(scheduled_posts)} post{'s' if len(scheduled_posts) != 1 else ''} scheduled for today
                </p>
            </div>
            
            <!-- Content -->
            <div style="padding: 32px 24px; color: #e2e8f0;">
                
                <p style="color: #cbd5e1; line-height: 1.7; margin: 0 0 24px; font-size: 15px;">
                    Hi{' ' + user.name if user.name and user.name != user.email else ''},
                </p>
                
                <p style="color: #cbd5e1; line-height: 1.7; margin: 0 0 24px; font-size: 15px;">
                    Here are your scheduled posts for <strong style="color: #ffffff;">{date.today().strftime('%A, %B %d, %Y')}</strong>:
                </p>
                
                {posts_html}
                
                <div style="background: #0f172a; border-left: 4px solid #3b82f6; padding: 16px 20px; margin: 24px 0; border-radius: 8px;">
                    <p style="color: #3b82f6; margin: 0 0 8px; font-weight: 700; font-size: 14px;">💡 Pro Tip:</p>
                    <p style="color: #94a3b8; margin: 0; line-height: 1.6; font-size: 13px;">
                        After posting, click "Mark as Posted" in your calendar to track your consistency and build your posting streak!
                    </p>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div style="background: #0f172a; padding: 24px; border-top: 1px solid #1e293b; text-align: center;">
                <p style="color: #64748b; font-size: 13px; margin: 0 0 12px;">
                    <a href="https://kriangle.com/dashboard" style="color: #3b82f6; text-decoration: none;">Open Calendar</a>
                    <span style="margin: 0 8px; color: #334155;">•</span>
                    <a href="https://kriangle.com/dashboard" style="color: #3b82f6; text-decoration: none;">Dashboard</a>
                    <span style="margin: 0 8px; color: #334155;">•</span>
                    <a href="mailto:info@kriangle.com" style="color: #3b82f6; text-decoration: none;">Contact</a>
                </p>
                <p style="color: #475569; font-size: 12px; margin: 0;">
                    <strong style="color: #64748b;">Threadangle</strong> • © 2026 Kriangle
                </p>
            </div>
            
        </div>
        
    </body>
    </html>
    """
    
    try:
        await send_email_async(user.email, subject, html_body)
        print(f"  ✅ Sent reminder to {user.email} ({len(scheduled_posts)} posts)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to send to {user.email}: {e}")
        return False


async def send_daily_reminders():
    """
    Send email reminders to all users with scheduled posts for today
    Run this daily at 9:00 AM via cron job
    """
    
    print("\n" + "="*60)
    print(f"📧 SENDING DAILY REMINDERS - {datetime.now()}")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            today = date.today()
            
            # Get all users who have posts scheduled for today
            result = await db.execute(
                select(User)
                .join(Generation)
                .filter(
                    and_(
                        Generation.scheduled_date == today,
                        Generation.posted == False
                    )
                )
                .distinct()
            )
            users_with_scheduled = result.scalars().all()
            
            print(f"Found {len(users_with_scheduled)} users with scheduled posts today")
            
            for user in users_with_scheduled:
                # Get user's scheduled posts for today
                result = await db.execute(
                    select(Generation).filter(
                        and_(
                            Generation.user_id == user.id,
                            Generation.scheduled_date == today,
                            Generation.posted == False
                        )
                    ).order_by(Generation.scheduled_time)
                )
                scheduled_posts = result.scalars().all()
                
                if scheduled_posts:
                    await send_scheduled_posts_email(user, scheduled_posts)
            
            print(f"✅ Sent {len(users_with_scheduled)} reminder emails")
            
        except Exception as e:
            print(f"❌ Error sending reminders: {e}")
            import traceback
            traceback.print_exc()
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(send_daily_reminders())
