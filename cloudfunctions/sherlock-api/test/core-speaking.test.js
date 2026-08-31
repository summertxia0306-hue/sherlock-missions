'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const crypto = require('node:crypto')
const { createService, hashPassword } = require('../core')

function fixtureCourse() {
  return {
    course_id: 'S01D39', title: 'Speaking', week: 5, day: 4, course_type: 'training', est_minutes: 10,
    questions: Array.from({ length: 8 }, (_, index) => index < 6
      ? { id: index + 1, type: 'repeat', text: `It is bright ${index + 1}.`, audio: `static/audio/speaking/S01D39/q0${index + 1}.mp3`, tag: 'tag' }
      : { id: index + 1, type: 'qa', question: 'What is it?', expected: 'It is bright.', hint: '用英语说：它很明亮。', audio: `static/audio/speaking/S01D39/q0${index + 1}.mp3`, tag: 'tag' })
  }
}

function memoryStore() {
  const sessions = new Map()
  const results = new Map()
  const takes = new Map()
  return {
    sessions, results, takes,
    async getFailures() { return [] }, async recordFailure() {}, async clearFailures() {},
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(hash) { return sessions.get(hash) || null },
    async saveResult(value) { results.set(value.result_id, value) },
    async getResult(id) { return results.get(id) || null },
    async updateResult(id, patch) { Object.assign(results.get(id), patch) },
    async listResults() { return [...results.values()] },
    async getSpeakingTake(id) { return takes.get(id) || null },
    async saveSpeakingTake(value) { takes.set(value.take_id, value) },
    async saveAudit() {}
  }
}

function memoryUploadStore() {
  const files = new Map()
  const removed = []
  return {
    files,
    removed,
    async upload(path, bytes) {
      files.set(path, Buffer.from(bytes))
      return { fileID: `cloud://test.bucket/${path}` }
    },
    async download(fileId) {
      const path = fileId.replace('cloud://test.bucket/', '')
      if (!files.has(path)) throw new Error('missing')
      return Buffer.from(files.get(path))
    },
    async remove(fileIds) {
      removed.push(...fileIds)
      for (const fileId of fileIds) files.delete(fileId.replace('cloud://test.bucket/', ''))
    }
  }
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

async function setup(scorer, { formal = false } = {}) {
  const store = memoryStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  const service = createService({
    store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
    formalEnabled: formal,
    speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
    speakingScorer: scorer,
    speakingRecordingUrl: async () => 'https://private.example.test/recording.wav'
  })
  const callerId = formal ? 'child' : 'parent'
  const auth = formal
    ? await service.handle({ action: 'startChildSession' }, { callerId })
    : await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId })
  return { store, service, token: auth.session_token, callerId }
}

function termCourse() {
  return {
    ...fixtureCourse(), course_id: 'S4A-T1-W01-D01', pair_id: '4A-T1-W01-D01',
    study_pack: '4A-T1-W01-D01', publication_status: 'test',
    questions: fixtureCourse().questions.map((question) => ({
      ...question, audio: question.audio.replace('S01D39', 'S4A-T1-W01-D01')
    }))
  }
}

describe('P3 speaking API', () => {
  it('uploads bounded private chunks, reassembles the WAV, and reuses the existing scoring contract', async () => {
    let scoredBase64 = ''
    const uploadStore = memoryUploadStore()
    const scorer = async (request) => {
      scoredBase64 = request.wav_base64
      return {
        ...request, total: 80, is_rejected: false, words: [],
        recording_path: 'sherlock-english/test/test/S01D39/r1/q01-take1.wav'
      }
    }
    const store = memoryStore()
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({
      store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
      speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
      speakingScorer: scorer, speakingUploadStore: uploadStore
    })
    const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
    const wav = Buffer.alloc(100_000, 9)
    const wavBase64 = wav.toString('base64')
    const chunks = wavBase64.match(/.{1,65536}/g)
    const common = {
      result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
      chunk_count: chunks.length, wav_byte_length: wav.length, wav_sha256: sha256(wav)
    }
    const partFileIds = []
    for (const [chunkIndex, chunkBase64] of chunks.entries()) {
      const bytes = Buffer.from(chunkBase64, 'base64')
      const uploaded = await service.handle({
        action: 'uploadSpeakingChunk', session_token: auth.session_token,
        request: {
          ...common, chunk_index: chunkIndex, chunk_base64: chunkBase64,
          chunk_sha256: sha256(bytes)
        }
      }, { callerId: 'parent' })
      partFileIds.push(uploaded.file_id)
      assert.match(uploaded.file_id, /sherlock-english\/tmp-speaking\/test\//)
    }

    const response = await service.handle({
      action: 'scoreUploadedSpeakingTake', session_token: auth.session_token,
      request: { ...common, part_file_ids: partFileIds }
    }, { callerId: 'parent' })

    assert.equal(response.stars, 3)
    assert.equal(scoredBase64, wavBase64)
    assert.equal(uploadStore.files.size, 0)
    assert.equal(uploadStore.removed.length, chunks.length)
  })

  it('rejects tampered chunks and foreign temporary paths before scoring', async () => {
    let scorerCalls = 0
    const uploadStore = memoryUploadStore()
    const store = memoryStore()
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({
      store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
      speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
      speakingScorer: async () => { scorerCalls += 1; return {} }, speakingUploadStore: uploadStore
    })
    const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
    const wav = Buffer.alloc(5_000, 3)
    const chunkBase64 = wav.toString('base64')
    const common = {
      result_id: 'r2', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
      chunk_count: 1, wav_byte_length: wav.length, wav_sha256: sha256(wav)
    }
    await assert.rejects(service.handle({
      action: 'uploadSpeakingChunk', session_token: auth.session_token,
      request: { ...common, chunk_index: 0, chunk_base64: chunkBase64, chunk_sha256: '0'.repeat(64) }
    }, { callerId: 'parent' }), /SPEAKING_UPLOAD_INCOMPLETE/)

    await assert.rejects(service.handle({
      action: 'scoreUploadedSpeakingTake', session_token: auth.session_token,
      request: { ...common, part_file_ids: ['cloud://test.bucket/sherlock-english/tmp-speaking/test/foreign/part-00.bin'] }
    }, { callerId: 'parent' }), /SPEAKING_UPLOAD_INCOMPLETE/)
    assert.equal(scorerCalls, 0)
  })

  it('derives the temporary chunk namespace from the server-side formal session', async () => {
    const uploadStore = memoryUploadStore()
    const service = createService({
      store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef', formalEnabled: true,
      randomToken: () => 'formal-token', speakingUploadStore: uploadStore,
      speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
      speakingScorer: async () => ({})
    })
    const auth = await service.handle({ action: 'startChildSession' }, { callerId: 'child' })
    const wav = Buffer.alloc(5_000, 2)
    const chunkBase64 = wav.toString('base64')
    const response = await service.handle({
      action: 'uploadSpeakingChunk', session_token: auth.session_token,
      request: {
        result_id: 'formal-r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
        chunk_count: 1, chunk_index: 0, chunk_base64: chunkBase64, chunk_sha256: sha256(wav),
        wav_byte_length: wav.length, wav_sha256: sha256(wav)
      }
    }, { callerId: 'child' })
    assert.match(response.file_id, /sherlock-english\/tmp-speaking\/formal\//)
    assert.doesNotMatch(response.file_id, /\/test\//)
  })

  it('allows hidden term takes only in parent test and blocks formal scoring before the provider call', async () => {
    let calls = 0
    const scorer = async (request) => {
      calls += 1
      return { ...request, total: 80, is_rejected: false, words: [], recording_path: 'private.wav' }
    }
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const testStore = memoryStore()
    const testService = createService({
      store: testStore, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
      speakingCourseProvider: { get: () => ({ course: termCourse(), version: 'term-version' }) }, speakingScorer: scorer
    })
    const testAuth = await testService.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
    const request = { result_id: 'term-r1', course_id: 'S4A-T1-W01-D01', course_version: 'term-version', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    await testService.handle({ action: 'scoreSpeakingTake', session_token: testAuth.session_token, request }, { callerId: 'parent' })
    assert.equal(calls, 1)

    const formalService = createService({
      store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef', formalEnabled: true,
      randomToken: () => 'formal-token', speakingCourseProvider: { get: () => ({ course: termCourse(), version: 'term-version' }) }, speakingScorer: scorer
    })
    const formalAuth = await formalService.handle({ action: 'startChildSession' }, { callerId: 'child' })
    await assert.rejects(formalService.handle({
      action: 'scoreSpeakingTake', session_token: formalAuth.session_token, request
    }, { callerId: 'child' }), /COURSE_NOT_FORMAL/)
    assert.equal(calls, 1)
  })

  it('scores only authenticated, course-bound test audio and returns a signed proof', async () => {
    let calls = 0
    const scorer = async (request) => { calls += 1; return ({
      ...request, total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false,
      words: [{ word: 'bright', score: 70 }], recording_path: 'sherlock-english/test/test/S01D39/r1/q01-take1.wav'
    }) }
    const { service, token } = await setup(scorer)
    const response = await service.handle({
      action: 'scoreSpeakingTake', session_token: token,
      request: { result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    }, { callerId: 'parent' })
    assert.equal(response.stars, 3)
    assert.equal(response.weak_words.includes('bright'), false)
    assert.equal(typeof response.proof, 'string')
    assert.equal(Object.hasOwn(response, 'total'), false)
    const repeated = await service.handle({
      action: 'scoreSpeakingTake', session_token: token,
      request: { result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    }, { callerId: 'parent' })
    assert.equal(repeated.proof, response.proof)
    assert.equal(calls, 1)
    await assert.rejects(service.handle({ action: 'scoreSpeakingTake', session_token: 'bad', request: {} }, { callerId: 'parent' }), /UNAUTHORIZED/)
  })

  it('does not convert scorer failures into valid takes', async () => {
    const { service, token } = await setup(async () => { throw new Error('provider secret') })
    await assert.rejects(service.handle({
      action: 'scoreSpeakingTake', session_token: token,
      request: { result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    }, { callerId: 'parent' }), /SPEAKING_SCORE_UNAVAILABLE/)
  })

  it('preserves only safe scorer diagnostic codes for the test UI', async () => {
    for (const code of ['SILENT_AUDIO', 'INVALID_AUDIO', 'RECORDING_UPLOAD_FAILED', 'ISE_10163', 'ISE_TIMEOUT']) {
      const { service, token } = await setup(async () => { throw new Error(code) })
      await assert.rejects(service.handle({
        action: 'scoreSpeakingTake', session_token: token,
        request: { result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
      }, { callerId: 'parent' }), new RegExp(code))
    }
    const { service, token } = await setup(async () => { throw new Error('provider secret') })
    await assert.rejects(service.handle({
      action: 'scoreSpeakingTake', session_token: token,
      request: { result_id: 'r2', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    }, { callerId: 'parent' }), /SPEAKING_SCORE_UNAVAILABLE/)
  })

  it('rejects malformed, stale, conflicting, and untrusted take requests', async () => {
    const scorer = async (request) => ({ ...request, total: 80, is_rejected: false, words: [], recording_path: 'private.wav' })
    const { store, service, token } = await setup(scorer)
    const base = { result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    for (const patch of [{ attempt: 0 }, { question_id: 0 }, { wav_base64: 'tiny' }]) {
      await assert.rejects(service.handle({ action: 'scoreSpeakingTake', session_token: token, request: { ...base, ...patch } }, { callerId: 'parent' }), /INVALID_SPEAKING_TAKE/)
    }
    await assert.rejects(service.handle({ action: 'scoreSpeakingTake', session_token: token, request: { ...base, course_version: 'stale' } }, { callerId: 'parent' }), /COURSE_VERSION_MISMATCH/)
    const takeId = require('node:crypto').createHash('sha256').update('test:r1:S01D39:1:1').digest('hex')
    store.takes.set(takeId, { created_by_session: 'another-session', data_kind: 'test', response: { ok: true } })
    await assert.rejects(service.handle({ action: 'scoreSpeakingTake', session_token: token, request: base }, { callerId: 'parent' }), /RESULT_ID_CONFLICT/)
  })

  it('rejects missing recordings and unavailable private URLs', async () => {
    const { service, token } = await setup(async () => ({}))
    await assert.rejects(service.handle({ action: 'getSpeakingRecordingUrl', session_token: token, result_id: 'missing', question_id: 1, attempt: 1 }, { callerId: 'parent' }), /RECORDING_NOT_FOUND/)
  })

  it('stores an idempotent test-only result and exposes parent detail plus recording URL', async () => {
    const scorer = async (request) => ({
      ...request, total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [],
      recording_path: 'sherlock-english/test/test/S01D39/r1/q01-take1.wav'
    })
    const { store, service, token } = await setup(scorer)
    const scored = []
    for (let questionId = 1; questionId <= 8; questionId += 1) {
      scored.push(await service.handle({
        action: 'scoreSpeakingTake', session_token: token,
        request: { result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1', question_id: questionId, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
      }, { callerId: 'parent' }))
    }
    const submission = {
      result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock', course_id: 'S01D39', course_version: 'version1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
      questions: scored.map((item, index) => ({ id: index + 1, proofs: [item.proof], passed_by_safety: false }))
    }
    const first = await service.handle({ action: 'submitSpeakingResult', session_token: token, submission }, { callerId: 'parent' })
    const second = await service.handle({ action: 'submitSpeakingResult', session_token: token, submission }, { callerId: 'parent' })
    assert.equal(first.result_id, second.result_id)
    assert.equal(store.results.size, 1)
    const listed = await service.handle({ action: 'listSpeakingTestResults', session_token: token }, { callerId: 'parent' })
    assert.equal(listed.results[0].question_results[0].best_total, 80)
    const url = await service.handle({ action: 'getSpeakingRecordingUrl', session_token: token, result_id: submission.result_id, question_id: 1, attempt: 1 }, { callerId: 'parent' })
    assert.match(url.url, /^https:\/\//)
  })

  it('scores and stores a formal result only through a formal child session', async () => {
    const scorer = async (request) => ({
      ...request, total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [],
      recording_path: `sherlock-english/${request.data_kind}/${request.data_kind}/S01D39/r1/q01-take1.wav`
    })
    const { store, service, token, callerId } = await setup(scorer, { formal: true })
    const scored = []
    for (let questionId = 1; questionId <= 8; questionId += 1) {
      scored.push(await service.handle({
        action: 'scoreSpeakingTake', session_token: token,
        request: { result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1', question_id: questionId, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
      }, { callerId }))
    }
    const response = await service.handle({
      action: 'submitSpeakingResult', session_token: token,
      submission: {
        result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock', course_id: 'S01D39', course_version: 'version1',
        started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
        questions: scored.map((item, index) => ({ id: index + 1, proofs: [item.proof], passed_by_safety: false }))
      }
    }, { callerId })
    assert.equal(response.data_kind, 'formal')
    assert.equal(response.formal_completion_eligible, true)
    const stored = store.results.get(response.result_id)
    assert.equal(stored.data_kind, 'formal')
    assert.equal(stored.question_results[0].recording_records[0].data_kind, 'formal')
  })

  it('reuses a scored formal take and final result after renewal for the same caller', async () => {
    let calls = 0
    const scorer = async (request) => {
      calls += 1
      return {
        ...request, total: 80, accuracy: 79, fluency: 78, integrity: 81, is_rejected: false, words: [],
        recording_path: `sherlock-english/formal/formal/S01D39/${request.result_id}/q${request.question_id}-take${request.attempt}.wav`
      }
    }
    const store = memoryStore()
    let tokenNumber = 0
    const service = createService({
      store, passwordHash: 'unused', hmacKey: '1234567890abcdef', formalEnabled: true,
      randomToken: () => `formal-token-${++tokenNumber}`,
      speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
      speakingScorer: scorer,
      speakingRecordingUrl: async () => 'https://private.example.test/recording.wav'
    })
    const firstSession = await service.handle({ action: 'startChildSession' }, { callerId: 'child' })
    const request = {
      result_id: '123e4567-e89b-42d3-a456-426614174000', course_id: 'S01D39', course_version: 'version1',
      question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64')
    }
    const firstTake = await service.handle({ action: 'scoreSpeakingTake', session_token: firstSession.session_token, request }, { callerId: 'child' })
    const renewedSession = await service.handle({ action: 'startChildSession' }, { callerId: 'child' })
    const replayedTake = await service.handle({ action: 'scoreSpeakingTake', session_token: renewedSession.session_token, request }, { callerId: 'child' })
    assert.equal(replayedTake.proof, firstTake.proof)
    assert.equal(replayedTake.idempotent, true)
    assert.equal(calls, 1)

    const proofs = [firstTake.proof]
    for (let questionId = 2; questionId <= 8; questionId += 1) {
      const scored = await service.handle({
        action: 'scoreSpeakingTake', session_token: renewedSession.session_token,
        request: { ...request, question_id: questionId }
      }, { callerId: 'child' })
      proofs.push(scored.proof)
    }
    const submission = {
      result_id: request.result_id, student_id: 'sherlock', course_id: 'S01D39', course_version: 'version1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
      questions: proofs.map((proof, index) => ({ id: index + 1, proofs: [proof], passed_by_safety: false }))
    }
    const firstResult = await service.handle({ action: 'submitSpeakingResult', session_token: renewedSession.session_token, submission }, { callerId: 'child' })
    const finalSession = await service.handle({ action: 'startChildSession' }, { callerId: 'child' })
    const replayedResult = await service.handle({ action: 'submitSpeakingResult', session_token: finalSession.session_token, submission }, { callerId: 'child' })
    assert.equal(replayedResult.result_id, firstResult.result_id)
    assert.equal(replayedResult.idempotent, true)
    assert.equal(store.results.size, 1)
  })

  it('keeps parent test take ownership bound to the authenticated test token', async () => {
    const scorer = async (request) => ({ ...request, total: 80, is_rejected: false, words: [], recording_path: 'private.wav' })
    const store = memoryStore()
    let tokenNumber = 0
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({
      store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => `test-token-${++tokenNumber}`,
      speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
      speakingScorer: scorer
    })
    const callerId = 'parent'
    const firstAuth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId })
    const token = firstAuth.session_token
    const request = { result_id: 'r-test', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: Buffer.alloc(5000).toString('base64') }
    await service.handle({ action: 'scoreSpeakingTake', session_token: token, request }, { callerId })
    const secondAuth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId })
    await assert.rejects(
      service.handle({ action: 'scoreSpeakingTake', session_token: secondAuth.session_token, request }, { callerId }),
      /RESULT_ID_CONFLICT/
    )
  })
})
