'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const crypto = require('node:crypto')
const { createService, hashPassword } = require('../core')

function fixtureCourse() {
  return {
    course_id: 'S01D39', title: 'Speaking', week: 5, day: 4, course_type: 'training', est_minutes: 10,
    questions: Array.from({ length: 8 }, (_, index) => index < 6
      ? { id: index + 1, type: 'repeat', text: `It is bright ${index + 1}.`, audio: `q${index + 1}.mp3`, tag: 'tag' }
      : { id: index + 1, type: 'qa', question: 'What is it?', expected: 'It is bright.', hint: '提示', audio: `q${index + 1}.mp3`, tag: 'tag' })
  }
}

function validWav(dataBytes = 8_000) {
  const output = Buffer.alloc(44 + dataBytes)
  output.write('RIFF', 0); output.writeUInt32LE(36 + dataBytes, 4); output.write('WAVE', 8)
  output.write('fmt ', 12); output.writeUInt32LE(16, 16); output.writeUInt16LE(1, 20); output.writeUInt16LE(1, 22)
  output.writeUInt32LE(16_000, 24); output.writeUInt32LE(32_000, 28); output.writeUInt16LE(2, 32); output.writeUInt16LE(16, 34)
  output.write('data', 36); output.writeUInt32LE(dataBytes, 40)
  for (let offset = 44; offset < output.length; offset += 2) output.writeInt16LE(4_000, offset)
  return output
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

function memoryStore() {
  const sessions = new Map()
  const takes = new Map()
  return {
    sessions, takes, audits: [],
    async getFailures() { return [] }, async recordFailure() {}, async clearFailures() {},
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(hash) { return sessions.get(hash) || null },
    async getSpeakingTake(id) { return takes.get(id) || null },
    async saveSpeakingTake(value) { takes.set(value.take_id, value) },
    async saveAudit(value) { this.audits.push(value) },
    async listParentResults() { return [] }
  }
}

function memoryDirectStore({ cleanupFails = false } = {}) {
  const files = new Map()
  const issued = []
  const removed = []
  let downloads = 0
  return {
    files, issued, removed,
    get downloads() { return downloads },
    async issue(path, options) {
      const fileId = `cloud://test.bucket/${path}`
      issued.push({ path, options, fileId })
      return { upload_url: `https://storage.example.test/${path}?signed=1`, file_id: fileId, expires_in: options.expiresIn }
    },
    async download(fileId) {
      downloads += 1
      if (!files.has(fileId)) throw new Error('missing')
      return Buffer.from(files.get(fileId))
    },
    async remove(fileId) {
      removed.push(fileId)
      if (cleanupFails) throw new Error('cleanup')
      files.delete(fileId)
    }
  }
}

async function setup(options = {}) {
  let nowValue = options.nowValue || 1_700_000_000_000
  const store = options.store || memoryStore()
  const directStore = options.directStore || memoryDirectStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  let scorerCalls = 0
  let scoredBase64 = ''
  const course = options.course || fixtureCourse()
  const service = createService({
    store, passwordHash, hmacKey: '1234567890abcdef', now: () => nowValue,
    randomToken: () => options.formal ? 'formal-token' : 'test-token',
    formalEnabled: options.formal === true,
    speakingDirectUploadEnabled: options.enabled !== false,
    speakingDirectUploadStore: directStore,
    speakingCourseProvider: {
      get: () => ({ course, version: 'version1' }),
      catalog: () => [{ course_id: 'S01D39', course_version: 'version1' }]
    },
    speakingScorer: async (request) => {
      scorerCalls += 1
      scoredBase64 = request.wav_base64
      if (options.scorerError) throw new Error(options.scorerError)
      return {
        ...request, total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [],
        recording_path: `sherlock-english/test/test/${request.course_id}/${request.result_id}/q01-take1.wav`
      }
    }
  })
  const callerId = options.formal ? 'child' : 'parent'
  const auth = options.formal
    ? await service.handle({ action: 'startChildSession' }, { callerId })
    : await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId })
  return {
    service, store, directStore, token: auth.session_token, callerId,
    scorerCalls: () => scorerCalls, scoredBase64: () => scoredBase64,
    advance(ms) { nowValue += ms }
  }
}

function directRequest(bytes, patch = {}) {
  return {
    result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
    byte_length: bytes.length, sha256: sha256(bytes), content_type: 'audio/wav', ...patch
  }
}

describe('TEST speaking direct upload scoring', () => {
  it('exposes only the server-side rollout state in health', async () => {
    const enabled = await setup()
    const disabled = await setup({ enabled: false })
    assert.equal((await enabled.service.handle({ action: 'health' })).speaking_direct_upload_test_enabled, true)
    assert.equal((await disabled.service.handle({ action: 'health' })).speaking_direct_upload_test_enabled, false)
  })

  it('issues one bound ticket, scores the verified WAV, and removes the temporary object', async () => {
    const wav = validWav()
    const context = await setup()
    const issued = await context.service.handle({
      action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav)
    }, { callerId: context.callerId })

    assert.equal(issued.ok, true)
    assert.equal(issued.data_kind, 'test')
    assert.equal(issued.byte_length, wav.length)
    assert.equal(issued.expires_at, new Date(1_700_000_120_000).toISOString())
    assert.equal(Object.hasOwn(issued, 'object_key'), false)
    assert.equal(Object.hasOwn(issued, 'file_id'), false)
    assert.match(context.directStore.issued[0].path, /^sherlock-english\/tmp-speaking-direct\/test\/[a-f0-9]{32}\/[a-f0-9]{64}\.wav$/)
    context.directStore.files.set(context.directStore.issued[0].fileId, wav)

    const response = await context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token,
      request: directRequest(wav), ticket: issued.ticket
    }, { callerId: context.callerId })

    assert.equal(response.stars, 3)
    assert.equal(response.transport, 'direct')
    assert.equal(response.cleaned_up, true)
    assert.equal(typeof response.server_timing.validation_ms, 'number')
    assert.equal(typeof response.server_timing.scoring_ms, 'number')
    assert.equal(context.scoredBase64(), wav.toString('base64'))
    assert.equal(context.scorerCalls(), 1)
    assert.equal(context.directStore.files.size, 0)
    assert.deepEqual(context.store.audits.map((item) => item.action).filter((action) => action.includes('direct_upload')), [
      'speaking_test_direct_upload_issued', 'speaking_test_direct_upload_scored'
    ])
  })

  it('returns the cached take before downloading after an ambiguous response loss', async () => {
    const wav = validWav()
    const context = await setup()
    const issued = await context.service.handle({
      action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav)
    }, { callerId: context.callerId })
    context.directStore.files.set(context.directStore.issued[0].fileId, wav)
    const first = await context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token, request: directRequest(wav), ticket: issued.ticket
    }, { callerId: context.callerId })
    const downloads = context.directStore.downloads

    const repeated = await context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token, request: directRequest(wav), ticket: issued.ticket
    }, { callerId: context.callerId })

    assert.equal(repeated.proof, first.proof)
    assert.equal(repeated.idempotent, true)
    assert.equal(context.scorerCalls(), 1)
    assert.equal(context.directStore.downloads, downloads)
  })

  it('is disabled by default and rejects formal sessions', async () => {
    const wav = validWav()
    const disabled = await setup({ enabled: false })
    await assert.rejects(disabled.service.handle({
      action: 'createSpeakingDirectUpload', session_token: disabled.token, request: directRequest(wav)
    }, { callerId: disabled.callerId }), /SPEAKING_DIRECT_UPLOAD_DISABLED/)

    const formal = await setup({ formal: true })
    await assert.rejects(formal.service.handle({
      action: 'createSpeakingDirectUpload', session_token: formal.token, request: directRequest(wav)
    }, { callerId: formal.callerId }), /UNAUTHORIZED/)
    assert.equal(formal.directStore.issued.length, 0)
  })

  it('rejects hidden test-only courses without changing the existing chunk test path', async () => {
    const wav = validWav()
    const hidden = await setup({ course: { ...fixtureCourse(), publication_status: 'test' } })

    await assert.rejects(hidden.service.handle({
      action: 'createSpeakingDirectUpload', session_token: hidden.token, request: directRequest(wav)
    }, { callerId: hidden.callerId }), /COURSE_NOT_FORMAL/)

    assert.equal(hidden.directStore.issued.length, 0)
  })

  it('rejects invalid declarations, tampered tickets, and expired tickets before scoring', async () => {
    const wav = validWav()
    const context = await setup()
    for (const patch of [
      { byte_length: 767 }, { byte_length: 700_001 }, { sha256: 'bad' },
      { content_type: 'application/octet-stream' }, { question_id: 9 }
    ]) {
      await assert.rejects(context.service.handle({
        action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav, patch)
      }, { callerId: context.callerId }), /INVALID_SPEAKING/)
    }

    const issued = await context.service.handle({
      action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav)
    }, { callerId: context.callerId })
    await assert.rejects(context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token,
      request: directRequest(wav), ticket: `${issued.ticket}x`
    }, { callerId: context.callerId }), /INVALID_SPEAKING_DIRECT_TICKET/)

    context.advance(120_001)
    await assert.rejects(context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token,
      request: directRequest(wav), ticket: issued.ticket
    }, { callerId: context.callerId }), /SPEAKING_DIRECT_TICKET_EXPIRED/)
    assert.equal(context.scorerCalls(), 0)
  })

  it('cleans corrupt and scorer-failed objects without creating a valid take', async () => {
    const expected = validWav()
    for (const scenario of ['hash', 'scorer']) {
      const context = await setup(scenario === 'scorer' ? { scorerError: 'ISE_TIMEOUT' } : {})
      const issued = await context.service.handle({
        action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(expected)
      }, { callerId: context.callerId })
      const actual = scenario === 'hash' ? Buffer.from(expected).fill(3, 100, 110) : expected
      context.directStore.files.set(context.directStore.issued[0].fileId, actual)
      await assert.rejects(context.service.handle({
        action: 'scoreDirectUploadedSpeakingTake', session_token: context.token,
        request: directRequest(expected), ticket: issued.ticket
      }, { callerId: context.callerId }), scenario === 'hash' ? /SPEAKING_DIRECT_INTEGRITY_FAILED/ : /ISE_TIMEOUT/)
      assert.equal(context.directStore.files.size, 0)
      assert.equal(context.store.takes.size, 0)
    }
  })

  it('reports cleanup failure without discarding an otherwise successful score', async () => {
    const wav = validWav()
    const context = await setup({ directStore: memoryDirectStore({ cleanupFails: true }) })
    const issued = await context.service.handle({
      action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav)
    }, { callerId: context.callerId })
    context.directStore.files.set(context.directStore.issued[0].fileId, wav)

    const response = await context.service.handle({
      action: 'scoreDirectUploadedSpeakingTake', session_token: context.token,
      request: directRequest(wav), ticket: issued.ticket
    }, { callerId: context.callerId })

    assert.equal(response.stars, 3)
    assert.equal(response.cleaned_up, false)
    assert.equal(context.store.takes.size, 1)
    assert.equal(context.store.audits.some((item) => item.action === 'speaking_test_direct_upload_cleanup_failed'), true)
  })

  it('cancels only the exact ticket object, including after ticket expiry', async () => {
    const wav = validWav()
    const context = await setup()
    const issued = await context.service.handle({
      action: 'createSpeakingDirectUpload', session_token: context.token, request: directRequest(wav)
    }, { callerId: context.callerId })
    context.directStore.files.set(context.directStore.issued[0].fileId, wav)
    context.advance(120_001)

    const cancelled = await context.service.handle({
      action: 'cancelSpeakingDirectUpload', session_token: context.token, ticket: issued.ticket
    }, { callerId: context.callerId })

    assert.deepEqual(cancelled, { ok: true, data_kind: 'test', cleaned_up: true })
    assert.equal(context.directStore.files.size, 0)
    assert.equal(context.store.audits.some((item) => item.action === 'speaking_test_direct_upload_cancelled'), true)
  })
})
