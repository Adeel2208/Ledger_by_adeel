import { chromium } from 'playwright';
const dir = 'C:/Users/HP/AppData/Local/Temp/claude/c--Users-HP-Videos-vc-brain/4f040d96-7801-414b-87c3-1d8331dfa7f2/scratchpad';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 1050 } });
const errs = [];
p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
p.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));

// Search: run the brief's example query end-to-end
await p.goto('http://localhost:5173/search', { waitUntil: 'networkidle' });
await p.click('text=technical founder, Berlin, AI infra, enterprise traction, no prior VC backing');
await p.waitForSelector('text=How the system read your query', { timeout: 30000 });
await p.waitForTimeout(1200);
await p.screenshot({ path: `${dir}/search.png`, fullPage: true });
console.log('shot search');

// Dashboard velocity tile
await p.goto('http://localhost:5173/dashboard', { waitUntil: 'networkidle' });
await p.waitForTimeout(2000);
await p.screenshot({ path: `${dir}/dashboard2.png`, fullPage: false });
console.log('shot dashboard');

console.log(errs.length ? 'CONSOLE ERRORS:\n' + errs.slice(0,5).join('\n') : 'no console errors');
await b.close();
