"""
Twitter/X OAuth and posting integration
Handles OAuth 2.0 PKCE flow and tweet posting with thread support
"""

import os
import base64
import hashlib
import secrets
import requests
from urllib.parse import urlencode
from typing import Optional, Dict, Tuple

# Twitter API credentials from environment
TWITTER_CLIENT_ID = os.getenv('TWITTER_CLIENT_ID')
TWITTER_CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET')
TWITTER_REDIRECT_URI = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/api/auth/twitter/callback')
TWITTER_OAUTH_SCOPE = os.getenv(
    'TWITTER_OAUTH_SCOPE',
    'tweet.read tweet.write users.read offline.access'
)


def _format_twitter_error(prefix: str, response: requests.Response) -> str:
    try:
        payload = response.json()
    except Exception:
        return f"{prefix}: {response.text}"

    reason = payload.get('reason')
    title = payload.get('title')
    detail = payload.get('detail')

    if reason == 'client-not-enrolled' or title == 'Client Forbidden':
        return (
            "Twitter app is not enrolled for API v2 (client-not-enrolled). "
            "Fix in X Developer Portal: create/select a Project, attach this App to that Project, "
            "ensure appropriate API access level is enabled, then use that App's OAuth2 Client ID/Secret in backend .env."
        )

    return f"{prefix}: {payload}"

def get_twitter_oauth_url(state: str) -> Tuple[str, str]:
    """
    Generate Twitter OAuth 2.0 PKCE authorization URL.

    Returns:
        Tuple of (authorization_url, code_verifier).
        The code_verifier must be stored and used during token exchange.
    """
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    params = {
        'response_type': 'code',
        'client_id': TWITTER_CLIENT_ID,
        'redirect_uri': TWITTER_REDIRECT_URI,
        'scope': TWITTER_OAUTH_SCOPE,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }

    auth_url = 'https://twitter.com/i/oauth2/authorize?' + urlencode(params)
    return auth_url, code_verifier

def exchange_twitter_code_for_token(code: str, code_verifier: str) -> Dict:
    """
    Exchange authorization code for access token using PKCE code_verifier.

    Args:
        code: Authorization code from OAuth callback
        code_verifier: The PKCE verifier generated during authorization URL creation

    Returns:
        Dictionary with access_token, refresh_token, expires_in
    """
    response = requests.post(
        'https://api.twitter.com/2/oauth2/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': TWITTER_REDIRECT_URI,
            'code_verifier': code_verifier,
        },
        auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET),
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=10,
    )

    if not response.ok:
        raise Exception(_format_twitter_error("Twitter token exchange failed", response))

    data = response.json()
    return {
        'access_token': data['access_token'],
        'refresh_token': data.get('refresh_token'),
        'expires_in': data.get('expires_in', 7200),
    }

def get_twitter_user_info(access_token: str) -> Dict:
    """
    Get Twitter user profile information

    Args:
        access_token: User OAuth access token

    Returns:
        Dictionary with user_id, username, profile_pic
    """
    response = requests.get(
        'https://api.twitter.com/2/users/me',
        headers={'Authorization': f'Bearer {access_token}'},
        params={'user.fields': 'profile_image_url,username'},
        timeout=10,
    )

    if not response.ok:
        raise Exception(_format_twitter_error("Failed to get Twitter user info", response))

    data = response.json().get('data', {})
    return {
        'user_id': str(data.get('id', '')),
        'username': data.get('username', ''),
        'profile_pic': data.get('profile_image_url'),
    }

def post_to_twitter(access_token: str, text: str) -> Dict:
    """
    Post a tweet to Twitter (supports threads).

    Args:
        access_token: Decrypted user OAuth access token
        text: Tweet text. For threads, prefix lines with 1/, 2/, etc.

    Returns:
        Dictionary with success status and tweet_id(s) or error message
    """
    try:
        import tweepy
        # OAuth2 user access token (not bearer/app token)
        client = tweepy.Client(access_token=access_token)

        # Check if text is a thread (contains 1/, 2/, etc.)
        if '\n1/' in text or text.startswith('1/'):
            tweets = text.split('\n')
            tweet_ids = []
            previous_tweet_id = None

            for tweet_text in tweets:
                if not tweet_text.strip():
                    continue

                if previous_tweet_id:
                    response = client.create_tweet(
                        text=tweet_text.strip(),
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                else:
                    response = client.create_tweet(text=tweet_text.strip())

                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                previous_tweet_id = tweet_id

            return {
                'success': True,
                'tweet_ids': tweet_ids,
                'tweet_url': f"https://twitter.com/i/web/status/{tweet_ids[0]}",
                'thread': True
            }
        else:
            response = client.create_tweet(text=text)
            tweet_id = response.data['id']
            return {
                'success': True,
                'tweet_id': tweet_id,
                'tweet_url': f"https://twitter.com/i/web/status/{tweet_id}",
                'thread': False
            }

    except Exception as e:
        return {'success': False, 'error': str(e)}

def refresh_twitter_token(refresh_token: str) -> Dict:
    """
    Refresh an expired Twitter access token using the refresh_token grant.

    Returns:
        Dictionary with new access_token, refresh_token, expires_in
    """
    try:
        response = requests.post(
            'https://api.twitter.com/2/oauth2/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': TWITTER_CLIENT_ID,
            },
            auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=10,
        )

        if not response.ok:
            raise Exception(f"Token refresh failed: {response.text}")

        data = response.json()
        return {
            'success': True,
            'access_token': data['access_token'],
            'refresh_token': data.get('refresh_token', refresh_token),
            'expires_in': data.get('expires_in', 7200),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
