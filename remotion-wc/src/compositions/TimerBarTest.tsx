import React, { useEffect, useState } from 'react';
import { AbsoluteFill, continueRender, delayRender, Img } from 'remotion';
import { TimerBar } from '../components/TimerBar';

const QUESTION = 'WHICH COUNTRY HAS WON THE MOST WORLD CUPS?';
const OPTIONS = [
  { label: 'A', text: 'Brazil' },
  { label: 'B', text: 'Germany' },
  { label: 'C', text: 'Italy' },
];
const BG_URL =
  'https://images.pexels.com/photos/46798/the-ball-stadion-football-the-pitch-46798.jpeg';

export const TimerBarTest: React.FC = () => {
  const [handle] = useState(() => delayRender('Loading Oswald font'));

  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href =
      'https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&display=swap';
    document.head.appendChild(link);
    document.fonts.ready.then(() => continueRender(handle));
  }, [handle]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#0D0D14',
        fontFamily: "'Oswald', 'Impact', 'Arial Black', sans-serif",
      }}
    >
      {/* --- Background image at 25% opacity --- */}
      <Img
        src={BG_URL}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          opacity: 0.25,
        }}
      />

      {/* --- Vignette overlay --- */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            'radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.7) 100%)',
        }}
      />

      {/* ── TOP SECTION (y 0→280) — question number pill ── */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 280,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          paddingTop: 60,
        }}
      >
        <div
          style={{
            backgroundColor: '#D4A843',
            color: '#000000',
            fontWeight: 700,
            fontSize: 28,
            fontFamily: 'inherit',
            padding: '10px 40px',
            borderRadius: 999,
            letterSpacing: 2,
          }}
        >
          Q 1 / 10
        </div>
      </div>

      {/* ── MIDDLE SECTION (y 280→680) — question text ── */}
      <div
        style={{
          position: 'absolute',
          top: 280,
          left: '50%',
          transform: 'translateX(-50%)',
          width: 1400,
          height: 400,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontSize: 56,
            fontWeight: 700,
            color: '#FFFFFF',
            textTransform: 'uppercase',
            lineHeight: 1.3,
            letterSpacing: 2,
            fontFamily: 'inherit',
          }}
        >
          {QUESTION}
        </div>
      </div>

      {/* ── BOTTOM SECTION (y 680→980) — answer options ── */}
      <div
        style={{
          position: 'absolute',
          top: 680,
          left: 0,
          right: 0,
          height: 300,
          display: 'flex',
          flexDirection: 'row',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 40,
        }}
      >
        {OPTIONS.map(({ label, text }) => (
          <div
            key={label}
            style={{
              width: 380,
              height: 120,
              backgroundColor: 'rgba(255,255,255,0.08)',
              border: '2px solid rgba(255,255,255,0.15)',
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'row',
              alignItems: 'center',
              paddingLeft: 24,
              paddingRight: 24,
              gap: 20,
              flexShrink: 0,
            }}
          >
            {/* Gold letter badge */}
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#D4A843',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                fontSize: 20,
                fontWeight: 700,
                color: '#000000',
                fontFamily: 'inherit',
              }}
            >
              {label}
            </div>
            {/* Option label */}
            <span
              style={{
                fontSize: 40,
                fontWeight: 600,
                color: '#FFFFFF',
                fontFamily: 'inherit',
              }}
            >
              {text}
            </span>
          </div>
        ))}
      </div>

      {/* ── TIMER ZONE (y 980→1080) — bar flush to bottom ── */}
      <div
        style={{
          position: 'absolute',
          top: 980,
          left: 0,
          right: 0,
          height: 100,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
        }}
      >
        <TimerBar
          durationFrames={300}
          startFrame={0}
          height={20}
          borderRadius={6}
          fps={30}
        />
      </div>
    </AbsoluteFill>
  );
};
