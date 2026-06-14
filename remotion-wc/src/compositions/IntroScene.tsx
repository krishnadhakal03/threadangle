import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/LilitaOne';

const { fontFamily } = loadFont();

// ── Shared tile data ──────────────────────────────────────────────────────────

const TILE_ICONS = ['⚽', '🧠', '💡', '❓'];
const TILE_COLS  = 14;
const TILE_ROWS  = 10;
const TILE_GAP_X = 152;
const TILE_GAP_Y = 118;

const BG_TILES = Array.from({ length: TILE_COLS * TILE_ROWS }, (_, i) => {
  const row = Math.floor(i / TILE_COLS);
  const col = i % TILE_COLS;
  return {
    x: col * TILE_GAP_X + (row % 2 === 1 ? TILE_GAP_X / 2 : 0),
    y: row * TILE_GAP_Y - 10,
    icon: TILE_ICONS[i % 4],
  };
});

// ── Component ─────────────────────────────────────────────────────────────────

export const IntroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lineSpring = (startFrame: number) =>
    spring({ frame: Math.max(0, frame - startFrame), fps, config: { stiffness: 200, damping: 22 } });

  const lineY = (startFrame: number) => {
    const s = lineSpring(startFrame);
    return interpolate(s, [0, 1], [80, 0]);
  };
  const lineO = (startFrame: number) => {
    return interpolate(frame, [startFrame, startFrame + 12], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  };

  // Subtitle fade-in after lines
  const subO = interpolate(frame, [50, 68], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Pulse on the football emoji
  const pulse = 1 + spring({ frame, fps, config: { stiffness: 60, damping: 8 } }) * 0.08;

  return (
    <AbsoluteFill style={{ backgroundColor: '#9B59B6', fontFamily, overflow: 'hidden' }}>

      {/* Tiled emoji pattern — 12% opacity */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.12, pointerEvents: 'none' }}>
        {BG_TILES.map((t, i) => (
          <span key={i} style={{ position: 'absolute', left: t.x, top: t.y, fontSize: 58, lineHeight: 1 }}>
            {t.icon}
          </span>
        ))}
      </div>

      {/* Dark overlay for readability */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.30)' }} />

      {/* Center content */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 28,
      }}>

        {/* Football emoji — pulsing */}
        <div style={{ transform: `scale(${pulse})`, transformOrigin: 'center', opacity: lineO(0) }}>
          <span style={{ fontSize: 130, lineHeight: 1 }}>⚽</span>
        </div>

        {/* Line 1 — main title */}
        <div style={{
          transform: `translateY(${lineY(8)}px)`,
          opacity: lineO(8),
        }}>
          <span style={{
            fontFamily, fontSize: 116, fontWeight: 900,
            color: '#FFD700', textTransform: 'uppercase',
            lineHeight: 1, display: 'block', textAlign: 'center',
            WebkitTextStroke: '5px #000000',
            textShadow: '4px 4px 0 #000000, -2px -2px 0 #000000',
            letterSpacing: 2,
          }}>
            FOOTBALL
          </span>
          <span style={{
            fontFamily, fontSize: 116, fontWeight: 900,
            color: '#FFD700', textTransform: 'uppercase',
            lineHeight: 1, display: 'block', textAlign: 'center',
            WebkitTextStroke: '5px #000000',
            textShadow: '4px 4px 0 #000000, -2px -2px 0 #000000',
            letterSpacing: 2,
          }}>
            WORLD CUP QUIZ
          </span>
        </div>

        {/* Line 2 — 10 questions */}
        <div style={{
          transform: `translateY(${lineY(22)}px)`,
          opacity: lineO(22),
        }}>
          <span style={{
            fontFamily, fontSize: 80, fontWeight: 900,
            color: '#FFFFFF', textTransform: 'uppercase',
            lineHeight: 1, display: 'block', textAlign: 'center',
            WebkitTextStroke: '3px #000000',
            textShadow: '2px 2px 0 #000000',
          }}>
            ❓ 10 QUESTIONS ❓
          </span>
        </div>

        {/* Line 3 — 10 seconds */}
        <div style={{
          transform: `translateY(${lineY(36)}px)`,
          opacity: lineO(36),
        }}>
          <span style={{
            fontFamily, fontSize: 80, fontWeight: 900,
            color: '#FFFFFF', textTransform: 'uppercase',
            lineHeight: 1, display: 'block', textAlign: 'center',
            WebkitTextStroke: '3px #000000',
            textShadow: '2px 2px 0 #000000',
          }}>
            ⏰ 10 SECONDS EACH ⏰
          </span>
        </div>

        {/* Subtitle */}
        <div style={{ opacity: subO, marginTop: 16 }}>
          <span style={{
            fontFamily, fontSize: 36, fontWeight: 700,
            color: 'rgba(255,255,255,0.75)',
            textTransform: 'uppercase', letterSpacing: 6,
            textAlign: 'center', display: 'block',
          }}>
            AI SIDEKICK SPORTS
          </span>
        </div>

      </div>
    </AbsoluteFill>
  );
};
