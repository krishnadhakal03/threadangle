# Remotion WC — Session Context

## Project goal
Animated World Cup videos — Shorts (1080×1920) + Long-form (1920×1080).
Quiz format is priority this week. One command per video type.

## Directory structure
src/components/     — reusable (StatCounter, OVRCircle, PlayerCard, TeamHook, CTAScene)
src/compositions/   — per-video (GermanyShort.tsx, QuizWC.tsx etc)
src/templates/      — copied from templates-lib (read-only, never modify)
src/transitions/    — copied from remotion-dev transitions (read-only)
public/germany/     — hook.mp4, player.mp4, cta.mp4
public/sfx/         — tick.wav, correct.wav, wrong.wav, cheer.wav
public/             — football_hype.mp3, dramatic.mp3

## Template libraries (ALWAYS read before coding)
81 templates:
  F:\Threadangle\remotion-wc\templates-lib\remotion-templates-main\templates\
  Key files: stat-counter.tsx, circular-progress.tsx,
  cinematic-title-intro.tsx, bounce-text.tsx,
  particle-explosion.tsx, typewriter-subtitle.tsx,
  pulsing-text.tsx, countdown-timer.tsx

Official transitions:
  F:\Threadangle\remotion-wc\remotion-dev\remotion-main\packages\transitions\src\presentations\
  Key files: dreamy-zoom.tsx, dissolve.tsx, fade.tsx

## RULES — ALWAYS FOLLOW
1. Read CLAUDE.md at start of every session
2. Read template file BEFORE using it
3. Copy templates to src/templates/ then import
4. Never modify copied templates
5. All team/quiz data in composition file only
6. Components accept props — zero hardcoded data inside
7. One task per session — do not scope creep
8. After each file written, confirm before next

## Current status
germany_reusable_v1.mp4 — DONE (5/10)
germany_reusable_v2.mp4 — NOT DONE (stuck on layout)

## Known bugs to fix
BUG 1: PlayerCard has black sidebars — card too small
        Fix: full-screen layout, remove floating card box
BUG 2: Flag emojis render as text on Windows
        Fix: use flagcdn.com <Img> tags
BUG 3: Player photo not loading
        Fix: use Remotion <Img> with Wikipedia URL

## Render commands
npx remotion render src/index.ts GermanyShort out/germany_v2.mp4
npx remotion render src/index.ts QuizWC out/quiz_wc_v1.mp4

## Sound effects
public/sfx/tick.wav     — timer countdown tick
public/sfx/correct.wav  — correct answer chime
public/sfx/wrong.wav    — wrong answer buzz
public/sfx/cheer.wav    — crowd cheer

## Next: Quiz video format — SUPER PRIORITY

QuizCard component needs:
  - Question text (large, centered, Oswald 700 64px)
  - Background: Pexels photo at 35% opacity per question
  - 3 answer options (A, B, C) — slide in staggered
  - HORIZONTAL timer bar (NOT circular):
      Full screen width, pinned to bottom
      Green (#22C55E) → Orange (#F97316) → Red (#EF4444)
      10 seconds total, always reveals correct answer
  - tick.wav every 3s (green), every 1s (red zone)
  - Reveal sequence (always same — pre-recorded video):
      Wrong options: red flash + ✗ icon + wrong.wav
      Correct option: green flash + ✓ icon + correct.wav
  - Explanation text fades in after reveal
  - Score counter top-right corner updates after each Q
  - dreamy-zoom transition between questions

TimerBar props:
  durationFrames: 300 (10s at 30fps)
  width: full screen
  position: pinned to bottom
  colorGreen: #22C55E
  colorOrange: #F97316  
  colorRed: #EF4444
  thresholdOrange: 0.5 (50% elapsed)
  thresholdRed: 0.8 (80% elapsed)

Data format per question:
  question: string
  options: {A, B, C}
  correct: 'A' | 'B' | 'C'
  explanation: string (max 10 words)
  bgQuery: string (Pexels search term)