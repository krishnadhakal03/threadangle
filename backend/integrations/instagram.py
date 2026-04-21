"""
Instagram (via Facebook Graph API) integration.

Uses Facebook Login for Business (www.facebook.com/dialog/oauth) to access
Instagram Business / Creator accounts connected to the user's Facebook Pages.

REQUIRED permissions in Meta Developer Portal → your app → Products:
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Add product: "Facebook Login for Business"  (NOT "Facebook Login")     │
  │                                                                          │
  │  Then under that product → Permissions, request:                        │
  │    • instagram_basic         ← REQUIRED (reads IG profile via Pages)    │
  │    • pages_show_list         ← REQUIRED (list user's FB Pages)          │
  │    • instagram_content_publish ← for posting content to Instagram       │
  └──────────────────────────────────────────────────────────────────────────┘

DO NOT add:
  ✗ instagram_business_basic  (that is for the SEPARATE "Instagram Login" API
                                 at api.instagram.com — wrong API entirely)
  ✗ instagram_basic Display API (the old deprecated Basic Display API)

OAuth flow (all endpoints on graph.facebook.com):
  1. Redirect user → www.facebook.com/v21.0/dialog/oauth?scope=instagram_basic,...
  2. User grants access, Facebook redirects back with ?code=...&state=...
  3. Exchange code → short-lived user token (GET /v21.0/oauth/access_token)
  4. Exchange short-lived → long-lived 60-day token (grant_type=fb_exchange_token)
  5. GET /v21.0/me/accounts → list of Facebook Pages
  6. GET /v21.0/{page_id}?fields=instagram_business_account → find connected IG account
  7. GET /v21.0/{ig_id}?fields=username,profile_picture_url → fetch profile

Ref: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/get-started
"""

import requests
import os
from typing import Dict
from urllib.parse import urlencode

FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
FACEBOOK_REDIRECT_URI = os.getenv('FACEBOOK_REDIRECT_URI', 'http://localhost:5173/auth/facebook/callback')

# API version — update as Meta releases new stable versions
_API_VER = "v21.0"


def get_instagram_oauth_url(state: str) -> str:
    """
    Return the Facebook Login for Business authorization URL.

    Scope per Meta docs (Step 2):
      https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/get-started
    """
    params = {
        'client_id': FACEBOOK_APP_ID,
        'redirect_uri': FACEBOOK_REDIRECT_URI,
        'state': state,
        # instagram_basic          → reads IG profile linked to the Page
        # pages_show_list           → lists the user's Facebook Pages
        # pages_read_engagement     → read page metadata
        # pages_manage_posts        → post on behalf of pages
        # instagram_content_publish → publish posts/reels to Instagram
        'scope': 'instagram_basic,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_content_publish',
        'response_type': 'code',
    }
    return f"https://www.facebook.com/{_API_VER}/dialog/oauth?{urlencode(params)}"


def exchange_instagram_code_for_token(code: str) -> Dict:
    """
    Exchange the authorization code for a long-lived Facebook/Instagram access token.

        Returns dict with:
            - access_token: long-lived user token (valid ~60 days)
            - short_access_token: short-lived user token from initial code exchange
            - expires_in: seconds until expiry
    """
    # Step 1: short-lived token
    r = requests.get(
        f"https://graph.facebook.com/{_API_VER}/oauth/access_token",
        params={
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'redirect_uri': FACEBOOK_REDIRECT_URI,
            'code': code,
        },
    )
    print(f"[IG] Short-lived token status: {r.status_code} body: {r.text[:300]}")
    if r.status_code != 200:
        err = r.json().get('error', {})
        if 'redirect_uri' in err.get('message', '').lower():
            raise Exception(
                f"Redirect URI mismatch: the URI '{FACEBOOK_REDIRECT_URI}' must be listed exactly "
                "in Meta App Dashboard → Facebook Login for Business → Settings → Valid OAuth Redirect URIs."
            )
        raise Exception(f"Facebook token exchange failed (code {err.get('code')}): {err.get('message', r.text)}")

    short_token = r.json()['access_token']

    # Step 2: exchange for long-lived token (valid ~60 days)
    r2 = requests.get(
        f"https://graph.facebook.com/{_API_VER}/oauth/access_token",
        params={
            'grant_type': 'fb_exchange_token',
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'fb_exchange_token': short_token,
        },
    )
    print(f"[IG] Long-lived token status: {r2.status_code} body: {r2.text[:300]}")
    if r2.status_code != 200:
        raise Exception(f"Long-lived token exchange failed: {r2.text}")

    data = r2.json()
    return {
        'access_token': data['access_token'],
        'short_access_token': short_token,
        'expires_in': data.get('expires_in', 5184000),
    }


def exchange_short_token_for_long_lived(short_token: str) -> Dict:
    """
    Exchange a short-lived Facebook user access token (e.g. from the JS SDK)
    for a long-lived token (valid ~60 days).

    This is step 2 only — used when the frontend already has the short-lived
    token from FB.login() and we just need to promote it to long-lived.
    """
    r = requests.get(
        f"https://graph.facebook.com/{_API_VER}/oauth/access_token",
        params={
            'grant_type': 'fb_exchange_token',
            'client_id': FACEBOOK_APP_ID,
            'client_secret': FACEBOOK_APP_SECRET,
            'fb_exchange_token': short_token,
        },
    )
    print(f"[IG] exchange_short→long status: {r.status_code} body: {r.text[:300]}")
    if r.status_code != 200:
        err = r.json().get('error', {})
        raise Exception(
            f"Long-lived token exchange failed ({err.get('code')}): {err.get('message', r.text)}"
        )
    data = r.json()
    return {
        'access_token': data['access_token'],
        'expires_in': data.get('expires_in', 5184000),
    }


def get_instagram_connection_data(user_access_token: str) -> Dict:
    """
    Resolve a Facebook user access token to the linked Instagram Business account
    by iterating every Facebook Page the user manages.

    Returns dict with:
      - page_access_token: page-scoped token (use this for all IG API calls)
      - page_id: Facebook Page ID
      - ig_account_id: Instagram Business Account ID
      - username: Instagram username
      - profile_pic: profile picture URL or None
    """
    # Step 1: list all Facebook Pages the user manages
    r = requests.get(
        f"https://graph.facebook.com/{_API_VER}/me/accounts",
        params={'access_token': user_access_token, 'fields': 'id,name,access_token'},
    )
    print(f"[IG] me/accounts status: {r.status_code} body: {r.text[:500]}")
    if r.status_code != 200:
        err = r.json().get('error', {})
        raise Exception(f"Failed to list Facebook Pages (code {err.get('code')}): {err.get('message', r.text)}")

    pages = r.json().get('data', [])
    print(f"[IG] Found {len(pages)} page(s): {[p.get('name') for p in pages]}")

    if not pages:
        # --- FALLBACK 1: try /me?fields=instagram_business_account directly ---
        # With Facebook Login for Business, the IG account is sometimes accessible
        # directly on the user node without needing to go through a page.
        print("[IG] /me/accounts empty — trying /me?fields=instagram_business_account fallback...")
        me_r = requests.get(
            f"https://graph.facebook.com/{_API_VER}/me",
            params={'access_token': user_access_token, 'fields': 'id,name,instagram_business_account'},
        )
        print(f"[IG] /me fallback status: {me_r.status_code} body: {me_r.text[:400]}")
        if me_r.status_code == 200:
            me_data = me_r.json()
            ig_account = me_data.get('instagram_business_account', {})
            ig_account_id = ig_account.get('id') if isinstance(ig_account, dict) else ig_account
            if ig_account_id:
                details = requests.get(
                    f"https://graph.facebook.com/{_API_VER}/{ig_account_id}",
                    params={'fields': 'username,profile_picture_url', 'access_token': user_access_token},
                )
                username = ig_account_id
                profile_pic = None
                if details.status_code == 200:
                    d = details.json()
                    username = d.get('username', ig_account_id)
                    profile_pic = d.get('profile_picture_url')
                print(f"[IG] Connected via /me fallback: @{username} (IG ID: {ig_account_id}) ✅")
                return {
                    'page_access_token': user_access_token,
                    'page_id': me_data.get('id'),
                    'ig_account_id': ig_account_id,
                    'username': username,
                    'profile_pic': profile_pic,
                }

        # --- Gather permissions for a diagnostic error message ---
        pr = requests.get(
            f"https://graph.facebook.com/{_API_VER}/me/permissions",
            params={'access_token': user_access_token},
        )
        granted = []
        if pr.status_code == 200:
            granted = [
                p['permission'] for p in pr.json().get('data', [])
                if p.get('status') == 'granted'
            ]
        print(f"[IG] Granted permissions: {granted}")

        has_pages_scope = 'pages_show_list' in granted
        has_ig_basic = 'instagram_basic' in granted

        if not has_pages_scope:
            raise Exception(
                "No Facebook Pages were shared — the 'pages_show_list' permission was not granted. "
                "In the Facebook login popup: (1) click 'Edit access' or 'Choose what you allow', "
                "(2) make sure the Pages toggle is ON, then (3) click Continue. "
                "Also verify 'pages_show_list' is listed under your Meta App's Facebook Login for Business permissions."
            )
        if not has_ig_basic:
            raise Exception(
                "The 'instagram_basic' permission was not granted. "
                "In Meta Developer Portal → your app → Products → Facebook Login for Business → Permissions, "
                "add 'instagram_basic'. Do NOT use 'instagram_business_basic' (that is a different API). "
                f"(Granted permissions: {granted})"
            )
        raise Exception(
            "No Facebook Pages were returned by the API despite permissions being granted. "
            "Make sure you manage at least one Facebook Page and selected it during the login flow. "
            f"(Granted permissions: {granted})"
        )

    # Step 2: find a page with a linked Instagram Business Account
    pages_without_ig = []
    for page in pages:
        page_id = page['id']
        page_name = page.get('name', page_id)
        page_token = page.get('access_token') or user_access_token

        ig_resp = requests.get(
            f"https://graph.facebook.com/{_API_VER}/{page_id}",
            params={'fields': 'instagram_business_account', 'access_token': page_token},
        )
        print(f"[IG] Page {page_id} ({page_name}) IG lookup: {ig_resp.status_code} {ig_resp.text[:300]}")

        ig_account_id = None
        if ig_resp.status_code == 200:
            ig_data = ig_resp.json()
            ig_account_id = ig_data.get('instagram_business_account', {}).get('id')

        if not ig_account_id:
            pages_without_ig.append(page_name)
            continue

        # Step 3: fetch the IG account username and profile picture
        details = requests.get(
            f"https://graph.facebook.com/{_API_VER}/{ig_account_id}",
            params={'fields': 'username,profile_picture_url', 'access_token': page_token},
        )
        username = 'Instagram'
        profile_pic = None
        if details.status_code == 200:
            d = details.json()
            username = d.get('username', 'Instagram')
            profile_pic = d.get('profile_picture_url')
        print(f"[IG] Connected: @{username} (IG ID: {ig_account_id})")
        return {
            'page_access_token': page_token,
            'page_id': page_id,
            'ig_account_id': ig_account_id,
            'username': username,
            'profile_pic': profile_pic,
        }

    # Ran out of pages — none had a connected Instagram Business account
    pages_str = ', '.join(f'"{p}"' for p in pages_without_ig) or "(none found)"
    raise Exception(
        f"No Instagram Business or Creator account found on your Facebook Page(s): {pages_str}. "
        "To fix this: "
        "(1) On Instagram → Settings → Account → Switch to Professional Account (Business or Creator). "
        "(2) In your Facebook Page → Settings → Linked Accounts → Instagram → Connect Account. "
        "Then reconnect here."
    )


# ── Backward-compat shims ──────────────────────────────────────────────────────

def get_instagram_account_id(access_token: str) -> str:
    try:
        return get_instagram_connection_data(access_token)['ig_account_id']
    except Exception:
        return None


def get_instagram_user_info(access_token: str) -> Dict:
    data = get_instagram_connection_data(access_token)
    return {
        'user_id': data['ig_account_id'],
        'username': data['username'],
        'profile_pic': data['profile_pic'],
    }


def post_to_instagram(access_token: str, caption: str, ig_account_id: str, image_url: str = None) -> Dict:
    """
    Post to Instagram via the Graph API (graph.facebook.com).

    NOTE: Instagram requires actual media. For caption-only MVP, we return the
    caption for manual posting.
    """
    if not image_url:
        return {
            'success': True,
            'note': 'Instagram caption ready - please post manually with your video',
            'caption': caption,
            'instructions': 'Copy this caption and post your Reel manually in the Instagram app',
        }

    try:
        r = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
            data={'image_url': image_url, 'caption': caption, 'access_token': access_token},
        )
        if r.status_code != 200:
            return {'success': False, 'error': f"Failed to create media container: {r.text}"}

        container_id = r.json()['id']

        r2 = requests.post(
            f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish",
            data={'creation_id': container_id, 'access_token': access_token},
        )
        if r2.status_code in [200, 201]:
            return {'success': True, 'media_id': r2.json()['id'], 'message': 'Posted to Instagram successfully'}
        return {'success': False, 'error': f"Failed to publish: {r2.text}"}

    except Exception as e:
        return {'success': False, 'error': str(e)}
