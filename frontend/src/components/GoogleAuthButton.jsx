// TODO: Set VITE_GOOGLE_CLIENT_ID in frontend/.env before testing Google OAuth
// TODO: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env
// Get credentials at: console.cloud.google.com
// Steps: Create project → Enable Google Identity API → Create OAuth 2.0 credentials
//        → Add http://localhost:5173 and https://kriangle.com as authorized origins

import { useGoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function GoogleAuthButton({ label = 'Continue with Google', onSuccess }) {
    const { loginWithGoogle } = useAuth();
    const navigate = useNavigate();
    // Use relative path so Vite proxy handles it in dev (avoids Mixed Content on HTTPS).
    // In production VITE_API_URL is set to the backend origin.
    const API_BASE = import.meta.env.VITE_API_URL || '';

    const login = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            try {
                // Get user info from Google using the access token
                const userInfoRes = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                    headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
                });
                const userInfo = await userInfoRes.json();

                // Send to our backend for verification and JWT creation
                const res = await fetch(`${API_BASE}/api/auth/google`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        token: tokenResponse.access_token,
                        email: userInfo.email,
                        name: userInfo.name,
                        google_id: userInfo.sub,
                    }),
                });
                const data = await res.json();
                if (res.ok) {
                    await loginWithGoogle(data);
                    if (onSuccess) {
                        onSuccess(data);
                    } else {
                        navigate(data.is_new_user ? '/dashboard?onboarding=true' : '/dashboard');
                    }
                } else {
                    console.error('Google auth backend error:', data);
                }
            } catch (err) {
                console.error('Google auth error:', err);
            }
        },
        onError: () => console.error('Google login failed'),
    });

    return (
        <button
            type="button"
            onClick={() => login()}
            style={{
                width: '100%',
                padding: '12px 16px',
                background: '#FAFAFA',
                border: '1px solid #E4E4E7',
                borderRadius: '8px',
                color: '#09090B',
                fontSize: '15px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                transition: 'background 0.15s',
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#F4F4F5')}
            onMouseOut={e => (e.currentTarget.style.background = '#FAFAFA')}
        >
            {/* Google logo */}
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            {label}
        </button>
    );
}
