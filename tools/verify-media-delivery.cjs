// Read-only production assets + isolated browser components. No learning API or score submission.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const base = 'https://sherlock-missions-pesuyw9p75offrqtdadiag.streamlit.app/~/+/';
const revision = 'a99d4ad37b2e6b6e02f015e638dff3fdd490190a';
const ids = ['L4A-T1-W01-D29', 'L4A-T1-W01-D30', 'S4A-T1-W01-D27', 'S4A-T1-W01-D28'];
const hash = x => crypto.createHash('sha256').update(x).digest('hex');
const assets = new Map(), first = [];
for (const id of ids) {
  const module = id[0] === 'L' ? 'listening' : 'speaking';
  const course = JSON.parse(fs.readFileSync(path.join(root, 'content', module, id + '.json')));
  const found = [];
  const visit = value => {
    if (!value || typeof value !== 'object') return;
    if (typeof value.audio === 'string') found.push(value.audio);
    for (const item of Object.values(value)) if (typeof item === 'object') visit(item);
  };
  visit(course);
  if (module === 'listening') found.push(`static/audio/listening/${id}/hello.mp3`);
  for (const file of new Set(found)) assets.set(file, fs.readFileSync(path.join(root, file)));
  first.push({ id, file: found[0] });
}
const local = file => `app/${file}?v=${hash(assets.get(file))}`;

async function verifyAssets() {
  let next = 0, checked = 0;
  const entries = [...assets];
  const times = [];
  await Promise.all(Array.from({ length: 4 }, async () => {
    while (next < entries.length) {
      const [file, bytes] = entries[next++], start = Date.now();
      const response = await fetch(new URL(local(file), base), { signal: AbortSignal.timeout(12000) });
      const data = Buffer.from(await response.arrayBuffer());
      if (response.status !== 200 || hash(data) !== hash(bytes)) throw new Error(`asset mismatch: ${file}`);
      times.push(Date.now() - start); checked++;
    }
  }));
  console.log(JSON.stringify({ assetCount: checked, shaMatches: checked,
    maxDownloadMs: Math.max(...times), courses: ids }));
}

async function verifyPlayer() {
  const browser = await chromium.launch({ headless: true,
    args: ['--autoplay-policy=no-user-gesture-required'] });
  const errors = [];
  try {
    const page = await browser.newPage();
    page.on('pageerror', error => errors.push(String(error)));
    await page.route('**/component/listening.audio.limited_audio/index.html*', route => route.fulfill({
      status: 200, contentType: 'text/html',
      body: fs.readFileSync(path.join(root, 'listening/frontend/index.html'), 'utf8'),
    }));
    await page.goto(base + 'component/listening.audio.limited_audio/index.html?streamlitUrl=' + encodeURIComponent(base));
    const results = [];
    for (let index = 0; index < 20; index++) {
      const { id, file } = first[index % first.length];
      await page.evaluate(({ qid, localSource, remoteSource }) => {
        window.dispatchEvent(new MessageEvent('message', { data: { type: 'streamlit:render', args: {
          qid, max_plays: 2, used: 0, local_src: localSource, sources: [remoteSource],
        } } }));
      }, { qid: 'probe-' + index, localSource: local(file),
        remoteSource: `https://raw.githubusercontent.com/summertxia0306-hue/sherlock-missions/${revision}/${file}` });
      const start = Date.now();
      await page.locator('#btn').click();
      await page.waitForFunction(() => window.au.currentTime > 0 && window.used === 1,
        null, { timeout: 10000 });
      const current = await page.evaluate(() => ({ currentSrc: window.au.currentSrc,
        readyState: window.au.readyState, buttonPresent: !!document.getElementById('btn') }));
      if (!current.currentSrc.startsWith(base + 'app/static/audio/') || !current.buttonPresent) {
        throw new Error(`same-origin playback failed: ${JSON.stringify(current)}`);
      }
      results.push({ course: id, startedMs: Date.now() - start, ...current });
    }

    const file = first[0].file;
    await page.route('**/*probe=stall*', async route => {
      await new Promise(resolve => setTimeout(resolve, 6500));
      await route.fulfill({ status: 200, contentType: 'audio/mpeg', body: assets.get(file) }).catch(() => {});
    });
    await page.evaluate(({ primary, backup }) => window.dispatchEvent(new MessageEvent('message', {
      data: { type: 'streamlit:render', args: { qid: 'fault-probe', max_plays: 2, used: 0,
        sources: [primary, backup] } },
    })), { primary: new URL(local(file) + '&probe=stall', base).href,
      backup: new URL(local(file) + '&probe=backup', base).href });
    const start = Date.now();
    await page.locator('#btn').click();
    await page.waitForFunction(() => window.au.currentTime > 0 && window.used === 1,
      null, { timeout: 10000 });
    const fallbackMs = Date.now() - start;
    await page.waitForTimeout(2700); // Let the deliberately late first response arrive.
    const used = await page.evaluate(() => window.used);
    if (used !== 1 || fallbackMs > 6000) throw new Error(`fallback/count failure: ${fallbackMs}ms, ${used}`);
    if (errors.length) throw new Error(errors.join('\n'));
    console.log(JSON.stringify({ realPlaybacks: results.length,
      firstFour: results.slice(0, 4), maxStartMs: Math.max(...results.map(x => x.startedMs)),
      stalledPrimaryFallbackMs: fallbackMs, countedOnceAfterLateResponse: used === 1, pageErrors: 0 }));
  } finally { await browser.close(); }
}

(async () => { await verifyAssets(); await verifyPlayer(); })().catch(error => {
  console.error(error); process.exitCode = 1;
});
