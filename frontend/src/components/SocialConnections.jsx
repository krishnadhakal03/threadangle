import React, { useState, useEffect } from 'react';
import { request } from '../utils/api';
import { useConnectedAccounts } from '../hooks/useConnectedAccounts';
import { useDialog } from '../context/DialogContext';

/**
 * SocialConnections Component
 * Displays connected social media accounts and allows connecting/disconnecting
 */
const SocialConnections = () => {
  const { accounts, loading, error: fetchError, refetch, isConnected, getAccountInfo } = useConnectedAccounts();
  const { confirm: confirmDialog } = useDialog();
  const [error, setError] = useState('');
  const [connectingPlatform, setConnectingPlatform] = useState(null);
  const [instagramDebug, setInstagramDebug] = useState(null);
  const LINKEDIN_ONLY_MODE = true;
  const unavailableReasons = {
    twitter: {
      title: '⚠️ Requires Twitter API subscription ($100/month minimum)',
      detail: 'Twitter/X posting requires a paid API plan and approved app enrollment before we can enable one-click connect.',
      ctaLabel: 'Learn more about Twitter API pricing →',
      ctaUrl: 'https://developer.twitter.com/en/portal/products',
      buttonLabel: 'Requires API Plan'
    },
    instagram: {
      title: '⚠️ App verification pending with Meta',
      detail: 'We are completing Meta verification and business asset approvals. Instagram connect will be enabled once approved.',
      buttonLabel: 'Coming Soon'
    }
  };

  // SVG icons for each platform
  const platformIcons = {
    twitter: (
      <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.631L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
    linkedin: (
      <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.067-2.063 2.062 2.062 0 012.067 2.063zm1.482 13.019H3.857V9h2.962v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    instagram: (
      <svg viewBox="0 0 24 24" className="w-6 h-6" fill="white">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
  };

  // Platform configurations
  const platforms = [
    {
      id: 'twitter',
      name: 'Twitter / X',
      color: 'bg-black',
      description: 'Post tweets and threads automatically'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      color: 'bg-[#0A66C2]',
      description: 'Share professional content'
    },
    {
      id: 'instagram',
      name: 'Instagram',
      color: 'bg-gradient-to-br from-[#F58529] via-[#DD2A7B] to-[#515BD4]',
      description: 'Share Reels and Stories'
    }
  ];

  const formatOAuthError = (platform, rawError = '') => {
    const message = String(rawError || '').trim();
    const lower = message.toLowerCase();

    if (platform === 'twitter') {
      if (!message || lower === 'connection_failed') {
        return 'Twitter connection failed. Please try again. If it still fails, open OAuth Test Console from Settings for detailed diagnostics.';
      }
      if (lower.includes('client-not-enrolled') || lower.includes('not enrolled for api v2') || lower.includes('client forbidden')) {
        return 'Twitter app is not enrolled for API v2. In X Developer Portal, attach your App to a Project and enable the required API access level, then update backend Twitter client credentials and retry.';
      }
      if (lower.includes('invalid_state') || lower.includes('expired')) {
        return 'Twitter session expired. Please click Connect again and complete authorization in one attempt.';
      }
      if (lower.includes('access denied') || lower.includes('oauth error')) {
        return `Twitter authorization was not completed: ${message}`;
      }
    }

    return `Failed to connect ${platform}: ${message || 'Unknown error'}`;
  };

  /**
   * Connect Instagram via the Facebook JS SDK (FB.login).
   *
   * @param {boolean} forceFresh - if true, calls FB.logout() first to clear
   *   the cached SDK session. This forces Facebook to show the FULL auth flow
   *   again including the page-selection checkboxes — which is the fix for the
   *   "No Facebook Pages returned" error when a user skipped the page step.
   */
  const connectInstagram = (forceFresh = false) => {
    if (!window.FB) {
      setError('Facebook SDK not loaded yet — please refresh and try again.');
      return;
    }

    setConnectingPlatform('instagram');
    setError('');
    setInstagramDebug(null);

    const runInstagramDebug = async (token) => {
      try {
        const debug = await request(`/auth/instagram/debug-pages?token=${encodeURIComponent(token)}`, {
          method: 'GET',
        });
        setInstagramDebug(debug?.summary || null);
      } catch (debugErr) {
        console.warn('Instagram debug endpoint failed:', debugErr);
        setInstagramDebug(null);
      }
    };

    const doLogin = () => {
      window.FB.login((response) => {
        if (!response.authResponse) {
          setConnectingPlatform(null);
          if (response.status !== 'unknown') {
            setError('Instagram connection was cancelled. Please try again and click "Continue" on all permission screens.');
          }
          return;
        }

        const { accessToken } = response.authResponse;
        request('/auth/instagram/connect-token', {
          method: 'POST',
          body: JSON.stringify({ access_token: accessToken }),
        })
          .then(() => {
            setInstagramDebug(null);
            return refetch();
          })
          .catch((err) => {
            console.error('Failed to connect Instagram:', err);
            const msg = err.message || '';
            if (msg.includes('No Facebook Pages')) {
              setError('NO_PAGES');
              runInstagramDebug(accessToken);
            } else {
              setError(`Instagram connection failed: ${msg}`);
            }
          })
          .finally(() => setConnectingPlatform(null));
      }, {
        scope: 'instagram_basic,pages_show_list,pages_read_engagement,pages_manage_posts,instagram_content_publish',
        return_scopes: true,
        auth_type: 'rerequest',
      });
    };

    if (forceFresh) {
      // Clear the SDK session so Facebook shows the FULL dialog (including page checkboxes)
      try {
        window.FB.logout(() => doLogin());
      } catch {
        doLogin();
      }
    } else {
      doLogin();
    }
  };

  /**
   * Connect Twitter or LinkedIn via server-side OAuth redirect.
   */
  const connectWithRedirect = async (platform) => {
    try {
      setConnectingPlatform(platform);
      setError('');

      const response = await request(`/auth/${platform}/connect`, { method: 'GET' });

      if (!response.auth_url) throw new Error('No auth URL provided');

      const width = 600, height = 700;
      const left = Math.round(window.screenLeft + (window.outerWidth - width) / 2);
      const top = Math.round(window.screenTop + (window.outerHeight - height) / 2);

      const authWindow = window.open(
        response.auth_url,
        `Connect ${platform}`,
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );

      if (!authWindow) throw new Error('Popup blocked — please allow popups for this site');

      // Listen for the postMessage sent by OAuthCallback page
      const onMessage = (event) => {
        if (event.origin !== window.location.origin) return;
        if (event.data?.type !== 'oauth_callback') return;
        window.removeEventListener('message', onMessage);
        clearInterval(fallback);
        setConnectingPlatform(null);
        if (event.data.error) {
          setError(formatOAuthError(platform, event.data.error));
        } else {
          refetch();
        }
      };
      window.addEventListener('message', onMessage);

      // Fallback: if popup closed without sending a message (e.g. user closed it manually)
      const fallback = setInterval(() => {
        if (authWindow.closed) {
          clearInterval(fallback);
          window.removeEventListener('message', onMessage);
          setConnectingPlatform(null);
          setTimeout(() => refetch(), 500);
        }
      }, 1000);
    } catch (err) {
      console.error(`Failed to connect ${platform}:`, err);
      setError(formatOAuthError(platform, err.message));
      setConnectingPlatform(null);
    }
  };

  const connectAccount = (platform) => {
    if (LINKEDIN_ONLY_MODE && platform !== 'linkedin') {
      setError(unavailableReasons[platform] || `${platform} is temporarily unavailable.`);
      return;
    }

    if (platform === 'instagram') {
      connectInstagram();
    } else {
      connectWithRedirect(platform);
    }
  };

  const disconnectAccount = async (platform) => {
    const confirmed = await confirmDialog({
      title: `Disconnect ${platform}?`,
      message: `You will need to reconnect ${platform} to enable auto-posting again.`,
      confirmText: 'Disconnect',
      cancelText: 'Keep Connected',
      tone: 'danger',
    });
    if (!confirmed) {
      return;
    }
    
    try {
      await request(`/auth/${platform}/disconnect`, {
        method: 'DELETE'
      });
      
      // Refresh accounts list
      refetch();
      setError('');
    } catch (err) {
      console.error(`Failed to disconnect ${platform}:`, err);
      setError(`Failed to disconnect ${platform}. Please try again.`);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-[#27272A] rounded w-1/3"></div>
          <div className="space-y-3 mt-4">
            <div className="h-20 bg-[#27272A] rounded"></div>
            <div className="h-20 bg-[#27272A] rounded"></div>
            <div className="h-20 bg-[#27272A] rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#18181B] border border-[#27272A] rounded-2xl p-6">
      <div className="mb-6">
        <h2 className="text-white font-bold text-lg mb-2">
          Connected Accounts
        </h2>
        <p className="text-[#A1A1AA] text-sm">
          Connect your social media accounts to enable auto-posting
        </p>
      </div>

      {LINKEDIN_ONLY_MODE && (
        <div className="mb-4 p-4 bg-[#3B82F6]/10 border border-[#3B82F6]/20 rounded-lg text-[#BFDBFE] text-sm">
          LinkedIn-only mode is enabled right now. Twitter/X and Instagram are paused until external platform requirements are completed.
        </div>
      )}

      {(error || fetchError) && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {(error === 'NO_PAGES') ? (
            <div className="space-y-3">
              <p className="font-semibold text-red-300">No Instagram Business Account was found.</p>
              <p className="text-red-400 text-xs">Facebook permissions were granted, but no Instagram account linked to your Pages could be found. Complete these steps, then click "Try Again" below:</p>
              <ol className="list-decimal list-inside space-y-2 pl-1 text-red-300 text-xs">
                <li>
                  <strong>Convert Instagram to a Professional account</strong> (if not already):<br />
                  <span className="text-red-400/80">Instagram → Profile → ☰ → Settings → Account → Switch to Professional Account → Creator or Business</span>
                </li>
                <li>
                  <strong>Link your Instagram to a Facebook Page</strong>:<br />
                  <span className="text-red-400/80">Instagram → Settings → Account → Linked Accounts → Facebook → choose a Page you admin</span>
                </li>
                <li>
                  <strong>When the Facebook popup reopens</strong>, look for the
                  <em> "Choose what you allow"</em> section and make sure to <strong>check the ✅ boxes next to your Facebook Pages</strong> before clicking Continue.
                </li>
              </ol>
              <button
                onClick={() => connectInstagram(true)}
                disabled={connectingPlatform === 'instagram'}
                className="mt-1 px-4 py-2 bg-red-500/20 text-red-300 border border-red-500/40 rounded-lg hover:bg-red-500/30 transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {connectingPlatform === 'instagram' ? 'Connecting…' : '🔄 Try Again (Fresh Login)'}
              </button>

              {instagramDebug && (
                <div className="mt-3 text-left bg-[#09090B] rounded-xl p-3 space-y-1 border border-red-500/20">
                  <p className="text-[#71717A] text-xs font-medium uppercase tracking-wide mb-2">Facebook Debug Summary</p>
                  <p className="text-red-300 text-xs">
                    Short-token page count: <strong>{instagramDebug.short_page_count ?? 0}</strong>
                  </p>
                  <p className="text-red-300 text-xs">
                    Long-token page count: <strong>{instagramDebug.long_page_count ?? 'n/a'}</strong>
                  </p>
                  <p className="text-red-300 text-xs break-words">
                    Short-token user: <strong>{instagramDebug.short_me?.name || 'unknown'} ({instagramDebug.short_me?.id || 'no-id'})</strong>
                  </p>
                  <p className="text-red-300 text-xs break-words">
                    Hint: <strong>{instagramDebug.hint || 'No hint available'}</strong>
                  </p>
                  <p className="text-red-300 text-xs break-words">
                    Granted permissions: <strong>{(instagramDebug.granted_permissions || []).join(', ') || 'none'}</strong>
                  </p>
                </div>
              )}
            </div>
          ) : (error || fetchError)}
        </div>
      )}

      <div className="space-y-4">
        {platforms.map(platform => {
          const connected = isConnected(platform.id);
          const accountInfo = getAccountInfo(platform.id);
          const isConnecting = connectingPlatform === platform.id;
          const isTemporarilyUnavailable = LINKEDIN_ONLY_MODE && platform.id !== 'linkedin' && !connected;
          const unavailableReason = unavailableReasons[platform.id];

          return (
            <div
              key={platform.id}
              className="bg-[#09090B] border border-[#27272A] rounded-xl p-4 hover:border-[#3B3B3F] transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`w-12 h-12 ${platform.color} rounded-xl flex items-center justify-center`}>
                    {platformIcons[platform.id]}
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="font-semibold text-white">
                      {platform.name}
                    </h3>
                    <p className="text-sm text-[#71717A]">
                      {platform.description}
                    </p>

                    {isTemporarilyUnavailable && unavailableReason && (
                      <div className="mt-2 p-2.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg space-y-1.5">
                        <p className="text-xs text-yellow-400 font-medium">{unavailableReason.title}</p>
                        <p className="text-xs text-[#A1A1AA]">{unavailableReason.detail}</p>
                        {unavailableReason.ctaUrl && (
                          <a
                            href={unavailableReason.ctaUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-block text-xs text-blue-400 hover:text-blue-300 underline"
                          >
                            {unavailableReason.ctaLabel}
                          </a>
                        )}
                      </div>
                    )}
                    
                    {connected && accountInfo && (
                      <p className="text-xs text-[#52525B] mt-1">
                        Connected as: <span className="font-medium text-[#A1A1AA]">@{accountInfo.username}</span>
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex-shrink-0">
                  {connected ? (
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 text-green-400 text-xs font-medium">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Connected
                      </div>
                      <button
                        onClick={() => disconnectAccount(platform.id)}
                        className="px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/20 transition font-medium text-sm"
                      >
                        Disconnect
                      </button>
                    </div>
                  ) : isTemporarilyUnavailable ? (
                    <button
                      disabled
                      className="px-4 py-2 bg-[#27272A] text-[#71717A] rounded-lg font-medium text-sm cursor-not-allowed"
                    >
                      {unavailableReason?.buttonLabel || 'Temporarily Unavailable'}
                    </button>
                  ) : (
                    <button
                      onClick={() => connectAccount(platform.id)}
                      disabled={isConnecting}
                      className="px-4 py-2 bg-[#3B82F6] text-white rounded-lg hover:bg-[#2563EB] transition font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isConnecting ? (
                        <span className="flex items-center gap-2">
                          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Connecting...
                        </span>
                      ) : (
                        'Connect'
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-[#3B82F6]/10 border border-[#3B82F6]/20 rounded-lg">
        <h4 className="font-semibold text-[#60A5FA] mb-2 text-sm">
          ⚡ Auto-Posting Ready
        </h4>
        <p className="text-sm text-[#A1A1AA]">
          Once connected, you can enable auto-posting when scheduling content. Your posts will be automatically published at the scheduled time.
        </p>
      </div>
    </div>
  );
};

export default SocialConnections;
