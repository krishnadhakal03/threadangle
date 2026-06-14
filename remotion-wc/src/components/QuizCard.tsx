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

// ── Tile background (static, computed once) ───────────────────────────────────

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

// ── Helpers ───────────────────────────────────────────────────────────────────

const hexToRgba = (hex: string, a: number): string => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
};

const darkenHex = (hex: string, amount: number): string => {
  const r = Math.max(0, parseInt(hex.slice(1, 3), 16) - amount);
  const g = Math.max(0, parseInt(hex.slice(3, 5), 16) - amount);
  const b = Math.max(0, parseInt(hex.slice(5, 7), 16) - amount);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
};

// ── Props ─────────────────────────────────────────────────────────────────────

export interface QuizCardProps {
  questionNumber: number;
  totalQuestions: number;
  question: string;
  options: { A: string; B: string; C: string };
  correctAnswer: 'A' | 'B' | 'C';
  explanation: string;
  imageUrl: string;
  themeColor: string;
  revealFrame: number;
  totalFrames: number;
  voiceUrl?: string;
}

// ── Tick schedule ─────────────────────────────────────────────────────────────
// Every 30f from 90→180, then every 15f from 210→revealFrame

const buildTickFrames = (revealFrame: number): number[] => [
  90, 120, 150, 180,
  ...Array.from(
    { length: Math.floor((revealFrame - 210) / 15) + 1 },
    (_, i) => 210 + i * 15,
  ).filter((f) => f <= revealFrame),
];

// ── Engagement prompts ────────────────────────────────────────────────────────

const PROMPT_MAP: Record<number, string> = {
  3: 'Got 3 RIGHT? 👍 HIT LIKE!',
  6: 'Comment your SCORE below! 💬',
  9: 'SUBSCRIBE for more! 🔔',
};

// ── Component ─────────────────────────────────────────────────────────────────

const KEYS = ['A', 'B', 'C'] as const;
const OPTIONS_TOP = 175;
const OPTION_H    = 154;
const OPTION_GAP  = 18;

export const QuizCard: React.FC<QuizCardProps> = ({
  questionNumber,
  totalQuestions,
  question,
  options,
  correctAnswer,
  imageUrl,
  themeColor,
  revealFrame,
  voiceUrl,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // ── Entrance: question text ───────────────────────────────────────────────
  const qO = interpolate(frame, [0, 20],   [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const qY = interpolate(frame, [0, 20], [-30, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // ── Entrance: left image ──────────────────────────────────────────────────
  const imgO = interpolate(frame, [0, 25], [0, 1],      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const imgS = interpolate(frame, [0, 25], [0.93, 1.0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // ── Entrance: options (A→10f, B→20f, C→30f) ──────────────────────────────
  const optX = (s: number) =>
    interpolate(frame, [s, s + 22], [-100, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const optO = (s: number) =>
    interpolate(frame, [s, s + 22], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const optEntrance = {
    A: { x: optX(5),  o: optO(5)  },
    B: { x: optX(10), o: optO(10) },
    C: { x: optX(15), o: optO(15) },
  } as const;

  // ── Reveal ────────────────────────────────────────────────────────────────
  const isRevealed = frame >= revealFrame;

  const flashO = interpolate(
    frame,
    [revealFrame, revealFrame + 1, revealFrame + 4],
    [0.35, 0.35, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  const wrongFade = interpolate(
    frame,
    [revealFrame, revealFrame + 18],
    [1, 0.55],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' },
  );

  const correctSpring = spring({
    frame: Math.max(0, frame - revealFrame),
    fps,
    config: { stiffness: 180, damping: 14 },
  });
  const correctScale = 1 + correctSpring * 0.04;

  // ── Timer ─────────────────────────────────────────────────────────────────
  const elapsed     = interpolate(frame, [0, revealFrame], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const timerWidth  = interpolate(elapsed, [0, 1], [100, 0]);
  const timerColor  = interpolateColors(elapsed, [0, 0.5, 0.8, 1], ['#22CC22', '#FF8C00', '#FF0000', '#FF0000']);
  const glowHex     = elapsed < 0.5 ? '#22CC22' : elapsed < 0.8 ? '#FF8C00' : '#FF0000';

  // ── Engagement prompt ─────────────────────────────────────────────────────
  const promptText = PROMPT_MAP[questionNumber];
  const promptSpr  = spring({ frame: Math.max(0, frame - revealFrame), fps, config: { stiffness: 120, damping: 14 } });
  const promptY    = interpolate(promptSpr, [0, 1], [120, 0]);

  // ── Per-option visual state ───────────────────────────────────────────────
  const getOpt = (key: typeof KEYS[number]) => {
    if (!isRevealed) return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#FF8C00,#FF6B00)',
      glow: '0 6px 24px rgba(0,0,0,0.30)',
      textColor: '#111111', opacity: 1, check: false, cross: false,
    };
    if (key === correctAnswer) return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#22CC22,#009A00)',
      glow: '0 0 0 5px #22CC22, 0 0 32px rgba(34,204,34,0.55)',
      textColor: '#111111', opacity: 1, check: true, cross: false,
    };
    return {
      bg: '#FFFFFF', badgeGrad: 'linear-gradient(135deg,#999,#666)',
      glow: '0 4px 12px rgba(0,0,0,0.15)',
      textColor: '#999999', opacity: wrongFade, check: false, cross: true,
    };
  };

  const tickFrames = buildTickFrames(revealFrame);

  return (
    <AbsoluteFill style={{ backgroundColor: themeColor, fontFamily, overflow: 'hidden' }}>

      {/* Tiled emoji background — 12% opacity */}
      <div style={{ position: 'absolute', inset: 0, opacity: 0.12, pointerEvents: 'none' }}>
        {BG_TILES.map((t, i) => (
          <span key={i} style={{ position: 'absolute', left: t.x, top: t.y, fontSize: 58, lineHeight: 1, userSelect: 'none' }}>
            {t.icon}
          </span>
        ))}
      </div>

      {/* Left edge label */}
      <div style={{ position: 'absolute', left: 4, top: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', fontFamily, fontSize: 24, fontWeight: 700, color: 'rgba(255,255,255,0.8)', letterSpacing: 4, whiteSpace: 'nowrap' }}>
          ▲ AI SIDEKICK SPORTS ▲
        </span>
      </div>

      {/* Right edge label */}
      <div style={{ position: 'absolute', right: 4, top: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ writingMode: 'vertical-rl', fontFamily, fontSize: 24, fontWeight: 700, color: 'rgba(255,255,255,0.8)', letterSpacing: 4, whiteSpace: 'nowrap' }}>
          ▼ SUBSCRIBE NOW ▼
        </span>
      </div>

      {/* ═══════════════════════════════════
          HEADER LAYER (absolute on canvas)
      ═══════════════════════════════════ */}

      {/* Q badge — top-left */}
      <div style={{
        position: 'absolute', top: 15, left: 15,
        width: 130, height: 130, borderRadius: 65,
        border: '8px solid #FFFFFF',
        background: `linear-gradient(135deg,${themeColor},${darkenHex(themeColor, 50)})`,
        boxShadow: '0 4px 20px rgba(0,0,0,0.55)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        zIndex: 10,
      }}>
        <span style={{ fontFamily, fontSize: 68, fontWeight: 900, color: '#FFFFFF', lineHeight: 1 }}>
          {questionNumber}
        </span>
        <span style={{ fontFamily, fontSize: 13, color: 'rgba(255,255,255,0.7)', lineHeight: 1 }}>
          OF {totalQuestions}
        </span>
      </div>

      {/* Question text — between badges */}
      <div style={{
        position: 'absolute', top: 15, left: 160, right: 160,
        transform: `translateY(${qY}px)`, opacity: qO,
        zIndex: 10, textAlign: 'center',
      }}>
        <span style={{
          fontFamily, fontSize: 72, fontWeight: 900,
          color: '#FFFFFF', textTransform: 'uppercase',
          lineHeight: 1.08, display: 'block',
          WebkitTextStroke: '4px #000000',
          textShadow: '3px 3px 0 #000000, -1px -1px 0 #000000',
        }}>
          {question}
        </span>
      </div>

      {/* Football icon — top-right */}
      <div style={{
        position: 'absolute', top: 15, right: 15,
        width: 130, height: 130, borderRadius: 65,
        border: '8px solid #FFFFFF',
        background: 'linear-gradient(135deg,#2196F3,#0D47A1)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.55)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 10, fontSize: 62, lineHeight: 1,
      }}>
        ⚽
      </div>

      {/* ═══════════════════════════════════
          CONTENT: IMAGE + OPTIONS (y:170→680)
      ═══════════════════════════════════ */}

      {/* Left image */}
      <div style={{
        position: 'absolute', top: OPTIONS_TOP, left: 40, width: 670, height: 510,
        borderRadius: 20, border: '8px solid #FFFFFF',
        boxShadow: '0 8px 36px rgba(0,0,0,0.55)',
        overflow: 'hidden',
        transform: `scale(${imgS})`, opacity: imgO,
        transformOrigin: 'center center',
      }}>
        <Img src={imageUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>

      {/* Options column */}
      <div style={{
        position: 'absolute', top: OPTIONS_TOP, left: 730, width: 1150, height: 510,
        display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: OPTION_GAP,
      }}>
        {KEYS.map((key) => {
          const st  = getOpt(key);
          const en  = optEntrance[key];
          const scl = key === correctAnswer && isRevealed ? correctScale : 1;
          return (
            <div key={key} style={{
              height: OPTION_H,
              transform: `translateX(${en.x}px) scaleX(${scl})`,
              opacity: st.opacity * en.o,
              transformOrigin: 'left center',
            }}>
              <div style={{
                height: '100%', backgroundColor: st.bg,
                borderRadius: 16, boxShadow: st.glow,
                display: 'flex', alignItems: 'center',
                padding: '0 28px', gap: 24, overflow: 'hidden',
              }}>
                {/* Letter badge */}
                <div style={{
                  width: 90, height: 90, borderRadius: 45, flexShrink: 0,
                  background: st.badgeGrad,
                  border: '4px solid rgba(255,255,255,0.9)',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.40)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <span style={{ fontFamily, fontSize: 54, fontWeight: 900, color: '#FFFFFF', lineHeight: 1 }}>
                    {key}
                  </span>
                </div>

                {/* Option text */}
                <span style={{
                  fontFamily, fontSize: 66, fontWeight: 900,
                  color: st.textColor, textTransform: 'uppercase',
                  flex: 1, letterSpacing: 1, lineHeight: 1,
                }}>
                  {options[key]}
                </span>

                {/* Correct checkmark */}
                {st.check && (
                  <span style={{ fontSize: 58, color: '#22CC22', lineHeight: 1, textShadow: '0 0 14px #22CC22' }}>
                    ✓
                  </span>
                )}
                {/* Wrong cross */}
                {st.cross && (
                  <span style={{ fontSize: 58, color: '#FF3333', lineHeight: 1, textShadow: '0 0 14px #FF3333' }}>
                    ✗
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* ═══════════════════════════════════
          TIMER BAR  (top:720, x:300→1620)
      ═══════════════════════════════════ */}
      <div style={{
        position: 'absolute', top: 720, left: 300, width: 1320, height: 60,
        borderRadius: 30,
        backgroundColor: 'rgba(255,255,255,0.28)',
        border: '3px solid rgba(255,255,255,0.50)',
        boxShadow: `0 0 22px ${hexToRgba(glowHex, 0.6)}, 0 0 44px ${hexToRgba(glowHex, 0.3)}`,
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: `${timerWidth}%`,
          backgroundColor: timerColor,
          borderRadius: 30,
        }}>
          {/* Chevron stripes */}
          <div style={{
            position: 'absolute', inset: 0,
            background: 'repeating-linear-gradient(60deg,transparent,transparent 10px,rgba(255,255,255,0.28) 10px,rgba(255,255,255,0.28) 16px)',
          }} />
        </div>
      </div>

      {/* ═══════════════════════════════════
          ENGAGEMENT PROMPT (below timer)
      ═══════════════════════════════════ */}
      {isRevealed && promptText && (
        <div style={{
          position: 'absolute', bottom: 36, left: 0, right: 0,
          display: 'flex', justifyContent: 'center',
          transform: `translateY(${promptY}px)`,
          zIndex: 20,
        }}>
          <div style={{
            backgroundColor: '#FFFFFF', borderRadius: 50,
            padding: '16px 64px',
            boxShadow: '0 4px 24px rgba(0,0,0,0.45)',
          }}>
            <span style={{ fontFamily, fontSize: 40, fontWeight: 900, color: '#FF6B00' }}>
              {promptText}
            </span>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════
          REVEAL FLASH
      ═══════════════════════════════════ */}
      {isRevealed && flashO > 0 && (
        <div style={{
          position: 'absolute', inset: 0,
          backgroundColor: '#FFFFFF', opacity: flashO,
          pointerEvents: 'none', zIndex: 99,
        }} />
      )}

      {/* ═══════════════════════════════════
          AUDIO
      ═══════════════════════════════════ */}
      {tickFrames.map((f) => (
        <Sequence key={f} from={f} durationInFrames={30}>
          <Audio src={staticFile('sfx/tick.wav')} volume={0.5} />
        </Sequence>
      ))}
      <Sequence from={revealFrame} durationInFrames={90}>
        <Audio src={staticFile('sfx/correct.wav')} volume={0.9} />
      </Sequence>

      {/* Voice narration — injected from parent via voiceUrl prop */}
      {voiceUrl && (
        <Audio src={voiceUrl} startFrom={30} volume={1.0} />
      )}

    </AbsoluteFill>
  );
};
