import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * Shown inside the OAuth popup after a successful connection.
 * Reads ?connected=platform from the URL, sends a message to the opener,
 * then closes itself automatically.
 */
const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const platform = searchParams.get('connected');
  const error = searchParams.get('error');

  useEffect(() => {
    // Notify the parent window so it can refetch accounts immediately
    if (window.opener) {
      window.opener.postMessage(
        { type: 'oauth_callback', platform, error },
        window.location.origin
      );
    }
    // Auto-close after a short delay so the user can see the result
    const t = setTimeout(() => window.close(), 1500);
    return () => clearTimeout(t);
  }, [platform, error]);

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
      <div className="text-center space-y-4 p-8">
        {error ? (
          <>
            <div className="text-5xl">❌</div>
            <p className="text-white text-xl font-semibold">Connection failed</p>
            <p className="text-red-400 text-sm max-w-xl mx-auto break-words">{decodeURIComponent(error)}</p>
            <p className="text-[#71717A] text-sm">You can close this window.</p>
          </>
        ) : (
          <>
            <div className="text-5xl">✅</div>
            <p className="text-white text-xl font-semibold capitalize">
              {platform || 'Account'} connected!
            </p>
            <p className="text-[#71717A] text-sm">This window will close automatically…</p>
          </>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
