import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  interpolateColors,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import { loadFont } from '@remotion/google-fonts/LilitaOne';

const { fontFamily } = loadFont();

// ── Layout constants (1080 × 1920) ────────────────────────────────────────────
const W           = 1080;
const H           = 1920;
const IMAGE_H     = Math.round(H * 0.35);  // 672 — top 35%
const QUESTION_Y  = IMAGE_H;               // 672
const QUESTION_H  = Math.round(H * 0.15);  // 288 — middle 15%
const OPTIONS_Y   = QUESTION_Y + QUESTION_H; // 960 — bottom 50%

const REVEAL_FRAME = 300;
const KEYS = ['A', 'B', 'C'] as const;

// ── Helpers ───────────────────────────────────────────────────────────────────
const hexToRgba = (hex: string, a: number) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
};

const darkenHex = (hex: string, amt: number) => {
  const r = Math.max(0, parseInt(hex.slice(1, 3), 16) - amt);
  const g = Math.max(0, parseInt(hex.slice(3, 5), 16) - amt);
  const b = Math.max(0, parseInt(hex.slice(5, 7), 16) - amt);
  return `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`;
};

const buildTickFrames = () => [
  90, 120, 150, 180,
  ...Array.from({ length: Math.floor((REVEAL_FRAME - 210) / 15) + 1 }, (_, i) => 210 + i * 15)
    .filter(f => f <= REVEAL_FRAME),
];
const TICK_FRAMES = buildTickFrames();

// ── Props ─────────────────────────────────────────────────────────────────────
export interface QuizShortProps {
  questionData: {
    id: number;
    question: string;
    options: { A: string; B: string; C: string };
    correct: string;
    explanation: string;
    themeColor: string;
  };
}

// ── Component ─────────────────────────────────────────────────────────────────
export const QuizShortCard: React.FC<QuizShortProps> = ({ questionData }) => {
  const { id, question, options, correct, explanation, themeColor } = questionData;
  const correctAnswer = correct as 'A' | 'B' | 'C';

  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isRevealed = frame >= REVEAL_FRAME;

  // ── Entrance ──────────────────────────────────────────────────────────────
  const imgO  = interpolate(frame, [0, 25], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const qO    = interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const qY    = interpolate(frame, [0, 20], [-30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const scoreO = interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // FIX 1: Start well past canvas right edge so no card is visible at frame 0.
  // Container has left:32, so card left-edge on screen = 32 + translateX.
  // W+200 = 1280 → screen x = 1312 → completely off-screen at frame 0 for all options.
  // Opacity stays at 0 until startFrame so there is no pre-frame flash.
  const slideX = (s: number) =>
    interpolate(frame, [s, s + 22], [W + 200, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const slideO = (s: number) =>
    interpolate(frame, [s, s + 22], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const optEntrance = {
    A: { x: slideX(5),  o: slideO(5)  },
    B: { x: slideX(10), o: slideO(10) },
    C: { x: slideX(15), o: slideO(15) },
  } as const;

  // ── Reveal ────────────────────────────────────────────────────────────────
  const wrongFade = interpolate(
    frame, [REVEAL_FRAME, REVEAL_FRAME + 18], [1, 0.45],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );
  const correctScale = 1 + spring({
    frame: Math.max(0, frame - REVEAL_FRAME), fps,
    config: { stiffness: 180, damping: 14 },
  }) * 0.04;

  const explainO = interpolate(
    frame, [REVEAL_FRAME + 15, REVEAL_FRAME + 35], [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  // ── Timer ─────────────────────────────────────────────────────────────────
  const elapsed    = interpolate(frame, [0, REVEAL_FRAME], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const timerWidth = interpolate(elapsed, [0, 1], [100, 0]);
  const timerColor = interpolateColors(elapsed, [0, 0.5, 0.8, 1], ['#22CC22', '#FF8C00', '#FF0000', '#FF0000']);
  const glowHex    = elapsed < 0.5 ? '#22CC22' : elapsed < 0.8 ? '#FF8C00' : '#FF0000';

  // ── Option state ──────────────────────────────────────────────────────────
  const getOpt = (key: typeof KEYS[number]) => {
    if (!isRevealed) return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#FF8C00,#FF6B00)',
      glow: '0 6px 24px rgba(0,0,0,0.28)', textColor: '#111111',
      opacity: 1, check: false, cross: false,
    };
    if (key === correctAnswer) return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#22CC22,#009A00)',
      glow: '0 0 0 5px #22CC22, 0 0 32px rgba(34,204,34,0.55)', textColor: '#111111',
      opacity: 1, check: true, cross: false,
    };
    return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#999,#666)',
      glow: '0 4px 12px rgba(0,0,0,0.15)', textColor: '#BBBBBB',
      opacity: wrongFade, check: false, cross: true,
    };
  };

  return (
    <AbsoluteFill style={{ backgroundColor: themeColor, fontFamily, overflow: 'hidden' }}>

      {/* ═══════════════════════════════════
          TOP 35% — IMAGE PANEL (0 → 672px)
          FIX 2: zIndex 1 — always rendered, never obscured by explanation
      ═══════════════════════════════════ */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: W, height: IMAGE_H, opacity: imgO, zIndex: 1 }}>
        <Img
          src={staticFile(`quiz_images/q${id}.jpg`)}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        {/* Gradient bleed into theme color */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: 180,
          background: `linear-gradient(to bottom, transparent, ${themeColor})`,
        }} />
      </div>

      {/* Score counter — top-right overlay on image */}
      <div style={{
        position: 'absolute', top: 40, right: 40,
        opacity: scoreO,
        background: 'rgba(0,0,0,0.60)',
        borderRadius: 50, padding: '12px 32px',
        border: `3px solid rgba(255,255,255,0.5)`,
      }}>
        <span style={{ fontFamily, fontSize: 40, fontWeight: 900, color: '#FFFFFF', lineHeight: 1 }}>
          Q{id} / 10
        </span>
      </div>

      {/* ═══════════════════════════════════
          MIDDLE 15% — QUESTION (672 → 960px)
          FIX 2: zIndex 2 — always rendered, persists through frame 750
      ═══════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: QUESTION_Y, left: 0, width: W, height: QUESTION_H, zIndex: 2,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '0 40px',
        transform: `translateY(${qY}px)`, opacity: qO,
      }}>
        <span style={{
          fontFamily, fontSize: 58, fontWeight: 900,
          color: '#FFFFFF', textTransform: 'uppercase',
          lineHeight: 1.1, textAlign: 'center', display: 'block',
          WebkitTextStroke: '3px #000000',
          textShadow: '2px 2px 0 #000000',
        }}>
          {question}
        </span>
      </div>

      {/* Timer bar — pinned just above options */}
      <div style={{
        position: 'absolute', top: OPTIONS_Y - 30, left: 56, right: 56, height: 44,
        borderRadius: 22,
        backgroundColor: 'rgba(255,255,255,0.25)',
        border: '3px solid rgba(255,255,255,0.45)',
        boxShadow: `0 0 18px ${hexToRgba(glowHex, 0.55)}`,
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: `${timerWidth}%`, backgroundColor: timerColor, borderRadius: 22,
        }}>
          <div style={{
            position: 'absolute', inset: 0,
            background: 'repeating-linear-gradient(60deg,transparent,transparent 10px,rgba(255,255,255,0.28) 10px,rgba(255,255,255,0.28) 16px)',
          }} />
        </div>
      </div>

      {/* ═══════════════════════════════════
          BOTTOM 50% — OPTIONS (960px → 1920px)
      ═══════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: OPTIONS_Y + 28, left: 32, right: 32, bottom: 32,
        display: 'flex', flexDirection: 'column', gap: 16,
        overflow: 'hidden',  // FIX 1: clips cards that are still translating off-screen right
        zIndex: 3,
      }}>
        {KEYS.map((key) => {
          const st  = getOpt(key);
          const en  = optEntrance[key];
          const scl = key === correctAnswer && isRevealed ? correctScale : 1;
          return (
            <div key={key} style={{
              flex: 1,
              transform: `translateX(${en.x}px) scaleX(${scl})`,
              opacity: st.opacity * en.o,
              transformOrigin: 'left center',
            }}>
              <div style={{
                height: '100%', backgroundColor: st.bg,
                borderRadius: 20, boxShadow: st.glow,
                display: 'flex', alignItems: 'center',
                padding: '0 32px', gap: 28, overflow: 'hidden',
              }}>
                {/* Letter badge */}
                <div style={{
                  width: 100, height: 100, borderRadius: 50, flexShrink: 0,
                  background: st.badgeGrad,
                  border: '4px solid rgba(255,255,255,0.9)',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.40)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span style={{ fontFamily, fontSize: 58, fontWeight: 900, color: '#FFFFFF', lineHeight: 1 }}>
                    {key}
                  </span>
                </div>

                {/* Option text */}
                <span style={{
                  fontFamily, fontSize: 58, fontWeight: 900,
                  color: st.textColor, textTransform: 'uppercase',
                  flex: 1, lineHeight: 1.1,
                }}>
                  {options[key]}
                </span>

                {st.check && (
                  <span style={{ fontSize: 64, color: '#22CC22', lineHeight: 1, textShadow: '0 0 14px #22CC22', flexShrink: 0 }}>✓</span>
                )}
                {st.cross && (
                  <span style={{ fontSize: 64, color: '#FF3333', lineHeight: 1, textShadow: '0 0 14px #FF3333', flexShrink: 0 }}>✗</span>
                )}
              </div>
            </div>
          );
        })}

      </div>

      {/* ═══════════════════════════════════
          FIX 3: EXPLANATION — sibling of options div, NOT inside flex container.
          Positioned explicitly: top=OPTIONS_Y → bottom=0 (covers bottom 50% only).
          zIndex 10 sits above options (zIndex 3) but image+question (zIndex 1,2) are untouched.
      ═══════════════════════════════════ */}
      {isRevealed && (
        <div style={{
          position: 'absolute', top: OPTIONS_Y, left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '0 32px',
          opacity: explainO,
          zIndex: 10,
          pointerEvents: 'none',
        }}>
          <div style={{
            backgroundColor: 'rgba(0,0,0,0.85)',
            borderRadius: 28, padding: '40px 48px',
            border: `4px solid ${themeColor}`,
            boxShadow: `0 0 40px ${hexToRgba(themeColor, 0.5)}`,
            width: '100%',
          }}>
            <div style={{
              fontFamily, fontSize: 34, fontWeight: 900,
              color: '#FFD700', textAlign: 'center',
              letterSpacing: 2, textTransform: 'uppercase',
              marginBottom: 20,
            }}>
              💡 ANSWER REVEALED
            </div>
            <div style={{
              fontFamily, fontSize: 52, fontWeight: 900,
              color: '#FFFFFF', textAlign: 'center', lineHeight: 1.25,
            }}>
              {explanation}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════
          AUDIO
      ═══════════════════════════════════ */}
      {TICK_FRAMES.map((f) => (
        <Sequence key={f} from={f} durationInFrames={30}>
          <Audio src={staticFile('sfx/tick.wav')} volume={0.5} />
        </Sequence>
      ))}
      <Sequence from={REVEAL_FRAME} durationInFrames={90}>
        <Audio src={staticFile('sfx/correct.wav')} volume={0.9} />
      </Sequence>
      <Audio src={staticFile(`voice/q${id}.mp3`)} startFrom={30} volume={1.0} />

    </AbsoluteFill>
  );
};
