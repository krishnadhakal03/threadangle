/**
 * Fetch AI-generated images from pollinations.ai per quiz question.
 * Run: npx ts-node src/data/fetch_images_v2.ts
 *
 * Uses imagePrompt from quiz_wc2026_v2.json for vivid AI images.
 * Fallback: Pexels (bgQuery) if pollinations.ai returns < 50 KB.
 * Saves to: public/quiz_images/q{id}.jpg
 */

import fs from 'fs';
import path from 'path';
import https from 'https';
import http from 'http';

// ── Load env ──────────────────────────────────────────────────────────────────

const envPath = path.resolve(__dirname, '../../../backend/.env');
const env: Record<string, string> = {};
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const eq = line.indexOf('=');
    if (eq > 0) env[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
  }
}
const PEXELS_KEY = env.PEXELS_API_KEY || process.env.PEXELS_API_KEY || '';

// ── Types ─────────────────────────────────────────────────────────────────────

interface Question { id: number; imagePrompt: string; bgQuery: string }

// ── Helpers ───────────────────────────────────────────────────────────────────

function downloadUrl(url: string, dest: string, maxRedirects = 5): Promise<number> {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    client.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      if ((res.statusCode === 301 || res.statusCode === 302) && res.headers.location && maxRedirects > 0) {
        resolve(downloadUrl(res.headers.location, dest, maxRedirects - 1));
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      const file = fs.createWriteStream(dest);
      res.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve(fs.statSync(dest).size);
      });
      file.on('error', reject);
    }).on('error', reject);
  });
}

function pexelsUrl(query: string): Promise<string | null> {
  return new Promise((resolve) => {
    const encoded = encodeURIComponent(query);
    const options = {
      hostname: 'api.pexels.com',
      path: `/v1/search?query=${encoded}&per_page=1&orientation=landscape`,
      headers: { Authorization: PEXELS_KEY },
    };
    https.get(options, (res) => {
      let body = '';
      res.on('data', (c) => { body += c; });
      res.on('end', () => {
        try {
          const data = JSON.parse(body);
          resolve(data.photos?.[0]?.src?.landscape ?? null);
        } catch { resolve(null); }
      });
    }).on('error', () => resolve(null));
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const quizPath  = path.resolve(__dirname, 'quiz_wc2026_v2.json');
  const outputDir = path.resolve(__dirname, '../../public/quiz_images');

  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const { questions }: { questions: Question[] } = JSON.parse(fs.readFileSync(quizPath, 'utf8'));

  for (const q of questions) {
    const dest = path.join(outputDir, `q${q.id}.jpg`);
    const promptEncoded = encodeURIComponent(q.imagePrompt);
    const pollinationsUrl = `https://image.pollinations.ai/prompt/${promptEncoded}?width=1280&height=720&nologo=true&model=flux`;

    console.log(`Q${q.id} — generating: "${q.imagePrompt}"`);

    try {
      const bytes = await downloadUrl(pollinationsUrl, dest);
      const kb = Math.round(bytes / 1024);
      if (kb >= 50) {
        console.log(`  ✓ pollinations.ai — ${kb} KB`);
        continue;
      }
      console.log(`  ✗ too small (${kb} KB) — falling back to Pexels`);
      fs.unlinkSync(dest);
    } catch (err) {
      console.log(`  ✗ pollinations.ai error: ${err} — falling back to Pexels`);
      if (fs.existsSync(dest)) fs.unlinkSync(dest);
    }

    // Pexels fallback
    if (!PEXELS_KEY) { console.log('  ✗ no PEXELS_API_KEY — skipping'); continue; }
    const fallbackUrl = await pexelsUrl(q.bgQuery);
    if (!fallbackUrl) { console.log('  ✗ Pexels no results'); continue; }
    const bytes = await downloadUrl(fallbackUrl, dest);
    console.log(`  ✓ Pexels fallback — ${Math.round(bytes / 1024)} KB`);
  }

  console.log('\nDone. Images in public/quiz_images/');
}

main().catch((e) => { console.error(e); process.exit(1); });
