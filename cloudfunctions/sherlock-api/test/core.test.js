'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createService, hashPassword } = require('../core')

function memoryStore() {
  const sessions = new Map()
  const results = []
  const audits = []
  const failures = new Map()
  return {
    sessions,
    results,
    audits,
    failures,
    async getFailures(callerId) { return failures.get(callerId) || [] },
    async recordFailure(callerId, occurredAt) {
      failures.set(callerId, [...(failures.get(callerId) || []), occurredAt])
    },
    async clearFailures(callerId) { failures.delete(callerId) },
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(tokenHash) { return sessions.get(tokenHash) || null },
    async saveResult(value) { results.push(value); return value.result_id },
    async listParentResults(filters) { return results.filter((item) => item.data_kind === filters.data_kind) },
    async saveAudit(value) { audits.push(value) }
  }
}

function validResult(overrides = {}) {
  return {
    student_id: 'sherlock',
    module_type: 'listening',
    course_id: 'W01D39',
    pair_id: 'S01D39',
    course_version: '1',
    started_at: '2026-08-24T10:00:00.000Z',
    submitted_at: '2026-08-24T10:02:00.000Z',
    duration_seconds: 120,
    device_info: { platform: 'iPad' },
    payload: { score: 15 },
    data_kind: 'formal',
    ...overrides
  }
}

describe('sherlock-api service', () => {
  it('reports P5 code with formal disabled until the cutover flag is enabled', async () => {
    const service = createService({ store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef' })
    const health = await service.handle({ action: 'health' }, { callerId: 'a' })
    assert.deepEqual({ ...health, speaking_course_versions: undefined }, {
      ok: true,
      service: 'sherlock-api',
      stage: 'P5',
      formal_enabled: false,
      writes: 'test-only',
      speaking_course_versions: undefined
    })
    assert.match(health.speaking_course_versions.S01D39, /^[a-f0-9]{16}$/)
  })

  it('creates a caller-bound formal child session and returns formal completion only', async () => {
    const store = memoryStore()
    store.results.push(
      { student_id: 'sherlock', course_id: 'W01D43', module_type: 'listening', data_kind: 'formal', status: 'completed' },
      { student_id: 'sherlock', course_id: 'W01D44', module_type: 'listening', data_kind: 'test', status: 'completed' },
      { student_id: 'sherlock', course_id: 'S01D43', module_type: 'speaking', data_kind: 'formal', status: 'completed' },
      { student_id: 'someone-else', course_id: 'W01D50', module_type: 'listening', data_kind: 'formal', status: 'completed' }
    )
    const service = createService({
      store, passwordHash: 'unused', hmacKey: '1234567890abcdef', formalEnabled: true,
      now: () => 1_777_000_000_000, randomToken: () => 'formal-token'
    })
    const session = await service.handle({ action: 'startChildSession' }, { callerId: 'child-1' })
    assert.equal(session.data_kind, 'formal')
    const progress = await service.handle({ action: 'getFormalProgress', session_token: session.session_token }, { callerId: 'child-1' })
    assert.deepEqual(progress.completed_course_ids, { listening: ['W01D43'], speaking: ['S01D43'] })
    await assert.rejects(
      service.handle({ action: 'getFormalProgress', session_token: session.session_token }, { callerId: 'other-child' }),
      /UNAUTHORIZED/
    )
  })

  it('does not create a formal child session before the cutover flag is enabled', async () => {
    const service = createService({ store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef' })
    await assert.rejects(service.handle({ action: 'startChildSession' }, { callerId: 'child' }), /FORMAL_DISABLED/)
  })

  it('authenticates a parent without returning or storing the password', async () => {
    const store = memoryStore()
    const passwordHash = await hashPassword('correct horse battery staple', '00112233445566778899aabbccddeeff')
    const service = createService({ store, passwordHash, hmacKey: 'test-hmac-key-123', now: () => 1_777_000_000_000, randomToken: () => 'opaque-token' })
    const response = await service.handle({ action: 'parentAuth', password: 'correct horse battery staple' }, { callerId: 'parent-1' })
    assert.equal(response.ok, true)
    assert.equal(response.session_token, 'opaque-token')
    assert.equal(response.data_kind, 'test')
    assert.equal(JSON.stringify([...store.sessions.values()]).includes('correct horse'), false)
  })

  it('rate limits repeated bad passwords without leaking details', async () => {
    const store = memoryStore()
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({ store, passwordHash, hmacKey: '1234567890abcdef', maxFailures: 2, now: () => 1_777_000_000_000 })
    await assert.rejects(service.handle({ action: 'parentAuth', password: 'wrong-password' }, { callerId: 'parent-2' }), /AUTH_FAILED/)
    await assert.rejects(service.handle({ action: 'parentAuth', password: 'still-wrong' }, { callerId: 'parent-2' }), /AUTH_FAILED/)
    await assert.rejects(service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent-2' }), /RATE_LIMITED/)
  })

  it('rejects unauthenticated writes', async () => {
    const service = createService({ store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef' })
    await assert.rejects(service.handle({ action: 'submitResult', session_token: 'bad', result: validResult() }, { callerId: 'x' }), /UNAUTHORIZED/)
  })

  it('forces authenticated P1 writes to test regardless of browser claim', async () => {
    const store = memoryStore()
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({ store, passwordHash, hmacKey: '1234567890abcdef', now: () => 1_777_000_000_000, randomToken: () => 'token' })
    const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'parent-3' })
    const response = await service.handle({ action: 'submitResult', session_token: auth.session_token, result: validResult() }, { callerId: 'parent-3' })
    assert.equal(response.ok, true)
    assert.equal(store.results[0].data_kind, 'test')
    assert.equal(store.results[0].formal_completion_eligible, false)
    assert.equal(store.results[0].payload.score, 15)
  })

  it('rejects invalid and oversized results', async () => {
    const store = memoryStore()
    const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
    const service = createService({ store, passwordHash, hmacKey: '1234567890abcdef', randomToken: () => 'token' })
    const auth = await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId: 'p' })
    await assert.rejects(service.handle({ action: 'submitResult', session_token: auth.session_token, result: validResult({ module_type: 'admin' }) }, { callerId: 'p' }), /INVALID_RESULT/)
    await assert.rejects(service.handle({ action: 'submitResult', session_token: auth.session_token, result: validResult({ payload: { text: 'x'.repeat(70_000) } }) }, { callerId: 'p' }), /INVALID_RESULT/)
  })

  it('rejects formal actions and unknown actions', async () => {
    const service = createService({ store: memoryStore(), passwordHash: 'unused', hmacKey: '1234567890abcdef' })
    await assert.rejects(service.handle({ action: 'formalLogin' }, { callerId: 'x' }), /FORMAL_DISABLED/)
    await assert.rejects(service.handle({ action: 'other' }, { callerId: 'x' }), /UNKNOWN_ACTION/)
  })
})
