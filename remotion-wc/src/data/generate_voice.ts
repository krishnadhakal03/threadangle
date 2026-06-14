/**
 * Generate ElevenLabs voiceover per quiz question.
 * Run: npx ts-node src/data/generate_voice.ts
 *
 * Saves audio to: public/voice/q{id}.mp3
 * Reads keys from: F:\Threadangle\backend\.env
 * Controlled by: WC_VOICE=true in backend/.env (default: false — skip)
 *
 * Voice: Adam (pNInz6obpgDQGcFmaJgB)
 */

import fs from 'fs';
import path from 'path';
import https from 'https';

// ── Load dotenv from backend ──────────────────────────────────────────────────

const envPath = path.join(__dirname, '../../../backend/.env');
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (const line of lines) {
    const [key, ...rest] = line.split('=');
    if (key && rest.length) process.env[key.trim()] = rest.join('=').trim();
  }
}

const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;
const WC_VOICE           = process.env.WC_VOICE === 'true';

if (!WC_VOICE) {
  console.log('WC_VOICE is not set to "true" — skipping voice generation.');
  console.log('Set WC_VOICE=true in backend/.env to enable ElevenLabs TTS.');
  process.exit(0);
}

if (!ELEVENLABS_API_KEY) throw new Error('ELEVENLABS_API_KEY not found in backend/.env');

// ── Constants ─────────────────────────────────────────────────────────────────

const VOICE_ID   = 'pNInz6obpgDQGcFmaJgB'; // Adam
const MODEL_ID   = 'eleven_flash_v2_5';

// ── Helpers ───────────────────────────────────────────────────────────────────

function httpsPost(hostname: string, path: string, body: string, headers: Record<string, string>): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const bodyBuf = Buffer.from(body, 'utf8');
    const chunks: Buffer[] = [];
    const req = https.request(
      { hostname, path, method: 'POST', headers: { ...headers, 'content-length': bodyBuf.length } },
      (res) => {
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => resolve(Buffer.concat(chunks)));
      },
    );
    req.on('error', reject);
    req.write(bodyBuf);
    req.end();
  });
}

interface Question {
  id: number;
  question: string;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const quizPath  = path.join(__dirname, 'quiz_wc2026_v2.json');
  const outputDir = path.join(__dirname, '../../public/voice');

  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const quiz      = JSON.parse(fs.readFileSync(quizPath, 'utf8'));
  const questions: Question[] = quiz.questions;

  for (const q of questions) {
    const dest = path.join(outputDir, `q${q.id}.mp3`);
    if (fs.existsSync(dest)) {
      console.log(`  Q${q.id} — already exists, skipping`);
      continue;
    }

    console.log(`  Q${q.id} — generating voice: "${q.question}"`);

    const payload = JSON.stringify({
      text: q.question,
      model_id: MODEL_ID,
      voice_settings: { stability: 0.5, similarity_boost: 0.75 },
    });

    try {
      const audioBuffer = await httpsPost(
        'api.elevenlabs.io',
        `/v1/text-to-speech/${VOICE_ID}`,
        payload,
        {
          'xi-api-key': ELEVENLABS_API_KEY!,
          'content-type': 'application/json',
          'accept': 'audio/mpeg',
        },
      );

      fs.writeFileSync(dest, audioBuffer);
      const kb = Math.round(audioBuffer.length / 1024);
      console.log(`  Q${q.id} — saved ${kb} KB → q${q.id}.mp3`);
    } catch (err) {
      console.error(`  Q${q.id} — ERROR: ${err}`);
    }
  }

  console.log('Voice generation complete.');
}

main().catch(console.error);
