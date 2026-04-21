// Pre-warm Railway MCP + Vercel dashboard + AI briefing cache.
// Run ~2 minutes before expected judging / live demo.
//
// Usage: node scripts/warmup.mjs

const targets = [
  ['Dashboard hub',       'https://web-umber-alpha-41.vercel.app/'],
  ['Dashboard (national)', 'https://web-umber-alpha-41.vercel.app/dashboard'],
  ['Dashboard (CA)',      'https://web-umber-alpha-41.vercel.app/dashboard?state=CA'],
  ['Facilities',          'https://web-umber-alpha-41.vercel.app/facilities'],
  ['Compare',             'https://web-umber-alpha-41.vercel.app/compare'],
  ['Equity',              'https://web-umber-alpha-41.vercel.app/equity'],
  ['Briefing (CA)',       'https://web-umber-alpha-41.vercel.app/briefing?state=CA'],
  ['Chat',                'https://web-umber-alpha-41.vercel.app/chat'],
  ['API: /api/data',      'https://web-umber-alpha-41.vercel.app/api/data'],
  ['API: /api/equity',    'https://web-umber-alpha-41.vercel.app/api/equity'],
  ['API: /api/briefing',  'https://web-umber-alpha-41.vercel.app/api/briefing?state=CA'],
  ['Railway MCP (probe)', 'https://health-pulse-mcp-production.up.railway.app/mcp'],
];

console.log(`Warming ${targets.length} endpoints...\n`);
const start = Date.now();

const results = await Promise.all(
  targets.map(async ([name, url]) => {
    const t0 = Date.now();
    try {
      const r = await fetch(url, { method: 'GET' });
      return { name, url, status: r.status, ms: Date.now() - t0 };
    } catch (e) {
      return { name, url, status: 'ERR', ms: Date.now() - t0, err: e.message };
    }
  })
);

for (const r of results) {
  const ok = r.status >= 200 && r.status < 500;
  const icon = ok ? 'OK ' : 'FAIL';
  console.log(`  ${icon}  ${String(r.status).padEnd(5)} ${String(r.ms).padStart(5)}ms  ${r.name}`);
  if (r.err) console.log(`         ${r.err}`);
}

const slow = results.filter(r => r.ms > 3000).length;
console.log(`\nTotal: ${Date.now() - start}ms. ${slow} slow (>3s). Re-run this script if any FAILs.`);
console.log(`For the AI briefing cache, also open /briefing?state=CA in a browser and click "Generate AI Narrative" once.`);
