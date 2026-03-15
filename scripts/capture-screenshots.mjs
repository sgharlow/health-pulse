/**
 * Capture screenshots from the live HealthPulse AI dashboard.
 * Uses Playwright with bundled Chromium (not system Chrome).
 */
import { chromium } from 'playwright';
import { join } from 'path';

const BASE = 'https://web-umber-alpha-41.vercel.app';
const OUT = join(import.meta.dirname, '..', 'assets', 'screenshots');

async function main() {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    colorScheme: 'dark',
  });
  const page = await ctx.newPage();

  async function capture(path, name, waitMs = 3000) {
    console.log(`Capturing ${name}...`);
    await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(waitMs);
    await page.screenshot({ path: join(OUT, `${name}.png`), fullPage: false });
    console.log(`  Saved ${name}.png`);
  }

  // 1. Hub / Landing Page
  await capture('/', '01-hub-landing');

  // 2. Dashboard with All States
  await capture('/dashboard', '02-dashboard-all-states', 5000);

  // 3. Dashboard filtered to CA
  await page.goto(`${BASE}/dashboard`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  const stateSelect = page.locator('select');
  if (await stateSelect.count() > 0) {
    await stateSelect.first().selectOption('CA');
    await page.waitForTimeout(3000);
  }
  await page.screenshot({ path: join(OUT, '03-dashboard-california.png'), fullPage: false });
  console.log('  Saved 03-dashboard-california.png');

  // 4. Facilities page
  await capture('/facilities', '04-facilities-table', 4000);

  // 5. Compare page
  await capture('/compare', '05-compare-facilities', 4000);

  // 6. Equity page
  await capture('/equity', '06-equity-analysis', 4000);

  // 7. Briefing page (CA default)
  await capture('/briefing', '07-briefing-executive', 5000);

  // 8. Chat page (with suggested queries visible)
  await capture('/chat', '08-chat-interface', 2000);

  // 9. Chat - send a real query
  await page.goto(`${BASE}/chat`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  // Click a suggested query chip if visible
  const chips = page.locator('button:has-text("worst quality")');
  if (await chips.count() > 0) {
    await chips.first().click();
    console.log('  Clicked suggested query chip...');
    await page.waitForTimeout(15000); // Wait for Claude response
    await page.screenshot({ path: join(OUT, '09-chat-quality-response.png'), fullPage: false });
    console.log('  Saved 09-chat-quality-response.png');
  } else {
    // Type manually
    const textarea = page.locator('textarea');
    if (await textarea.count() > 0) {
      await textarea.first().fill('What are the worst quality hospitals in California?');
      await page.locator('button:has-text("Send")').click();
      await page.waitForTimeout(15000);
      await page.screenshot({ path: join(OUT, '09-chat-quality-response.png'), fullPage: false });
      console.log('  Saved 09-chat-quality-response.png');
    }
  }

  // 10. Briefing with AI narrative (if available)
  await page.goto(`${BASE}/briefing`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  const genBtn = page.locator('button:has-text("Generate AI Briefing")');
  if (await genBtn.count() > 0) {
    await genBtn.first().click();
    console.log('  Generating AI briefing...');
    await page.waitForTimeout(20000);
    await page.screenshot({ path: join(OUT, '10-briefing-ai-narrative.png'), fullPage: false });
    console.log('  Saved 10-briefing-ai-narrative.png');
  }

  await browser.close();
  console.log('\nDone! Screenshots saved to assets/screenshots/');
}

main().catch(e => { console.error(e); process.exit(1); });
