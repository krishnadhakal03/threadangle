"""
Social media OAuth authentication routes
Handles OAuth flows for Twitter, LinkedIn, and Instagram/Facebook
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, SocialAccount, OAuthState
from auth import get_current_user
from sqlalchemy import delete
from integrations.twitter import (
    get_twitter_oauth_url,
    exchange_twitter_code_for_token,
    get_twitter_user_info
)
from integrations.linkedin import (
    get_linkedin_oauth_url,
    exchange_linkedin_code_for_token,
    get_linkedin_user_info,
    post_to_linkedin,
)
from integrations.instagram import (
    get_instagram_oauth_url,
    exchange_instagram_code_for_token,
    exchange_short_token_for_long_lived,
    get_instagram_user_info,
    get_instagram_connection_data,
)
from utils.encryption import encrypt_token, decrypt_token
from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets
import os
import json
from urllib.parse import quote_plus

router = APIRouter()

@router.get("/api/auth/{platform}/connect")
async def connect_social_account(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate OAuth flow for connecting a social media account.
    State is persisted in the database so backend restarts don't invalidate
    in-flight OAuth flows.
    """
    if platform not in ('twitter', 'linkedin', 'instagram'):
        raise HTTPException(status_code=400, detail="Unsupported platform. Use 'twitter', 'linkedin', or 'instagram'")

    # Purge any expired states for this user+platform (housekeeping)
    await db.execute(
        delete(OAuthState).where(
            OAuthState.expires_at < datetime.utcnow()
        )
    )
    await db.commit()

    state = secrets.token_urlsafe(32)
    code_verifier = None

    try:
        if platform == 'twitter':
            auth_url, code_verifier = get_twitter_oauth_url(state)
        elif platform == 'linkedin':
            auth_url = get_linkedin_oauth_url(state)
        else:  # instagram
            auth_url = get_instagram_oauth_url(state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}")

    db.add(OAuthState(
        state=state,
        user_id=current_user.id,
        platform=platform,
        code_verifier=code_verifier,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    ))
    await db.commit()

    return {'auth_url': auth_url, 'state': state}

@router.get("/api/auth/{platform}/callback")
async def social_auth_callback(
    platform: str,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from social media platform (Twitter, LinkedIn).
    Instagram uses /facebook/exchange instead.
    """
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # Provider-level OAuth denial/error (e.g. from Twitter/X)
    if error:
        msg = f"{platform} oauth error: {error}"
        if error_description:
            msg += f" ({error_description})"
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error={quote_plus(msg)}")

    if not code or not state:
        msg = quote_plus(f"{platform} oauth error: missing code/state")
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error={msg}")

    # Look up state in DB
    result = await db.execute(
        select(OAuthState).where(OAuthState.state == state)
    )
    state_row = result.scalar_one_or_none()

    if not state_row:
        return RedirectResponse(url=f"{frontend_url}/dashboard?error=invalid_state")

    if datetime.utcnow() > state_row.expires_at:
        await db.delete(state_row)
        await db.commit()
        return RedirectResponse(url=f"{frontend_url}/dashboard?error=expired")

    user_id = state_row.user_id
    code_verifier = state_row.code_verifier

    # Consume the state (one-time use)
    await db.delete(state_row)
    await db.commit()

    try:
        if platform == 'twitter':
            token_data = exchange_twitter_code_for_token(code, code_verifier)
            user_info = get_twitter_user_info(token_data['access_token'])
        elif platform == 'linkedin':
            token_data = exchange_linkedin_code_for_token(code)
            user_info = get_linkedin_user_info(token_data['access_token'])
        elif platform == 'instagram':
            token_data = exchange_instagram_code_for_token(code)
            user_info = get_instagram_user_info(token_data['access_token'])
        else:
            return RedirectResponse(url=f"{frontend_url}/dashboard?error=unsupported_platform")

        encrypted_access = encrypt_token(token_data['access_token'])
        encrypted_refresh = encrypt_token(token_data.get('refresh_token')) if token_data.get('refresh_token') else None
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 7200))

        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == platform
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.access_token = encrypted_access
            existing.refresh_token = encrypted_refresh
            existing.token_expires_at = expires_at
            existing.platform_user_id = user_info['user_id']
            existing.platform_username = user_info['username']
            existing.platform_profile_pic = user_info.get('profile_pic')
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
        else:
            db.add(SocialAccount(
                user_id=user_id,
                platform=platform,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expires_at=expires_at,
                platform_user_id=user_info['user_id'],
                platform_username=user_info['username'],
                platform_profile_pic=user_info.get('profile_pic')
            ))

        await db.commit()
        return RedirectResponse(url=f"{frontend_url}/auth/callback?connected={platform}")

    except Exception as e:
        print(f"❌ OAuth callback error for {platform}: {e}")
        err_msg = quote_plus(f"{platform} oauth error: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/auth/callback?error={err_msg}")


@router.post("/api/auth/facebook/exchange")
async def facebook_exchange(
    payload: Dict = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Facebook OAuth code exchange initiated by the frontend callback page.

    The frontend receives the OAuth code at http://localhost:5173/auth/facebook/callback
    and POSTs it here to complete the token exchange and account storage.
    State verification maps back to the authenticated user who initiated the flow.
    """
    code = payload.get('code')
    state = payload.get('state')

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Look up state in DB (survives backend restarts)
    state_result = await db.execute(
        select(OAuthState).where(OAuthState.state == state)
    )
    state_row = state_result.scalar_one_or_none()

    if not state_row:
        raise HTTPException(status_code=400, detail="Invalid or expired state. Please try connecting again.")

    if datetime.utcnow() > state_row.expires_at:
        await db.delete(state_row)
        await db.commit()
        raise HTTPException(status_code=400, detail="OAuth session expired. Please try connecting again.")

    user_id = state_row.user_id

    # Consume the state (one-time use)
    await db.delete(state_row)
    await db.commit()

    try:
        # Step 1: exchange the code for a long-lived Facebook user token
        token_data = exchange_instagram_code_for_token(code)
        short_token = token_data.get('short_access_token')
        long_token = token_data['access_token']

        # Step 2: resolve token → page token + IG account ID/username.
        # IMPORTANT: try short-lived token first because in some Meta app
        # configurations, fb_exchange_token can drop page-list visibility.
        ig_data = None
        if short_token:
            print("[IG] facebook/exchange trying short-lived token for /me/accounts first...")
            try:
                ig_data = get_instagram_connection_data(short_token)
                print("[IG] facebook/exchange short-lived lookup worked ✅")
            except Exception as short_err:
                print(f"[IG] facebook/exchange short-lived lookup failed: {short_err}")

        if ig_data is None:
            print("[IG] facebook/exchange trying long-lived token for /me/accounts...")
            ig_data = get_instagram_connection_data(long_token)

        # Store the PAGE access token (not the user token) — long-lived when
        # derived from a long-lived user token (Meta docs guarantee this).
        encrypted_access = encrypt_token(ig_data['page_access_token'])
        # Instagram long-lived tokens last 60 days; no refresh token issued.
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 5184000))

        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == 'instagram'
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.access_token = encrypted_access
            existing.refresh_token = None
            existing.token_expires_at = expires_at
            existing.platform_user_id = ig_data['ig_account_id']
            existing.platform_username = ig_data['username']
            existing.platform_profile_pic = ig_data.get('profile_pic')
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
        else:
            db.add(SocialAccount(
                user_id=user_id,
                platform='instagram',
                access_token=encrypted_access,
                refresh_token=None,
                token_expires_at=expires_at,
                platform_user_id=ig_data['ig_account_id'],
                platform_username=ig_data['username'],
                platform_profile_pic=ig_data.get('profile_pic'),
            ))

        await db.commit()
        print(f"✅ Instagram connected: @{ig_data['username']} (IG ID: {ig_data['ig_account_id']})")
        return {'success': True, 'username': ig_data['username']}

    except HTTPException:
        raise  # pass through validation errors as-is
    except Exception as e:
        print(f"❌ Facebook exchange error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/auth/instagram/connect-token")
async def instagram_connect_token(
    payload: Dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Accept a short-lived Facebook user access token obtained via the Facebook
    JavaScript SDK (FB.login in the browser), exchange it for a long-lived token,
    then resolve the linked Instagram Business account and save it to the DB.

    This is the simpler alternative to the popup → redirect → FacebookCallback flow.
    The JS SDK handles the OAuth dialog internally and delivers the token directly.
    """
    short_token = payload.get('access_token')
    if not short_token:
        raise HTTPException(status_code=400, detail="Missing access_token")

    try:
        # IMPORTANT: Try the short-lived token FIRST for /me/accounts.
        # The FB_exchange_token conversion is known to strip page-level scope
        # in the Facebook Login for Business flow, causing /me/accounts to return [].
        ig_data = None
        token_data = None

        print("[IG] Trying short-lived token for /me/accounts first...")
        try:
            ig_data = get_instagram_connection_data(short_token)
            print("[IG] Short-lived token worked for page lookup ✅")
        except Exception as short_err:
            print(f"[IG] Short-lived token approach failed: {short_err}")
            ig_data = None

        # Always exchange to long-lived for storage (60-day token)
        token_data = exchange_short_token_for_long_lived(short_token)
        long_token = token_data['access_token']

        if ig_data is None:
            # Short-lived token didn't find pages — try long-lived token
            print("[IG] Trying long-lived token for /me/accounts...")
            ig_data = get_instagram_connection_data(long_token)

        # Store the page access token (required for IG content publish API)
        encrypted_access = encrypt_token(ig_data['page_access_token'])
        expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 5184000))

        result = await db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == current_user.id,
                SocialAccount.platform == 'instagram'
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.access_token = encrypted_access
            existing.refresh_token = None
            existing.token_expires_at = expires_at
            existing.platform_user_id = ig_data['ig_account_id']
            existing.platform_username = ig_data['username']
            existing.platform_profile_pic = ig_data.get('profile_pic')
            existing.is_active = True
            existing.connected_at = datetime.utcnow()
        else:
            db.add(SocialAccount(
                user_id=current_user.id,
                platform='instagram',
                access_token=encrypted_access,
                refresh_token=None,
                token_expires_at=expires_at,
                platform_user_id=ig_data['ig_account_id'],
                platform_username=ig_data['username'],
                platform_profile_pic=ig_data.get('profile_pic'),
            ))

        await db.commit()
        print(f"✅ Instagram connected via JS SDK: @{ig_data['username']} (IG ID: {ig_data['ig_account_id']})")
        return {'success': True, 'username': ig_data['username']}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Instagram connect-token error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/auth/instagram/debug-pages")
async def debug_instagram_pages(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint: call me/accounts with provided user token and return raw result.
    Only available in local/dev. Remove before production.
    """
    import requests as req

    def _safe_json(resp):
        try:
            return resp.json()
        except Exception:
            return {'raw_text': resp.text[:1000]}

    def _token_report(label: str, access_token: str):
        me_resp = req.get(
            "https://graph.facebook.com/v21.0/me",
            params={'access_token': access_token, 'fields': 'id,name'},
        )
        pages_resp = req.get(
            "https://graph.facebook.com/v21.0/me/accounts",
            params={'access_token': access_token, 'fields': 'id,name,access_token'},
        )
        perms_resp = req.get(
            "https://graph.facebook.com/v21.0/me/permissions",
            params={'access_token': access_token},
        )

        pages = _safe_json(pages_resp).get('data', []) if pages_resp.status_code == 200 else []
        ig_results = []
        for page in pages:
            page_token = page.get('access_token') or access_token
            ig_resp = req.get(
                f"https://graph.facebook.com/v21.0/{page['id']}",
                params={'fields': 'instagram_business_account', 'access_token': page_token},
            )
            ig_results.append({
                'page_id': page['id'],
                'page_name': page.get('name'),
                'ig_status': ig_resp.status_code,
                'ig_response': _safe_json(ig_resp),
            })

        perms_json = _safe_json(perms_resp)
        granted_permissions = [
            p.get('permission')
            for p in perms_json.get('data', [])
            if p.get('status') == 'granted'
        ]

        return {
            'label': label,
            'me_status': me_resp.status_code,
            'me': _safe_json(me_resp),
            'permissions_status': perms_resp.status_code,
            'permissions': perms_json,
            'pages_status': pages_resp.status_code,
            'pages_raw': _safe_json(pages_resp),
            'page_names': [p.get('name') for p in pages],
            'ig_per_page': ig_results,
            'summary': {
                'page_count': len(pages),
                'pages_with_ig': sum(1 for r in ig_results if r.get('ig_response', {}).get('instagram_business_account')),
                'granted_permissions': granted_permissions,
            },
        }

    short_report = _token_report('short_lived', token)

    # Compare with long-lived token behavior as Meta sometimes changes page visibility
    long_report = None
    exchange_error = None
    try:
        ll = exchange_short_token_for_long_lived(token)
        long_report = _token_report('long_lived', ll['access_token'])
    except Exception as e:
        exchange_error = str(e)

    # Optional token introspection (app-scoped)
    token_debug = None
    app_id = os.getenv('FACEBOOK_APP_ID')
    app_secret = os.getenv('FACEBOOK_APP_SECRET')
    if app_id and app_secret:
        try:
            dbg = req.get(
                "https://graph.facebook.com/debug_token",
                params={
                    'input_token': token,
                    'access_token': f"{app_id}|{app_secret}",
                },
            )
            token_debug = _safe_json(dbg)
        except Exception as e:
            token_debug = {'error': str(e)}

    short_pages = short_report['summary']['page_count']
    long_pages = long_report['summary']['page_count'] if long_report else None
    if short_pages == 0 and (long_pages == 0 or long_pages is None):
        hint = (
            "Token has permissions but returns zero pages. Most likely wrong Facebook login profile, "
            "or no Full Control on target Page, or page was not selected in consent dialog."
        )
    elif short_pages > 0 and long_pages == 0:
        hint = (
            "Short-lived token sees pages but long-lived does not. This is a Meta token-exchange behavior; "
            "keep using short token for discovery then store page token."
        )
    elif short_pages > 0:
        hint = "Pages are visible. If connect still fails, issue is likely missing linked Instagram professional account on that page."
    else:
        hint = "Review raw responses below for exact API denial reason."

    return {
        'short_token_report': short_report,
        'long_token_report': long_report,
        'long_token_exchange_error': exchange_error,
        'token_debug': token_debug,
        'summary': {
            'short_page_count': short_pages,
            'long_page_count': long_pages,
            'short_pages_with_ig': short_report['summary']['pages_with_ig'],
            'long_pages_with_ig': (long_report['summary']['pages_with_ig'] if long_report else None),
            'short_me': short_report.get('me'),
            'long_me': (long_report.get('me') if long_report else None),
            'granted_permissions': short_report['summary']['granted_permissions'],
            'hint': hint,
        },
    }


@router.get("/api/auth/social-accounts")
async def get_connected_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's connected social media accounts
    
    Returns:
        Dictionary with list of connected accounts
    """
    
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True
        )
    )
    accounts = result.scalars().all()
    
    return {
        'accounts': [
            {
                'platform': acc.platform,
                'username': acc.platform_username,
                'profile_pic': acc.platform_profile_pic,
                'connected_at': acc.connected_at.isoformat() if acc.connected_at else None,
                'expires_at': acc.token_expires_at.isoformat() if acc.token_expires_at else None
            }
            for acc in accounts
        ]
    }


@router.post("/api/auth/linkedin/test-post")
async def test_linkedin_post(
    payload: Dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a test post directly to LinkedIn using the currently connected account.
    Intended for quick smoke testing from local/dev UI.
    """
    text = (payload.get('text') or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail="Post text is required")

    if len(text) > 3000:
        raise HTTPException(status_code=400, detail="LinkedIn post text cannot exceed 3000 characters")

    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == 'linkedin',
            SocialAccount.is_active == True
        )
    )
    linkedin_account = result.scalar_one_or_none()

    if not linkedin_account:
        raise HTTPException(status_code=404, detail="LinkedIn account not connected")

    access_token = decrypt_token(linkedin_account.access_token)
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to decrypt LinkedIn access token")

    post_result = post_to_linkedin(access_token, text, linkedin_account.platform_user_id)
    if not post_result.get('success'):
        raise HTTPException(status_code=400, detail=post_result.get('error') or 'LinkedIn post failed')

    linkedin_account.last_used_at = datetime.utcnow()
    await db.commit()

    return {
        'success': True,
        'post_id': post_result.get('post_id'),
        'message': post_result.get('message') or 'LinkedIn post published successfully'
    }

@router.delete("/api/auth/{platform}/disconnect")
async def disconnect_social_account(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disconnect a social media account
    
    Args:
        platform: 'twitter', 'linkedin', or 'instagram'
        
    Returns:
        Success confirmation
    """
    
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == platform
        )
    )
    account = result.scalar_one_or_none()
    
    if account:
        await db.delete(account)
        await db.commit()
        return {'success': True, 'message': f'{platform.capitalize()} account disconnected'}
    
    return {'success': False, 'message': 'Account not found'}

@router.post("/api/auth/refresh-token/{platform}")
async def refresh_platform_token(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually refresh an expired token (usually automatic)
    
    Args:
        platform: 'twitter', 'linkedin', or 'instagram'
    """
    
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == platform
        )
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not connected")
    
    if not account.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")
    
    # Implement token refresh logic here if needed
    raise HTTPException(status_code=501, detail="Token refresh not yet implemented")
