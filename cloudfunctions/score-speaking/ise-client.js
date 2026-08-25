'use strict'

const crypto = require('node:crypto')
const { format } = require('node:util')

const HOST = 'ise-api.xfyun.cn'
const PATH = '/v2/open-ise'
const FRAME_SIZE = 1280
const FRAME_INTERVAL_MS = 10

class IseError extends Error {
  constructor(code = 'ISE_UNAVAILABLE') { super(code); this.name = 'IseError'; this.code = code }
}

function buildAuthUrl(apiKey, apiSecret, date = new Date().toUTCString()) {
  const origin = `host: ${HOST}\ndate: ${date}\nGET ${PATH} HTTP/1.1`
  const signature = crypto.createHmac('sha256', apiSecret).update(origin).digest('base64')
  const authorization = Buffer.from(format('api_key="%s", algorithm="hmac-sha256", headers="host date request-line", signature="%s"', apiKey, signature)).toString('base64')
  const query = new URLSearchParams({ authorization, date, host: HOST })
  return `wss://${HOST}${PATH}?${query}`
}

function numberAttr(attrs, name) {
  const match = attrs.match(new RegExp(`\\b${name}="([^"]*)"`))
  const value = match ? Number(match[1]) : NaN
  return Number.isFinite(value) ? value : null
}

function parseResult(xml) {
  const empty = { total: null, accuracy: null, fluency: null, integrity: null, standard: null, is_rejected: false, words: [] }
  if (typeof xml !== 'string' || !xml.includes('<') || !xml.includes('>')) return empty
  const scoredTag = xml.match(/<(?:read_sentence|read_chapter|sentence)\b([^>]*)\btotal_score="[^"]*"[^>]*/i)
    || xml.match(/<[^!?/][^>]*\btotal_score="[^"]*"[^>]*/i)
  if (!scoredTag) return empty
  const attrs = scoredTag[0]
  const words = []
  for (const match of xml.matchAll(/<word\b([^>]*)>/gi)) {
    const content = match[1].match(/\bcontent="([^"]*)"/i)?.[1]?.trim()
    if (!content || ['sil', 'fil'].includes(content)) continue
    words.push({ word: content, score: numberAttr(match[1], 'total_score') })
  }
  return {
    total: numberAttr(attrs, 'total_score'), accuracy: numberAttr(attrs, 'accuracy_score'),
    fluency: numberAttr(attrs, 'fluency_score'), integrity: numberAttr(attrs, 'integrity_score'),
    standard: numberAttr(attrs, 'standard_score'), is_rejected: /\bis_rejected="true"/i.test(attrs), words
  }
}

function firstFrame(appId, text) {
  return {
    common: { app_id: appId },
    business: {
      sub: 'ise', ent: 'en_vip', category: 'read_sentence', cmd: 'ssb', text: `\ufeff${text}`,
      tte: 'utf-8', ttp_skip: true, aue: 'raw', auf: 'audio/L16;rate=16000', rstcd: 'utf8',
      rst: 'entirety', ise_unite: '1', extra_ability: 'multi_dimension', group: 'pupil'
    },
    data: { status: 0 }
  }
}

async function evaluateOnce({ appId, apiKey, apiSecret, text, pcm, timeoutMs = 20000, frameIntervalMs = FRAME_INTERVAL_MS, WebSocketImpl }) {
  if (![appId, apiKey, apiSecret, text].every((value) => typeof value === 'string' && value.length > 0) || !Buffer.isBuffer(pcm) || pcm.length === 0) throw new IseError('ISE_CONFIG_ERROR')
  const WebSocket = WebSocketImpl || require('ws')
  return new Promise((resolve, reject) => {
    let settled = false
    const socket = new WebSocket(buildAuthUrl(apiKey, apiSecret), { handshakeTimeout: timeoutMs })
    const finish = (error, value) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      try { socket.close() } catch {}
      if (error) reject(error); else resolve(value)
    }
    const timer = setTimeout(() => finish(new IseError('ISE_TIMEOUT')), timeoutMs)
    socket.once('error', () => finish(new IseError('ISE_UNAVAILABLE')))
    socket.on('message', (raw) => {
      try {
        const message = JSON.parse(raw.toString())
        if (message.code !== 0) return finish(new IseError(`ISE_${message.code || 'ERROR'}`))
        if (message.data?.status === 2) {
          const xml = Buffer.from(message.data.data || '', 'base64').toString('utf8')
          const parsed = parseResult(xml)
          if (!Number.isFinite(parsed.total) && !parsed.is_rejected) return finish(new IseError('ISE_INVALID_RESULT'))
          finish(null, parsed)
        }
      } catch { finish(new IseError('ISE_INVALID_RESULT')) }
    })
    socket.once('open', async () => {
      try {
        socket.send(JSON.stringify(firstFrame(appId, text)))
        for (let offset = 0; offset < pcm.length; offset += FRAME_SIZE) {
          const chunk = pcm.subarray(offset, offset + FRAME_SIZE)
          const first = offset === 0
          const last = offset + FRAME_SIZE >= pcm.length
          socket.send(JSON.stringify({
            business: { cmd: 'auw', aus: last ? 4 : (first ? 1 : 2) },
            data: { status: last ? 2 : 1, data: chunk.toString('base64') }
          }))
          if (!last && frameIntervalMs) await new Promise((done) => setTimeout(done, frameIntervalMs))
        }
      } catch { finish(new IseError('ISE_UNAVAILABLE')) }
    })
  })
}

async function evaluateRetry(options) {
  try { return await evaluateOnce(options) } catch (first) {
    if (first?.code === 'ISE_CONFIG_ERROR') throw first
    const retryDelayMs = Number.isFinite(options.retryDelayMs) ? options.retryDelayMs : 1000
    if (retryDelayMs > 0) await new Promise((done) => setTimeout(done, retryDelayMs))
    return evaluateOnce(options)
  }
}

module.exports = { IseError, buildAuthUrl, parseResult, evaluateOnce, evaluateRetry, FRAME_INTERVAL_MS }
