'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const crypto = require('node:crypto')
const { createService, hashPassword } = require('../core')

function memoryStore() {
  const sessions = new Map()
  return {
    audits: [],
    async getFailures() { return [] },
    async recordFailure() {},
    async clearFailures() {},
    async saveAudit(value) { this.audits.push(value) },
    async saveSession(value) { sessions.set(value.token_hash, value) },
    async getSession(key) { return sessions.get(key) },
    async listParentResults() { return [] }
  }
}

function memoryProbeStore() {
  const files = new Map()
  const issued = []
  const removed = []
  return {
    files,
    issued,
    removed,
    async issue(path, options) {
      issued.push({ path, options })
      return {
        upload_url: `https://storage.example.test/${path}?signed=short-lived`,
        file_id: `cloud://test.bucket/${path}`,
        expires_in: options.expiresIn
      }
    },
    async download(fileId) {
      if (!files.has(fileId)) throw new Error('missing')
      return Buffer.from(files.get(fileId))
    },
    async remove(fileId) {
      removed.push(fileId)
      files.delete(fileId)
    }
  }
}

function sha256(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

async function setup(options = {}) {
  const nowValue = options.nowValue || 1_700_000_000_000
  const store = memoryStore()
  const probeStore = options.probeStore || memoryProbeStore()
  const passwordHash = await hashPassword('right-password', '00112233445566778899aabbccddeeff')
  const service = createService({
    store,
    passwordHash,
    hmacKey: '1234567890abcdef',
    now: () => nowValue,
    randomToken: () => 'test-session-token',
    randomProbeId: () => 'probe-id-1234',
    directUploadProbeStore: probeStore,
    formalEnabled: options.formal === true
  })
  const callerId = options.callerId || (options.formal ? 'child' : 'parent')
  const auth = options.formal
    ? await service.handle({ action: 'startChildSession' }, { callerId })
    : await service.handle({ action: 'parentAuth', password: 'right-password' }, { callerId })
  return { service, store, probeStore, token: auth.session_token, callerId, nowValue }
}

function probeRequest(bytes) {
  return {
    byte_length: bytes.length,
    sha256: sha256(bytes),
    content_type: 'audio/wav'
  }
}

describe('direct storage upload feasibility probe', () => {
  it('issues one exact 120-second private upload target and verifies then removes the object', async () => {
    const bytes = Buffer.alloc(150 * 1024, 7)
    const { service, probeStore, token, callerId, nowValue } = await setup()

    const issued = await service.handle({
      action: 'createDirectUploadProbe',
      session_token: token,
      request: probeRequest(bytes)
    }, { callerId })

    assert.equal(issued.ok, true)
    assert.equal(issued.data_kind, 'test')
    assert.equal(issued.byte_length, bytes.length)
    assert.equal(issued.expires_at, new Date(nowValue + 120_000).toISOString())
    assert.match(issued.object_key, /^sherlock-english\/test\/direct-upload-probe\/probe-id-1234\.wav$/)
    assert.equal(probeStore.issued[0].options.expiresIn, 120)
    assert.equal(Object.hasOwn(issued, 'authorization'), false)
    assert.equal(Object.hasOwn(issued, 'token'), false)

    probeStore.files.set(issued.file_id, bytes)
    const verified = await service.handle({
      action: 'verifyDirectUploadProbe',
      session_token: token,
      ticket: issued.ticket
    }, { callerId })

    assert.deepEqual(verified, {
      ok: true,
      data_kind: 'test',
      byte_length: bytes.length,
      sha256: sha256(bytes),
      cleaned_up: true
    })
    assert.equal(probeStore.files.size, 0)
    assert.deepEqual(probeStore.removed, [issued.file_id])
  })

  it('requires a parent test session and rejects invalid upload declarations', async () => {
    const bytes = Buffer.alloc(150 * 1024, 1)
    const { service, token, callerId } = await setup()
    const valid = probeRequest(bytes)

    await assert.rejects(service.handle({ action: 'createDirectUploadProbe', request: valid }, { callerId }), /UNAUTHORIZED/)
    for (const request of [
      { ...valid, byte_length: 1024 },
      { ...valid, byte_length: 201 * 1024 },
      { ...valid, sha256: 'bad' },
      { ...valid, content_type: 'application/octet-stream' }
    ]) {
      await assert.rejects(service.handle({
        action: 'createDirectUploadProbe', session_token: token, request
      }, { callerId }), /INVALID_DIRECT_UPLOAD_PROBE/)
    }

    const formal = await setup({ formal: true })
    await assert.rejects(formal.service.handle({
      action: 'createDirectUploadProbe', session_token: formal.token, request: valid
    }, { callerId: formal.callerId }), /UNAUTHORIZED/)
  })

  it('rejects tampered, expired, and foreign-owner tickets without reading an object', async () => {
    const bytes = Buffer.alloc(150 * 1024, 2)
    const first = await setup()
    const issued = await first.service.handle({
      action: 'createDirectUploadProbe', session_token: first.token, request: probeRequest(bytes)
    }, { callerId: first.callerId })

    await assert.rejects(first.service.handle({
      action: 'verifyDirectUploadProbe', session_token: first.token, ticket: `${issued.ticket}x`
    }, { callerId: first.callerId }), /INVALID_DIRECT_UPLOAD_TICKET/)

    const foreign = await setup({ callerId: 'another-parent', probeStore: first.probeStore })
    await assert.rejects(foreign.service.handle({
      action: 'verifyDirectUploadProbe', session_token: foreign.token, ticket: issued.ticket
    }, { callerId: foreign.callerId }), /INVALID_DIRECT_UPLOAD_TICKET/)

    const expired = await setup({ nowValue: first.nowValue + 120_001, probeStore: first.probeStore })
    await assert.rejects(expired.service.handle({
      action: 'verifyDirectUploadProbe', session_token: expired.token, ticket: issued.ticket
    }, { callerId: expired.callerId }), /UPLOAD_TICKET_EXPIRED/)
    assert.equal(first.probeStore.removed.length, 0)
  })

  it('removes a mismatched object before returning a safe integrity error', async () => {
    const expected = Buffer.alloc(150 * 1024, 3)
    const actual = Buffer.alloc(150 * 1024, 4)
    const { service, probeStore, token, callerId } = await setup()
    const issued = await service.handle({
      action: 'createDirectUploadProbe', session_token: token, request: probeRequest(expected)
    }, { callerId })
    probeStore.files.set(issued.file_id, actual)

    await assert.rejects(service.handle({
      action: 'verifyDirectUploadProbe', session_token: token, ticket: issued.ticket
    }, { callerId }), /UPLOAD_HASH_MISMATCH/)
    assert.equal(probeStore.files.size, 0)
    assert.deepEqual(probeStore.removed, [issued.file_id])
  })

  it('cancels only the exact object carried by a valid current ticket', async () => {
    const bytes = Buffer.alloc(150 * 1024, 5)
    const { service, probeStore, token, callerId } = await setup()
    const issued = await service.handle({
      action: 'createDirectUploadProbe', session_token: token, request: probeRequest(bytes)
    }, { callerId })
    probeStore.files.set(issued.file_id, bytes)

    const cancelled = await service.handle({
      action: 'cancelDirectUploadProbe', session_token: token, ticket: issued.ticket
    }, { callerId })
    assert.deepEqual(cancelled, { ok: true, data_kind: 'test', cleaned_up: true })
    assert.equal(probeStore.files.size, 0)
    assert.deepEqual(probeStore.removed, [issued.file_id])
  })
})
