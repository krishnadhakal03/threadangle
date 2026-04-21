// This creates a 120x120 PNG from the SVG for Google OAuth consent screen
// Run with: node scripts/export-logo.js

import sharp from 'sharp';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const svgContent = readFileSync(join(__dirname, '../public/favicon.svg'));

sharp(svgContent)
  .resize(120, 120)
  .png()
  .toFile(join(__dirname, '../public/threadangle-logo-120.png'))
  .then(() => console.log('✅ Logo exported to public/threadangle-logo-120.png'))
  .catch(err => console.error('Export failed:', err));
