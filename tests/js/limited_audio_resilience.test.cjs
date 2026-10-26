const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const script = fs.readFileSync(path.join(__dirname, '../../listening/frontend/index.html'), 'utf8')
  .match(/<script>([\s\S]*?)<\/script>/)[1];

function harness() {
  let now = 1000, sequence = 0;
  const tasks = new Map(), sent = [], requests = [], listeners = {};
  const elements = Object.fromEntries(['au', 'btn', 'cnt', 'err'].map(id => [id,
    { style: {}, innerHTML: '', textContent: '', disabled: false, currentTime: 0 }]));
  const au = elements.au;
  au.pause = () => {};
  au.load = () => {};
  au.play = () => new Promise((resolve, reject) => {
    requests.push({ src: au.src, resolve, reject });
  });
  const sandbox = { URL, URLSearchParams, Promise, Date: { now: () => now },
    document: { body: { scrollHeight: 150 }, getElementById: id => elements[id] },
    location: { origin: 'https://example.test', search: '?streamlitUrl=https%3A%2F%2Fexample.test%2F~%2F%2B%2F' },
    parent: { postMessage: x => sent.push(x) },
    addEventListener: (name, fn) => { listeners[name] = fn; },
    setTimeout: (fn, delay) => { const id = ++sequence; tasks.set(id, { fn, at: now + delay }); return id; },
    clearTimeout: id => tasks.delete(id),
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(script, context);
  return { context, elements, requests, sent,
    render(extra = {}) { listeners.message({ data: { type: 'streamlit:render', args: {
      qid: 'q1', used: 0, max_plays: 2,
      sources: ['https://slow.test/audio.mp3', 'https://backup.test/audio.mp3'], ...extra,
    } } }); },
    advance(ms) {
      const end = now + ms;
      for (let i = 0; i < 100; i++) {
        const task = [...tasks].filter(x => x[1].at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!task) break;
        now = task[1].at; tasks.delete(task[0]); task[1].fn();
      }
      now = end;
    } };
}
async function settle() { await new Promise(setImmediate); }

test('the served app audio is preferred and keeps the Streamlit proxy prefix', () => {
  const h = harness(); h.render({ local_src: 'app/static/audio/course/q01.mp3?v=abc' });
  h.elements.btn.onclick();
  assert.equal(h.requests[0].src, 'https://example.test/~/+/app/static/audio/course/q01.mp3?v=abc');
});

test('a source that never starts switches within four seconds without charging a play', async () => {
  const h = harness(); h.render(); h.elements.btn.onclick(); h.advance(4000);
  assert.equal(h.requests.length, 2);
  assert.equal(h.context.used, 0);
  h.requests[1].resolve(); await settle();
  assert.equal(h.context.used, 1);
});

test('a late promise from the abandoned source cannot consume a play', async () => {
  const h = harness(); h.render(); h.elements.btn.onclick();
  h.context.failSource(h.context.playToken, 0);
  h.requests[0].resolve(); await settle();
  assert.equal(h.context.used, 0);
  h.requests[1].resolve(); await settle();
  assert.equal(h.context.used, 1);
});

test('changing audio cancels pending callbacks and does not count on the next question', async () => {
  const h = harness(); h.render(); h.elements.btn.onclick();
  h.render({ qid: 'q2', sources: ['https://new.test/next.mp3'] });
  h.requests[0].resolve(); await settle(); h.advance(10000);
  assert.equal(h.context.used, 0);
  assert.equal(h.elements.btn.disabled, false);
});

test('all stalled sources fail visibly and the button is usable again', () => {
  const h = harness(); h.render(); h.elements.btn.onclick(); h.advance(9000);
  assert.equal(h.context.playing, false);
  assert.equal(h.context.used, 0);
  assert.equal(h.elements.err.style.display, 'block');
  assert.equal(h.elements.btn.disabled, false);
});

test('a mid-playback media error does not leave the play button locked forever', async () => {
  const h = harness(); h.render(); h.elements.btn.onclick();
  h.requests[0].resolve(); await settle(); h.elements.au.onerror();
  assert.equal(h.context.playing, false);
  assert.equal(h.elements.btn.disabled, false);
  assert.equal(h.context.used, 1);
});
