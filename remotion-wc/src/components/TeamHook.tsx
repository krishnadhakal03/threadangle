import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from 'remotion';
import CinematicTitleIntro from '../templates/cinematic-title-intro';
import ParticleExplosion from '../templates/particle-explosion';

const ACCENT_GOLD   = '#D4A843';
const SPRING_BOUNCY = { damping: 12, stiffness: 200 };

export interface TeamHookProps {
  teamName: string;
  flagUrl: string;
  groupId: string;
  accentColor: string;
  bgVideoPath: string;
}

export const TeamHook: React.FC<TeamHookProps> = ({
  teamName,
  flagUrl,
  groupId,
  accentColor,
  bgVideoPath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // GERMANY text: cinematic entrance — translateY + opacity (CinematicTitleIntro pattern)
  const titleY = spring({
    frame,
    fps,
    from: 60,
    to: 0,
    durationInFrames: 40,
    config: { damping: 14, mass: 0.8 },
  });
  const titleOpacity = spring({
    frame,
    fps,
    from: 0,
    to: 1,
    durationInFrames: 30,
  });

  // Gold underline draws left-to-right
  const lineWidth = interpolate(frame, [20, 60], [0, 380], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Flag springs in with bounce (delayed 40 frames)
  const flagSpring = spring({ frame: Math.max(0, frame - 40), fps, config: SPRING_BOUNCY });
  const flagScale  = interpolate(flagSpring, [0, 1], [0.4, 1.0]);

  // Subtitle fades in late
  const subOpacity = interpolate(frame, [70, 100], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const subSpacing = interpolate(frame, [70, 100], [0, 6], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Pulsing glow in team colour
  const glowOpacity = Math.sin(frame / 10) * 0.05 + 0.10;

  // Particle gold burst opacity (peaks early then fades)
  const particleOpacity = interpolate(frame, [0, 10, 80, 120], [0, 0.55, 0.55, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      {/* Footage background */}
      <AbsoluteFill>
        <Video
          src={bgVideoPath}
          style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.4 }}
          muted
          loop
        />
      </AbsoluteFill>

      {/* CinematicTitleIntro: subtle animated gradient background layer */}
      <AbsoluteFill style={{ opacity: 0.10 }}>
        <CinematicTitleIntro />
      </AbsoluteFill>

      {/* ParticleExplosion: gold-tinted burst overlay */}
      <AbsoluteFill style={{
        opacity: particleOpacity,
        filter: 'hue-rotate(165deg) saturate(2.5) brightness(1.4)',
        mixBlendMode: 'screen',
      }}>
        <ParticleExplosion />
      </AbsoluteFill>

      {/* Large faint "2026" watermark */}
      <div style={{
        position:   'absolute',
        fontSize:   600,
        fontWeight: 900,
        color:      ACCENT_GOLD,
        opacity:    0.04,
        fontFamily: 'Arial Black, Impact, sans-serif',
        userSelect: 'none',
        letterSpacing: -20,
        lineHeight: 1,
      }}>
        2026
      </div>

      {/* Pulsing radial glow */}
      <div style={{
        position:     'absolute',
        width:        640,
        height:       320,
        borderRadius: '50%',
        background:   `radial-gradient(ellipse, ${accentColor}, transparent 70%)`,
        opacity:      glowOpacity,
        top:          '34%',
      }} />

      {/* Team name — cinematic entrance: translateY + opacity */}
      <div style={{
        transform:  `translateY(${titleY}px)`,
        opacity:    titleOpacity,
        display:    'flex',
        fontFamily: "'Oswald', 'Arial Narrow', Arial, sans-serif",
        fontWeight: 700,
        fontSize:   120,
        marginBottom: 16,
        zIndex:     2,
        letterSpacing: 10,
      }}>
        {teamName.split('').map((letter, i) => {
          const lf = Math.max(0, frame - i * 3);
          const brightness = interpolate(lf, [0, 3, 8], [1, 3, 1], { extrapolateRight: 'clamp' });
          return (
            <span key={i} style={{
              color:   'white',
              filter:  `brightness(${brightness})`,
              display: 'inline-block',
            }}>
              {letter}
            </span>
          );
        })}
      </div>

      {/* Gold underline */}
      <div style={{
        width:           lineWidth,
        height:          4,
        backgroundColor: ACCENT_GOLD,
        borderRadius:    2,
        zIndex:          2,
        marginBottom:    28,
        boxShadow:       `0 0 12px ${ACCENT_GOLD}`,
      }} />

      {/* Flag with bounce scale */}
      <img
        src={flagUrl}
        style={{
          transform:    `scale(${flagScale})`,
          width:        280,
          height:       'auto',
          borderRadius: 8,
          zIndex:       2,
          marginBottom: 22,
          boxShadow:    `0 0 40px ${accentColor}55`,
        }}
      />

      {/* FIFA WORLD CUP 2026 · GROUP X */}
      <div style={{
        opacity:       subOpacity,
        fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
        fontWeight:    400,
        fontSize:      26,
        color:         ACCENT_GOLD,
        letterSpacing: subSpacing,
        zIndex:        2,
      }}>
        FIFA WORLD CUP 2026 · GROUP {groupId}
      </div>
    </AbsoluteFill>
  );
};
