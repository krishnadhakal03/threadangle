export default function ThreadangleLogo({ size = 32, showText = true, textSize = 20 }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
      {/* Icon mark */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        shapeRendering="crispEdges"
        style={{ imageRendering: 'crisp-edges' }}
      >
        <defs>
          <linearGradient id="bgGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
          <linearGradient id="boltGrad" x1="0" y1="0" x2="20" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FCD34D" />
            <stop offset="100%" stopColor="#F59E0B" />
          </linearGradient>
        </defs>

        {/* Background rounded square */}
        <rect width="40" height="40" rx="10" fill="url(#bgGrad)" />

        {/* Subtle inner glow */}
        <rect width="40" height="40" rx="10" fill="white" fillOpacity="0.05" />

        {/* Lightning bolt / angle mark */}
        <path
          d="M23 7L13 22H20L17 33L27 18H20L23 7Z"
          fill="url(#boltGrad)"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Subtle thread lines */}
        <line x1="8" y1="12" x2="13" y2="12" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" />
        <line x1="8" y1="16" x2="12" y2="16" stroke="white" strokeWidth="1.5" strokeOpacity="0.3" strokeLinecap="round" />
        <line x1="27" y1="24" x2="32" y2="24" stroke="white" strokeWidth="1.5" strokeOpacity="0.4" strokeLinecap="round" />
        <line x1="28" y1="28" x2="32" y2="28" stroke="white" strokeWidth="1.5" strokeOpacity="0.3" strokeLinecap="round" />
      </svg>

      {/* Wordmark */}
      {showText && (
        <span style={{
          fontSize: textSize,
          fontWeight: 700,
          color: '#FAFAFA',
          letterSpacing: '-0.5px',
          fontFamily: 'Inter, system-ui, sans-serif',
        }}>
          Threadangle
        </span>
      )}
    </div>
  );
}
