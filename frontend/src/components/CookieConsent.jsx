import { useState, useEffect } from 'react';

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      setTimeout(() => setVisible(true), 1000);
    }
  }, []);

  const acceptAll = () => {
    localStorage.setItem('cookie_consent', 'all');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    setVisible(false);
  };

  const acceptEssential = () => {
    localStorage.setItem('cookie_consent', 'essential');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    setVisible(false);
  };

  if (!visible) return null;

  const cookies = [
    {
      name: 'Essential Cookies',
      desc: 'Authentication and session management. Cannot be disabled.',
      required: true,
    },
    {
      name: 'Analytics Cookies',
      desc: 'Google Analytics — helps us understand how users use Threadangle.',
      required: false,
    },
  ];

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      left: '24px',
      right: '24px',
      maxWidth: '480px',
      background: '#18181B',
      border: '1px solid #27272A',
      borderRadius: '12px',
      padding: '20px 24px',
      zIndex: 9999,
      boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <span style={{ fontSize: '18px' }}>🍪</span>
        <span style={{ color: '#FAFAFA', fontWeight: 700, fontSize: '15px' }}>We use cookies</span>
      </div>

      <p style={{ color: '#A1A1AA', fontSize: '13px', lineHeight: 1.6, marginBottom: '16px' }}>
        We use essential cookies to keep you logged in and analytics cookies to improve Threadangle.{' '}
        <a href="/privacy" target="_blank" style={{ color: '#3B82F6', textDecoration: 'none' }}>
          Privacy Policy
        </a>
      </p>

      {showDetails && (
        <div style={{ background: '#0D0D0F', borderRadius: '8px', padding: '12px', marginBottom: '16px', fontSize: '12px' }}>
          {cookies.map((cookie, i) => (
            <div
              key={cookie.name}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
                marginBottom: i < cookies.length - 1 ? '8px' : 0,
                paddingBottom: i < cookies.length - 1 ? '8px' : 0,
                borderBottom: i < cookies.length - 1 ? '1px solid #1C1C1F' : 'none',
              }}
            >
              <div>
                <div style={{ color: '#FAFAFA', fontWeight: 600, marginBottom: '2px' }}>{cookie.name}</div>
                <div style={{ color: '#71717A' }}>{cookie.desc}</div>
              </div>
              <div style={{
                color: cookie.required ? '#52525B' : '#3B82F6',
                fontSize: '11px', fontWeight: 700, whiteSpace: 'nowrap', marginLeft: '12px',
              }}>
                {cookie.required ? 'REQUIRED' : 'OPTIONAL'}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
        <button
          onClick={acceptAll}
          style={{
            flex: 1, padding: '10px 16px', background: '#3B82F6', color: 'white',
            border: 'none', borderRadius: '8px', fontWeight: 700, fontSize: '13px',
            cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          Accept All
        </button>
        <button
          onClick={acceptEssential}
          style={{
            flex: 1, padding: '10px 16px', background: 'transparent', color: '#A1A1AA',
            border: '1px solid #3F3F46', borderRadius: '8px', fontWeight: 600, fontSize: '13px',
            cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          Essential Only
        </button>
        <button
          onClick={() => setShowDetails(!showDetails)}
          style={{
            padding: '10px 12px', background: 'transparent', color: '#52525B',
            border: '1px solid #27272A', borderRadius: '8px', fontSize: '12px',
            cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          {showDetails ? 'Hide' : 'Details'}
        </button>
      </div>
    </div>
  );
}
