import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          background: '#09090B',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '24px',
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚡</div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#FAFAFA', marginBottom: '12px' }}>
            Something went wrong
          </h1>
          <p style={{
            color: '#71717A', fontSize: '15px', marginBottom: '32px',
            maxWidth: '400px', lineHeight: 1.6,
          }}>
            Threadangle hit an unexpected error. Your data is safe.
            Please refresh the page or go back home.
          </p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '12px 24px', background: '#3B82F6', color: 'white',
                border: 'none', borderRadius: '8px', fontWeight: 700,
                cursor: 'pointer', fontSize: '15px',
              }}
            >
              Refresh Page
            </button>
            <a
              href="/"
              style={{
                padding: '12px 24px', background: 'transparent', color: '#A1A1AA',
                border: '1px solid #27272A', borderRadius: '8px', fontWeight: 600,
                fontSize: '15px', textDecoration: 'none',
              }}
            >
              Go Home
            </a>
          </div>

          {import.meta.env.DEV && this.state.error && (
            <details style={{
              marginTop: '32px', maxWidth: '600px', textAlign: 'left',
              background: '#18181B', padding: '16px', borderRadius: '8px',
              border: '1px solid #27272A',
            }}>
              <summary style={{ color: '#EF4444', cursor: 'pointer', marginBottom: '8px' }}>
                Error details (dev only)
              </summary>
              <pre style={{ color: '#F87171', fontSize: '12px', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
                {this.state.error.toString()}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}
