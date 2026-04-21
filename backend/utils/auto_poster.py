"""
Auto-posting worker - posts scheduled content to social platforms
Run this periodically (every 5 minutes) via cron job or task scheduler
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from database import AsyncSessionLocal
from models import Generation, SocialAccount, User
from integrations.twitter import post_to_twitter
from integrations.linkedin import post_to_linkedin
from integrations.instagram import post_to_instagram
from utils.encryption import decrypt_token
from email_service import send_auto_post_success_email, send_auto_post_failure_email
from datetime import datetime
import json

async def process_auto_posts():
    """
    Check for scheduled posts that need to be published
    Run this every 5 minutes via cron job or Windows Task Scheduler
    """
    
    print("\n🤖 AUTO-POSTING CHECK:", datetime.now())
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get generations scheduled for posting (within last 5 minutes)
            now = datetime.utcnow()
            
            result = await db.execute(
                select(Generation).where(
                    Generation.auto_post_enabled == True,
                    Generation.auto_posted == False,
                    Generation.auto_post_time <= now
                )
            )
            pending_posts = result.scalars().all()
            
            print(f"Found {len(pending_posts)} posts to publish")
            
            for gen in pending_posts:
                print(f"\n📤 Processing generation {gen.id}...")
                
                # Get user info for notifications
                user_result = await db.execute(
                    select(User).where(User.id == gen.user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    print(f"   ❌ User not found for generation {gen.id}")
                    continue
                
                platforms = json.loads(gen.auto_post_platforms) if gen.auto_post_platforms else []
                results = {}
                
                for platform in platforms:
                    print(f"   → Posting to {platform}...")
                    
                    # Get user's connected account
                    account_result = await db.execute(
                        select(SocialAccount).where(
                            SocialAccount.user_id == gen.user_id,
                            SocialAccount.platform == platform,
                            SocialAccount.is_active == True
                        )
                    )
                    social_account = account_result.scalar_one_or_none()
                    
                    if not social_account:
                        results[platform] = {
                            'success': False,
                            'error': 'Account not connected'
                        }
                        print(f"      ❌ Account not connected")
                        continue
                    
                    # Decrypt token
                    access_token = decrypt_token(social_account.access_token)
                    
                    if not access_token:
                        results[platform] = {
                            'success': False,
                            'error': 'Failed to decrypt token'
                        }
                        print(f"      ❌ Failed to decrypt token")
                        continue
                    
                    # Get content for this platform
                    try:
                        if platform == 'twitter':
                            # Use edited version if available, otherwise original
                            content = gen.twitter_content_edited if gen.twitter_content_edited else (
                                gen.twitter_output.get('thread') if gen.twitter_output else None
                            )
                            if not content:
                                results[platform] = {'success': False, 'error': 'No content found'}
                                print(f"      ❌ No content found")
                                continue
                            
                            result = post_to_twitter(access_token, content)
                            
                        elif platform == 'linkedin':
                            content = gen.linkedin_content_edited if gen.linkedin_content_edited else (
                                gen.linkedin_output.get('content') if gen.linkedin_output else None
                            )
                            if not content:
                                results[platform] = {'success': False, 'error': 'No content found'}
                                print(f"      ❌ No content found")
                                continue
                            
                            result = post_to_linkedin(access_token, content, social_account.platform_user_id)
                            
                        elif platform == 'instagram':
                            content = gen.reels_description_edited if gen.reels_description_edited else gen.reels_description
                            if not content:
                                results[platform] = {'success': False, 'error': 'No content found'}
                                print(f"      ❌ No content found")
                                continue
                            
                            result = post_to_instagram(access_token, content, social_account.platform_user_id)
                        
                        results[platform] = result
                        
                        if result.get('success'):
                            print(f"      ✅ Posted successfully")
                            # Update last used time
                            social_account.last_used_at = datetime.utcnow()
                        else:
                            print(f"      ❌ Failed: {result.get('error')}")
                    
                    except Exception as e:
                        results[platform] = {
                            'success': False,
                            'error': str(e)
                        }
                        print(f"      ❌ Exception: {e}")
                
                # Update generation
                gen.auto_posted = True
                gen.auto_posted_at = datetime.utcnow()
                gen.auto_post_results = json.dumps(results)
                
                await db.commit()
                
                success_platforms = [p for p, r in results.items() if r.get('success')]
                failed_platforms = {p: r for p, r in results.items() if not r.get('success')}
                
                if success_platforms:
                    print(f"✅ Posted to: {', '.join(success_platforms)}")
                    
                    # Get content preview for email (first 200 chars)
                    content_preview = ""
                    if success_platforms[0] == 'twitter' and gen.twitter_output:
                        content_preview = gen.twitter_output.get('thread', '')[:200]
                    elif success_platforms[0] == 'linkedin' and gen.linkedin_output:
                        content_preview = gen.linkedin_output.get('content', '')[:200]
                    elif success_platforms[0] == 'instagram' and gen.reels_description:
                        content_preview = gen.reels_description[:200]
                    
                    # Send success email
                    try:
                        await send_auto_post_success_email(
                            user_email=user.email,
                            user_name=user.name or user.email.split('@')[0],
                            platforms=success_platforms,
                            content_preview=content_preview
                        )
                        print(f"📧 Success notification sent to {user.email}")
                    except Exception as e:
                        print(f"⚠️  Failed to send success email: {e}")
                
                if failed_platforms:
                    print(f"⚠️  Failed on: {', '.join(failed_platforms.keys())}")
                    
                    # Send failure email
                    try:
                        await send_auto_post_failure_email(
                            user_email=user.email,
                            user_name=user.name or user.email.split('@')[0],
                            failed_platforms=failed_platforms
                        )
                        print(f"📧 Failure notification sent to {user.email}")
                    except Exception as e:
                        print(f"⚠️  Failed to send failure email: {e}")
            
            if len(pending_posts) == 0:
                print("No posts scheduled for this time")
        
        except Exception as e:
            print(f"❌ Auto-posting error: {e}")
            import traceback
            traceback.print_exc()
    
    print("="*60 + "\n")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(process_auto_posts())
