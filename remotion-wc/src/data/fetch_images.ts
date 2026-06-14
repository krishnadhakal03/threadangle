/**
 * Fetch one Pexels landscape photo per quiz question.
 * Run: npx ts-node src/data/fetch_images.ts
 *
 * Saves images to: public/quiz_images/q{id}.jpg
 * Reads API key from: F:\Threadangle\backend\.env (PEXELS_API_KEY)
 * Reads questions from: src/data/quiz_wc2026.json
 */

import fs from 'fs';
import path from 'path';
import https from 'https';

// ── Load dotenv from backend ──────────────────────────────────────────────────

const envPath = path.join(__dirname, '../../../../backend/.env');
if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (const line of lines) {
    const [key, ...rest] = line.split('=');
    if (key && rest.length) process.env[key.trim()] = rest.join('=').trim();
  }
}

const PEXELS_API_KEY = process.env.PEXELS_API_KEY;
if (!PEXELS_API_KEY) throw new Error('PEXELS_API_KEY not found in backend/.env');

// ── Types ─────────────────────────────────────────────────────────────────────

interface PexelsPhoto {
  src: { landscape: string; original: string };
}
interface PexelsResponse {
  photos: PexelsPhoto[];
}
interface Question {
  id: number;
  bgQuery: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function httpsGet(url: string, headers: Record<string, string> = {}): Promise<string> {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers }, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => resolve(body));
    });
    req.on('error', reject);
  });
}

function downloadFile(url: string, dest: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (res) => {
      // Follow redirects
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        downloadFile(res.headers.location!, dest).then(resolve).catch(reject);
        return;
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function fetchPexelsPhoto(query: string): Promise<string | null> {
  const encoded = encodeURIComponent(query);
  const url = `https://api.pexels.com/v1/search?query=${encoded}&per_page=1&orientation=landscape`;
  const body = await httpsGet(url, { Authorization: PEXELS_API_KEY! });
  const data: PexelsResponse = JSON.parse(body);
  if (!data.photos || data.photos.length === 0) return null;
  return data.photos[0].src.landscape;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  const quizPath  = path.join(__dirname, 'quiz_wc2026.json');
  const outputDir = path.join(__dirname, '../../public/quiz_images');

  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

  const quiz = JSON.parse(fs.readFileSync(quizPath, 'utf8'));
  const questions: Question[] = quiz.questions;

  for (const q of questions) {
    const dest = path.join(outputDir, `q${q.id}.jpg`);
    if (fs.existsSync(dest)) {
      console.log(`  Q${q.id} — already exists, skipping`);
      continue;
    }
    console.log(`  Q${q.id} — fetching: "${q.bgQuery}"`);
    try {
      const photoUrl = await fetchPexelsPhoto(q.bgQuery);
      if (!photoUrl) { console.warn(`  Q${q.id} — no results, skipping`); continue; }
      await downloadFile(photoUrl, dest);
      const size = (fs.statSync(dest).size / 1024).toFixed(0);
      console.log(`  Q${q.id} — saved ${size} KB → q${q.id}.jpg`);
    } catch (err) {
      console.error(`  Q${q.id} — ERROR: ${err}`);
    }
  }
  console.log('Done.');
}

main().catch(console.error);
