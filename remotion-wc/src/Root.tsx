import React from 'react';
import { Composition } from 'remotion';
import { WorldCupShort }    from './WorldCupShort';
import { GermanyShort }     from './compositions/GermanyShort';
import { TimerBarTest }     from './compositions/TimerBarTest';
import { QuizCardTest }     from './compositions/QuizCardTest';
import { IntroScene }       from './compositions/IntroScene';
import { OutroScene }       from './compositions/OutroScene';
import { QuizWC }           from './compositions/QuizWC';
import { QuizShortCard }    from './components/QuizShortCard';
import { MatchdayHype, type MatchdayHypeProps } from './compositions/MatchdayHype';
import quizData             from './data/quiz_wc2026_v2.json';

export const RemotionRoot: React.FC = () => (
  <>
    {/* Original monolithic composition (kept for reference) */}
    <Composition
      id="WorldCupShort"
      component={WorldCupShort}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
    />

    {/* Reusable component architecture — Germany */}
    <Composition
      id="GermanyShort"
      component={GermanyShort}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
    />

    {/* TimerBar component test — 10s countdown with color transitions */}
    <Composition
      id="TimerBarTest"
      component={TimerBarTest}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
    />

    {/* QuizCard master component test */}
    <Composition
      id="QuizCardTest"
      component={QuizCardTest}
      durationInFrames={900}
      fps={30}
      width={1920}
      height={1080}
    />

    {/* Quiz intro — 8s purple title card */}
    <Composition
      id="IntroScene"
      component={IntroScene}
      durationInFrames={240}
      fps={30}
      width={1920}
      height={1080}
    />

    {/* Quiz outro — 15s subscribe / watch-next card */}
    <Composition
      id="OutroScene"
      component={OutroScene}
      durationInFrames={450}
      fps={30}
      width={1920}
      height={1080}
    />

    {/* Full quiz v2 — Intro + 10×600f questions + Outro = 6690 frames (3m 43s) */}
    <Composition
      id="QuizWC"
      component={QuizWC}
      durationInFrames={6690}
      fps={30}
      width={1920}
      height={1080}
    />

    {/* Matchday hype shorts — one composition per fixture */}
    <Composition<MatchdayHypeProps>
      id="Short-Matchday-Brazil"
      component={MatchdayHype}
      durationInFrames={750}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ matchId: 'brazil_vs_morocco' as const }}
    />
    <Composition
      id="Short-Matchday-Japan"
      component={MatchdayHype}
      durationInFrames={750}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ matchId: 'japan_vs_netherlands' as const }}
    />

    {/* Shorts — one 25s vertical composition per question */}
    {quizData.questions.map((q) => (
      <Composition
        key={q.id}
        id={`QuizShort-Q${q.id}`}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        component={QuizShortCard as React.ComponentType<any>}
        durationInFrames={750}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{ questionData: q }}
      />
    ))}
  </>
);
