# Manual Testing Instructions for Threadangle

## 🚀 Start All Services

### Terminal 1: Backend Server
```bash
cd F:\Threadforge\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend Dev Server
```bash
cd F:\Threadforge\frontend
npm run dev
```

### Terminal 3: Stripe Webhook Listener (Optional but recommended)
```bash
stripe listen --forward-to http://localhost:8000/api/payments/webhook
```

### Open Application
Navigate to: **http://localhost:5173**

---

## 📋 COMPREHENSIVE TESTING CHECKLIST

### 1. AUTHENTICATION & ONBOARDING (5 minutes)
- [ ] Sign up with new test account
- [ ] Verify welcome email received
- [ ] Check free tier shows: "0/5 generations"
- [ ] Verify Google OAuth login works
- [ ] Test logout functionality
- [ ] Test login with email/password

### 2. CONTENT GENERATION - TEXT INPUT (10 minutes)
- [ ] Click "Raw Text" tab
- [ ] Paste sample text (150 words)
- [ ] Select all 3 platforms: Twitter, LinkedIn, TikTok
- [ ] Click "Generate Content"
- [ ] Verify loading state appears with spinner
- [ ] Check all 3 platforms generated successfully
- [ ] Verify counter increments: "1/5"
- [ ] Check content quality (8/10+ rating)
- [ ] Test character counts are accurate
- [ ] Verify Twitter thread has proper numbering (1/, 2/, 3/)

### 3. CONTENT GENERATION - YOUTUBE URL (10 minutes)
- [ ] Click "Blog / Article URL" tab
- [ ] Paste: `https://www.youtube.com/watch?v=LCmiKLMk2SI`
- [ ] Verify YouTube metadata shows (title, channel, thumbnail)
- [ ] Click "Generate Content"
- [ ] Check all 5 platforms generated:
  - **Twitter thread** (numbered 1/, 2/, 3/)
  - **LinkedIn post** (professional tone)
  - **TikTok script** (emoji sections: 🎬 HOOK, 📚 CONTENT, 🔥 CTA)
  - **Instagram Reels** (title, description, hashtags)
  - **YouTube Shorts** (title, description, tags)
- [ ] Verify counter increments: "2/5"
- [ ] Check transcript was properly extracted
- [ ] Test with different YouTube URL formats (youtu.be shortlinks)

### 4. VOICE LEARNING (15 minutes)
- [ ] Generate 3rd piece of content (use raw text)
- [ ] Check sidebar: Should show "Learning your voice... 3/3"
- [ ] Check email inbox: "Voice Learned" notification received
- [ ] Generate 4th piece of content
- [ ] Verify backend logs show: "🎤 Using learned voice profile"
- [ ] Compare 4th output to 1st-3rd (should feel more consistent)
- [ ] Check sidebar: "🎤 VOICE LEARNED" badge appears
- [ ] Verify voice profile stored in database

### 5. IN-APP CONTENT EDITOR (15 minutes)
- [ ] Click on generated Twitter content
- [ ] Verify content is editable (click and type)
- [ ] Make an edit (change one sentence)
- [ ] Wait 1 second for autosave
- [ ] Check for "Saving..." indicator appears briefly
- [ ] Refresh page
- [ ] Verify edit persisted after refresh
- [ ] Test character counter updates live as you type
- [ ] Click "Copy" button
- [ ] Paste somewhere (verify edited version copied)
- [ ] Test "Reset" button (restores original AI content)
- [ ] Test editing on all platforms (Twitter, LinkedIn, TikTok)

### 6. HOOK VARIATIONS (10 minutes)
- [ ] Expand "🔥 Try These Alternative Hooks" section
- [ ] Verify 5 hooks shown with labels:
  - 🔍 **Curiosity** (questions, intrigue)
  - ⚡ **Controversial** (bold statements)
  - 📊 **Statistics** (data-driven)
  - 📖 **Story** (narrative)
  - 🎯 **Promise** (benefit-focused)
- [ ] Click "Use This" on one hook
- [ ] Verify content updates with new hook seamlessly
- [ ] Check toast notification: "🔥 Hook updated!"
- [ ] Copy content and verify new hook is included
- [ ] Test on different content types (Twitter vs LinkedIn)

### 7. REELS & SHORTS METADATA (10 minutes)
- [ ] Generate content from YouTube video
- [ ] Click "Instagram Reels" tab
- [ ] Verify displays:
  - **Title** (catchy, under 100 chars)
  - **Description** (paragraph with context)
  - **Hashtags** (20-30 relevant hashtags)
- [ ] Count hashtags (should be 20-30)
- [ ] Click "Copy All Reels Metadata"
- [ ] Paste and verify format is correct
- [ ] Click "YouTube Shorts" tab
- [ ] Verify displays:
  - **Title** (under 60 characters)
  - **Description** (optimized for YouTube)
  - **Tags** (comma-separated, no # symbol)
- [ ] Check tags are comma-separated (no hashtag symbols)
- [ ] Click "Copy All Shorts Metadata"
- [ ] Verify copied format is ready to paste into YouTube Studio

### 8. PAYMENT FLOW (20 minutes)
- [ ] Click "Upgrade to Solo" button in sidebar
- [ ] Verify Stripe checkout modal opens (embedded, not redirect)
- [ ] Check pricing displays correctly ($5/month)
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Expiry: Any future date (e.g., 12/28)
- [ ] CVC: Any 3 digits (e.g., 123)
- [ ] Complete payment
- [ ] Check modal closes automatically
- [ ] Verify "Activating subscription..." toast appears
- [ ] Wait 2-6 seconds for webhook processing
- [ ] Check "Subscription Activated!" success toast
- [ ] Verify sidebar updates: "⚡ SOLO" badge appears
- [ ] Check counter updates: "0/30 generated this month"
- [ ] Verify email: "Subscription Confirmation" received
- [ ] Generate content (should work with new 30 generation limit)
- [ ] Test webhook handling (check Terminal 3 for webhook events)

### 9. CONTENT CALENDAR (15 minutes)
- [ ] Click "Calendar" tab in sidebar/navigation
- [ ] Verify current week displays (Mon-Sun with dates)
- [ ] Check today is highlighted
- [ ] Click "History" tab
- [ ] Click "📅 Schedule" button on a generation
- [ ] Select tomorrow's date from date picker
- [ ] Select time: 10:00 AM
- [ ] Select platforms: Twitter and LinkedIn
- [ ] Click "Schedule"
- [ ] Verify success toast appears
- [ ] Go back to Calendar tab
- [ ] Verify scheduled item appears on tomorrow's date
- [ ] Click on scheduled item to expand details
- [ ] Verify shows: time, platforms, content preview
- [ ] Click "Mark Posted" button
- [ ] Verify checkmark appears next to item
- [ ] Test week navigation (prev/next week buttons)
- [ ] Verify calendar updates correctly

### 10. HISTORY & FILTERS (10 minutes)
- [ ] Click "History" tab
- [ ] Verify all generations shown in reverse chronological order
- [ ] Count total (should match your generation count in sidebar)
- [ ] Test "Show failed" / "Hide failed" toggle if any failed generations
- [ ] Check if filter works properly
- [ ] Click on a past generation to expand
- [ ] Verify all content platforms visible
- [ ] Test scrolling (if 10+ generations)
- [ ] Check generation metadata (date, status, platforms)
- [ ] Test search/filter functionality if implemented

### 11. MOBILE RESPONSIVE TESTING (15 minutes)

**Option 1: Use Browser DevTools**
- [ ] Open Chrome DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Test on iPhone 12 Pro (390x844)
- [ ] Test on Samsung Galaxy S21 (360x800)
- [ ] Test on iPad (768x1024)

**Option 2: Use ngrok for Real Device Testing**
```bash
# In new terminal
ngrok http 5173
```
- [ ] Open ngrok URL on your phone
- [ ] Test all functionality on mobile

**Mobile Test Checklist:**
- [ ] Test login screen layout
- [ ] Test navigation menu (hamburger if collapsed)
- [ ] Test content generation form
- [ ] Test tab switching (Raw Text vs URL)
- [ ] Test calendar view on mobile
- [ ] Check if all buttons are tappable (not too small)
- [ ] Verify text is readable (not too small)
- [ ] Test copy buttons work
- [ ] Check content editor is usable on mobile
- [ ] Test landscape orientation
- [ ] Screenshot any UI issues

### 12. EDGE CASES & ERROR HANDLING (15 minutes)
- [ ] Try invalid YouTube URL (e.g., "https://youtube.com/invalid")
- [ ] Verify error message shows clearly
- [ ] Check credit is NOT deducted for failed generation
- [ ] Try URL that doesn't exist (404)
- [ ] Generate with empty text input
- [ ] Verify validation error appears
- [ ] Try extremely short text (under 50 words)
- [ ] Try extremely long text (over 5000 words)
- [ ] Hit generation limit (if on free tier)
- [ ] Verify paywall appears when limit reached
- [ ] Try to access paid features without upgrading
- [ ] Test logout and login again (state persistence)
- [ ] Test with slow internet (throttle in DevTools)
- [ ] Check browser console for any errors (should be clean)

### 13. EMAIL REMINDERS (Manual Trigger Test)
- [ ] Schedule a post for today
- [ ] Open terminal in backend directory
- [ ] Run: `python run_daily_reminders.py`
- [ ] Check email inbox
- [ ] Verify reminder email received within 1-2 minutes
- [ ] Check email shows scheduled posts correctly
- [ ] Verify "View Calendar" link in email works
- [ ] Test email renders properly in Gmail/Outlook

### 14. SETTINGS & PROFILE (5 minutes)
- [ ] Click "Settings" in sidebar
- [ ] Verify displays:
  - Account email
  - Subscription status
  - Generation count/limit
- [ ] Test any profile editing functionality
- [ ] Check subscription management (cancel option if subscribed)
- [ ] Verify timezone settings if implemented

### 15. BROWSER COMPATIBILITY (10 minutes)
- [ ] Test in Chrome (primary)
- [ ] Test in Firefox
- [ ] Test in Edge
- [ ] Test in Safari (if on Mac)
- [ ] Verify consistent behavior across browsers
- [ ] Check for any browser-specific console errors

---

## 🐛 BUG REPORTING CHECKLIST

When you find a bug, document:

1. **What you did** (steps to reproduce)
2. **What you expected** (expected behavior)
3. **What actually happened** (actual behavior)
4. **Browser and OS** (e.g., Chrome 120 on Windows 11)
5. **Screenshots** (if UI issue)
6. **Console errors** (F12 → Console tab)
7. **Network errors** (F12 → Network tab)

---

## ✅ SUCCESS CRITERIA

All tests should pass with:
- ✅ No JavaScript console errors
- ✅ No backend 500 errors in terminal
- ✅ All features working as described
- ✅ Fast performance (generations under 30 seconds)
- ✅ Smooth UI animations and transitions
- ✅ Responsive design on all screen sizes
- ✅ Payment flow working perfectly
- ✅ Emails sending successfully

---

## 🚨 CRITICAL ISSUES (Fix Immediately)

Priority 1 (Launch Blockers):
- Payment flow broken
- Content generation failing
- Database errors
- Authentication broken
- Email notifications not sending

Priority 2 (Fix Before Launch):
- Mobile UI issues
- Console errors
- Slow performance
- Calendar bugs
- Editor autosave issues

Priority 3 (Fix After Launch):
- Minor UI tweaks
- Nice-to-have features
- Performance optimizations
- Additional error messages

---

## 📊 EXPECTED RESULTS

After completing all tests:

**Passed:** 95-100% of test cases

**Ready for Production:** Yes ✅

**Launch Confidence:** High 🚀

---

## 🎯 NEXT STEPS AFTER TESTING

1. ✅ Fix all critical bugs found
2. ✅ Re-test fixed issues
3. ✅ Configure production environment (.env.production)
4. ✅ Update Stripe webhook endpoint for production
5. ✅ Test on production domain (kriangle.com)
6. ✅ Deploy to production server
7. ✅ Run smoke tests on live site
8. 🚀 **LAUNCH!**

---

## 💡 TIPS FOR EFFECTIVE TESTING

- **Take your time** - Don't rush through checklist
- **Test like a real user** - Don't skip steps
- **Document everything** - Screenshots help debugging
- **Test edge cases** - Break things intentionally
- **Ask questions** - "What if..." scenarios
- **Test on real devices** - Not just desktop
- **Check emails** - Verify all notifications work
- **Monitor logs** - Watch backend terminal for errors

---

**Good luck with testing, Krishna!** 🎉

**You're about to launch something amazing!** 🚀
