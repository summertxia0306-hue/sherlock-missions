// Read-only live deployment/asset checks. Never start a formal course or submit answers.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const host = 'https://sherlock-missions-pesuyw9p75offrqtdadiag.streamlit.app/';
const base = host + '~/+/';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const plan = JSON.parse(fs.readFileSync(path.join(root, 'content/drafts/4A-T1-W01-UNIT5/audio-generation-plan.json')));
const revision = process.argv[2];

async function checkedFetch(url, expected) {
  let failure;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(15000) });
      const bytes = Buffer.from(await response.arrayBuffer());
      assert.equal(response.status, 200, url);
      if (expected) assert.equal(sha(bytes), sha(expected), url);
      return bytes;
    } catch (error) { failure = error; }
  }
  throw failure;
}

async function main() {
  assert.equal(plan.items.length, 154);
  assert.match(revision || '', /^[a-f0-9]{40}$/, 'Pass the fixed Unit 5 content commit');
  let next = 0, checked = 0;
  await Promise.all(Array.from({ length: 4 }, async () => {
    while (next < plan.items.length) {
      const item = plan.items[next++];
      const bytes = fs.readFileSync(path.join(root, item.path));
      await checkedFetch(new URL('app/' + item.path + '?v=' + sha(bytes), base), bytes);
      await checkedFetch(`https://raw.githubusercontent.com/summertxia0306-hue/sherlock-missions/${revision}/${item.path}`, bytes);
      checked++;
    }
  }));
  console.log(JSON.stringify({ sameOriginAudioShaMatches: checked, immutableBackupShaMatches: checked, revision }));
  const normalize = value => Buffer.from(value.toString('utf8').replaceAll('\r\n', '\n'));
  for (const [module, local] of [
    ['listening.audio.limited_audio', 'listening/frontend/index.html'],
    ['speaking.recorder.sherlock_recorder', 'speaking/frontend/index.html'],
  ]) {
    const online = await checkedFetch(base + 'component/' + module + '/index.html');
    assert.equal(sha(normalize(online)), sha(normalize(fs.readFileSync(path.join(root, local)))));
  }
  console.log(JSON.stringify({ deployedPlayerAndRecorderMatchLocal: true }));
  const browser = await chromium.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  try {
    const page = await browser.newPage();
    const pageErrors = [];
    page.on('pageerror', e => pageErrors.push(String(e)));
    const pages = [];
    for (let day = 31; day <= 35; day++) {
      for (const prefix of ['L', 'S']) {
        const id = prefix + '4A-T1-W01-D' + day;
        await page.goto(host + '?course_id=' + id, { waitUntil: 'domcontentloaded' });
        const app = page.frameLocator('iframe[title="streamlitApp"]');
        await app.getByRole('heading', { name: new RegExp('第' + day + '课') }).waitFor({ timeout: 45000 });
        assert.equal(await app.locator('[data-testid="stException"]').count(), 0, id);
        const expected = prefix === 'L' ? (day <= 33 ? 20 : 25) : (day <= 32 ? 10 : 12);
        const body = await app.locator('body').innerText();
        assert.ok(body.includes('共 ' + expected + ' 题'), id + ' wrong count');
        const component = prefix === 'L' ? 'limited_audio' : 'sherlock_recorder';
        const button = app.frameLocator('iframe[title*="' + component + '"]').locator(prefix === 'L' ? '#btn' : '#mic');
        await button.waitFor({ state: 'visible', timeout: 15000 });
        if (prefix === 'L') {
          const args = await button.evaluate(() => ({ sources: window.args.sources, local: window.args.local_src }));
          assert.ok(args.sources[0].includes(revision), id + ' stale backup revision');
          assert.ok(args.local.startsWith('app/static/audio/listening/' + id + '/'), id + ' stale same-origin source');
        }
        pages.push({ course: id, count: expected, controlVisible: true });
      }
    }
    console.log(JSON.stringify({ liveCoursePages: pages }));
    const playerUrl = base + 'component/listening.audio.limited_audio/index.html?streamlitUrl=' + encodeURIComponent(base);
    await page.goto(playerUrl);
    const playback = [];
    for (let day = 31; day <= 35; day++) {
      const course = JSON.parse(fs.readFileSync(path.join(root, `content/speaking/S4A-T1-W01-D${day}.json`)));
      for (const q of [course.questions[0], course.questions.at(-1)]) {
        const bytes = fs.readFileSync(path.join(root, q.audio));
        await page.evaluate(({ qid, src }) => window.dispatchEvent(new MessageEvent('message', {
          data: { type: 'streamlit:render', args: { qid, max_plays: 2, used: 0, local_src: src, sources: [] } },
        })), { qid: course.course_id + '-' + q.id, src: 'app/' + q.audio + '?v=' + sha(bytes) });
        const start = Date.now();
        await page.locator('#btn').click();
        await page.waitForFunction(() => window.au.currentTime > 0 && window.used === 1, null, { timeout: 12000 });
        playback.push({ course: course.course_id, question: q.id, startedMs: Date.now() - start });
      }
    }
    assert.equal(pageErrors.length, 0, pageErrors.join('\n'));
    console.log(JSON.stringify({ standaloneLivePlayerPlaybacks: playback, pageErrors: 0, learningResultsSubmitted: 0 }));
  } finally { await browser.close(); }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
