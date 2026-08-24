'use strict'

const crypto = require('node:crypto')
const { promisify } = require('node:util')

const scryptAsync = promisify(crypto.scrypt)
const ALLOWED_MODULES = new Set(['listening', 'speaking', 'vocabulary'])

class ServiceError extends Error {
  constructor(code, message = code) {
    super(message)
    this.name = 'ServiceError'
    this.code = code
  }
}

function boundedString(value, min, max) {
  return typeof value === 'string' && value.length >= min && value.length <= max
}

function isIsoDate(value) {
  return boundedString(value, 20, 40) && Number.isFinite(Date.parse(value))
}

function validateResult(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    throw new ServiceError('INVALID_RESULT')
  }
  if (!boundedString(input.student_id, 1, 80)
    || !ALLOWED_MODULES.has(input.module_type)
    || !boundedString(input.course_id, 1, 80)
    || (input.pair_id !== undefined && !boundedString(input.pair_id, 1, 80))
    || !boundedString(input.course_version, 1, 40)
    || !isIsoDate(input.started_at)
    || !isIsoDate(input.submitted_at)
    || !Number.isInteger(input.duration_seconds)
    || input.duration_seconds < 0
    || input.duration_seconds > 86_400
    || !input.payload
    || typeof input.payload !== 'object'
    || Array.isArray(input.payload)) {
    throw new ServiceError('INVALID_RESULT')
  }
  let payloadBytes
  try {
    payloadBytes = Buffer.byteLength(JSON.stringify(input.payload), 'utf8')
  } catch {
    throw new ServiceError('INVALID_RESULT')
  }
  if (payloadBytes > 64 * 1024) {
    throw new ServiceError('INVALID_RESULT')
  }
}

async function hashPassword(password, fixedSalt) {
  if (!boundedString(password, 8, 256)) {
    throw new ServiceError('INVALID_PASSWORD')
  }
  const salt = fixedSalt || crypto.randomBytes(16).toString('hex')
  const derived = await scryptAsync(password, Buffer.from(salt, 'hex'), 64)
  return `scrypt$v1$${salt}$${derived.toString('hex')}`
}

async function verifyPassword(password, encoded) {
  if (!boundedString(password, 1, 256) || !boundedString(encoded, 1, 512)) {
    return false
  }
  const parts = encoded.split('$')
  if (parts.length !== 4 || parts[0] !== 'scrypt' || parts[1] !== 'v1' || !/^[0-9a-f]{32}$/i.test(parts[2]) || !/^[0-9a-f]{128}$/i.test(parts[3])) {
    return false
  }
  const actual = await scryptAsync(password, Buffer.from(parts[2], 'hex'), 64)
  const expected = Buffer.from(parts[3], 'hex')
  return expected.length === actual.length && crypto.timingSafeEqual(expected, actual)
}

function tokenHash(token, hmacKey) {
  return crypto.createHmac('sha256', hmacKey).update(token).digest('hex')
}

function createService(options) {
  const store = options.store
  const passwordHash = options.passwordHash
  const hmacKey = options.hmacKey
  const now = options.now || Date.now
  const randomToken = options.randomToken || (() => crypto.randomBytes(32).toString('base64url'))
  const sessionTtlMs = (options.sessionTtlSeconds || 7200) * 1000
  const authWindowMs = (options.authWindowSeconds || 900) * 1000
  const maxFailures = options.maxFailures || 5

  async function authenticate(event, requestContext) {
    if (!boundedString(passwordHash, 1, 512) || !boundedString(hmacKey, 16, 512)) {
      throw new ServiceError('CONFIG_ERROR')
    }
    if (!boundedString(event.password, 1, 256)) {
      throw new ServiceError('AUTH_FAILED')
    }
    const timestamp = now()
    const cutoff = timestamp - authWindowMs
    const failures = (await store.getFailures(requestContext.callerId)).filter((value) => Number(value) >= cutoff)
    if (failures.length >= maxFailures) {
      throw new ServiceError('RATE_LIMITED')
    }
    if (!(await verifyPassword(event.password, passwordHash))) {
      await store.recordFailure(requestContext.callerId, timestamp)
      await store.saveAudit({ action: 'parent_auth_failed', caller_id: requestContext.callerId, occurred_at: new Date(timestamp), log_tag: 'sherlock-english' })
      throw new ServiceError('AUTH_FAILED')
    }
    await store.clearFailures(requestContext.callerId)
    const token = randomToken()
    const expiresAt = timestamp + sessionTtlMs
    await store.saveSession({
      token_hash: tokenHash(token, hmacKey),
      caller_id: requestContext.callerId,
      data_kind: 'test',
      created_at: new Date(timestamp),
      expires_at: new Date(expiresAt)
    })
    await store.saveAudit({ action: 'parent_auth_succeeded', caller_id: requestContext.callerId, occurred_at: new Date(timestamp), log_tag: 'sherlock-english' })
    return { ok: true, session_token: token, expires_at: new Date(expiresAt).toISOString(), data_kind: 'test' }
  }

  async function submitResult(event, requestContext) {
    if (!boundedString(hmacKey, 16, 512) || !boundedString(event.session_token, 1, 512)) {
      throw new ServiceError('UNAUTHORIZED')
    }
    const session = await store.getSession(tokenHash(event.session_token, hmacKey))
    const expiresAt = session?.expires_at instanceof Date ? session.expires_at.getTime() : Date.parse(session?.expires_at)
    if (!session || session.caller_id !== requestContext.callerId || !Number.isFinite(expiresAt) || expiresAt <= now() || session.data_kind !== 'test') {
      throw new ServiceError('UNAUTHORIZED')
    }
    validateResult(event.result)
    const resultId = crypto.randomUUID()
    const submitted = {
      result_id: resultId,
      student_id: event.result.student_id,
      module_type: event.result.module_type,
      course_id: event.result.course_id,
      ...(event.result.pair_id ? { pair_id: event.result.pair_id } : {}),
      data_kind: 'test',
      course_version: event.result.course_version,
      started_at: new Date(event.result.started_at),
      submitted_at: new Date(event.result.submitted_at),
      duration_seconds: event.result.duration_seconds,
      device_info: event.result.device_info || {},
      payload: event.result.payload,
      formal_completion_eligible: false,
      created_at: new Date(now()),
      created_by_session: session.token_hash.slice(0, 16)
    }
    await store.saveResult(submitted)
    await store.saveAudit({ action: 'test_result_created', caller_id: requestContext.callerId, result_id: resultId, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return { ok: true, result_id: resultId, data_kind: 'test', formal_completion_eligible: false }
  }

  return {
    async handle(event = {}, requestContext = { callerId: 'unknown' }) {
      if (event.action === 'health') {
        return { ok: true, service: 'sherlock-api', stage: 'P1', formal_enabled: false, writes: 'test-only' }
      }
      if (event.action === 'parentAuth') {
        return authenticate(event, requestContext)
      }
      if (event.action === 'submitResult') {
        return submitResult(event, requestContext)
      }
      if (typeof event.action === 'string' && event.action.toLowerCase().includes('formal')) {
        throw new ServiceError('FORMAL_DISABLED')
      }
      throw new ServiceError('UNKNOWN_ACTION')
    }
  }
}

module.exports = { ServiceError, createService, hashPassword, verifyPassword, validateResult }

