import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from 'remotion';
import { StatCounter } from './StatCounter';
import { OVRCircle } from './OVRCircle';

const ACCENT_GOLD   = '#D4A843';
const SPRING_BOUNCY = { damping: 12, stiffness: 200 };
const SPRING_SMOOTH = { damping: 18, stiffness: 100 };

export interface PlayerCardProps {
  name?: string;
  displayName: string;
  position: string;
  club: string;
  goals: number;
  caps: number;
  clubGoals: number;
  marketValue: string;
  ovr: number;
  accentColor: string;
  secondaryColor: string;
  bgVideoPath: string;
  photoUrl: string;
  flagCode: string;
  countryCode: string;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  displayName,
  position,
  club,
  goals,
  caps,
  clubGoals,
  marketValue,
  ovr,
  accentColor,
  secondaryColor,
  bgVideoPath,
  photoUrl,
  flagCode,
  countryCode,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Photo circle scales in
  const photoSpring = spring({ frame, fps, config: SPRING_BOUNCY });
  const photoScale  = interpolate(photoSpring, [0, 1], [0.7, 1.0]);

  // OVR badge drops in from top
  const ovrSpring = spring({ frame: Math.max(0, frame - 4), fps, config: SPRING_BOUNCY });
  const ovrY      = interpolate(ovrSpring, [0, 1], [-100, 0]);

  // Flag badge drops in from top (slight delay)
  const flagSpring = spring({ frame: Math.max(0, frame - 10), fps, config: SPRING_BOUNCY });
  const flagY      = interpolate(flagSpring, [0, 1], [-100, 0]);

  // Stats panel slides up from bottom
  const panelSpring = spring({ frame: Math.max(0, frame - 8), fps, config: SPRING_SMOOTH });
  const panelY      = interpolate(panelSpring, [0, 1], [160, 0]);

  // Player name fades in
  const nameOpacity = interpolate(frame, [15, 35], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const nameY = interpolate(frame, [15, 35], [30, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Position pill slides in from left
  const pillSpring = spring({ frame: Math.max(0, frame - 25), fps, config: SPRING_BOUNCY });
  const pillX      = interpolate(pillSpring, [0, 1], [-80, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0D0D14' }}>

      {/* Layer 1: Full bleed video background */}
      <Video
        src={bgVideoPath}
        style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.4 }}
        muted
        loop
      />

      {/* Layer 2: Dark gradient — bottom half only */}
      <AbsoluteFill style={{
        background: 'linear-gradient(transparent 35%, rgba(0,0,0,0.97) 62%)',
      }} />

      {/* Layer 3: OVR circle — top left */}
      <div style={{
        position: 'absolute', top: 70, left: 70, zIndex: 10,
        transform: `translateY(${ovrY}px)`,
      }}>
        <OVRCircle ovr={ovr} color={secondaryColor} size={160} />
      </div>

      {/* Layer 4: Flag badge — top right */}
      <div style={{
        position: 'absolute', top: 70, right: 70, zIndex: 10,
        transform: `translateY(${flagY}px)`,
        background: 'rgba(0,0,0,0.7)',
        border: `2px solid ${ACCENT_GOLD}`,
        borderRadius: 12,
        padding: '8px 16px',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <Img
          src={`https://flagcdn.com/w80/${flagCode}.png`}
          style={{ height: 36, borderRadius: 4 }}
        />
        <span style={{
          color: ACCENT_GOLD, fontSize: 20,
          fontWeight: 700, letterSpacing: 3,
        }}>
          {countryCode}
        </span>
      </div>

      {/* Layer 5: Player photo — centered, top area */}
      <div style={{
        position: 'absolute', top: 140,
        left: '50%', transform: `translateX(-50%) scale(${photoScale})`,
        zIndex: 5,
      }}>
        <div style={{
          width: 520, height: 520, borderRadius: '50%',
          overflow: 'hidden',
          border: `5px solid ${secondaryColor}`,
          boxShadow: `0 0 60px ${secondaryColor}40`,
        }}>
          <Img
            src={photoUrl}
            style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }}
          />
        </div>
      </div>

      {/* Layer 6: Stats panel — pinned to bottom */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        padding: '28px 60px 80px',
        background: 'rgba(0,0,0,0.92)',
        borderTop: `2px solid ${ACCENT_GOLD}`,
        transform: `translateY(${panelY}px)`,
      }}>

        {/* Player name */}
        <div style={{
          fontSize: 80, fontWeight: 700, color: '#fff',
          fontFamily: "'Oswald', Arial, sans-serif",
          letterSpacing: 2, marginBottom: 8,
          textShadow: `0 0 40px ${accentColor}60`,
          opacity: nameOpacity,
          transform: `translateY(${nameY}px)`,
        }}>
          {displayName}
        </div>

        {/* Position pill */}
        <div style={{
          display: 'inline-block',
          background: accentColor, color: '#fff',
          fontSize: 22, fontWeight: 700,
          padding: '6px 24px', borderRadius: 50,
          letterSpacing: 3, marginBottom: 16,
          transform: `translateX(${pillX}px)`,
        }}>
          {position}
        </div>

        {/* Club line */}
        <div style={{
          color: ACCENT_GOLD, fontSize: 20,
          fontFamily: "'Oswald', Arial, sans-serif",
          letterSpacing: 3, marginBottom: 16,
          textTransform: 'uppercase',
        }}>
          {club}
        </div>

        {/* Gold divider */}
        <div style={{ height: 2, background: ACCENT_GOLD, marginBottom: 20, borderRadius: 1 }} />

        {/* Stats row */}
        <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: 16 }}>
          <StatCounter value={goals}     label="GOALS"    color={secondaryColor} fontSize={72} />
          <StatCounter value={caps}      label="CAPS"     color={accentColor}    fontSize={72} />
          <StatCounter value={clubGoals} label="CLUB GLS" color={accentColor}    fontSize={72} />
        </div>

        {/* Gold divider */}
        <div style={{ height: 2, background: ACCENT_GOLD, marginBottom: 16, borderRadius: 1 }} />

        {/* Market value */}
        <div style={{ fontSize: 32, color: ACCENT_GOLD, fontWeight: 700, letterSpacing: 3 }}>
          {'💰 ' + marketValue}
        </div>
      </div>

    </AbsoluteFill>
  );
};
