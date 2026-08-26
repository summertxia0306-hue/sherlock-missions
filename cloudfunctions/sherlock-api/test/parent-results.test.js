'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createService, hashPassword } = require('../core')

function parentStore() {
  const sessions = new Map()
  const rows = [
    { result_id: 'formal-listening', module_type: 'listening', course_id: 'W01D01', data_kind: 'formal', submitted_at: new Date('2026-06-27T06:53:00+08:00'), score: 100 },
    { result_id: 'formal-speaking', module_type: 'speaking', course_id: 'S01D01', data_kind: 'formal', submitted_at: new Date('2026-06-27T15:01:00+08:00'), score: 99, question_results: [{ id: 1, recording_records: [{ file_id: 'cloud://formal.wav', data_kind: 'formal' }] }] },
    { result_id: 'test-listening', module_type: 'listening', course_id: 'W01D02', data_kind: 'test', submitted_at: new Date('2026-06-12T21:00:00+08:00'), score: 80 }
  ]
  return {
    rows,
    async getFailures() { return [] }, async recordFailure() {}, async clearFailures() {},
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(hash) { return sessions.get(hash) || null },
    async saveAudit() {},
    async listParentResults(filters) {
      return rows.filter((row) => row.data_kind === filters.data_kind
        && (!filters.module_type || row.module_type === filters.module_type)
        && (!filters.course_id || row.course_id === filters.course_id))
    },
    async getResult(resultId) { return rows.find((row) => row.result_id === resultId) || null }
  }
}

async function authenticatedService() {
  const store = parentStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  const service = createService({
    store, passwordHash, hmacKey: '1234567890abcdef', now: () => 1_777_000_000_000,
    randomToken: () => 'parent-token', speakingRecordingUrl: async (fileId) => `https://private.test/${encodeURIComponent(fileId)}`
  })
  const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent' })
  return { service, auth }
}

describe('P4 authenticated parent history', () => {
  it('defaults to formal and keeps test in an explicit independent filter', async () => {
    const { service, auth } = await authenticatedService()
    const formal = await service.handle({ action: 'listParentResults', session_token: auth.session_token, filters: {} }, { callerId: 'parent' })
    const test = await service.handle({ action: 'listParentResults', session_token: auth.session_token, filters: { data_kind: 'test' } }, { callerId: 'parent' })

    assert.equal(formal.data_kind, 'formal')
    assert.deepEqual(formal.results.map((item) => item.result_id), ['formal-speaking', 'formal-listening'])
    assert.equal(formal.summary.result_count, 2)
    assert.equal(test.data_kind, 'test')
    assert.deepEqual(test.results.map((item) => item.result_id), ['test-listening'])
    assert.equal(test.summary.formal_completion_count, 0)
  })

  it('validates module/course filters and permits temporary playback for authenticated formal history', async () => {
    const { service, auth } = await authenticatedService()
    const response = await service.handle({ action: 'listParentResults', session_token: auth.session_token, filters: { data_kind: 'formal', module_type: 'speaking', course_id: 'S01D01' } }, { callerId: 'parent' })
    assert.deepEqual(response.results.map((item) => item.result_id), ['formal-speaking'])

    const recording = await service.handle({ action: 'getParentRecordingUrl', session_token: auth.session_token, result_id: 'formal-speaking', question_id: 1, attempt: 1 }, { callerId: 'parent' })
    assert.match(recording.url, /^https:\/\/private\.test\//)
    assert.equal(recording.expires_in, 600)

    await assert.rejects(service.handle({ action: 'listParentResults', session_token: auth.session_token, filters: { data_kind: 'formal', module_type: 'admin' } }, { callerId: 'parent' }), /INVALID_FILTER/)
  })
})
