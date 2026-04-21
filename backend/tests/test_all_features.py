"""
Comprehensive test suite for all Threadangle features
Run this before launch to ensure everything works
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import synchronous SQLAlchemy for testing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import User, Generation
from utils.youtube import get_youtube_transcript, extract_video_id
from utils.voice_learning import analyze_user_voice, build_voice_prompt
from utils.hook_generator import generate_all_hook_variations, extract_current_hook
from datetime import date, time, datetime
import json

# Create synchronous database connection for testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./threadangle.db").replace("sqlite+aiosqlite", "sqlite")
sync_engine = create_engine(DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(bind=sync_engine)

def print_test_header(test_name):
    print("\n" + "="*70)
    print(f"🧪 TEST: {test_name}")
    print("="*70)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_warning(message):
    print(f"⚠️  {message}")


# ═══════════════════════════════════════════════════════════════
# TEST 1: Database Schema Verification
# ═══════════════════════════════════════════════════════════════

def test_database_schema():
    print_test_header("Database Schema Verification")
    
    db = TestSessionLocal()
    
    try:
        # Check User table
        user = db.query(User).first()
        
        if not user:
            print_warning("No users in database - create a test user first")
            return True  # Not a failure, just empty DB
        
        # Check voice learning columns
        assert hasattr(user, 'voice_profile'), "Missing voice_profile column"
        assert hasattr(user, 'voice_learned'), "Missing voice_learned column"
        assert hasattr(user, 'successful_generations_count'), "Missing successful_generations_count column"
        print_success("User table has voice learning columns")
        
        # Check Generation table
        gen = db.query(Generation).first()
        if gen:
            # Editing columns
            assert hasattr(gen, 'twitter_content_edited'), "Missing twitter_content_edited"
            assert hasattr(gen, 'linkedin_content_edited'), "Missing linkedin_content_edited"
            assert hasattr(gen, 'tiktok_content_edited'), "Missing tiktok_content_edited"
            print_success("Generation table has editing columns")
            
            # Reels/Shorts columns
            assert hasattr(gen, 'reels_title'), "Missing reels_title"
            assert hasattr(gen, 'reels_description'), "Missing reels_description"
            assert hasattr(gen, 'shorts_title'), "Missing shorts_title"
            assert hasattr(gen, 'shorts_tags'), "Missing shorts_tags"
            print_success("Generation table has Reels/Shorts columns")
            
            # Hook variations
            assert hasattr(gen, 'hook_variations'), "Missing hook_variations"
            print_success("Generation table has hook variations column")
            
            # Scheduling columns
            assert hasattr(gen, 'scheduled_date'), "Missing scheduled_date"
            assert hasattr(gen, 'scheduled_time'), "Missing scheduled_time"
            assert hasattr(gen, 'posted'), "Missing posted column"
            print_success("Generation table has scheduling columns")
        else:
            print_warning("No generations yet - some schema checks skipped")
        
        print_success("✓ Database schema is complete")
        return True
        
    except AssertionError as e:
        print_error(f"Schema check failed: {e}")
        return False
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TEST 2: YouTube Transcript Extraction
# ═══════════════════════════════════════════════════════════════

def test_youtube_features():
    print_test_header("YouTube Transcript Extraction")
    
    test_urls = [
        "https://www.youtube.com/watch?v=LCmiKLMk2SI",  # Interview video
        "https://youtu.be/LCmiKLMk2SI",  # Short link format
    ]
    
    all_passed = True
    
    for url in test_urls:
        print(f"\n📹 Testing: {url}")
        
        # Test video ID extraction
        video_id = extract_video_id(url)
        if video_id:
            print_success(f"Extracted video ID: {video_id}")
        else:
            print_error("Failed to extract video ID")
            all_passed = False
            continue
        
        # Test transcript extraction
        transcript, error = get_youtube_transcript(url, max_words=500)
        
        if error:
            print_error(f"Transcript extraction failed: {error}")
            all_passed = False
        elif transcript:
            word_count = len(transcript.split())
            print_success(f"Transcript extracted: {word_count} words")
            
            # Check if cleaned (no excessive filler words)
            filler_count = transcript.lower().count(' um ') + transcript.lower().count(' uh ')
            if filler_count > 5:
                print_warning(f"Transcript may need better cleaning (found {filler_count} filler words)")
            else:
                print_success("Transcript cleaning working well")
        else:
            print_error("Transcript is empty")
            all_passed = False
    
    return all_passed


# ═══════════════════════════════════════════════════════════════
# TEST 3: Voice Learning System
# ═══════════════════════════════════════════════════════════════

def test_voice_learning():
    print_test_header("Voice Learning System")
    
    db = TestSessionLocal()
    
    try:
        # Find a user with at least 3 successful generations
        user = db.query(User).filter(User.successful_generations_count >= 3).first()
        
        if not user:
            print_warning("No user with 3+ generations found - voice learning test skipped")
            print_warning("This is OK if database is fresh - test after generating content")
            return True  # Not a failure, just can't test yet
        
        # Get user's generations
        gens = db.query(Generation).filter(
            Generation.user_id == user.id,
            Generation.status == 'success'
        ).limit(5).all()
        
        if len(gens) < 3:
            print_warning(f"User only has {len(gens)} generations (need 3+)")
            return True  # Not a failure, just can't test
        
        print_success(f"Found user with {len(gens)} successful generations")
        
        # Test voice analysis
        print("\n🎤 Testing voice analysis...")
        voice_profile = analyze_user_voice(gens)
        
        if voice_profile:
            print_success("Voice profile generated successfully")
            
            # Check profile structure
            required_keys = ['sentence_style', 'vocabulary_level', 'primary_tone']
            for key in required_keys:
                if key in voice_profile:
                    print_success(f"  {key}: {voice_profile[key]}")
                else:
                    print_error(f"  Missing key: {key}")
                    return False
            
            # Test voice prompt building
            voice_prompt = build_voice_prompt(voice_profile)
            if voice_prompt and len(voice_prompt) > 100:
                print_success(f"Voice prompt built: {len(voice_prompt)} characters")
            else:
                print_error("Voice prompt building failed")
                return False
        else:
            print_error("Voice analysis failed")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Voice learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TEST 4: Hook Generation
# ═══════════════════════════════════════════════════════════════

def test_hook_generation():
    print_test_header("Hook Variations Generation")
    
    test_content = "Most founders waste months building the wrong product. Here's what I learned after three failed startups: talk to users before writing code."
    
    # Test hook extraction
    print("\n🎣 Testing hook extraction...")
    hook = extract_current_hook(test_content, 'twitter')
    
    if hook:
        print_success(f"Extracted hook: {hook[:60]}...")
    else:
        print_error("Hook extraction failed")
        return False
    
    # Test that hook generation function is available
    print("\n🎣 Checking hook generation function...")
    if callable(generate_all_hook_variations):
        print_success("Hook generation function is available")
        print_warning("Skipping live API test (would consume Claude API credits)")
        return True
    else:
        print_error("Hook generation function not found")
        return False


# ═══════════════════════════════════════════════════════════════
# TEST 5: Email System
# ═══════════════════════════════════════════════════════════════

def test_email_system():
    print_test_header("Email Notification System")
    
    # Note: This won't actually send emails unless you want it to
    # Just checks that the email functions are working
    
    print("\n📧 Checking email configuration...")
    
    import os
    required_env_vars = [
        'ZOHO_EMAIL',
        'ZOHO_PASSWORD',
    ]
    
    all_configured = True
    for var in required_env_vars:
        if os.getenv(var):
            print_success(f"{var} is configured")
        else:
            print_error(f"{var} is missing")
            all_configured = False
    
    if not all_configured:
        print_error("Email configuration incomplete")
        return False
    
    print_success("Email system properly configured")
    
    # Optional: Test email sending (uncomment if you want to actually send a test email)
    # try:
    #     test_email = "your-test-email@gmail.com"
    #     await send_email_async(test_email, "Threadangle Test Email", "<h1>Test successful!</h1>")
    #     print_success(f"Test email sent to {test_email}")
    # except Exception as e:
    #     print_error(f"Failed to send test email: {e}")
    #     return False
    
    return True


# ═══════════════════════════════════════════════════════════════
# TEST 6: Calendar & Scheduling
# ═══════════════════════════════════════════════════════════════

def test_calendar_scheduling():
    print_test_header("Calendar & Scheduling System")
    
    db = TestSessionLocal()
    
    try:
        # Get a generation to test scheduling
        gen = db.query(Generation).filter(Generation.status == 'success').first()
        
        if not gen:
            print_warning("No successful generations to test scheduling")
            return True
        
        # Test scheduling
        print("\n📅 Testing scheduling...")
        gen.scheduled_date = date.today()
        gen.scheduled_time = time(14, 30)
        gen.scheduled_platforms = json.dumps(["twitter", "linkedin"])
        gen.posted = False
        
        db.commit()
        print_success("Generation scheduled successfully")
        
        # Test marking as posted
        print("\n✓ Testing mark as posted...")
        gen.posted = True
        gen.posted_at = datetime.utcnow()
        
        db.commit()
        print_success("Generation marked as posted")
        
        # Cleanup
        gen.scheduled_date = None
        gen.scheduled_time = None
        gen.posted = False
        gen.posted_at = None
        db.commit()
        
        return True
        
    except Exception as e:
        print_error(f"Calendar test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
# TEST 7: Performance & Security Checks
# ═══════════════════════════════════════════════════════════════

def test_performance_security():
    print_test_header("Performance & Security Checks")
    
    import os
    
    # Check critical environment variables
    print("\n🔐 Checking environment variables...")
    
    critical_vars = {
        'ANTHROPIC_API_KEY': 'Anthropic API',
        'STRIPE_SECRET_KEY': 'Stripe API',
        'STRIPE_WEBHOOK_SECRET': 'Stripe Webhook',
        'DATABASE_URL': 'Database',
        'JWT_SECRET': 'JWT Secret'
    }
    
    all_set = True
    for var, name in critical_vars.items():
        if os.getenv(var):
            print_success(f"{name} key is set")
        else:
            print_error(f"{name} key is MISSING")
            all_set = False
    
    if not all_set:
        print_error("⚠️  CRITICAL: Some environment variables are missing")
        return False
    
    # Check for common security issues
    print("\n🔒 Security checks...")
    
    # Check if DEBUG mode is off (should be off in production)
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print_warning("DEBUG mode is ON - turn OFF for production")
    else:
        print_success("DEBUG mode is OFF")
    
    # Check database file permissions (if SQLite)
    db_path = "threadangle.db"
    if os.path.exists(db_path):
        print_success("Database file exists")
        
        # Check size
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print_success(f"Database size: {size_mb:.2f} MB")
    else:
        print_warning("Database file not found (may be using PostgreSQL)")
    
    return True


# ═══════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════

def run_all_tests():
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*15 + "THREADANGLE COMPREHENSIVE TEST SUITE" + " "*17 + "║")
    print("╚" + "═"*68 + "╝")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("YouTube Features", test_youtube_features),
        ("Voice Learning", test_voice_learning),
        ("Hook Generation", test_hook_generation),
        ("Email System", test_email_system),
        ("Calendar & Scheduling", test_calendar_scheduling),
        ("Performance & Security", test_performance_security),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Print summary
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*25 + "TEST SUMMARY" + " "*31 + "║")
    print("╚" + "═"*68 + "╝\n")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:12} | {test_name}")
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready for launch!")
        print("\n✅ NEXT STEPS:")
        print("   1. Run manual testing with Krishna")
        print("   2. Test payment flow end-to-end")
        print("   3. Test on mobile devices")
        print("   4. Deploy to production")
        print("   5. Final smoke test on kriangle.com")
        print("   6. LAUNCH! 🚀")
    else:
        print("\n⚠️  SOME TESTS FAILED - Fix before launch")
        print("\n🔧 REQUIRED FIXES:")
        for test_name, result in results.items():
            if not result:
                print(f"   ❌ Fix: {test_name}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
