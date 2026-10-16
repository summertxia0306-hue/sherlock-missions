/* Native browser capture with generated audio; never uses a real microphone or results API.
 * Requires Playwright and installed Chromium (may be supplied through NODE_PATH).
 * RECORDER_BROWSER=webkit/all also checks builds with Web Audio and MediaRecorder.
 */
const fs = require('node:fs');
const path = require('node:path');
const { chromium, webkit } = require('playwright');

const syntheticMicrophone = `<script>
window.__syntheticStreams = [];
window.__captureEvents = [];
var NativeRecorder=window.MediaRecorder;
if(NativeRecorder) window.MediaRecorder=class extends NativeRecorder {
  constructor(stream, options) {
    super(stream, options);
    for (var type of ['start','dataavailable','stop','error']) {
      this.addEventListener(type, event => window.__captureEvents.push({
        type:event.type, bytes:event.data?.size, mime:this.mimeType,
        tracks:stream.getTracks().map(t=>t.readyState)
      }));
    }
  }
};
Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: {
  getUserMedia: async function() {
    var audio = new (window.AudioContext || window.webkitAudioContext)();
    await audio.resume();
    window.__syntheticAudio = audio;
    var buffer = audio.createBuffer(1, audio.sampleRate * 3, audio.sampleRate);
    var samples = buffer.getChannelData(0), seed = 173;
    for (var i=0;i<samples.length;i++) {
      seed = (seed * 16807) % 2147483647;
      samples[i] = 0.15 * (seed / 2147483647 * 2 - 1);
    }
    var source=audio.createBufferSource(), destination=audio.createMediaStreamDestination();
    source.buffer=buffer; source.loop=true; source.connect(destination); source.start();
    var stream=destination.stream;
    stream.getTracks().forEach(function(track) {
      var original=track.stop.bind(track);
      track.stop=function() { original(); source.stop(); audio.close().catch(function(){}); };
    });
    window.__syntheticStreams.push(stream);
    return stream;
  }
} });
</script>`;
const html = fs.readFileSync(path.join(__dirname, '../speaking/frontend/index.html'), 'utf8')
  .replace('<head>', '<head>' + syntheticMicrophone);

async function verify(name, engine) {
  const browser = await engine.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    await page.setContent(html);
    const capabilities = await page.evaluate(() => ({
      recorder: typeof window.MediaRecorder === 'function',
      audioContext: typeof (window.AudioContext || window.webkitAudioContext) === 'function',
    }));
    if (!capabilities.recorder || !capabilities.audioContext) {
      return { browser: name, status: 'unavailable', capabilities };
    }
    const captures = [];
    for (let index = 0; index < 30; index++) {
      if (index < 12) {
        await page.evaluate(qid => window.dispatchEvent(new MessageEvent('message', {
          data: { type: 'streamlit:render', args: { qid: String(qid), take: 1,
            countdown: 0, max_sec: 20 } },
        })), index + 1);
      } else {
        await page.locator('#redo').click(); // Same Q12/take, no Streamlit reset.
      }
      await page.locator('#mic').click();
      try {
        await page.waitForFunction(() => window.state === 'recording', null, { timeout: 10000 });
      } catch (error) {
        const diagnostic = await page.evaluate(() => ({ state: window.state,
          error: document.getElementById('err').textContent,
          recorder: typeof window.MediaRecorder, events: window.__captureEvents,
          streams: window.__syntheticStreams.length }));
        throw new Error(`${name} start ${index + 1}: ${JSON.stringify(diagnostic)}; ${errors}`);
      }
      // Headless audio may start later than wall-clock input. Measure the audio
      // clock so this stress test actually supplies more than 0.4s of samples.
      const audioStart = await page.evaluate(() => window.__syntheticAudio.currentTime);
      await page.waitForFunction(start => window.__syntheticAudio.currentTime - start >= 1.4,
        audioStart, { timeout: 10000 });
      await page.locator('#mic').click();
      await page.waitForFunction(() => window.state === 'review' || window.state === 'idle',
        null, { timeout: 12000 });
      const result = await page.evaluate(() => ({
        state: window.state, error: document.getElementById('err').textContent,
        bytes: window.wavB64 ? atob(window.wavB64).length : 0,
        ended: window.__syntheticStreams.every(s => s.getTracks().every(t => t.readyState === 'ended')),
        events: window.__captureEvents.slice(-4),
      }));
      if (result.state !== 'review' || result.bytes < 12844 || !result.ended) {
        throw new Error(`${name} capture ${index + 1}: ${JSON.stringify(result)}`);
      }
      captures.push(result.bytes);
    }
    if (errors.length) throw new Error(errors.join('\n'));
    return { browser: name, status: 'passed', captures: captures.length,
      minimumWavBytes: Math.min(...captures), allTracksReleased: true, pageErrors: 0 };
  } finally { await browser.close(); }
}

(async () => {
  const engines = [['chromium', chromium], ['webkit', webkit]];
  const requested = process.env.RECORDER_BROWSER || 'chromium';
  for (const [name, engine] of engines.filter(([name]) => requested === 'all' || requested === name)) {
    const result = await verify(name, engine);
    console.log(JSON.stringify(result));
    if (result.status !== 'passed') process.exitCode = 1;
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
