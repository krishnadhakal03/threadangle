import React from 'react';
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { QuizCard } from '../components/QuizCard';
import { IntroScene } from './IntroScene';
import { OutroScene } from './OutroScene';
import quizData from '../data/quiz_wc2026_v2.json';

// Set to true after running: npx ts-node src/data/generate_voice.ts
const WC_VOICE = true;

// ── Timing constants ──────────────────────────────────────────────────────────

const INTRO_FRAMES  = 240;   //  8 s
const Q_FRAMES      = 600;   // 20 s per question
const OUTRO_FRAMES  = 450;   // 15 s
const REVEAL_FRAME  = 300;   // timer ends at 10 s

const Q_COUNT = quizData.questions.length; // 10

// Total: 240 + (10×600) + 450 = 6690 frames = 3 min 43 s

// ── Slide-in transition wrapper ───────────────────────────────────────────────

const SlideIn: React.FC<{ themeColor: string; children: React.ReactNode }> = ({ themeColor, children }) => {
  const frame = useCurrentFrame();
  const slideX = interpolate(frame, [0, 20], [1920, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div style={{ position: 'absolute', inset: 0, transform: `translateX(${slideX}px)` }}>
      {/* Color flash behind slide */}
      {frame < 20 && (
        <div style={{ position: 'absolute', inset: 0, backgroundColor: themeColor, opacity: interpolate(frame, [0, 20], [0.6, 0]) }} />
      )}
      {children}
    </div>
  );
};

// ── Component ─────────────────────────────────────────────────────────────────

export const QuizWC: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>

      {/* BGM — loops throughout entire video */}
      <Audio src={staticFile('bgm/football_hype.mp3')} volume={0.12} loop />

      {/* ── Intro (0 → 239) ── */}
      <Sequence from={0} durationInFrames={INTRO_FRAMES}>
        <IntroScene />
      </Sequence>

      {/* ── Questions ── */}
      {quizData.questions.map((q, i) => {
        const startFrame = INTRO_FRAMES + i * Q_FRAMES;
        return (
          <Sequence key={q.id} from={startFrame} durationInFrames={Q_FRAMES}>
            <SlideIn themeColor={q.themeColor}>
              <QuizCard
                questionNumber={q.id}
                totalQuestions={Q_COUNT}
                question={q.question}
                options={q.options as { A: string; B: string; C: string }}
                correctAnswer={q.correct as 'A' | 'B' | 'C'}
                explanation={q.explanation}
                imageUrl={staticFile(`quiz_images/q${q.id}.jpg`)}
                themeColor={q.themeColor}
                revealFrame={REVEAL_FRAME}
                totalFrames={Q_FRAMES}
                voiceUrl={WC_VOICE ? staticFile(`voice/q${q.id}.mp3`) : undefined}
              />
            </SlideIn>
          </Sequence>
        );
      })}

      {/* ── Outro ── */}
      <Sequence from={INTRO_FRAMES + Q_COUNT * Q_FRAMES} durationInFrames={OUTRO_FRAMES}>
        <OutroScene />
      </Sequence>

    </AbsoluteFill>
  );
};
