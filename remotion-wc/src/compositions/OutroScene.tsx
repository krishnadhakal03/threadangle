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

// ── Placeholder thumbnail data ────────────────────────────────────────────────

const THUMBNAILS = [
  { label: 'Top 10 World Cup Goals', color: '#E74C3C' },
  { label: 'EURO 2024 Quiz', color: '#2980B9' },
];

// ── Component ─────────────────────────────────────────────────────────────────

export const OutroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const spr = (startF: number, stiffness = 180, damping = 18) =>
    spring({ frame: Math.max(0, frame - startF), fps, config: { stiffness, damping } });

  const fromBelow = (startF: number) => {
    const s = spr(startF);
    return interpolate(s, [0, 1], [60, 0]);
  };
  const fadeIn = (startF: number) =>
    interpolate(frame, [startF, startF + 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // "WATCH NEXT" banner entrance — fast fade so frame 0 is not empty
  const bannerY = fromBelow(0);
  const bannerO = interpolate(frame, [0, 8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // Thumbnails stagger in
  const thumb0Y = fromBelow(12);
  const thumb0O = fadeIn(12);
  const thumb1Y = fromBelow(22);
  const thumb1O = fadeIn(22);

  // Channel logo
  const logoScale = 1 + spr(35) * 0.05;
  const logoO = fadeIn(35);

  // Subscribe CTA
  const ctaO = fadeIn(50);
  const ctaPulse = 1 + Math.sin(frame * 0.12) * 0.04;

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

      {/* Dark overlay */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.25)' }} />

      {/* ══════════════════════
          WATCH NEXT banner
      ══════════════════════ */}
      <div style={{
        position: 'absolute', top: 40, left: 0, right: 0,
        display: 'flex', justifyContent: 'center',
        transform: `translateY(${bannerY}px)`, opacity: bannerO,
      }}>
        <div style={{
          background: 'linear-gradient(135deg,#FF8C00,#FF6B00)',
          borderRadius: 50, padding: '14px 72px',
          boxShadow: '0 6px 28px rgba(0,0,0,0.5)',
          border: '4px solid rgba(255,255,255,0.4)',
        }}>
          <span style={{
            fontFamily, fontSize: 56, fontWeight: 900,
            color: '#FFFFFF', textTransform: 'uppercase',
            letterSpacing: 4,
            WebkitTextStroke: '2px rgba(0,0,0,0.3)',
          }}>
            WATCH NEXT
          </span>
        </div>
      </div>

      {/* ══════════════════════
          THUMBNAIL CARDS
      ══════════════════════ */}
      <div style={{
        position: 'absolute', top: 180, left: 0, right: 0,
        display: 'flex', justifyContent: 'center', gap: 48,
      }}>
        {THUMBNAILS.map((th, idx) => {
          const tY = idx === 0 ? thumb0Y : thumb1Y;
          const tO = idx === 0 ? thumb0O : thumb1O;
          return (
            <div key={idx} style={{
              width: 530, height: 320,
              transform: `translateY(${tY}px)`, opacity: tO,
            }}>
              <div style={{
                width: '100%', height: '100%',
                backgroundColor: th.color,
                borderRadius: 20,
                border: '6px solid #FFFFFF',
                boxShadow: '0 8px 32px rgba(0,0,0,0.55)',
                overflow: 'hidden',
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                position: 'relative',
              }}>
                {/* Placeholder content */}
                <span style={{ fontSize: 80, lineHeight: 1 }}>⚽</span>
                {/* Title overlay */}
                <div style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0,
                  background: 'rgba(0,0,0,0.70)',
                  padding: '14px 20px',
                }}>
                  <span style={{
                    fontFamily, fontSize: 30, fontWeight: 900,
                    color: '#FFFFFF', textTransform: 'uppercase',
                    lineHeight: 1.15, display: 'block', textAlign: 'center',
                  }}>
                    {th.label}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ══════════════════════
          CHANNEL LOGO
      ══════════════════════ */}
      <div style={{
        position: 'absolute', bottom: 190, left: 0, right: 0,
        display: 'flex', justifyContent: 'center',
        transform: `scale(${logoScale})`, opacity: logoO,
        transformOrigin: 'center bottom',
      }}>
        <div style={{
          width: 160, height: 160, borderRadius: 80,
          border: '8px solid #FFFFFF',
          background: 'linear-gradient(135deg,#2C3E50,#1A252F)',
          boxShadow: '0 6px 28px rgba(0,0,0,0.6)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 4,
        }}>
          <span style={{ fontSize: 52, lineHeight: 1 }}>⚽</span>
          <span style={{ fontFamily, fontSize: 16, fontWeight: 900, color: '#FFD700', letterSpacing: 1 }}>
            AI SIDEKICK
          </span>
        </div>
      </div>

      {/* ══════════════════════
          SUBSCRIBE CTA
      ══════════════════════ */}
      <div style={{
        position: 'absolute', bottom: 50, left: 0, right: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
        opacity: ctaO,
        transform: `scale(${ctaPulse})`,
        transformOrigin: 'center bottom',
      }}>
        <div style={{
          background: '#FF0000',
          borderRadius: 50, padding: '16px 72px',
          boxShadow: '0 6px 28px rgba(255,0,0,0.5)',
          border: '4px solid rgba(255,255,255,0.3)',
        }}>
          <span style={{
            fontFamily, fontSize: 48, fontWeight: 900,
            color: '#FFFFFF', textTransform: 'uppercase', letterSpacing: 3,
          }}>
            🔔 SUBSCRIBE NOW
          </span>
        </div>
        <span style={{
          fontFamily, fontSize: 28, fontWeight: 700,
          color: 'rgba(255,255,255,0.80)', letterSpacing: 4, textTransform: 'uppercase',
        }}>
          NEW QUIZ EVERY WEEK
        </span>
      </div>

    </AbsoluteFill>
  );
};
