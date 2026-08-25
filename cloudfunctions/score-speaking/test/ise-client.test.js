'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { EventEmitter } = require('node:events')
const { buildAuthUrl, parseResult, evaluateOnce, evaluateRetry, FRAME_INTERVAL_MS } = require('../ise-client')

const successXml = '<xml><rec_paper><read_sentence total_score="78.5" accuracy_score="77" fluency_score="76" integrity_score="80" standard_score="79" is_rejected="false"><word content="bright" total_score="31"/></read_sentence></rec_paper></xml>'

class FakeSocket extends EventEmitter {
  static mode = 'success'
  static instances = 0
  static last = null
  constructor() {
    super(); FakeSocket.instances += 1
    this.frames = []; FakeSocket.last = this
    queueMicrotask(() => FakeSocket.mode === 'socket-error' ? this.emit('error', new Error('network')) : this.emit('open'))
  }
  send(raw) {
    const frame = JSON.parse(raw)
    this.frames.push(frame)
    if (frame.data?.status !== 2) return
    queueMicrotask(() => {
      if (FakeSocket.mode === 'provider-error') this.emit('message', Buffer.from(JSON.stringify({ code: 10163 })))
      else if (FakeSocket.mode === 'invalid') this.emit('message', Buffer.from(JSON.stringify({ code: 0, data: { status: 2, data: Buffer.from('<bad').toString('base64') } })))
      else this.emit('message', Buffer.from(JSON.stringify({ code: 0, data: { status: 2, data: Buffer.from(successXml).toString('base64') } })))
    })
  }
  close() {}
}

describe('Xunfei ISE protocol adapter', () => {
  it('builds a deterministic signed websocket URL without exposing the secret', () => {
    const url = buildAuthUrl('api-key', 'api-secret', 'Tue, 25 Aug 2026 00:00:00 GMT')
    assert.match(url, /^wss:\/\/ise-api\.xfyun\.cn\/v2\/open-ise\?/)
    assert.match(url, /authorization=/)
    assert.equal(url.includes('api-secret'), false)
  })

  it('parses sentence dimensions, rejection, and word scores defensively', () => {
    const xml = successXml.replace('</read_sentence>', '<word content="sil" total_score="0"/></read_sentence>')
    assert.deepEqual(parseResult(xml), {
      total: 78.5, accuracy: 77, fluency: 76, integrity: 80, standard: 79,
      is_rejected: false, words: [{ word: 'bright', score: 31 }]
    })
    assert.equal(parseResult('<bad').total, null)
  })

  it('streams frames and resolves only the final valid result', async () => {
    FakeSocket.mode = 'success'
    const result = await evaluateOnce({ appId: 'app', apiKey: 'key', apiSecret: 'secret', text: 'It is bright.', pcm: Buffer.alloc(3000, 1), frameIntervalMs: 0, WebSocketImpl: FakeSocket })
    assert.equal(result.total, 78.5)
  })

  it('mirrors the verified legacy Streamlit English request contract', async () => {
    FakeSocket.mode = 'success'
    await evaluateOnce({ appId: 'app', apiKey: 'key', apiSecret: 'secret', text: 'It is bright.', pcm: Buffer.alloc(3000, 1), frameIntervalMs: 0, WebSocketImpl: FakeSocket })
    const [parameters, ...audioFrames] = FakeSocket.last.frames
    assert.equal(parameters.business.text, '\ufeffIt is bright.')
    assert.equal(parameters.business.group, 'pupil')
    assert.equal(FRAME_INTERVAL_MS, 10)
    assert.deepEqual(audioFrames.map((frame) => [frame.business.aus, frame.data.status, frame.data.data.length > 0]), [
      [1, 1, true], [2, 1, true], [4, 2, true]
    ])
  })

  it('maps socket, provider, and malformed-result failures to stable errors', async () => {
    for (const mode of ['socket-error', 'provider-error', 'invalid']) {
      FakeSocket.mode = mode
      await assert.rejects(evaluateOnce({ appId: 'app', apiKey: 'key', apiSecret: 'secret', text: 'Text', pcm: Buffer.alloc(2000), frameIntervalMs: 0, WebSocketImpl: FakeSocket }), /ISE_/)
    }
    await assert.rejects(evaluateOnce({ appId: '', apiKey: 'key', apiSecret: 'secret', text: 'Text', pcm: Buffer.alloc(1), WebSocketImpl: FakeSocket }), /ISE_CONFIG_ERROR/)
  })

  it('retries one transient failure and then succeeds', async () => {
    let instances = 0
    class RetrySocket extends FakeSocket {
      failed = false
      constructor() {
        super()
        instances += 1
      }
      send(raw) {
        if (instances === 1) {
          if (!this.failed) { this.failed = true; queueMicrotask(() => this.emit('error', new Error('first'))) }
          return
        }
        super.send(raw)
      }
    }
    FakeSocket.mode = 'success'
    const result = await evaluateRetry({ appId: 'app', apiKey: 'key', apiSecret: 'secret', text: 'Text', pcm: Buffer.alloc(2000, 1), frameIntervalMs: 0, retryDelayMs: 0, WebSocketImpl: RetrySocket })
    assert.equal(result.total, 78.5)
    assert.equal(instances, 2)
  })
})
