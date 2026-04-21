import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { request } from '../utils/api';

/**
 * Handles the Facebook/Instagram OAuth callback.
 *
 * Meta redirects to http://localhost:5173/auth/facebook/callback?code=...&state=...
 * This page picks up those params, exchanges them via the backend, then closes the popup.
 */
export default function FacebookCallback() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading'); // 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('Connecting your Instagram account...');
  const hasFired = useRef(false); // Prevent React Strict Mode double-invoke

  const notifyOpener = (payload) => {
    try {
      localStorage.setItem('oauth-last-result', JSON.stringify({
        platform: 'instagram',
        ...payload,
        at: Date.now(),
      }));
    } catch {
      // ignore storage errors
    }

    if (window.opener) {
      window.opener.postMessage(
        { type: 'oauth_callback', platform: 'instagram', ...payload },
        window.location.origin
      );
    }
  };

  useEffect(() => {
    if (hasFired.current) return;
    hasFired.current = true;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');
    const errorReason = searchParams.get('error_reason');

    if (error) {
      const reason = errorReason || error;
      setStatus('error');
      setMessage(`Authorization denied: ${reason}`);
      notifyOpener({ error: `Authorization denied: ${reason}` });
      // Close popup after a short delay so user can read the message
      setTimeout(() => {
        if (window.opener) {
          window.close();
        } else {
          window.location.href = '/dashboard?error=instagram_denied';
        }
      }, 2500);
      return;
    }

    if (!code || !state) {
      setStatus('error');
      setMessage('Missing authorization code. Please try again.');
      notifyOpener({ error: 'Missing authorization code. Please try again.' });
      setTimeout(() => {
        if (window.opener) window.close();
        else window.location.href = '/dashboard?error=instagram_failed';
      }, 2500);
      return;
    }

    const exchangeCode = async () => {
      try {
        await request('/auth/facebook/exchange', {
          method: 'POST',
          body: JSON.stringify({ code, state }),
        });
        setStatus('success');
        setMessage('Instagram connected successfully!');
        notifyOpener({ success: true });
        // Signal the parent window to refresh connected accounts immediately
        if (window.opener) {
          localStorage.setItem('oauth-completed', 'instagram');
        }
        // Close popup after a short delay so user can see the success screen
        setTimeout(() => {
          if (window.opener) {
            window.close();
          } else {
            window.location.href = '/dashboard?connected=instagram';
          }
        }, 1200);
      } catch (err) {
        setStatus('error');
        const errorMessage = err.message || 'Failed to connect Instagram. Please try again.';
        setMessage(errorMessage);
        notifyOpener({ error: errorMessage });
        // Give the user more time to read actionable error messages
        setTimeout(() => {
          if (window.opener) window.close();
          else window.location.href = '/dashboard?error=instagram_failed';
        }, 5000);
      }
    };

    exchangeCode();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-8 max-w-sm w-full text-center">
        {/* Instagram gradient icon */}
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#F58529] via-[#DD2A7B] to-[#515BD4] flex items-center justify-center mx-auto mb-5">
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="white">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
          </svg>
        </div>

        {status === 'loading' && (
          <>
            <div className="flex justify-center mb-4">
              <svg className="w-6 h-6 animate-spin text-[#DD2A7B]" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <h2 className="text-white font-semibold text-lg mb-1">Connecting Instagram</h2>
            <p className="text-[#A1A1AA] text-sm">{message}</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="flex justify-center mb-4">
              <svg className="w-8 h-8 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-white font-semibold text-lg mb-1">Connected!</h2>
            <p className="text-[#A1A1AA] text-sm">{message}</p>
            <p className="text-[#52525B] text-xs mt-2">This window will close automatically.</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="flex justify-center mb-4">
              <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <h2 className="text-white font-semibold text-lg mb-2">Connection Failed</h2>
            <p className="text-[#A1A1AA] text-sm mb-3">{message}</p>

            {/* No Facebook Pages — user didn't share a page */}
            {(message.includes('Facebook Page') || message.includes('pages_show_list')) && (
              <div className="text-left bg-[#09090B] rounded-xl p-3 mb-3 space-y-1">
                <p className="text-[#71717A] text-xs font-medium uppercase tracking-wide mb-2">Fix required:</p>
                <p className="text-[#A1A1AA] text-xs">1. Click <strong>Connect Instagram</strong> again</p>
                <p className="text-[#A1A1AA] text-xs">2. In the Facebook popup, click <strong>"Edit"</strong> next to Pages</p>
                <p className="text-[#A1A1AA] text-xs">3. Select your Facebook Page, then click <strong>Continue</strong></p>
                <p className="text-[#A1A1AA] text-xs">4. If you don't have a Page: <a href="https://www.facebook.com/pages/create" target="_blank" rel="noreferrer" className="text-[#DD2A7B] underline">Create one here</a></p>
              </div>
            )}

            {/* instagram_basic permission missing */}
            {message.includes('instagram_basic') && (
              <div className="text-left bg-[#09090B] rounded-xl p-3 mb-3 space-y-1">
                <p className="text-[#71717A] text-xs font-medium uppercase tracking-wide mb-2">Meta App config needed:</p>
                <p className="text-[#A1A1AA] text-xs">1. Go to <a href="https://developers.facebook.com/apps" target="_blank" rel="noreferrer" className="text-[#DD2A7B] underline">Meta Developer Portal</a></p>
                <p className="text-[#A1A1AA] text-xs">2. Your App → Products → <strong>Facebook Login for Business</strong></p>
                <p className="text-[#A1A1AA] text-xs">3. Permissions → add <strong>instagram_basic</strong> and <strong>pages_show_list</strong></p>
                <p className="text-[#A1A1AA] text-xs">4. <span className="text-red-400">Remove</span> instagram_business_basic (wrong API)</p>
              </div>
            )}

            {/* No Instagram linked to page */}
            {message.includes('Instagram Business') && (
              <div className="text-left bg-[#09090B] rounded-xl p-3 mb-3 space-y-1">
                <p className="text-[#71717A] text-xs font-medium uppercase tracking-wide mb-2">Link Instagram to your Page:</p>
                <p className="text-[#A1A1AA] text-xs">1. On Instagram → Settings → Account → <strong>Switch to Professional</strong></p>
                <p className="text-[#A1A1AA] text-xs">2. Go to your Facebook Page → Settings → <strong>Linked Accounts</strong> → Instagram</p>
                <p className="text-[#A1A1AA] text-xs">3. Connect your Instagram account, then try again</p>
              </div>
            )}

            <p className="text-[#52525B] text-xs">This window will close automatically.</p>
          </>
        )}
      </div>
    </div>
  );
}
