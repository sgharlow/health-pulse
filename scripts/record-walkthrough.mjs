// Automated Playwright video walkthrough of HealthPulse AI.
//
// Structure:
//   1. Hub (opening)                              ~3s
//   2. MCP LAYER — primary  (~75s)
//      • /chat — three MCP-style tool calls       ~50s
//      • /briefing — get_ai_briefing narrative    ~26s
//   3. WEB SCREENS — secondary, all critical views (~55s)
//      • /dashboard national + CA filter
//      • /facilities search
//      • /compare side-by-side benchmark
//      • /equity visualization
//   4. Hub (close)                                ~3s
//
// Total: ~135s real-time (~2:15). Fits inside the 3:00 video budget
// with headroom for post-edit narration pacing.
//
// Run: node scripts/record-walkthrough.mjs (from health-pulse/ directory)
// Output: .webm in ./screenshots/ (Playwright's native format)

import { chromium } from 'playwright';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const outDir = path.join(repoRoot, 'screenshots');
await mkdir(outDir, { recursive: true });

const BASE = 'https://web-umber-alpha-41.vercel.app';

const beat = async (page, ms) => page.waitForTimeout(ms);

console.log('Launching chromium (headed) and recording video to:', outDir);

const browser = await chromium.launch({ headless: false });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  recordVideo: {
    dir: outDir,
    size: { width: 1920, height: 1080 },
  },
});
const page = await context.newPage();

const t0 = Date.now();
const mark = (label) => console.log(`[${((Date.now() - t0) / 1000).toFixed(1)}s] ${label}`);

// Helper: submit a chat query, wait for Claude's tool-routed response.
// The chat UI exposes 5 MCP-style tools (get_quality_data, get_briefing,
// get_equity_analysis, compare_facilities, get_ai_briefing) — mirrors of
// the 11 tools the MCP server exposes on Railway.
async function askChat(query, waitMs = 16000) {
  const input = page.getByRole('textbox').first();
  await input.click();
  await input.fill(query);
  await beat(page, 800);
  await input.press('Enter');
  await beat(page, waitMs);
}

try {
  // ── Opening ──────────────────────────────────────────────────────
  mark('Hub');
  await page.goto(BASE);
  await beat(page, 3000);

  // ── MCP LAYER — primary (~75s) ───────────────────────────────────
  // Three chat queries demonstrating MCP-style tool routing on real
  // CMS data. Each response visibly shows the tool name + structured
  // data the Claude SDK synthesized into prose.

  mark('MCP #1: open /chat');
  await page.goto(`${BASE}/chat`);
  await beat(page, 2500);

  mark('MCP #1: quality anomalies — CA (get_quality_data)');
  await askChat('Show me quality anomalies in California hospitals');

  mark('MCP #2: equity disparity — TX (get_equity_analysis)');
  await askChat("What's the equity disparity in Texas hospitals?");

  mark('MCP #3: facility benchmark (compare_facilities)');
  await askChat('Compare UCSF Medical Center and Cleveland Clinic');

  // AI narrative — get_ai_briefing, shown in its dedicated page.
  // Belongs with the MCP arc because the narrative IS the tool's output.
  mark('MCP #4: /briefing CA → Generate AI narrative');
  await page.goto(`${BASE}/briefing?state=CA`);
  await beat(page, 4000);
  await page.getByRole('button', { name: /Generate AI Briefing/i }).click();
  await beat(page, 22000); // ~19s typical + buffer

  // ── WEB SCREENS — secondary, all critical views (~55s) ───────────
  // Same MCP-backed data, rendered as charts for human consumption.

  mark('Web #1: dashboard national');
  await page.goto(`${BASE}/dashboard`);
  await beat(page, 7000);

  mark('Web #2: dashboard filtered to CA');
  await page.selectOption('select', 'CA');
  await beat(page, 5000);

  mark('Web #3: facilities table');
  await page.goto(`${BASE}/facilities`);
  await beat(page, 4000);

  mark('Web #4: search UCSF');
  await page
    .getByPlaceholder('Search by name or state...')
    .fill('UCSF');
  await beat(page, 4500);

  mark('Web #5: compare page');
  await page.goto(`${BASE}/compare`);
  await beat(page, 2500);

  mark('Web #6: select UCSF + Cleveland and compare');
  const [facA, facB] = await page.locator('select').all();
  await facA.selectOption('050454');
  await beat(page, 1200);
  await facB.selectOption('360180');
  await beat(page, 1200);
  await page.getByRole('button', { name: 'Compare' }).click();
  await beat(page, 6000);

  mark('Web #7: equity visualization');
  await page.goto(`${BASE}/equity`);
  await beat(page, 6000);

  // ── Close ────────────────────────────────────────────────────────
  mark('Close on hub');
  await page.goto(BASE);
  await beat(page, 3000);
} catch (e) {
  console.error('Walkthrough error:', e);
} finally {
  await context.close(); // finalizes the .webm
  await browser.close();
  mark('Video finalized');
  console.log('Check:', outDir, 'for .webm output.');
}
