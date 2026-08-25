'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
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

async function setup(scorer) {
  const store = memoryStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  const service = createService({
    store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
    speakingCourseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) },
    speakingScorer: scorer,
    speakingRecordingUrl: async () => 'https://private.example.test/recording.wav'
  })
  const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
  return { store, service, token: auth.session_token }
}

describe('P3 speaking API', () => {
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
    const takeId = require('node:crypto').createHash('sha256').update('r1:S01D39:1:1').digest('hex')
    store.takes.set(takeId, { created_by_session: 'another-session', response: { ok: true } })
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
})
