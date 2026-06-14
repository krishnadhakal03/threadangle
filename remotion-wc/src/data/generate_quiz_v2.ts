import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';
import path from 'path';

// Load ANTHROPIC_API_KEY from backend/.env
const envPath = path.resolve(__dirname, '../../../backend/.env');
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const eq = line.indexOf('=');
    if (eq > 0) process.env[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
  }
}

const PROMPT = `Generate 10 FIFA World Cup 2026 trivia questions.
CRITICAL: All questions must be SPECIFICALLY about WC 2026.

Focus areas:
- 48 teams (new format, not 32)
- Host nations: USA, Canada, Mexico (three nations co-hosting)
- Group stage: 12 groups of 4 (Groups A-L), top 2 plus 8 best 3rd-place advance
- Round of 32 is brand new (was Round of 16)
- Key players: Messi final World Cup, Ronaldo at 41 years old, Mbappe captain France, Haaland Norway did not qualify
- Stadiums: MetLife (New York), AT&T (Dallas), SoFi (Los Angeles), Estadio Azteca (Mexico City), BC Place (Vancouver)
- 104 total matches (up from 64 in 2022)
- 2026 marks the centenary of the first World Cup
- Opening match: Mexico City, Estadio Azteca

Mix difficulty: 4 easy, 4 medium, 2 hard.
Each question has exactly 3 options (A, B, C), one correct answer.
Explanation: max 8 words, plain English.
Use ONLY plain ASCII text — no accents, no special characters.

imagePrompt: 8-15 words, vivid and specific for AI image generation.
Good examples:
  FIFA World Cup 2026 trophy golden MetLife stadium New York night
  Lionel Messi Argentina blue jersey celebrating World Cup 2026 final
  USA USMNT soccer team celebrating World Cup 2026 home crowd stadium
  Kylian Mbappe France captain 2026 World Cup blue jersey action
  Estadio Azteca Mexico City World Cup 2026 opening ceremony crowd

bgQuery: 3-5 word Pexels search fallback (real photo, no AI)

Rotate themeColors exactly in this order:
Q1:#2196F3  Q2:#FF8C00  Q3:#32CD32  Q4:#9B59B6  Q5:#E91E63
Q6:#FF5722  Q7:#009688  Q8:#FF9800  Q9:#3F51B5  Q10:#F44336

Return ONLY valid JSON, absolutely no markdown fences or commentary:
{"questions":[{"id":1,"difficulty":"easy","question":"...","options":{"A":"...","B":"...","C":"..."},"correct":"A","explanation":"...","imagePrompt":"...","bgQuery":"...","themeColor":"#2196F3"}]}`;

async function main() {
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log('Calling claude-opus-4-6...');
  const message = await client.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: 3500,
    messages: [{ role: 'user', content: PROMPT }],
  });

  const raw = (message.content[0] as { text: string }).text.trim();

  // Strip markdown fences if present
  const clean = raw.replace(/^```json\s*/m, '').replace(/```\s*$/m, '').trim();

  const parsed = JSON.parse(clean);
  console.log(`Generated ${parsed.questions.length} questions:`);
  for (const q of parsed.questions) {
    console.log(`  Q${q.id} [${q.difficulty}] ${q.question}`);
  }

  const outPath = path.resolve(__dirname, 'quiz_wc2026_v2.json');
  fs.writeFileSync(outPath, JSON.stringify(parsed, null, 2), 'utf8');
  console.log(`\nSaved: ${outPath}`);
}

main().catch((err) => { console.error(err); process.exit(1); });
