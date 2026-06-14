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
import BounceText from '../templates/bounce-text';
import PulsingText from '../templates/pulsing-text';

const ACCENT_GOLD    = '#D4A843';
const SPRING_BOUNCY  = { damping: 12, stiffness: 200 };
const SPRING_GRAVITY = { damping: 20, stiffness: 300 };

const CONTENDER_CODES = ['de', 'fr', 'br', 'ar', 'pt'];

export interface CTASceneProps {
  teamName: string;
  accentColor: string;
  bgVideoPath: string;
}

export const CTAScene: React.FC<CTASceneProps> = ({
  teamName,
  accentColor,
  bgVideoPath,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // "CAN {TEAM}" — scale-bounce entrance
  const line1Spring = spring({ frame, fps, config: SPRING_BOUNCY });
  const line1Scale  = interpolate(line1Spring, [0, 1], [0.5, 1.0]);

  // "WIN IT ALL?" — per-word bounce (BounceText pattern: spring slideIn from left)
  const winWords = [
    { text: 'WIN',  delay: 10 },
    { text: 'IT',   delay: 18 },
    { text: 'ALL?', delay: 26 },
  ];
  const winAnims = winWords.map(({ text, delay }) => {
    const s = spring({ frame: Math.max(0, frame - delay), fps, config: SPRING_BOUNCY });
    return { text, x: interpolate(s, [0, 1], [-80, 0]), opacity: interpolate(s, [0, 1], [0, 1]) };
  });

  // Gold divider grows from centre outward
  const halfWidth = interpolate(frame, [30, 60], [0, 100], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // "COMMENT BELOW" — PulsingText pattern: per-character scale pulse
  const commentText = 'COMMENT BELOW 👇';
  const charPulseAnims = commentText.split('').map((char, i) => {
    const delay = i * 5;
    const pulse = interpolate(
      ((frame - delay) % 30) / 30,
      [0, 0.5, 1],
      [1, 1.18, 1],
      { extrapolateRight: 'clamp' }
    );
    const charOpacity = interpolate(frame - delay, [0, 8], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
    return { char, pulse, charOpacity };
  });

  // Flag images: fall from above with gravity-spring stagger
  const flagAnims = CONTENDER_CODES.map((code, i) => {
    const fFrame  = Math.max(0, frame - i * 8 - 60);
    const fSpring = spring({ frame: fFrame, fps, config: SPRING_GRAVITY });
    return {
      code,
      y:       interpolate(fSpring, [0, 1], [-220, 0]),
      opacity: interpolate(fFrame, [0, 6], [0, 1], { extrapolateRight: 'clamp' }),
    };
  });

  // Subtle camera pull-back near end
  const zoomOut = interpolate(frame, [270, 290], [1.0, 0.97], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
      {/* Celebration footage */}
      <AbsoluteFill>
        <Video
          src={bgVideoPath}
          style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.3 }}
          muted
          loop
        />
      </AbsoluteFill>

      {/* BounceText: subtle background texture layer (slide-in animation from template) */}
      <AbsoluteFill style={{ opacity: 0.06 }}>
        <BounceText />
      </AbsoluteFill>

      {/* PulsingText: subtle background texture layer (pulse animation from template) */}
      <AbsoluteFill style={{ opacity: 0.05 }}>
        <PulsingText />
      </AbsoluteFill>

      {/* "?" watermark */}
      <div style={{
        position:   'absolute',
        fontSize:   500,
        fontWeight: 900,
        color:      ACCENT_GOLD,
        opacity:    0.04,
        fontFamily: 'Arial Black, Impact, sans-serif',
        userSelect: 'none',
        lineHeight: 1,
      }}>
        ?
      </div>

      {/* Main content — zooms out at the very end */}
      <div style={{
        transform:     `scale(${zoomOut})`,
        display:       'flex',
        flexDirection: 'column',
        alignItems:    'center',
        zIndex:        2,
      }}>
        {/* CAN {teamName} */}
        <div style={{
          transform:     `scale(${line1Scale})`,
          fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
          fontWeight:    700,
          fontSize:      80,
          color:         'white',
          textAlign:     'center',
          letterSpacing: 4,
          marginBottom:  6,
        }}>
          CAN {teamName}
        </div>

        {/* WIN IT ALL? — BounceText-style per-word slide from left */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
          {winAnims.map(({ text, x, opacity }) => (
            <div key={text} style={{
              transform:     `translateX(${x}px)`,
              opacity,
              fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
              fontWeight:    700,
              fontSize:      80,
              color:         accentColor,
              letterSpacing: 4,
            }}>
              {text}
            </div>
          ))}
        </div>

        {/* Gold divider growing from centre */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 56 }}>
          <div style={{
            width:        halfWidth,
            height:       4,
            backgroundColor: ACCENT_GOLD,
            borderRadius: '4px 0 0 4px',
          }} />
          <div style={{
            width:        halfWidth,
            height:       4,
            backgroundColor: ACCENT_GOLD,
            borderRadius: '0 4px 4px 0',
          }} />
        </div>

        {/* COMMENT BELOW — PulsingText-style per-character scale pulse */}
        <div style={{ display: 'flex', marginBottom: 44, flexWrap: 'wrap', justifyContent: 'center' }}>
          {charPulseAnims.map(({ char, pulse, charOpacity }, i) => (
            <span key={i} style={{
              display:    'inline-block',
              transform:  `scale(${pulse})`,
              opacity:    charOpacity,
              fontFamily: 'Arial Black, Arial, sans-serif',
              fontWeight: 700,
              fontSize:   52,
              color:      'white',
            }}>
              {char === ' ' ? ' ' : char}
            </span>
          ))}
        </div>

        {/* Contender flags — flagcdn.com <Img> tags, fall from top with gravity */}
        <div style={{ display: 'flex', gap: 20 }}>
          {flagAnims.map(({ code, y, opacity }) => (
            <div key={code} style={{
              transform: `translateY(${y}px)`,
              opacity,
            }}>
              <Img
                src={`https://flagcdn.com/w80/${code}.png`}
                style={{ width: 80, height: 54, borderRadius: 8, display: 'block' }}
              />
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
