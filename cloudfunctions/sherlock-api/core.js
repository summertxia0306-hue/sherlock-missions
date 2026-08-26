'use strict'

const crypto = require('node:crypto')
const { promisify } = require('node:util')
const { createFileCourseProvider, scoreListeningSubmission } = require('./listening-service')
const {
  createFileSpeakingCourseProvider, scoreToStars, feedbackForTake,
  signTakeProof, buildSpeakingResult
} = require('./speaking-service')

const scryptAsync = promisify(crypto.scrypt)
const ALLOWED_MODULES = new Set(['listening', 'speaking', 'vocabulary'])
const SAFE_SPEAKING_SCORE_ERRORS = new Set(['SILENT_AUDIO', 'INVALID_AUDIO', 'RECORDING_UPLOAD_FAILED', 'SCORE_UNAVAILABLE'])
const PARENT_RESULT_MODULES = new Set(['listening', 'speaking'])

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

function safeSpeakingScoreError(error) {
  const code = typeof error?.message === 'string' ? error.message : ''
  if (SAFE_SPEAKING_SCORE_ERRORS.has(code) || /^ISE_(?:[0-9]{1,8}|TIMEOUT|UNAVAILABLE|INVALID_RESULT|CONFIG_ERROR)$/.test(code)) return code
  return 'SPEAKING_SCORE_UNAVAILABLE'
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
  const speakingCourseProvider = options.speakingCourseProvider || createFileSpeakingCourseProvider()
  const speakingScorer = options.speakingScorer
  const speakingRecordingUrl = options.speakingRecordingUrl

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
    const rows = await store.listResults('listening')
    return {
      ok: true,
      data_kind: 'test',
      results: rows.filter((item) => item.module_type === 'listening' && item.data_kind === 'test')
        .sort((left, right) => new Date(right.created_at) - new Date(left.created_at))
    }
  }

  async function scoreSpeakingTake(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    const request = event.request
    if (!request || !boundedString(request.result_id, 1, 80)
      || !boundedString(request.course_id, 1, 80) || !boundedString(request.course_version, 1, 40)
      || !Number.isInteger(request.question_id) || !Number.isInteger(request.attempt)
      || request.attempt < 1 || request.attempt > 3
      || !boundedString(request.wav_base64, 1024, 900_000)) {
      throw new ServiceError('INVALID_SPEAKING_TAKE')
    }
    let loaded
    try { loaded = speakingCourseProvider.get(request.course_id) } catch { throw new ServiceError('COURSE_NOT_FOUND') }
    if (loaded.version !== request.course_version) throw new ServiceError('COURSE_VERSION_MISMATCH')
    const question = loaded.course.questions.find((item) => item.id === request.question_id)
    if (!question) throw new ServiceError('INVALID_SPEAKING_TAKE')
    const takeId = crypto.createHash('sha256').update(`${request.result_id}:${request.course_id}:${request.question_id}:${request.attempt}`).digest('hex')
    const cached = typeof store.getSpeakingTake === 'function' ? await store.getSpeakingTake(takeId) : null
    if (cached) {
      if (cached.created_by_session !== session.token_hash.slice(0, 16)) throw new ServiceError('RESULT_ID_CONFLICT')
      return { ...cached.response, idempotent: true }
    }
    if (typeof speakingScorer !== 'function') throw new ServiceError('SPEAKING_SCORE_UNAVAILABLE')
    let scored
    try {
      scored = await speakingScorer({
        result_id: request.result_id, course_id: request.course_id, course_version: request.course_version,
        question_id: request.question_id, attempt: request.attempt,
        target_text: question.text || question.expected, wav_base64: request.wav_base64,
        session_marker: session.token_hash.slice(0, 16)
      })
    } catch (error) {
      throw new ServiceError(safeSpeakingScoreError(error))
    }
    if (!scored || scored.course_id !== request.course_id || scored.course_version !== request.course_version
      || scored.question_id !== request.question_id || scored.attempt !== request.attempt
      || (!Number.isFinite(scored.total) && !scored.is_rejected)
      || !boundedString(scored.recording_path, 1, 512)) {
      throw new ServiceError('SPEAKING_SCORE_UNAVAILABLE')
    }
    const trusted = {
      course_id: request.course_id, course_version: request.course_version,
      question_id: request.question_id, attempt: request.attempt,
      total: scored.total ?? null, accuracy: scored.accuracy ?? null, fluency: scored.fluency ?? null,
      integrity: scored.integrity ?? null, is_rejected: Boolean(scored.is_rejected),
      words: Array.isArray(scored.words) ? scored.words.slice(0, 80) : [],
      recording_path: scored.recording_path,
      recording_file_id: boundedString(scored.recording_file_id, 1, 1024) ? scored.recording_file_id : scored.recording_path
    }
    const feedback = feedbackForTake(trusted)
    const stars = scoreToStars(trusted.total, trusted.is_rejected)
    await store.saveAudit({ action: 'speaking_test_take_scored', caller_id: requestContext.callerId, course_id: request.course_id, question_id: request.question_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    const response = {
      ok: true, stars, child_feedback: feedback.child_feedback,
      weak_words: feedback.weak_words, word_lights: feedback.word_lights,
      proof: signTakeProof(trusted, hmacKey), can_retry: stars < 3 && request.attempt < 3,
      can_skip: stars < 3 && request.attempt >= 3
    }
    if (typeof store.saveSpeakingTake === 'function') {
      await store.saveSpeakingTake({ take_id: takeId, response, created_by_session: session.token_hash.slice(0, 16), created_at: new Date(now()), data_kind: 'test' })
    }
    return { ...response, idempotent: false }
  }

  async function submitSpeakingResult(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    const requestedId = event.submission?.result_id
    if (!boundedString(requestedId, 1, 80)) throw new ServiceError('INVALID_SPEAKING_RESULT')
    const existing = await store.getResult(requestedId)
    if (existing) {
      if (existing.created_by_session !== session.token_hash.slice(0, 16) || existing.module_type !== 'speaking') throw new ServiceError('RESULT_ID_CONFLICT')
      return { ok: true, result_id: existing.result_id, data_kind: 'test', formal_completion_eligible: false, idempotent: true }
    }
    let loaded
    try { loaded = speakingCourseProvider.get(event.submission?.course_id) } catch { throw new ServiceError('COURSE_NOT_FOUND') }
    let submitted
    try { submitted = buildSpeakingResult(loaded.course, event.submission, loaded.version, hmacKey) } catch { throw new ServiceError('INVALID_SPEAKING_RESULT') }
    submitted.created_at = new Date(now())
    submitted.created_by_session = session.token_hash.slice(0, 16)
    await store.saveResult(submitted)
    await store.saveAudit({ action: 'speaking_test_result_created', caller_id: requestContext.callerId, result_id: submitted.result_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return { ok: true, result_id: submitted.result_id, data_kind: 'test', formal_completion_eligible: false, idempotent: false }
  }

  async function listSpeakingTestResults(event, requestContext) {
    await requireTestSession(event, requestContext)
    const rows = await store.listResults('speaking')
    return { ok: true, data_kind: 'test', results: rows.filter((item) => item.module_type === 'speaking' && item.data_kind === 'test').sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) }
  }

  function parentFilters(value) {
    const filters = value && typeof value === 'object' && !Array.isArray(value) ? value : {}
    const dataKind = filters.data_kind === undefined ? 'formal' : filters.data_kind
    if (!['formal', 'test'].includes(dataKind)
      || (filters.module_type !== undefined && !PARENT_RESULT_MODULES.has(filters.module_type))
      || (filters.course_id !== undefined && !/^[WS]\d{2}D\d{2}$/.test(filters.course_id))
      || (filters.date_from !== undefined && !isIsoDate(filters.date_from))
      || (filters.date_to !== undefined && !isIsoDate(filters.date_to))) throw new ServiceError('INVALID_FILTER')
    if (filters.date_from && filters.date_to && Date.parse(filters.date_from) > Date.parse(filters.date_to)) throw new ServiceError('INVALID_FILTER')
    return {
      data_kind: dataKind,
      ...(filters.module_type ? { module_type: filters.module_type } : {}),
      ...(filters.course_id ? { course_id: filters.course_id } : {}),
      ...(filters.date_from ? { date_from: filters.date_from } : {}),
      ...(filters.date_to ? { date_to: filters.date_to } : {})
    }
  }

  async function listParentResults(event, requestContext) {
    await requireTestSession(event, requestContext)
    const filters = parentFilters(event.filters)
    let rows = await store.listParentResults(filters)
    if (filters.date_from) rows = rows.filter((item) => Date.parse(item.submitted_at || item.created_at) >= Date.parse(filters.date_from))
    if (filters.date_to) rows = rows.filter((item) => Date.parse(item.submitted_at || item.created_at) <= Date.parse(filters.date_to))
    rows.sort((left, right) => Date.parse(right.submitted_at || right.created_at) - Date.parse(left.submitted_at || left.created_at))
    const completedCourses = new Set(rows.filter((item) => item.status === 'completed').map((item) => item.course_id))
    return {
      ok: true,
      data_kind: filters.data_kind,
      filters,
      summary: {
        result_count: rows.length,
        completed_course_count: completedCourses.size,
        formal_completion_count: filters.data_kind === 'formal' ? completedCourses.size : 0
      },
      results: rows
    }
  }

  async function getParentRecordingUrl(event, requestContext, testOnly = false) {
    await requireTestSession(event, requestContext)
    const result = await store.getResult(event.result_id)
    if (!result || result.module_type !== 'speaking' || (testOnly && result.data_kind !== 'test') || typeof speakingRecordingUrl !== 'function') throw new ServiceError('RECORDING_NOT_FOUND')
    const question = result.question_results?.find((item) => item.id === event.question_id)
    const record = question?.recording_records?.[Number(event.attempt) - 1]
    const fileId = record?.file_id || question?.recordings?.[Number(event.attempt) - 1]
    if (!fileId || (record?.data_kind && record.data_kind !== result.data_kind)) throw new ServiceError('RECORDING_NOT_FOUND')
    try {
      const url = await speakingRecordingUrl(fileId)
      if (!boundedString(url, 8, 4096)) throw new Error('invalid')
      return { ok: true, url, expires_in: 600 }
    } catch { throw new ServiceError('RECORDING_UNAVAILABLE') }
  }

  async function getSpeakingRecordingUrl(event, requestContext) {
    return getParentRecordingUrl(event, requestContext, true)
  }

  return {
    async handle(event = {}, requestContext = { callerId: 'unknown' }) {
      if (event.action === 'health') {
        return {
          ok: true, service: 'sherlock-api', stage: 'P4', formal_enabled: false, writes: 'test-only',
          speaking_course_versions: Object.fromEntries(speakingCourseProvider.catalog().map((item) => [item.course_id, item.course_version]))
        }
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
      if (event.action === 'scoreSpeakingTake') return scoreSpeakingTake(event, requestContext)
      if (event.action === 'submitSpeakingResult') return submitSpeakingResult(event, requestContext)
      if (event.action === 'listSpeakingTestResults') return listSpeakingTestResults(event, requestContext)
      if (event.action === 'getSpeakingRecordingUrl') return getSpeakingRecordingUrl(event, requestContext)
      if (event.action === 'listParentResults') return listParentResults(event, requestContext)
      if (event.action === 'getParentRecordingUrl') return getParentRecordingUrl(event, requestContext)
      if (typeof event.action === 'string' && event.action.toLowerCase().includes('formal')) {
        throw new ServiceError('FORMAL_DISABLED')
      }
      throw new ServiceError('UNKNOWN_ACTION')
    }
  }
}

module.exports = { ServiceError, createService, hashPassword, verifyPassword, validateResult }
