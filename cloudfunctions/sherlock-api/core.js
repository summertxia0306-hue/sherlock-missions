'use strict'

const crypto = require('node:crypto')
const { promisify } = require('node:util')
const { createFileCourseProvider, scoreListeningSubmission } = require('./listening-service')

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
  const courseProvider = options.courseProvider || createFileCourseProvider()

  async function requireTestSession(event, requestContext) {
    if (!boundedString(hmacKey, 16, 512) || !boundedString(event.session_token, 1, 512)) {
      throw new ServiceError('UNAUTHORIZED')
    }
    const hash = tokenHash(event.session_token, hmacKey)
    const session = await store.getSession(hash)
    const expiresAt = session?.expires_at instanceof Date ? session.expires_at.getTime() : Date.parse(session?.expires_at)
    if (!session || session.caller_id !== requestContext.callerId || !Number.isFinite(expiresAt) || expiresAt <= now() || session.data_kind !== 'test') {
      throw new ServiceError('UNAUTHORIZED')
    }
    return { ...session, token_hash: session.token_hash || hash }
  }

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
    const session = await requireTestSession(event, requestContext)
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

  async function submitListeningResult(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    const requestedId = event.submission?.result_id
    if (!boundedString(requestedId, 1, 80)) throw new ServiceError('INVALID_LISTENING_RESULT')
    const existing = await store.getResult(requestedId)
    if (existing) {
      if (existing.created_by_session !== session.token_hash.slice(0, 16) || existing.module_type !== 'listening') {
        throw new ServiceError('RESULT_ID_CONFLICT')
      }
      return {
        ok: true, result_id: existing.result_id, data_kind: 'test', formal_completion_eligible: false,
        wrong_question_ids: (existing.wrong_answers || []).map((item) => item.id), idempotent: true
      }
    }
    let loaded
    try {
      loaded = courseProvider.get(event.submission?.course_id)
    } catch {
      throw new ServiceError('COURSE_NOT_FOUND')
    }
    let submitted
    try {
      submitted = scoreListeningSubmission(loaded.course, event.submission, loaded.version)
    } catch {
      throw new ServiceError('INVALID_LISTENING_RESULT')
    }
    submitted.created_at = new Date(now())
    submitted.created_by_session = session.token_hash.slice(0, 16)
    await store.saveResult(submitted)
    await store.saveAudit({ action: 'listening_test_result_created', caller_id: requestContext.callerId, result_id: submitted.result_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return {
      ok: true, result_id: submitted.result_id, data_kind: 'test', formal_completion_eligible: false,
      wrong_question_ids: submitted.wrong_answers.map((item) => item.id), idempotent: false
    }
  }

  function transcriptFor(course, question) {
    const section = course.sections.find((item) => item.id === question.section)
    const source = question.type === 'passage_judge' ? section?.passage_transcript : section?.questions.find((item) => item.id === question.id)?.transcript
    return Array.isArray(source) ? source.map((part) => Array.isArray(part) ? String(part[1]) : String(part)) : []
  }

  async function checkListeningCorrection(event, requestContext) {
    await requireTestSession(event, requestContext)
    const result = await store.getResult(event.result_id)
    if (!result || result.module_type !== 'listening' || result.data_kind !== 'test') throw new ServiceError('RESULT_NOT_FOUND')
    const wrong = result.wrong_answers.find((item) => item.id === event.question_id)
    if (!wrong || ![1, 2].includes(event.attempt)) throw new ServiceError('INVALID_CORRECTION')
    let loaded
    try { loaded = courseProvider.get(result.course_id) } catch { throw new ServiceError('COURSE_NOT_FOUND') }
    const section = loaded.course.sections.find((item) => item.id === wrong.section)
    const question = section?.questions.find((item) => item.id === event.question_id)
    if (!question) throw new ServiceError('INVALID_CORRECTION')
    const previous = result.corrections?.[String(question.id)]
    if (event.attempt === 2 && (!previous || previous.attempts?.[0]?.correct !== false)) throw new ServiceError('INVALID_CORRECTION')
    if (previous?.marker) return { ok: true, correct: previous.marker !== '✗', marker: previous.marker, done: true }
    const correct = event.pick === question.answer
    const entry = previous || { attempts: [] }
    entry.attempts = [...entry.attempts, { attempt: event.attempt, correct }]
    if (event.attempt === 1 && correct) entry.marker = '✓'
    if (event.attempt === 2) entry.marker = correct ? '✓²' : '✗'
    const corrections = { ...(result.corrections || {}), [String(question.id)]: entry }
    await store.updateResult(result.result_id, { corrections })
    return {
      ok: true,
      correct,
      ...(entry.marker ? { marker: entry.marker, done: true } : { reveal_transcript: transcriptFor(loaded.course, wrong), next_attempt: 2, done: false })
    }
  }

  async function listListeningTestResults(event, requestContext) {
    await requireTestSession(event, requestContext)
    const rows = await store.listResults()
    return {
      ok: true,
      data_kind: 'test',
      results: rows.filter((item) => item.module_type === 'listening' && item.data_kind === 'test')
        .sort((left, right) => new Date(right.created_at) - new Date(left.created_at))
    }
  }

  return {
    async handle(event = {}, requestContext = { callerId: 'unknown' }) {
      if (event.action === 'health') {
        return { ok: true, service: 'sherlock-api', stage: 'P2', formal_enabled: false, writes: 'test-only' }
      }
      if (event.action === 'parentAuth') {
        return authenticate(event, requestContext)
      }
      if (event.action === 'submitResult') {
        return submitResult(event, requestContext)
      }
      if (event.action === 'submitListeningResult') {
        return submitListeningResult(event, requestContext)
      }
      if (event.action === 'checkListeningCorrection') {
        return checkListeningCorrection(event, requestContext)
      }
      if (event.action === 'listListeningTestResults') {
        return listListeningTestResults(event, requestContext)
      }
      if (typeof event.action === 'string' && event.action.toLowerCase().includes('formal')) {
        throw new ServiceError('FORMAL_DISABLED')
      }
      throw new ServiceError('UNKNOWN_ACTION')
    }
  }
}

module.exports = { ServiceError, createService, hashPassword, verifyPassword, validateResult }
