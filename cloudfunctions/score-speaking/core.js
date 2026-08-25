'use strict'

const crypto = require('node:crypto')

class ScoreError extends Error {
  constructor(code) { super(code); this.name = 'ScoreError'; this.code = code }
}

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().filter((key) => value[key] !== undefined)
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

function signInternalRequest(payload, key) {
  if (typeof key !== 'string' || key.length < 16) throw new ScoreError('CONFIG_ERROR')
  return crypto.createHmac('sha256', key).update(canonicalJson(payload)).digest('base64url')
}

function verifySignature(payload, signature, key) {
  if (typeof signature !== 'string') return false
  let expected
  try { expected = signInternalRequest(payload, key) } catch { return false }
  const left = Buffer.from(signature)
  const right = Buffer.from(expected)
  return left.length === right.length && crypto.timingSafeEqual(left, right)
}

function parsePcmWav(wav) {
  if (!Buffer.isBuffer(wav) || wav.length < 44 || wav.subarray(0, 4).toString() !== 'RIFF' || wav.subarray(8, 12).toString() !== 'WAVE') throw new ScoreError('INVALID_AUDIO')
  let offset = 12
  let format
  let pcm
  while (offset + 8 <= wav.length) {
    const id = wav.subarray(offset, offset + 4).toString()
    const size = wav.readUInt32LE(offset + 4)
    const start = offset + 8
    const end = start + size
    if (end > wav.length) throw new ScoreError('INVALID_AUDIO')
    if (id === 'fmt ' && size >= 16) format = {
      encoding: wav.readUInt16LE(start), channels: wav.readUInt16LE(start + 2), sampleRate: wav.readUInt32LE(start + 4), bits: wav.readUInt16LE(start + 14)
    }
    if (id === 'data') pcm = wav.subarray(start, end)
    offset = end + (size % 2)
  }
  if (!format || !pcm || format.encoding !== 1 || format.channels !== 1 || format.sampleRate !== 16000 || format.bits !== 16 || pcm.length < 8000 || pcm.length > 640000 || pcm.length % 2) throw new ScoreError('INVALID_AUDIO')
  let peak = 0
  for (let index = 0; index < pcm.length; index += 2) peak = Math.max(peak, Math.abs(pcm.readInt16LE(index)) / 32768)
  if (peak < 0.01) throw new ScoreError('SILENT_AUDIO')
  return { pcm, sampleRate: format.sampleRate, peak }
}

function safeSegment(value, pattern) {
  return typeof value === 'string' && pattern.test(value)
}

function validatePayload(payload) {
  if (!payload || !safeSegment(payload.result_id, /^[A-Za-z0-9-]{1,80}$/)
    || !safeSegment(payload.course_id, /^S01D(?:39|4\d|50)$/)
    || !safeSegment(payload.course_version, /^[A-Za-z0-9_-]{1,40}$/)
    || !Number.isInteger(payload.question_id) || payload.question_id < 1 || payload.question_id > 8
    || !Number.isInteger(payload.attempt) || payload.attempt < 1 || payload.attempt > 3
    || typeof payload.target_text !== 'string' || payload.target_text.length < 1 || payload.target_text.length > 500
    || !safeSegment(payload.session_marker, /^[a-f0-9]{16}$/)
    || typeof payload.wav_base64 !== 'string' || payload.wav_base64.length < 1024 || payload.wav_base64.length > 900000) throw new ScoreError('INVALID_REQUEST')
}

function createService({ internalKey, evaluator, uploader }) {
  return {
    async handle(event = {}) {
      if (!verifySignature(event.payload, event.signature, internalKey)) throw new ScoreError('UNAUTHORIZED')
      validatePayload(event.payload)
      let wav
      try { wav = Buffer.from(event.payload.wav_base64, 'base64') } catch { throw new ScoreError('INVALID_AUDIO') }
      const { pcm } = parsePcmWav(wav)
      let evaluation
      try { evaluation = await evaluator({ text: event.payload.target_text, pcm }) } catch (error) {
        const code = typeof error?.code === 'string' && /^ISE_(?:[0-9]{1,8}|TIMEOUT|UNAVAILABLE|INVALID_RESULT|CONFIG_ERROR)$/.test(error.code)
          ? error.code : 'SCORE_UNAVAILABLE'
        throw new ScoreError(code)
      }
      if (!evaluation || (!Number.isFinite(evaluation.total) && !evaluation.is_rejected)) throw new ScoreError('SCORE_UNAVAILABLE')
      const qid = String(event.payload.question_id).padStart(2, '0')
      const recordingPath = `sherlock-english/test/test/${event.payload.course_id}/${event.payload.result_id}/q${qid}-take${event.payload.attempt}.wav`
      let uploaded
      try { uploaded = await uploader(recordingPath, wav) } catch { throw new ScoreError('RECORDING_UPLOAD_FAILED') }
      return {
        course_id: event.payload.course_id, course_version: event.payload.course_version,
        question_id: event.payload.question_id, attempt: event.payload.attempt,
        total: evaluation.total ?? null, accuracy: evaluation.accuracy ?? null, fluency: evaluation.fluency ?? null,
        integrity: evaluation.integrity ?? null, is_rejected: Boolean(evaluation.is_rejected),
        words: Array.isArray(evaluation.words) ? evaluation.words.slice(0, 80) : [], recording_path: recordingPath,
        recording_file_id: typeof uploaded?.fileID === 'string' ? uploaded.fileID : recordingPath
      }
    }
  }
}

module.exports = { ScoreError, signInternalRequest, parsePcmWav, createService }
