# Threadangle — Quiz Video Product
## Super Priority Component — Premium Interactive Quiz

**Vision:** Build the best automated football quiz video pipeline on YouTube.
**Quality target:** Match or exceed "The Best Football Quiz" channel.
**Timeline:** 7 days to first premium video posted.

---

## What "Premium" Actually Means

Looking at the reference channel your kid was watching:

| Element | Their quality | Our target |
|---|---|---|
| Background | Real trophy/stadium photos | Same — Pexels API |
| Typography | Bold, large, high contrast | Oswald 700, 100px+ |
| Timer | Circular countdown, color change | circular-progress.tsx |
| Reveal | Color flash + icon | Green ✓ / Red ✗ animation |
| Score | Running total top corner | StatCounter component |
| Transitions | Smooth between questions | dreamy-zoom.tsx |
| Audio | Tick + correct + wrong + cheer | sfx/ folder ready |
| Branding | Logo top corner | AI Sidekick Sports logo |

---

## Paid Tools — Honest Assessment

### Worth buying:
| Tool | Cost | What it adds | Decision |
|---|---|---|---|
| ElevenLabs | $5/mo (Starter) | Real voice narrating questions | YES — buy Starter |
| Envato Elements | $16.50/mo | 50,000 premium sound effects, music | OPTIONAL — freesound.org is fine for now |
| Storyblocks | $15/mo | Royalty-free video footage library | OPTIONAL — Pexels free is sufficient |
| Adobe Fonts | Free with Creative Cloud | Better than Google Fonts | NO — Oswald is good enough |

### Not worth buying yet:
| Tool | Why not yet |
|---|---|
| Runway ML | We don't need AI video generation |
| Midjourney | Wikipedia + Pexels photos are sufficient |
| Motion Array | Templates we already have from remotion-templates |

**Honest bottom line:**
Free tools are sufficient for 8.5/10 quality.
ElevenLabs Starter ($5/mo) is the ONLY paid tool worth buying right now.
Buy it when quiz video is ready for production — not before.

---

## The Premium Quiz Architecture

### File: src/compositions/QuizWC.tsx
```
Data source: src/data/quiz_wc2026.json (Claude API generated)
Duration:    ~5 minutes (9000 frames at 30fps)
Resolution:  Both 1920×1080 (long-form) and 1080×1920 (Short teaser)
```

### Scene structure:
```
IntroScene      (0-240,    8s)   — hook, title, thumbnail moment
QuizScene × 10  (240-9240, ~5min) — 30s per question
OutroScene      (9240-9540, 10s) — score reveal, CTA, subscribe
```

### QuizScene breakdown (900 frames = 30s per question):
```
Frame 0-30    Question slides up with spring bounce
Frame 30-60   Background photo fades in at 35% opacity
Frame 60-90   Option A slides from left
Frame 75-105  Option B slides from left (15 frame delay)
Frame 90-120  Option C slides from left (15 frame delay)
Frame 120     Countdown timer starts (300 frames = 10 seconds)
              tick.wav fires every 90 frames (every 3s)
              Timer ring: gold → orange (50%) → red (80%)
Frame 420     Timer ends — REVEAL MOMENT
              Wrong options: red flash + ✗ icon + wrong.wav
              Correct option: green flash + ✓ icon + correct.wav
Frame 450-540 Explanation text fades in below correct answer
              e.g. "Brazil — 5 titles (1958, 62, 70, 94, 2002)"
Frame 540-600 Score counter updates top-right corner
Frame 600-660 dreamy-zoom transition to next question
Frame 660-900 Buffer + next question loads
```

---

## Component Specs

### QuizCard.tsx (NEW — core component)
```typescript
interface QuizCardProps {
  question: string
  options: { A: string; B: string; C: string }
  correctAnswer: 'A' | 'B' | 'C'
  explanation: string
  bgImageUrl: string
  questionNumber: number
  totalQuestions: number
  accentColor?: string        // default gold #D4A843
  revealFrame: number         // frame when timer ends
}
```

### CountdownTimer.tsx (NEW — built on circular-progress.tsx)
```typescript
interface CountdownTimerProps {
  durationFrames: number      // 300 = 10 seconds at 30fps
  startFrame: number
  size: number                // px diameter
  colorGold: string           // start color
  colorOrange: string         // 50% warning
  colorRed: string            // 80% danger
  onTickFrame: number[]       // frames to trigger tick.wav
}
```

### AnswerOption.tsx (NEW)
```typescript
interface AnswerOptionProps {
  letter: 'A' | 'B' | 'C'
  text: string
  state: 'idle' | 'correct' | 'wrong' | 'hidden'
  enterFrame: number          // stagger timing
  revealFrame: number         // when state changes
  accentColor: string
}
```

### ScoreTracker.tsx (NEW — top corner)
```typescript
interface ScoreTrackerProps {
  correct: number
  total: number
  updateFrame: number         // animate on update
}
```

---

## Data Layer — Quiz JSON Format

### src/data/quiz_wc2026.json
```json
{
  "title": "FIFA World Cup 2026 Quiz",
  "subtitle": "How Much Do You Know?",
  "totalQuestions": 10,
  "accentColor": "#D4A843",
  "bgVideoPath": "germany/hook.mp4",
  "questions": [
    {
      "id": 1,
      "difficulty": "easy",
      "question": "Which country has won the most World Cups?",
      "options": {
        "A": "Germany",
        "B": "Brazil",
        "C": "Italy"
      },
      "correct": "B",
      "explanation": "Brazil — 5 titles (1958, 62, 70, 94, 2002)",
      "bgQuery": "FIFA World Cup trophy gold stadium",
      "bgImageUrl": ""
    }
  ]
}
```

### Script to generate questions (worldcup/data/generate_quiz.py):
```python
import anthropic
import json

def generate_quiz(topic: str, count: int = 10) -> dict:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Generate {count} {topic} trivia questions.
            Mix: 4 easy, 4 medium, 2 hard.
            Each has exactly 3 options (A, B, C).
            One correct answer.
            Short explanation for correct answer (max 10 words).
            Return ONLY valid JSON, no markdown:
            {{"questions": [
              {{"id": 1, "difficulty": "easy",
                "question": "...", 
                "options": {{"A":"...","B":"...","C":"..."}},
                "correct": "A",
                "explanation": "...",
                "bgQuery": "relevant pexels search query"}}
            ]}}"""
        }]
    )
    return json.loads(response.content[0].text)
```

---

## Premium Visual Design Decisions

### Typography
```
Questions:    Oswald 700, 64px, white, text-shadow gold glow
Options:      Oswald 600, 48px, white on dark panel
Timer number: Oswald 700, 80px, color-coded
Explanation:  Roboto 400, 28px, rgba(255,255,255,0.8)
Score:        Oswald 700, 36px, gold
```

### Colors
```
Background:   #0D0D14 (near black)
Gold:         #D4A843 (primary accent)
Correct:      #22C55E (green)
Wrong:        #EF4444 (red)
Idle option:  rgba(255,255,255,0.08) background
Timer gold:   #D4A843 → #F97316 → #EF4444
```

### Layout (1920×1080 landscape)
```
Top bar:      Question number + Score tracker (80px height)
Centre:       Question text + background photo
Bottom half:  Three answer options stacked
Timer:        Bottom right corner, 120px circle
```

### Layout (1080×1920 portrait — Short teaser)
```
Top 20%:      Question number + category
Middle 40%:   Question text (large)
Bottom 40%:   Answer options (3 rows)
Timer:        Bottom centre
```

---

## Audio Design

### Per question timing:
```
Question appears:   BGM continues at vol 0.15
Options appear:     Subtle whoosh per option (optional)
Timer running:      tick.wav every 3 seconds (frames 120, 210, 300, 390)
Timer at 50%:       tick.wav frequency increases (every 2s)
Timer at 80%:       tick.wav every second
Reveal — correct:   correct.wav + crowd.wav briefly
Reveal — wrong:     wrong.wav
Score update:       short chime
Transition:         BGM swells slightly
```

---

## Build Order (7 days)

### Day 1 (TODAY): Foundation fix
- Fix PlayerCard.tsx full-screen layout
- Confirm Musiala photo renders
- germany_reusable_v2.mp4 — 8/10 quality

### Day 2: CountdownTimer + AnswerOption
- Build CountdownTimer from circular-progress.tsx
- Build AnswerOption with idle/correct/wrong states
- Test: single question renders correctly
- No full quiz yet — just one question

### Day 3: QuizCard + data layer
- Build QuizCard composing CountdownTimer + AnswerOption
- Build generate_quiz.py (Claude API)
- Generate quiz_wc2026.json (10 questions)
- Fetch Pexels bg image per question

### Day 4: Full quiz composition
- Build QuizWC.tsx (IntroScene + 10×QuizScene + OutroScene)
- Wire audio: tick.wav, correct.wav, wrong.wav, cheer.wav
- First full render — landscape 1920×1080
- Watch end to end, note issues

### Day 5: Audio + voice
- Add ElevenLabs narration per question (if quota allows)
- Or gTTS for timing check
- BGM ducking under voice
- Captions synced

### Day 6: Short teaser version
- Build QuizWCShort.tsx — one question as 30s Short
- 1080×1920 portrait layout
- Same components, different dimensions
- Post as teaser → "Full quiz link in bio"

### Day 7: Post + data collection
- Upload long-form quiz to YouTube
- Upload teaser Short
- Check analytics after 24hrs
- Retention curve tells us which questions viewers drop off

---

## The Reuse Roadmap

### After WC 2026:
```
quiz_epl_2526.json       → EPL season quiz
quiz_ucl_2526.json       → UCL group stage quiz  
quiz_top_scorers.json    → All-time top scorers
quiz_wc_history.json     → WC history 1930-2022
quiz_wc_players.json     → Guess the player from stats
quiz_transfers.json      → Most expensive transfers
```

### Each new quiz = 1 JSON file + 1 Pexels API call per question.
### Zero new code. Zero new components.

---

## GitHub Issues to Create

### #222 — QuizCard component (SUPER PRIORITY)
### #223 — CountdownTimer component  
### #224 — AnswerOption component
### #225 — ScoreTracker component
### #226 — QuizWC composition (full video)
### #227 — generate_quiz.py (Claude API data layer)
### #228 — QuizWCShort (portrait teaser)

---

*Created: 2026-06-10*
*Priority: SUPER — above all other issues*
*Owner: Krishna + Claude TPM*