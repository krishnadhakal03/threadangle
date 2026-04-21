"""
LinkedIn OAuth and posting integration
Handles OAuth 2.0 flow and post creation
"""

import requests
import os
from typing import Dict
from urllib.parse import urlencode

# LinkedIn API credentials from environment
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8000/api/auth/linkedin/callback')

def get_linkedin_oauth_url(state: str) -> str:
    """
    Generate LinkedIn OAuth 2.0 authorization URL
    
    Args:
        state: Random string for CSRF protection
        
    Returns:
        Authorization URL for user to visit
    """
    
    scope = 'openid profile email w_member_social'
    
    params = {
        'response_type': 'code',
        'client_id': LINKEDIN_CLIENT_ID,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'state': state,
        'scope': scope
    }
    
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return auth_url

def exchange_linkedin_code_for_token(code: str) -> Dict:
    """
    Exchange authorization code for access token
    
    Args:
        code: Authorization code from OAuth callback
        
    Returns:
        Dictionary with access_token and expires_in
    """
    
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINKEDIN_REDIRECT_URI,
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET
    }
    
    response = requests.post(token_url, data=data)
    token_data = response.json()
    
    if 'access_token' not in token_data:
        raise Exception(f"LinkedIn token exchange failed: {token_data}")
    
    return {
        'access_token': token_data['access_token'],
        'expires_in': token_data.get('expires_in', 5184000)  # 60 days default
    }

def get_linkedin_user_info(access_token: str) -> Dict:
    """
    Get LinkedIn user profile information
    
    Args:
        access_token: Decrypted access token
        
    Returns:
        Dictionary with user_id, username, profile_pic
    """
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Get basic profile using userinfo endpoint
    profile_response = requests.get(
        'https://api.linkedin.com/v2/userinfo',
        headers=headers
    )
    
    if profile_response.status_code != 200:
        raise Exception(f"LinkedIn userinfo failed: {profile_response.text}")
    
    profile = profile_response.json()
    
    return {
        'user_id': profile.get('sub'),  # LinkedIn user ID
        'username': profile.get('name'),  # Full name
        'profile_pic': profile.get('picture')  # Profile picture URL
    }

def post_to_linkedin(access_token: str, text: str, user_id: str) -> Dict:
    """
    Post content to LinkedIn
    
    Args:
        access_token: Decrypted access token
        text: Post text/content
        user_id: LinkedIn user ID (sub from userinfo)
        
    Returns:
        Dictionary with success status, post_id or error
    """
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        # LinkedIn UGC (User Generated Content) API
        post_data = {
            "author": f"urn:li:person:{user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(
            'https://api.linkedin.com/v2/ugcPosts',
            headers=headers,
            json=post_data
        )
        
        if response.status_code in [200, 201]:
            post_id = response.json().get('id')
            return {
                'success': True,
                'post_id': post_id,
                'message': 'Posted to LinkedIn successfully'
            }
        else:
            return {
                'success': False,
                'error': f"LinkedIn API error: {response.status_code} - {response.text}"
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def refresh_linkedin_token(refresh_token: str) -> Dict:
    """
    Refresh LinkedIn access token
    Note: LinkedIn tokens are long-lived (60 days) but can be refreshed
    
    Args:
        refresh_token: Current refresh token
        
    Returns:
        Dictionary with new access_token
    """
    
    try:
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': LINKEDIN_CLIENT_ID,
            'client_secret': LINKEDIN_CLIENT_SECRET
        }
        
        response = requests.post(token_url, data=data)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            raise Exception(f"LinkedIn token refresh failed: {token_data}")
        
        return {
            'success': True,
            'access_token': token_data['access_token'],
            'expires_in': token_data.get('expires_in', 5184000)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
