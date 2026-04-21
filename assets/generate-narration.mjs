// Generate narration.mp3 from narration.txt via OpenAI TTS.
//
// Usage:
//   export OPENAI_API_KEY=sk-...        # required
//   node generate-narration.mjs          # defaults: onyx, tts-1-hd, speed=0.90
//
// Env overrides:
//   VOICE=onyx|nova|alloy|echo|fable|shimmer   (default: onyx)
//   MODEL=tts-1-hd|tts-1                       (default: tts-1-hd)
//   SPEED=0.25..4.0                            (default: 0.90)
//
// Target: walkthrough.mp4 is 138.7s. The narration is 334 words, so an
// effective cadence of ~140 wpm hits the duration. Start at SPEED=0.90;
// if narration.mp3 is too short, drop to 0.87; if too long, raise to 0.93.

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  console.error('ERROR: set OPENAI_API_KEY in your environment.');
  process.exit(1);
}

const voice = process.env.VOICE || 'onyx';
const model = process.env.MODEL || 'tts-1-hd';
const speed = parseFloat(process.env.SPEED || '0.90');

const input = await fs.readFile(path.join(here, 'narration.txt'), 'utf8');
const wordCount = input.trim().split(/\s+/).length;

console.log(`voice=${voice}  model=${model}  speed=${speed}`);
console.log(`narration: ${wordCount} words, ${input.length} chars`);
console.log('calling OpenAI...');

const t0 = Date.now();
const resp = await fetch('https://api.openai.com/v1/audio/speech', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ model, voice, input, response_format: 'mp3', speed }),
});

if (!resp.ok) {
  console.error(`OpenAI error: ${resp.status}`);
  console.error(await resp.text());
  process.exit(1);
}

const buf = Buffer.from(await resp.arrayBuffer());
const outPath = path.join(here, 'narration.mp3');
await fs.writeFile(outPath, buf);
console.log(`wrote ${outPath} (${(buf.length / 1024).toFixed(1)} KB) in ${Date.now() - t0}ms`);
console.log('');
console.log('Next: check duration with');
console.log('  ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 assets/narration.mp3');
console.log('Target: 138.7s. If too short, lower SPEED. If too long, raise SPEED.');
