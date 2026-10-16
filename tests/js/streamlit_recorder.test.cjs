const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const html = fs.readFileSync(path.join(__dirname, '../../speaking/frontend/index.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

function harness(options = {}) {
  let now = 1000, sequence = 0, empty = options.empty || 0;
  const tasks = new Map(), listeners = {}, elements = {}, streams = [], contexts = [], sent = [];
  function element() {
    return { style: {}, textContent: '', classList: { toggle() {} },
      set innerHTML(value) { if (value.includes('id="mic"')) elements.mic = element(); } };
  }
  for (const id of ['stage', 'mic', 'hint', 'timer', 'play', 'row', 'err', 'redo', 'use']) {
    elements[id] = element();
  }
  function schedule(fn, delay, repeat = false) {
    const id = ++sequence;
    tasks.set(id, { fn, at: now + delay, repeat: repeat ? delay : 0 });
    return id;
  }
  function advance(ms) {
    const end = now + ms;
    for (let count = 0; count < 10000; count++) {
      let selected;
      for (const item of tasks) {
        if (item[1].at <= end && (!selected || item[1].at < selected[1].at)) selected = item;
      }
      if (!selected) break;
      const [id, task] = selected;
      now = task.at;
      if (task.repeat) task.at += task.repeat; else tasks.delete(id);
      task.fn();
    }
    now = end;
  }
  class Recorder {
    static isTypeSupported(type) { return type === 'audio/mp4'; }
    constructor(stream) { this.stream = stream; this.state = 'inactive'; this.mimeType = 'audio/mp4'; }
    start() { this.state = 'recording'; }
    stop() {
      this.state = 'inactive';
      if (options.neverStops) return;
      schedule(() => {
        // Adversarial device: encoder needs the live track until its final flush.
        const bytes = !this.stream.track.stopped && empty-- <= 0 ? [1, 2, 3, 4] : [];
        this.ondataavailable?.({ data: new Blob([new Uint8Array(bytes)], { type: this.mimeType }) });
        this.onstop?.();
      }, 30);
    }
  }
  class AudioContext {
    constructor() { this.state = 'running'; this.sampleRate = 48000; contexts.push(this); }
    close() { this.state = 'closed'; return Promise.resolve(); }
    decodeAudioData(_buffer, success) {
      const samples = Float32Array.from({ length: 32000 }, (_, i) =>
        0.2 * Math.sin(i * 0.03 + i * i * 0.000013));
      const audio = { length: samples.length, numberOfChannels: 1,
        sampleRate: 48000, getChannelData: () => samples };
      if (options.deferDecode) return new Promise(resolve => {
        options.resolveDecode = () => { success(audio); resolve(audio); };
      });
      success(audio);
      return Promise.resolve(audio);
    }
  }
  const sandbox = {
    Blob, Float32Array, Int16Array, Uint8Array, ArrayBuffer, DataView,
    Date: { now: () => now }, Promise, Math, String, Object,
    btoa: value => Buffer.from(value, 'binary').toString('base64'),
    URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
    document: { body: { scrollHeight: 300 }, getElementById: id => elements[id] },
    navigator: { mediaDevices: { getUserMedia() {
      const track = { stopped: false, stop() { this.stopped = true; } };
      const stream = { track, getTracks: () => [track] };
      streams.push(stream);
      if (options.deferPermission) return new Promise(resolve => { options.resolvePermission = () => resolve(stream); });
      return Promise.resolve(stream);
    } } },
    MediaRecorder: Recorder, AudioContext,
    setTimeout: (fn, ms) => schedule(fn, ms), clearTimeout: id => tasks.delete(id),
    setInterval: (fn, ms) => schedule(fn, ms, true), clearInterval: id => tasks.delete(id),
    addEventListener: (name, fn) => { listeners[name] = fn; },
    parent: { postMessage: value => sent.push(value) },
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(script, context);
  return { context, elements, streams, contexts, sent, advance,
    render(args) { listeners.message({ data: { type: 'streamlit:render', args: {
      qid: '12', take: 1, countdown: 0, max_sec: 20, ...args,
    } } }); } };
}

async function settle() { for (let i = 0; i < 8; i++) await new Promise(setImmediate); }
async function start(h) { h.context.onMicTap(); await settle(); h.advance(1000); }

test('stop waits for the final native chunk before releasing the microphone', async () => {
  const h = harness(); h.render({}); await start(h);
  h.context.stopRecord();
  assert.equal(h.streams[0].track.stopped, false, 'track closed before dataavailable');
  h.advance(30); await settle();
  assert.equal(h.context.state, 'review');
  assert.equal(h.streams[0].track.stopped, true);
  assert.ok(h.context.wavB64);
});

test('a native empty result can be retried successfully on the same last question', async () => {
  const h = harness({ empty: 1 }); h.render({}); await start(h);
  h.context.stopRecord(); h.advance(30); await settle();
  assert.equal(h.context.state, 'idle');
  assert.match(h.elements.err.textContent, /没有生成录音/);
  await start(h); h.context.stopRecord(); h.advance(30); await settle();
  assert.equal(h.context.state, 'review');
  const controls = h.sent.filter(x => x.type === 'streamlit:setComponentValue');
  assert.equal(controls.length, 1);
  assert.equal(controls[0].value.capture_error, 'empty_native');
  assert.equal(controls[0].value.wav_b64, undefined);
});

test('thirty consecutive takes across twelve questions produce separate recordings', async () => {
  const h = harness();
  for (let i = 0; i < 30; i++) {
    h.render({ qid: String(i % 12 + 1), take: Math.floor(i / 12) + 1 });
    await start(h); h.context.stopRecord(); h.advance(30); await settle();
    assert.equal(h.context.state, 'review', `capture ${i + 1}`);
    assert.ok(h.context.wavB64);
  }
  assert.ok(h.streams.every(s => s.track.stopped));
});

test('repeated taps while microphone permission is pending request only one stream', async () => {
  const options = { deferPermission: true }, h = harness(options); h.render({});
  h.context.onMicTap(); h.context.onMicTap();
  assert.equal(h.streams.length, 1);
  options.resolvePermission(); await settle();
});

test('changing question cancels the old countdown and pending microphone permission', async () => {
  const h = harness(); h.render({ countdown: 3 });
  h.context.onMicTap(); await settle();
  h.render({ qid: 'next' }); h.advance(3000); await settle();
  assert.equal(h.context.state, 'idle');
  const options = { deferPermission: true }, pending = harness(options); pending.render({});
  pending.context.onMicTap(); pending.render({ qid: 'next' });
  options.resolvePermission(); await settle();
  assert.equal(pending.context.state, 'idle');
  assert.equal(pending.streams[0].track.stopped, true);
});

test('a missing native stop event releases resources and offers a new recording', async () => {
  const h = harness({ neverStops: true }); h.render({}); await start(h);
  h.context.stopRecord(); h.advance(10000); await settle();
  assert.equal(h.context.state, 'idle');
  assert.equal(h.streams[0].track.stopped, true);
});

test('a cancelled decode cannot put an old recording onto the next question', async () => {
  const options = { deferDecode: true }, h = harness(options); h.render({}); await start(h);
  h.context.stopRecord(); h.advance(30); await settle();
  assert.equal(typeof options.resolveDecode, 'function');
  h.render({ qid: 'next' }); options.resolveDecode(); await settle();
  assert.equal(h.context.state, 'idle');
  assert.equal(h.context.wavB64, null);
  assert.ok(h.contexts.every(c => c.state === 'closed'));
});

test('a decode that never resolves times out and closes its audio context', async () => {
  const options = { deferDecode: true }, h = harness(options); h.render({}); await start(h);
  h.context.stopRecord(); h.advance(30); await settle(); h.advance(10000);
  assert.equal(h.context.state, 'idle');
  assert.ok(h.contexts.every(c => c.state === 'closed'));
  options.resolveDecode(); await settle();
  assert.equal(h.context.wavB64, null);
});

test('an automatic time limit still flushes the native recording before cleanup', async () => {
  const h = harness(); h.render({ max_sec: 1 }); await start(h);
  h.advance(50); await settle();
  assert.equal(h.context.state, 'review');
  assert.equal(h.streams[0].track.stopped, true);
});

test('a late cancelled recorder cannot finish or contaminate the new capture', async () => {
  const h = harness(); h.render({}); await start(h);
  const oldData = h.context.mediaRecorder.ondataavailable;
  const oldStop = h.context.mediaRecorder.onstop;
  h.render({ qid: 'next' }); await start(h);
  oldData({ data: new Blob(['stale']) }); oldStop();
  assert.equal(h.context.state, 'recording');
  h.context.stopRecord(); h.advance(30); await settle();
  assert.equal(h.context.state, 'review');
});

test('an empty microphone trial stays locked and sends no scored-answer event', async () => {
  const h = harness({ empty: 1 }); h.render({ qid: 'test' }); await start(h);
  h.context.stopRecord(); h.advance(30); await settle();
  assert.equal(h.context.state, 'idle');
  assert.equal(h.sent.filter(x => x.type === 'streamlit:setComponentValue').length, 0);
});
