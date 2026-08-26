'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createService, signInternalRequest, parsePcmWav } = require('../core')

function wav({ seconds = 0.5, sampleRate = 16000, amplitude = 0.2 } = {}) {
  const samples = Math.floor(seconds * sampleRate)
  const dataBytes = samples * 2
  const output = Buffer.alloc(44 + dataBytes)
  output.write('RIFF', 0); output.writeUInt32LE(36 + dataBytes, 4); output.write('WAVE', 8)
  output.write('fmt ', 12); output.writeUInt32LE(16, 16); output.writeUInt16LE(1, 20); output.writeUInt16LE(1, 22)
  output.writeUInt32LE(sampleRate, 24); output.writeUInt32LE(sampleRate * 2, 28); output.writeUInt16LE(2, 32); output.writeUInt16LE(16, 34)
  output.write('data', 36); output.writeUInt32LE(dataBytes, 40)
  for (let i = 0; i < samples; i += 1) output.writeInt16LE(Math.round(Math.sin(i / 8) * amplitude * 32767), 44 + i * 2)
  return output
}

function request(overrides = {}) {
  return {
    result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1',
    question_id: 1, attempt: 1, target_text: 'It is bright.', session_marker: '0123456789abcdef',
    data_kind: 'test', wav_base64: wav().toString('base64'), ...overrides
  }
}

describe('private speaking scorer', () => {
  it('accepts only PCM 16k mono WAV with audible input', () => {
    assert.equal(parsePcmWav(wav()).sampleRate, 16000)
    assert.throws(() => parsePcmWav(wav({ sampleRate: 44100 })), /INVALID_AUDIO/)
    assert.throws(() => parsePcmWav(wav({ amplitude: 0 })), /SILENT_AUDIO/)
    assert.throws(() => parsePcmWav(Buffer.alloc(44)), /INVALID_AUDIO/)
    const stereo = wav(); stereo.writeUInt16LE(2, 22)
    assert.throws(() => parsePcmWav(stereo), /INVALID_AUDIO/)
    const float = wav(); float.writeUInt16LE(3, 20)
    assert.throws(() => parsePcmWav(float), /INVALID_AUDIO/)
    const bits = wav(); bits.writeUInt16LE(8, 34)
    assert.throws(() => parsePcmWav(bits), /INVALID_AUDIO/)
  })

  it('requires a valid internal HMAC before evaluation', async () => {
    const service = createService({ internalKey: '1234567890abcdef', evaluator: async () => ({}), uploader: async () => {} })
    await assert.rejects(service.handle({ payload: request(), signature: 'bad' }), /UNAUTHORIZED/)
    assert.throws(() => signInternalRequest({}, 'short'), /CONFIG_ERROR/)
    const invalids = [
      { result_id: '../bad' }, { course_id: 'S01D38' }, { course_version: '' }, { question_id: 9 },
      { attempt: 0 }, { target_text: '' }, { session_marker: 'bad' }, { data_kind: 'production' }, { wav_base64: 'tiny' }
    ]
    for (const patch of invalids) {
      const payload = request(patch)
      await assert.rejects(service.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') }), /INVALID_REQUEST/)
    }
  })

  it('accepts an equivalent payload after CloudBase reorders JSON fields', async () => {
    const original = request()
    const reordered = Object.fromEntries(Object.entries(original).reverse())
    const service = createService({
      internalKey: '1234567890abcdef',
      evaluator: async () => ({ total: 80, is_rejected: false, words: [] }),
      uploader: async () => ({ fileID: 'private-test-recording' })
    })
    const result = await service.handle({ payload: reordered, signature: signInternalRequest(original, '1234567890abcdef') })
    assert.equal(result.total, 80)
  })

  it('evaluates then uploads to the private path for the authenticated data kind', async () => {
    const uploads = []
    const payload = request()
    const service = createService({
      internalKey: '1234567890abcdef',
      evaluator: async ({ text, pcm }) => {
        assert.equal(text, 'It is bright.')
        assert.ok(pcm.length > 1000)
        return { total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [] }
      },
      uploader: async (path, content) => { uploads.push({ path, size: content.length }) }
    })
    const response = await service.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') })
    assert.equal(response.total, 80)
    assert.equal(uploads.length, 1)
    assert.equal(uploads[0].path, 'sherlock-english/test/test/S01D39/123e4567-e89b-42d3-a456-426614174000/q01-take1.wav')
    assert.equal(response.recording_path, uploads[0].path)
    assert.equal(response.recording_file_id, uploads[0].path)
  })

  it('keeps formal recordings isolated from test recordings', async () => {
    const uploads = []
    const payload = request({ data_kind: 'formal' })
    const service = createService({
      internalKey: '1234567890abcdef',
      evaluator: async () => ({ total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [] }),
      uploader: async (path) => { uploads.push(path) }
    })
    await service.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') })
    assert.deepEqual(uploads, ['sherlock-english/formal/formal/S01D39/123e4567-e89b-42d3-a456-426614174000/q01-take1.wav'])
  })

  it('does not upload or turn provider failures into scored attempts', async () => {
    let uploaded = false
    const payload = request()
    const service = createService({
      internalKey: '1234567890abcdef', evaluator: async () => { throw new Error('provider') },
      uploader: async () => { uploaded = true }
    })
    await assert.rejects(service.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') }), /SCORE_UNAVAILABLE/)
    assert.equal(uploaded, false)
    const malformed = createService({ internalKey: '1234567890abcdef', evaluator: async () => ({}), uploader: async () => ({}) })
    await assert.rejects(malformed.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') }), /SCORE_UNAVAILABLE/)
    const uploadFailure = createService({ internalKey: '1234567890abcdef', evaluator: async () => ({ total: 70, is_rejected: false }), uploader: async () => { throw new Error('storage') } })
    await assert.rejects(uploadFailure.handle({ payload, signature: signInternalRequest(payload, '1234567890abcdef') }), /RECORDING_UPLOAD_FAILED/)
  })
})
