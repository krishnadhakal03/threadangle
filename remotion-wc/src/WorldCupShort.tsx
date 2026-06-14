import React from 'react';
import {
  AbsoluteFill,
  Audio,
  interpolate,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from 'remotion';

// ─── Color Constants ───────────────────────────────────────────────────────────
const GERMANY_BLACK = "#1a1a1a";
const GERMANY_RED   = "#DD0000";
const GERMANY_GOLD  = "#FFCE00";
const ACCENT_GOLD   = "#D4A843";
const BG            = "#0D0D14";

// ─── Spring Configs ────────────────────────────────────────────────────────────
const SPRING_BOUNCY = { damping: 12,  stiffness: 200 }; // snappy entrance
const SPRING_SMOOTH = { damping: 200, stiffness: 80  }; // stat count-up

// ─── Shared: OVR Circle SVG ───────────────────────────────────────────────────
const OVRCircle: React.FC<{ frame: number }> = ({ frame }) => {
  const radius       = 80;
  const circumference = 2 * Math.PI * radius;
  const progress     = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const strokeDashoffset = interpolate(progress, [0, 1], [circumference, 0]);

  return (
    <svg
      width={200} height={200} viewBox="0 0 200 200"
      style={{ position: 'absolute', top: 40, right: 40 }}
    >
      <circle cx={100} cy={100} r={radius} fill="none" stroke="#2a2a2a" strokeWidth={8} />
      <circle
        cx={100} cy={100} r={radius} fill="none"
        stroke={GERMANY_GOLD} strokeWidth={8}
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        transform="rotate(-90 100 100)"
      />
      <text x={100} y={96}  textAnchor="middle" fill="white"       fontSize={36} fontWeight="700" fontFamily="Arial">91</text>
      <text x={100} y={120} textAnchor="middle" fill={GERMANY_GOLD} fontSize={16} fontFamily="Arial">OVR</text>
    </svg>
  );
};

// ─── Shared: Radial Particles ─────────────────────────────────────────────────
const Particles: React.FC<{ frame: number }> = ({ frame }) => (
  <>
    {Array.from({ length: 8 }, (_, i) => {
      const angle    = (i / 8) * 2 * Math.PI;
      const progress = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
      const radius   = progress * 200;
      const opacity  = interpolate(frame, [0, 15, 30], [1, 0.8, 0], { extrapolateRight: 'clamp' });
      return (
        <div
          key={i}
          style={{
            position:        'absolute',
            width:           12,
            height:          12,
            borderRadius:    '50%',
            backgroundColor: GERMANY_GOLD,
            opacity,
            left:            '50%',
            top:             '42%',
            transform:       `translate(calc(-50% + ${Math.cos(angle) * radius}px), calc(-50% + ${Math.sin(angle) * radius}px))`,
          }}
        />
      );
    })}
  </>
);

// ─── Scene 1: Hook (local frames 0–149) ───────────────────────────────────────
const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // "GERMANY" scale: 2.0 → 1.0 with bouncy spring
  const scaleSpring = spring({ frame, fps, config: SPRING_BOUNCY });
  const textScale   = interpolate(scaleSpring, [0, 1], [2.0, 1.0]);

  // Letter-spacing for subtitle: 0 → 8px
  const subLetterSpacing = interpolate(frame, [80, 100], [0, 8], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Subtitle opacity
  const subOpacity = interpolate(frame, [70, 100], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Gold accent line
  const lineWidth = interpolate(frame, [20, 60], [0, 320], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Flag: scale 0.5 → 1.0 with spring (delayed 40 frames)
  const flagSpring = spring({ frame: Math.max(0, frame - 40), fps, config: SPRING_BOUNCY });
  const flagScale  = interpolate(flagSpring, [0, 1], [0.5, 1.0]);

  const glowOpacity = Math.sin(frame / 10) * 0.05 + 0.1;

  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      {/* Stadium footage background */}
      <AbsoluteFill>
        <Video
          src={staticFile('hook.mp4')}
          style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.3 }}
          muted
          loop
        />
      </AbsoluteFill>

      {/* "2026" watermark */}
      <div style={{
        position: 'absolute', fontSize: 600, fontWeight: 900,
        color: ACCENT_GOLD, opacity: 0.04,
        fontFamily: 'Arial Black, Impact, sans-serif',
        userSelect: 'none', letterSpacing: -20, lineHeight: 1,
      }}>
        2026
      </div>

      {/* Pulsing radial glow */}
      <div style={{
        position: 'absolute', width: 600, height: 300,
        borderRadius: '50%',
        background: `radial-gradient(ellipse, ${ACCENT_GOLD}, transparent 70%)`,
        opacity: glowOpacity,
        top: '35%',
      }} />

      {/* Particles radiating from centre */}
      <Particles frame={frame} />

      {/* GERMANY — letter stagger flash */}
      <div style={{
        transform:   `scale(${textScale})`,
        display:     'flex',
        fontFamily:  "'Oswald', 'Arial Narrow', Arial, sans-serif",
        fontWeight:  700,
        fontSize:    120,
        marginBottom: 16,
        zIndex:      2,
      }}>
        {'GERMANY'.split('').map((letter, i) => {
          const lf         = Math.max(0, frame - i * 3);
          const brightness = interpolate(lf, [0, 3, 8], [1, 3, 1], { extrapolateRight: 'clamp' });
          const lOpacity   = interpolate(lf, [0, 3], [0, 1], { extrapolateRight: 'clamp' });
          return (
            <span
              key={i}
              style={{
                color:          'white',
                filter:         `brightness(${brightness})`,
                opacity:        lOpacity,
                display:        'inline-block',
                letterSpacing:  8,
              }}
            >
              {letter}
            </span>
          );
        })}
      </div>

      {/* Animated gold line */}
      <div style={{
        width: lineWidth, height: 4,
        backgroundColor: ACCENT_GOLD, borderRadius: 2,
        zIndex: 2, marginBottom: 30,
      }} />

      {/* German flag — spring scale-in */}
      <div style={{
        transform:     `scale(${flagScale})`,
        display:       'flex',
        flexDirection: 'column',
        width:         280,
        borderRadius:  8,
        overflow:      'hidden',
        zIndex:        2,
        marginBottom:  24,
      }}>
        <div style={{ height: 60, backgroundColor: GERMANY_BLACK }} />
        <div style={{ height: 60, backgroundColor: GERMANY_RED   }} />
        <div style={{ height: 60, backgroundColor: GERMANY_GOLD  }} />
      </div>

      {/* FIFA WORLD CUP 2026 — letter-spacing reveal */}
      <div style={{
        opacity:        subOpacity,
        fontFamily:     "'Oswald', 'Arial Narrow', Arial, sans-serif",
        fontWeight:     400,
        fontSize:       28,
        color:          ACCENT_GOLD,
        letterSpacing:  subLetterSpacing,
        zIndex:         2,
      }}>
        FIFA WORLD CUP 2026
      </div>
    </AbsoluteFill>
  );
};

// ─── Scene 2: Player Card (local frames 0–449) ────────────────────────────────
const PlayerCardScene: React.FC = () => {
  const localFrame = useCurrentFrame();
  const { fps }    = useVideoConfig();

  // Card slides up + slight rotation
  const cardSpring   = spring({ frame: localFrame, fps, config: SPRING_BOUNCY });
  const cardY        = interpolate(cardSpring, [0, 1], [200, 0]);
  const cardRotation = interpolate(cardSpring, [0, 1], [-2,  0]);

  // Player circle fade
  const playerOpacity = interpolate(localFrame, [10, 40], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Name: "JAMAL" then "MUSIALA" 5 frames later
  const word1Spring = spring({ frame: localFrame,                fps, config: SPRING_BOUNCY });
  const word2Spring = spring({ frame: Math.max(0, localFrame - 5), fps, config: SPRING_BOUNCY });
  const word1Y = interpolate(word1Spring, [0, 1], [40, 0]);
  const word2Y = interpolate(word2Spring, [0, 1], [40, 0]);

  // MID pill slides from right (delayed 20f)
  const pillSpring = spring({ frame: Math.max(0, localFrame - 20), fps, config: SPRING_BOUNCY });
  const pillX      = interpolate(pillSpring, [0, 1], [100, 0]);

  // Stats — spring so they accelerate then ease (delayed 30f)
  const goalsSpring  = spring({ frame: Math.max(0, localFrame - 30), fps, config: SPRING_SMOOTH });
  const capsSpring   = spring({ frame: Math.max(0, localFrame - 30), fps, config: SPRING_SMOOTH });
  const clubGlsSpring = spring({ frame: Math.max(0, localFrame - 30), fps, config: SPRING_SMOOTH });
  const goals   = Math.round(interpolate(goalsSpring,   [0, 1], [0, 22]));
  const caps    = Math.round(interpolate(capsSpring,    [0, 1], [0, 54]));
  const clubGls = Math.round(interpolate(clubGlsSpring, [0, 1], [0, 18]));

  // Pulsing glow on stat numbers
  const statGlow = 10 + Math.sin(localFrame * 0.2) * 5;

  // Stat labels fade after count settles
  const labelsOpacity = interpolate(localFrame, [90, 110], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Divider draws across
  const dividerWidth = interpolate(localFrame, [60, 100], [0, 700], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Market value — typewriter effect
  const mvText      = '200M EUR';
  const charsVisible = Math.floor(interpolate(
    localFrame,
    [110, 110 + mvText.length * 3],
    [0, mvText.length],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  ));
  const cursor   = localFrame > 110 && charsVisible < mvText.length ? '|' : '';
  const displayMV = mvText.slice(0, charsVisible) + cursor;
  const mvOpacity = interpolate(localFrame, [108, 112], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: BG, alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        transform:       `translateY(${cardY}px) rotate(${cardRotation}deg)`,
        width:           800,
        height:          1100,
        backgroundColor: '#161B22',
        borderRadius:    24,
        border:          `2px solid ${ACCENT_GOLD}44`,
        position:        'relative',
        display:         'flex',
        flexDirection:   'column',
        alignItems:      'center',
        padding:         40,
        boxSizing:       'border-box',
        boxShadow:       `0 0 60px ${ACCENT_GOLD}22`,
      }}>
        {/* OVR ring */}
        <OVRCircle frame={localFrame} />

        {/* Player placeholder — gradient circle */}
        <div style={{
          width:           280,
          height:          280,
          borderRadius:    '50%',
          background:      `radial-gradient(circle at 40% 35%, #FF4444, ${GERMANY_BLACK} 80%)`,
          opacity:         playerOpacity,
          marginTop:       40,
          marginBottom:    30,
          border:          `4px solid ${GERMANY_GOLD}`,
          display:         'flex',
          alignItems:      'center',
          justifyContent:  'center',
        }}>
          <span style={{ fontSize: 80, color: 'white' }}>⚽</span>
        </div>

        {/* Divider top */}
        <div style={{ width: dividerWidth, height: 2, backgroundColor: ACCENT_GOLD, marginBottom: 20, borderRadius: 1 }} />

        {/* Name — word stagger */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          {[
            { text: 'JAMAL',   y: word1Y },
            { text: 'MUSIALA', y: word2Y },
          ].map(({ text, y }) => (
            <div key={text} style={{
              transform:   `translateY(${y}px)`,
              fontFamily:  "'Oswald', 'Arial Narrow', Arial, sans-serif",
              fontWeight:  700,
              fontSize:    48,
              color:       'white',
              letterSpacing: 3,
            }}>
              {text}
            </div>
          ))}
        </div>

        {/* MID pill */}
        <div style={{
          transform:    `translateX(${pillX}px)`,
          backgroundColor: GERMANY_RED,
          paddingLeft:  24, paddingRight: 24,
          paddingTop:    8, paddingBottom: 8,
          borderRadius: 50, marginBottom: 32,
        }}>
          <span style={{ color: 'white', fontWeight: 700, fontSize: 22, fontFamily: 'Arial, sans-serif', letterSpacing: 2 }}>
            MID
          </span>
        </div>

        {/* Stats */}
        <div style={{ display: 'flex', gap: 60, marginBottom: 24 }}>
          {[
            { label: 'GOALS',    value: goals,   color: GERMANY_GOLD },
            { label: 'CAPS',     value: caps,    color: GERMANY_RED  },
            { label: 'CLUB GLS', value: clubGls, color: GERMANY_RED  },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{
                fontSize:   52,
                fontWeight: 700,
                color,
                fontFamily: 'Arial Black, Arial, sans-serif',
                textShadow: `0 0 ${statGlow}px ${color}`,
              }}>
                {value}
              </div>
              <div style={{
                opacity:      labelsOpacity,
                fontSize:     16,
                color:        '#aaa',
                fontFamily:   'Arial, sans-serif',
                letterSpacing: 1,
                marginTop:    4,
              }}>
                {label}
              </div>
            </div>
          ))}
        </div>

        {/* Divider bottom */}
        <div style={{ width: dividerWidth, height: 2, backgroundColor: ACCENT_GOLD, marginBottom: 20, borderRadius: 1 }} />

        {/* Market value — typewriter */}
        <div style={{
          opacity:       mvOpacity,
          fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
          fontSize:      36,
          color:         GERMANY_GOLD,
          fontWeight:    700,
          letterSpacing: 2,
        }}>
          💰 {displayMV}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Scene 3: CTA (local frames 0–299) ────────────────────────────────────────
const CTAScene: React.FC = () => {
  const localFrame = useCurrentFrame();
  const { fps }    = useVideoConfig();

  // "CAN GERMANY" scale bounce
  const line1Spring = spring({ frame: localFrame, fps, config: SPRING_BOUNCY });
  const line1Scale  = interpolate(line1Spring, [0, 1], [0.5, 1.0]);

  // "WIN IT ALL?" — each word 5f staggered slide-up
  const winWords = [
    { text: 'WIN',  delay: 10 },
    { text: 'IT',   delay: 15 },
    { text: 'ALL?', delay: 20 },
  ];
  const winAnimations = winWords.map(({ text, delay }) => {
    const s = spring({ frame: Math.max(0, localFrame - delay), fps, config: SPRING_BOUNCY });
    return { text, y: interpolate(s, [0, 1], [60, 0]) };
  });

  // Center-out gold divider: two halves grow outward
  const halfWidth = interpolate(localFrame, [30, 60], [0, 100], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // "COMMENT BELOW" pulse
  const commentScale = 1 + Math.sin(localFrame * 0.15) * 0.025;

  // Flags: fall from above with high-damping spring (gravity feel), 8f stagger
  const FLAGS = ['🇩🇪', '🇫🇷', '🇧🇷', '🇦🇷', '🇵🇹'];
  const flagAnims = FLAGS.map((flag, i) => {
    const fFrame  = Math.max(0, localFrame - i * 8 - 60);
    const fSpring = spring({ frame: fFrame, fps, config: { damping: 20, stiffness: 300 } });
    return {
      flag,
      y:       interpolate(fSpring, [0, 1], [-200, 0]),
      opacity: interpolate(fFrame, [0, 5], [0, 1], { extrapolateRight: 'clamp' }),
    };
  });

  // Final zoom-out (last ~20 frames of scene)
  const zoomOut = interpolate(localFrame, [270, 290], [1.0, 0.97], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
      {/* Celebration footage background */}
      <AbsoluteFill>
        <Video
          src={staticFile('cta.mp4')}
          style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.3 }}
          muted
          loop
        />
      </AbsoluteFill>

      {/* "?" watermark */}
      <div style={{
        position:   'absolute',
        fontSize:    500,
        fontWeight:  900,
        color:       ACCENT_GOLD,
        opacity:     0.04,
        fontFamily:  'Arial Black, Impact, sans-serif',
        userSelect:  'none',
        lineHeight:  1,
      }}>
        ?
      </div>

      {/* Main content — scales out at the end */}
      <div style={{
        transform:     `scale(${zoomOut})`,
        display:       'flex',
        flexDirection: 'column',
        alignItems:    'center',
        zIndex:        2,
      }}>
        {/* CAN GERMANY — scale bounce */}
        <div style={{
          transform:     `scale(${line1Scale})`,
          fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
          fontWeight:    700,
          fontSize:      80,
          color:         'white',
          textAlign:     'center',
          letterSpacing: 4,
          marginBottom:  8,
        }}>
          CAN GERMANY
        </div>

        {/* WIN IT ALL? — word stagger slide-up */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 36 }}>
          {winAnimations.map(({ text, y }) => (
            <div key={text} style={{
              transform:     `translateY(${y}px)`,
              fontFamily:    "'Oswald', 'Arial Narrow', Arial, sans-serif",
              fontWeight:    700,
              fontSize:      80,
              color:         GERMANY_GOLD,
              letterSpacing: 4,
            }}>
              {text}
            </div>
          ))}
        </div>

        {/* Gold divider — grows from centre outward */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 60 }}>
          <div style={{ width: halfWidth, height: 4, backgroundColor: ACCENT_GOLD, borderRadius: '4px 0 0 4px' }} />
          <div style={{ width: halfWidth, height: 4, backgroundColor: ACCENT_GOLD, borderRadius: '0 4px 4px 0' }} />
        </div>

        {/* COMMENT BELOW — pulsing scale */}
        <div style={{
          transform:   `scale(${commentScale})`,
          fontFamily:  'Arial Black, Arial, sans-serif',
          fontWeight:  700,
          fontSize:    52,
          color:       'white',
          textAlign:   'center',
          marginBottom: 48,
        }}>
          COMMENT BELOW 👇
        </div>

        {/* 5 flag emojis — fall from top with gravity, 8f stagger */}
        <div style={{ display: 'flex', gap: 24, position: 'relative' }}>
          {flagAnims.map(({ flag, y, opacity }) => (
            <span key={flag} style={{
              fontSize:  64,
              transform: `translateY(${y}px)`,
              opacity,
              display:   'inline-block',
            }}>
              {flag}
            </span>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Main Composition ──────────────────────────────────────────────────────────
export const WorldCupShort: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: BG }}>
    {/*
      AUDIO NOTE:
      - BGM at 0.25 (reduced from v1's 0.3 to leave room for SFX)
      - SFX HOOK POINT — frame 0: whoosh/impact on GERMANY entrance
        Would be: <Audio src={staticFile('whoosh.mp3')} />
      - SFX HOOK POINT — frame 150: card slam sound on player card entrance
        Would be: inside PlayerCardScene Sequence
    */}
    <Audio src={staticFile('football_hype.mp3')} volume={0.25} />

    {/* Scene 1 — Hook: 0–149 (5s) */}
    <Sequence durationInFrames={150}>
      <HookScene />
    </Sequence>

    {/* Scene 2 — Player Card: 150–599 (15s) */}
    <Sequence from={150} durationInFrames={450}>
      <PlayerCardScene />
    </Sequence>

    {/* Scene 3 — CTA: 600–899 (10s) */}
    <Sequence from={600} durationInFrames={300}>
      <CTAScene />
    </Sequence>
  </AbsoluteFill>
);
