'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createService, hashPassword } = require('../core')

function fixtureCourse() {
  return {
    course_id: 'W01D39', title: 'Course', week: 5, day: 4, course_type: 'training', est_minutes: 20,
    scoring: { per_question: 5, total: 10 },
    sections: [
      { id: 'words', name: 'Words', tip: 'Listen', max_plays: 2, questions: [
        { id: 1, type: 'word_choice', options: ['one', 'two'], answer: 0, transcript: [['n', 'one']], audio: 'static/audio/listening/W01D39/q01.mp3', tag: 'word' }
      ] },
      { id: 'passage', name: 'Passage', tip: 'Listen', max_plays: 2, shared_audio: true,
        passage_audio: 'static/audio/listening/W01D39/p01.mp3', passage_transcript: [['n', 'Story text.']], questions: [
          { id: 2, type: 'passage_judge', statement: 'True.', answer: 'true', tag: 'passage' }
        ] }
    ]
  }
}

function memoryStore() {
  const sessions = new Map()
  const results = new Map()
  return {
    sessions, results,
    async getFailures() { return [] }, async recordFailure() {}, async clearFailures() {},
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(hash) { return sessions.get(hash) || null },
    async saveResult(value) { results.set(value.result_id, value) },
    async getResult(resultId) { return results.get(resultId) || null },
    async updateResult(resultId, patch) { Object.assign(results.get(resultId), patch) },
    async listResults() { return [...results.values()] },
    async saveAudit() {}
  }
}

async function authenticatedService() {
  const store = memoryStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  const service = createService({
    store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'test-token',
    courseProvider: { get: () => ({ course: fixtureCourse(), version: 'version1' }) }
  })
  const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
  return { store, service, token: auth.session_token }
}

function submission() {
  return {
    result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock',
    course_id: 'W01D39', course_version: 'version1',
    started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z',
    duration_seconds: 120, answers: { '1': 0, '2': 'false' }, play_counts: { '1': 1, passage: 2 }
  }
}

describe('P2 listening API', () => {
  it('stores one server-scored test result for repeated result_id submissions', async () => {
    const { store, service, token } = await authenticatedService()
    const event = { action: 'submitListeningResult', session_token: token, submission: submission() }
    const first = await service.handle(event, { callerId: 'parent' })
    const second = await service.handle(event, { callerId: 'parent' })
    assert.equal(first.result_id, second.result_id)
    assert.deepEqual(first.wrong_question_ids, [2])
    assert.equal(Object.hasOwn(first, 'score'), false)
    assert.equal(Object.hasOwn(first, 'wrong_answers'), false)
    assert.equal(store.results.size, 1)
    assert.equal(store.results.get(first.result_id).data_kind, 'test')
  })

  it('keeps correction one blind and reveals transcript only after it is wrong', async () => {
    const { store, service, token } = await authenticatedService()
    await service.handle({ action: 'submitListeningResult', session_token: token, submission: submission() }, { callerId: 'parent' })
    const first = await service.handle({
      action: 'checkListeningCorrection', session_token: token,
      result_id: submission().result_id, question_id: 2, attempt: 1, pick: 'false'
    }, { callerId: 'parent' })
    assert.equal(first.correct, false)
    assert.deepEqual(first.reveal_transcript, ['Story text.'])
    assert.equal(Object.hasOwn(first, 'correct_answer'), false)
    const second = await service.handle({
      action: 'checkListeningCorrection', session_token: token,
      result_id: submission().result_id, question_id: 2, attempt: 2, pick: 'true'
    }, { callerId: 'parent' })
    assert.equal(second.correct, true)
    assert.equal(second.marker, '✓²')
    assert.equal(store.results.get(submission().result_id).corrections['2'].marker, '✓²')
  })

  it('returns full test detail only through the authenticated parent action', async () => {
    const { service, token } = await authenticatedService()
    await service.handle({ action: 'submitListeningResult', session_token: token, submission: submission() }, { callerId: 'parent' })
    const response = await service.handle({ action: 'listListeningTestResults', session_token: token }, { callerId: 'parent' })
    assert.equal(response.results[0].score, 5)
    assert.equal(response.results[0].wrong_answers[0].tag, 'passage')
    await assert.rejects(service.handle({ action: 'listListeningTestResults', session_token: 'bad' }, { callerId: 'parent' }), /UNAUTHORIZED/)
  })
})
