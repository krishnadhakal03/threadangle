# Auto-Posting Frontend Testing Guide

## Prerequisites (MUST SETUP BEFORE TESTING)

### 1. OAuth Credentials Setup
You need active OAuth apps for each platform. Verify these are configured:

#### Twitter/X OAuth 2.0
- [ ] Created app at https://developer.twitter.com/en/portal/dashboard
- [ ] OAuth 2.0 enabled in app settings
- [ ] Callback URI set to: `http://localhost:8000/api/auth/twitter/callback`
- [ ] Client ID and Secret in backend `.env` file as `TWITTER_CLIENT_ID` and `TWITTER_CLIENT_SECRET`
- [ ] Has "Read", "Write", and "Direct Message" permissions

#### LinkedIn OAuth
- [ ] Created app at https://www.linkedin.com/developers/apps
- [ ] OAuth 2.0 redirect URL set to: `http://localhost:8000/api/auth/linkedin/callback`
- [ ] Client ID and Secret in backend `.env` file as `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`
- [ ] Requested `w_member_social` and `r_basicprofile` scopes

#### Instagram/Facebook OAuth
- [ ] Created app at https://developers.facebook.com/
- [ ] Added Instagram Graph API product
- [ ] Callback URL set to: `http://localhost:8000/api/auth/instagram/callback`
- [ ] App ID and Secret in backend `.env` file as `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET`

### 2. Backend Services Running
```bash
# Terminal 1: Start Backend
cd backend
python start_backend.py

# Terminal 2: Start Frontend Dev Server
cd frontend
npm run dev

# Terminal 3: Start Auto-Posting Worker (optional, for testing auto-posting)
cd backend
python run_auto_poster.py
```

---

## Test Plan

### Phase 1: Connected Accounts Display

**Test 1.1: Initial State (No Connections)**
- [ ] Navigate to Settings page
- [ ] See "Connected Accounts" section
- [ ] All three platforms show "Connect" button
- [ ] All platforms show their correct icons (𝕏, 💼, 📸)
- [ ] Description text shows for each platform
- [ ] Info box shows "⚡ Auto-Posting Ready"

**Test 1.2: Account Loading**
- [ ] Wait for page to load completely
- [ ] "Connected Accounts" section loads without errors
- [ ] No "Failed to load" error message appears
- [ ] Loading animation appears briefly (if components are slow)

### Phase 2: OAuth Connection Flow

**Test 2.1: Twitter Connection**
- [ ] Click "Connect" button on Twitter/X
- [ ] OAuth popup window opens (width 600x700)
- [ ] Popup is centered on screen
- [ ] Twitter OAuth login page appears in popup
- [ ] Complete OAuth flow (login/authorize)
- [ ] Popup closes automatically when OAuth completes
- [ ] Background page doesn't reload or navigate
- [ ] Twitter status changes to "Connected as @[username]"
- [ ] "Disconnect" button appears instead of "Connect"
- [ ] Username from Twitter account displays correctly
- [ ] Green checkmark shows "Connected" status

**Test 2.2: LinkedIn Connection**
- [ ] Click "Connect" button on LinkedIn
- [ ] OAuth popup opens (follow same process as Twitter)
- [ ] Complete LinkedIn OAuth flow
- [ ] LinkedIn shows connected status
- [ ] Username displays correctly

**Test 2.3: Instagram Connection**
- [ ] Click "Connect" button on Instagram
- [ ] OAuth popup opens
- [ ] Complete Instagram OAuth flow
- [ ] Instagram shows connected status

### Phase 3: Disconnect Flow

**Test 3.1: Disconnect Account**
- [ ] Click "Disconnect" button on Twitter
- [ ] Confirmation dialog appears: "Are you sure you want to disconnect Twitter? You'll need to reconnect to enable auto-posting."
- [ ] Click "Cancel" → Dialog closes, account remains connected
- [ ] Click "Disconnect" again, click "OK" → Account disconnects
- [ ] Twitter status changes back to "Connect" button
- [ ] Username text disappears
- [ ] Green checkmark disappears

### Phase 4: Schedule Modal with Auto-Posting

**Test 4.1: Open Schedule Modal**
- [ ] Go to History tab
- [ ] Click "Schedule" button on any generation
- [ ] Schedule modal opens
- [ ] Date field shows today's date
- [ ] Time field shows "09:00"
- [ ] Auto-Posting toggle shows OFF (gray)
- [ ] No platform checkboxes visible yet
- [ ] "Schedule" button ready to click

**Test 4.2: Auto-Post Toggle OFF (Manual Scheduling)**
- [ ] Keep auto-post toggle OFF
- [ ] Set date to tomorrow
- [ ] Set time to 14:00
- [ ] Click "Schedule" button
- [ ] Success toast: "✅ Post scheduled successfully!"
- [ ] Modal closes
- [ ] Check Calendar → New scheduled item appears on correct date/time
- [ ] Calendar shows correct platforms
- [ ] No "⚡ Auto-posting" badge on item

**Test 4.3: Auto-Post Toggle ON (With Connections)**
- [ ] Have at least one account connected (e.g., Twitter)
- [ ] Click "Schedule" on another generation
- [ ] Toggle Auto-Posting ON
- [ ] Platform checkboxes appear
- [ ] Connected platforms are pre-selected (checkmark visible)
- [ ] Platform shows username: "(@username)"
- [ ] Can uncheck platforms if desired
- [ ] Toggle button animates (white circle moves right)

**Test 4.4: Auto-Post with No Connections**
- [ ] Disconnect all accounts
- [ ] Click "Schedule" on a generation
- [ ] Toggle Auto-Posting ON
- [ ] See yellow warning: "No accounts connected. Go to Settings to connect accounts for auto-posting."
- [ ] Platform list is empty
- [ ] "⚡ Schedule & Auto-Post" button is DISABLED
- [ ] Click "Schedule" without auto-post or with 0 platforms → Button doesn't work

**Test 4.5: Auto-Post with Selections**
- [ ] Toggle Auto-Posting ON (with 2+ accounts connected)
- [ ] Uncheck one platform
- [ ] Check that selection persists as you interact
- [ ] Only selected platform has checkmark
- [ ] Set date and time
- [ ] Click "⚡ Schedule & Auto-Post" button
- [ ] Success toast: "✅ Post scheduled with auto-posting!"
- [ ] Modal closes

### Phase 5: Calendar Auto-Post Indicators

**Test 5.1: Calendar Item Display**
- [ ] Go to Calendar tab
- [ ] Find scheduled item from Test 4.5
- [ ] See "⚡ Auto-posting" badge (blue, with lightning bolt)
- [ ] Shows correct time (14:00)
- [ ] Shows correct platforms (only the ones you selected)
- [ ] Content preview displays

**Test 5.2: Calendar Multiple Items**
- [ ] Schedule 2-3 items with auto-posting enabled
- [ ] Schedule 2-3 items without auto-posting
- [ ] Calendar view shows correct badges:
  - Items with auto-post: Show "⚡ Auto-posting" badge
  - Items without auto-post: No badge, just time and platforms

**Test 5.3: Posted Status**
- [ ] Mark an auto-posted item as "Posted"
- [ ] Calendar shows green checkmark and "Posted" status
- [ ] Badge still visible (if applicable)
- [ ] Can unschedule posted items

---

## Edge Cases & Error Handling

**Test 6.1: Browser Popup Blocking**
- [ ] If browser blocks popup, error message appears:
  - "Popup blocked - please allow popups for this site"
- [ ] Doesn't break the app, user can retry

**Test 6.2: OAuth Timeout**
- [ ] If OAuth completes but takes >5 seconds:
  - Page handles it gracefully
  - Connected accounts loaded when callback completes

**Test 6.3: Disconnect Cancellation**
- [ ] Start disconnect flow on Twitter
- [ ] Click "Cancel" in confirmation dialog
- [ ] Account remains connected
- [ ] UI shows "Connected" status

**Test 6.4: Auto-Post Without Selection**
- [ ] Toggle auto-post ON
- [ ] Uncheck all platforms
- [ ] Try to click "Schedule & Auto-Post" button
- [ ] Button appears disabled (opacity-50, cursor shows not-allowed)
- [ ] No API call made

---

## API Verification

**Test 7.1: Verify API Calls (Browser DevTools)**
- [ ] Open DevTools Network tab
- [ ] Go to Settings
- [ ] Check that `GET /api/auth/social-accounts` is called
- [ ] Response shows: `{"accounts": [...]}`

**Test 7.2: OAuth API Calls**
- [ ] Click "Connect" on Twitter
- [ ] See `GET /api/auth/twitter/connect` API call
- [ ] Response includes `{"auth_url": "https://twitter.com/i/oauth2/..."}`

**Test 7.3: Disconnect API Call**
- [ ] Click disconnect and confirm
- [ ] See `DELETE /api/auth/twitter/disconnect` API call
- [ ] Status code 200
- [ ] UI updates immediately

**Test 7.4: Schedule API Call**
- [ ] Schedule with auto-posting enabled
- [ ] See `PUT /generations/{id}/schedule` API call
- [ ] Request body includes:
  ```json
  {
    "scheduled_date": "2026-03-15",
    "scheduled_time": "14:00",
    "platforms": ["twitter", "linkedin"],
    "auto_post_enabled": true
  }
  ```

---

## Performance & UX Tests

**Test 8.1: Loading Performance**
- [ ] Settings page loads in <2 seconds
- [ ] Connected accounts fetch in <1 second
- [ ] Schedule modal opens instantly
- [ ] No lag when toggling auto-post

**Test 8.2: Mobile Responsiveness**
- [ ] Test on mobile (viewport <768px)
- [ ] Schedule modal is readable and usable
- [ ] Platform checkboxes are clickable
- [ ] Settings section is properly formatted

**Test 8.3: Dark Mode**
- [ ] All colors match dark theme
- [ ] Toggle and checkboxes are visible
- [ ] Text contrast is sufficient (WCAG AA)

---

## Sign-Off Checklist

- [ ] All Phase 1 tests pass (Account display)
- [ ] All Phase 2 tests pass (OAuth flow)
- [ ] All Phase 3 tests pass (Disconnect)
- [ ] All Phase 4 tests pass (Schedule modal)
- [ ] All Phase 5 tests pass (Calendar indicators)
- [ ] All Phase 6 tests pass (Error handling)
- [ ] All Phase 7 tests pass (API verification)
- [ ] All Phase 8 tests pass (Performance)
- [ ] No console errors in DevTools
- [ ] No network errors (all 200/201 responses)
- [ ] Backend auto-posting worker tested (optional)

## Final Notes

- If you encounter any issues, check backend logs for OAuth errors
- Verify .env variables are set correctly before testing
- If OAuth callback doesn't work, check firewall/ports
- Clear browser cache if seeing stale state
- Test in both Chrome and Firefox for compatibility

**Ready to ship! 🚀**
