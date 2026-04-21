import { Link } from 'react-router-dom';
import ThreadangleLogo from '../components/ThreadangleLogo';

export default function NotFound() {
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
      <ThreadangleLogo size={48} showText={false} />

      <div style={{
        fontSize: '120px',
        fontWeight: 900,
        color: '#18181B',
        lineHeight: 1,
        margin: '24px 0 0',
        userSelect: 'none',
      }}>
        404
      </div>

      <h1 style={{
        fontSize: '24px',
        fontWeight: 700,
        color: '#FAFAFA',
        marginBottom: '12px',
        marginTop: '8px',
      }}>
        This page lost its angle
      </h1>

      <p style={{
        color: '#71717A',
        fontSize: '16px',
        marginBottom: '32px',
        maxWidth: '360px',
        lineHeight: 1.6,
      }}>
        The page you are looking for does not exist or has been moved.
      </p>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
        <Link
          to="/"
          style={{
            padding: '12px 24px',
            background: '#3B82F6',
            color: 'white',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 700,
            fontSize: '15px',
          }}
        >
          Go Home
        </Link>
        <Link
          to="/dashboard"
          style={{
            padding: '12px 24px',
            background: 'transparent',
            color: '#A1A1AA',
            border: '1px solid #27272A',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 600,
            fontSize: '15px',
          }}
        >
          Go to Dashboard
        </Link>
      </div>

      <div style={{ marginTop: '48px', color: '#3F3F46', fontSize: '13px' }}>
        Lost? Try{' '}
        <Link to="/blog" style={{ color: '#52525B' }}>Blog</Link>
        {' · '}
        <Link to="/pricing" style={{ color: '#52525B' }}>Pricing</Link>
        {' · '}
        <Link to="/contact" style={{ color: '#52525B' }}>Contact</Link>
      </div>
    </div>
  );
}
