import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { request } from '../utils/api';
import { useConnectedAccounts } from '../hooks/useConnectedAccounts';

export default function OAuthTestPage() {
  const { refetch, isConnected, getAccountInfo } = useConnectedAccounts();
  const [busy, setBusy] = useState('');
  const [status, setStatus] = useState('Click a test button to start OAuth.');
  const [linkedinPostText, setLinkedinPostText] = useState('Threadforge LinkedIn posting smoke test from OAuth Test Console.');
  const [postingLinkedIn, setPostingLinkedIn] = useState(false);

  const testOAuth = async (platform) => {
    try {
      setBusy(platform);
      setStatus(`Starting ${platform} OAuth...`);

      const response = await request(`/auth/${platform}/connect`, { method: 'GET' });
      if (!response.auth_url) throw new Error('No auth URL returned');

      const width = 640;
      const height = 760;
      const left = Math.round(window.screenLeft + (window.outerWidth - width) / 2);
      const top = Math.round(window.screenTop + (window.outerHeight - height) / 2);

      const popup = window.open(
        response.auth_url,
        `OAuth ${platform}`,
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );

      if (!popup) throw new Error('Popup blocked — please allow popups.');

      const onMessage = async (event) => {
        if (event.origin !== window.location.origin) return;
        if (event.data?.type !== 'oauth_callback') return;

        const callbackPlatform = event.data.platform || platform;

        window.removeEventListener('message', onMessage);
        clearInterval(fallback);
        setBusy('');

        if (event.data.error) {
          setStatus(`❌ ${callbackPlatform} failed: ${event.data.error}`);
          return;
        }

        await refetch();
        const info = getAccountInfo(callbackPlatform);
        setStatus(`✅ ${callbackPlatform} connected${info?.username ? ` as @${info.username}` : ''}`);
      };

      window.addEventListener('message', onMessage);

      const fallback = setInterval(async () => {
        if (!popup.closed) return;
        clearInterval(fallback);
        window.removeEventListener('message', onMessage);
        setBusy('');

        try {
          const raw = localStorage.getItem('oauth-last-result');
          if (raw) {
            const parsed = JSON.parse(raw);
            const isRecent = Date.now() - (parsed.at || 0) < 120000;
            if (parsed?.platform === platform && isRecent) {
              if (parsed.error) {
                setStatus(`❌ ${platform} failed: ${parsed.error}`);
                return;
              }
              if (parsed.success) {
                await refetch();
                const info = getAccountInfo(platform);
                setStatus(`✅ ${platform} connected${info?.username ? ` as @${info.username}` : ''}`);
                return;
              }
            }
          }
        } catch {
          // ignore storage parse errors and continue with standard fallback
        }

        await refetch();
        const connected = isConnected(platform);
        setStatus(connected ? `✅ ${platform} connected` : `Popup closed. ${platform} not connected.`);
      }, 800);
    } catch (err) {
      setBusy('');
      setStatus(`❌ ${platform} error: ${err.message || 'Unknown error'}`);
    }
  };

  const testLinkedInPost = async () => {
    if (!linkedinPostText.trim()) {
      setStatus('❌ Please enter LinkedIn post text first.');
      return;
    }

    try {
      setPostingLinkedIn(true);
      setStatus('Posting test message to LinkedIn...');

      const response = await request('/auth/linkedin/test-post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: linkedinPostText.trim() })
      });

      if (response?.success) {
        setStatus(`✅ LinkedIn post published successfully${response?.post_id ? ` (ID: ${response.post_id})` : ''}`);
      } else {
        setStatus(`❌ LinkedIn post failed: ${response?.error || 'Unknown error'}`);
      }
    } catch (err) {
      setStatus(`❌ LinkedIn post failed: ${err.message || 'Unknown error'}`);
    } finally {
      setPostingLinkedIn(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-8 space-y-6">
      <header>
        <h2 className="text-3xl font-bold text-white mb-1">OAuth Test Console</h2>
        <p className="text-[#A1A1AA]">Use this page to test backend OAuth flows using credentials from backend .env</p>
      </header>

      <section className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6 space-y-4">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => testOAuth('instagram')}
            disabled={busy !== ''}
            className="px-5 py-2.5 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white text-sm font-bold rounded-xl disabled:opacity-50"
          >
            {busy === 'instagram' ? 'Testing Instagram...' : 'Test Facebook/Instagram OAuth'}
          </button>

          <button
            onClick={() => testOAuth('twitter')}
            disabled={busy !== ''}
            className="px-5 py-2.5 bg-black hover:bg-[#111] text-white text-sm font-bold rounded-xl border border-[#27272A] disabled:opacity-50"
          >
            {busy === 'twitter' ? 'Testing Twitter...' : 'Test Twitter OAuth'}
          </button>

          <button
            onClick={() => testOAuth('linkedin')}
            disabled={busy !== ''}
            className="px-5 py-2.5 bg-[#0A66C2] hover:bg-[#0959AA] text-white text-sm font-bold rounded-xl disabled:opacity-50"
          >
            {busy === 'linkedin' ? 'Testing LinkedIn...' : 'Test LinkedIn OAuth'}
          </button>
        </div>

        <div className="bg-[#09090B] border border-[#27272A] rounded-xl p-4 space-y-3">
          <p className="text-xs uppercase tracking-wide text-[#71717A]">LinkedIn Posting Smoke Test</p>
          <textarea
            value={linkedinPostText}
            onChange={(e) => setLinkedinPostText(e.target.value)}
            rows={4}
            className="w-full bg-[#18181B] border border-[#27272A] rounded-lg p-3 text-sm text-white focus:outline-none focus:border-[#3B82F6]"
            placeholder="Enter text to publish to LinkedIn"
          />
          <button
            onClick={testLinkedInPost}
            disabled={postingLinkedIn}
            className="px-4 py-2 bg-[#16A34A] hover:bg-[#15803D] text-white text-sm font-bold rounded-lg disabled:opacity-50"
          >
            {postingLinkedIn ? 'Posting to LinkedIn...' : 'Publish LinkedIn Test Post'}
          </button>
        </div>

        <div className="bg-[#09090B] border border-[#27272A] rounded-xl p-4">
          <p className="text-xs uppercase tracking-wide text-[#71717A] mb-2">Status</p>
          <p className="text-sm text-white break-words">{status}</p>
        </div>

        <div className="text-xs text-[#71717A]">
          Backend endpoints used: <span className="text-[#A1A1AA]">/api/auth/instagram/connect</span>, <span className="text-[#A1A1AA]">/api/auth/twitter/connect</span>, <span className="text-[#A1A1AA]">/api/auth/linkedin/connect</span>, and <span className="text-[#A1A1AA]">/api/auth/linkedin/test-post</span>
        </div>
      </section>

      <div>
        <Link
          to="/dashboard"
          className="inline-block px-4 py-2 text-sm font-bold rounded-xl bg-[#27272A] text-white hover:bg-[#3B3B3F]"
        >
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
