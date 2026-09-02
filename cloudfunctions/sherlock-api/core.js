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
const PARENT_COURSE_ID = /^(?:[WS]\d{2}D\d{2}|[LS][1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})$/
const SHA256_PATTERN = /^[a-f0-9]{64}$/
const MAX_SPEAKING_WAV_BYTES = 700_000
const MAX_SPEAKING_CHUNKS = 16
const MAX_SPEAKING_CHUNK_BASE64 = 65_536
const DIRECT_UPLOAD_PROBE_ALLOWED_BYTES = new Set([150 * 1024, 400 * 1024, 700_000])
const DIRECT_UPLOAD_PROBE_TTL_MS = 120_000
const DIRECT_UPLOAD_PROBE_PREFIX = 'sherlock-english/test/direct-upload-probe'
const SPEAKING_DIRECT_UPLOAD_TTL_MS = 120_000
const SPEAKING_DIRECT_UPLOAD_PREFIX = 'sherlock-english/tmp-speaking-direct/test'
const FORMAL_ENTRY_MODES = new Set(['dual', 'github-http-only', 'cloudbase-event-only'])

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

function strictBase64(value, min, max) {
  if (!boundedString(value, min, max) || value.length % 4 !== 0 || !/^[A-Za-z0-9+/]+={0,2}$/.test(value)) return null
  const bytes = Buffer.from(value, 'base64')
  return bytes.toString('base64') === value ? bytes : null
}

function sha256Hex(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex')
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

function callerOwnerHash(callerId, hmacKey) {
  return crypto.createHmac('sha256', hmacKey).update(`formal-caller:${callerId}`).digest('hex')
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
  const speakingUploadStore = options.speakingUploadStore
  const directUploadProbeStore = options.directUploadProbeStore
  const speakingDirectUploadStore = options.speakingDirectUploadStore
  const randomProbeId = options.randomProbeId || (() => crypto.randomUUID())
  const formalEnabled = options.formalEnabled === true
  const formalEntryMode = options.formalEntryMode || 'dual'
  const speakingDirectUploadEnabled = options.speakingDirectUploadEnabled === true
  const monotonicNow = options.monotonicNow || Date.now

  function requestTransport(requestContext) {
    return requestContext?.transport === 'github-http' ? 'github-http' : 'cloudbase-event'
  }

  function assertFormalEntry(requestContext, session) {
    if (!FORMAL_ENTRY_MODES.has(formalEntryMode)) throw new ServiceError('CONFIG_ERROR')
    const transport = requestTransport(requestContext)
    if ((formalEntryMode === 'github-http-only' && transport !== 'github-http')
      || (formalEntryMode === 'cloudbase-event-only' && transport !== 'cloudbase-event')) {
      throw new ServiceError('FORMAL_ENTRY_REQUIRED')
    }
    if (session?.entry_channel && session.entry_channel !== transport) throw new ServiceError('FORMAL_ENTRY_REQUIRED')
    if (formalEntryMode !== 'dual' && !session?.entry_channel && session !== undefined) throw new ServiceError('FORMAL_ENTRY_REQUIRED')
    return transport
  }

  function ownershipFields(session, requestContext) {
    return {
      created_by_session: session.token_hash.slice(0, 16),
      ...(session.data_kind === 'formal' ? { created_by_caller: callerOwnerHash(requestContext.callerId, hmacKey) } : {})
    }
  }

  function belongsToSession(record, session, requestContext) {
    if (session.data_kind === 'formal' && boundedString(record?.created_by_caller, 64, 64)) {
      return record.created_by_caller === callerOwnerHash(requestContext.callerId, hmacKey)
    }
    return record?.created_by_session === session.token_hash.slice(0, 16)
  }

  function assertCourseAllowedForSession(course, session) {
    if (session.data_kind === 'formal' && course?.publication_status === 'test') {
      throw new ServiceError('COURSE_NOT_FORMAL')
    }
  }

  function speakingTakeId(session, request) {
    return crypto.createHash('sha256').update(`${session.data_kind}:${request.result_id}:${request.course_id}:${request.question_id}:${request.attempt}`).digest('hex')
  }

  function speakingUploadOwner(session, requestContext) {
    const identity = session.data_kind === 'formal'
      ? callerOwnerHash(requestContext.callerId, hmacKey)
      : session.token_hash
    return crypto.createHmac('sha256', hmacKey).update(`speaking-upload:${identity}`).digest('hex').slice(0, 32)
  }

  function speakingChunkPath(session, request, requestContext, chunkIndex) {
    const part = String(chunkIndex).padStart(2, '0')
    return `sherlock-english/tmp-speaking/${session.data_kind}/${speakingUploadOwner(session, requestContext)}/${speakingTakeId(session, request)}/part-${part}.bin`
  }

  function fileIdMatchesPath(fileId, path) {
    if (!boundedString(fileId, 1, 1024)) return false
    try { return decodeURIComponent(fileId).endsWith(`/${path}`) } catch { return false }
  }

  function directUploadProbeOwner(session, requestContext) {
    return crypto.createHmac('sha256', hmacKey)
      .update(`direct-upload-probe:${session.token_hash}:${requestContext.callerId}`)
      .digest('hex')
  }

  function speakingDirectUploadOwner(session, requestContext) {
    return crypto.createHmac('sha256', hmacKey)
      .update(`speaking-direct-upload:${session.token_hash}:${requestContext.callerId}`)
      .digest('hex')
  }

  function speakingDirectUploadPath(session, request, requestContext) {
    const owner = speakingDirectUploadOwner(session, requestContext).slice(0, 32)
    return `${SPEAKING_DIRECT_UPLOAD_PREFIX}/${owner}/${speakingTakeId(session, request)}.wav`
  }

  function signDirectUploadTicket(payload) {
    const encoded = Buffer.from(JSON.stringify(payload)).toString('base64url')
    const signature = crypto.createHmac('sha256', hmacKey).update(encoded).digest('hex')
    return `${encoded}.${signature}`
  }

  function readDirectUploadTicket(ticket, session, requestContext, { allowExpired = false } = {}) {
    if (!boundedString(ticket, 80, 4096)) throw new ServiceError('INVALID_DIRECT_UPLOAD_TICKET')
    const parts = ticket.split('.')
    if (parts.length !== 2 || !/^[A-Za-z0-9_-]+$/.test(parts[0]) || !/^[0-9a-f]{64}$/.test(parts[1])) {
      throw new ServiceError('INVALID_DIRECT_UPLOAD_TICKET')
    }
    const expected = crypto.createHmac('sha256', hmacKey).update(parts[0]).digest()
    const actual = Buffer.from(parts[1], 'hex')
    if (actual.length !== expected.length || !crypto.timingSafeEqual(actual, expected)) {
      throw new ServiceError('INVALID_DIRECT_UPLOAD_TICKET')
    }
    let payload
    try { payload = JSON.parse(Buffer.from(parts[0], 'base64url').toString('utf8')) } catch { throw new ServiceError('INVALID_DIRECT_UPLOAD_TICKET') }
    const valid = payload && payload.v === 1
      && payload.owner === directUploadProbeOwner(session, requestContext)
      && boundedString(payload.object_key, DIRECT_UPLOAD_PROBE_PREFIX.length + 10, DIRECT_UPLOAD_PROBE_PREFIX.length + 90)
      && payload.object_key.startsWith(`${DIRECT_UPLOAD_PROBE_PREFIX}/`)
      && payload.object_key.endsWith('.wav')
      && fileIdMatchesPath(payload.file_id, payload.object_key)
      && Number.isInteger(payload.byte_length)
      && DIRECT_UPLOAD_PROBE_ALLOWED_BYTES.has(payload.byte_length)
      && SHA256_PATTERN.test(payload.sha256 || '')
      && payload.content_type === 'audio/wav'
      && Number.isFinite(payload.issued_at)
      && Number.isFinite(payload.expires_at)
      && payload.expires_at - payload.issued_at === DIRECT_UPLOAD_PROBE_TTL_MS
    if (!valid) throw new ServiceError('INVALID_DIRECT_UPLOAD_TICKET')
    if (!allowExpired && payload.expires_at <= now()) throw new ServiceError('UPLOAD_TICKET_EXPIRED')
    return payload
  }

  function readSpeakingDirectUploadTicket(ticket, session, request, requestContext, { allowExpired = false } = {}) {
    if (!boundedString(ticket, 80, 4096)) throw new ServiceError('INVALID_SPEAKING_DIRECT_TICKET')
    const parts = ticket.split('.')
    if (parts.length !== 2 || !/^[A-Za-z0-9_-]+$/.test(parts[0]) || !/^[0-9a-f]{64}$/.test(parts[1])) {
      throw new ServiceError('INVALID_SPEAKING_DIRECT_TICKET')
    }
    const expected = crypto.createHmac('sha256', hmacKey).update(parts[0]).digest()
    const actual = Buffer.from(parts[1], 'hex')
    if (actual.length !== expected.length || !crypto.timingSafeEqual(actual, expected)) {
      throw new ServiceError('INVALID_SPEAKING_DIRECT_TICKET')
    }
    let payload
    try { payload = JSON.parse(Buffer.from(parts[0], 'base64url').toString('utf8')) } catch { throw new ServiceError('INVALID_SPEAKING_DIRECT_TICKET') }
    const boundRequest = request || payload || {}
    const expectedPath = speakingDirectUploadPath(session, boundRequest, requestContext)
    const expectedTakeId = speakingTakeId(session, boundRequest)
    const valid = payload && payload.v === 2
      && payload.owner === speakingDirectUploadOwner(session, requestContext)
      && payload.data_kind === 'test'
      && payload.result_id === boundRequest.result_id
      && payload.course_id === boundRequest.course_id
      && payload.course_version === boundRequest.course_version
      && payload.question_id === boundRequest.question_id
      && payload.attempt === boundRequest.attempt
      && payload.take_id === expectedTakeId
      && payload.object_key === expectedPath
      && fileIdMatchesPath(payload.file_id, expectedPath)
      && payload.byte_length === boundRequest.byte_length
      && payload.sha256 === boundRequest.sha256
      && payload.content_type === boundRequest.content_type
      && Number.isFinite(payload.issued_at)
      && Number.isFinite(payload.expires_at)
      && payload.expires_at - payload.issued_at === SPEAKING_DIRECT_UPLOAD_TTL_MS
    if (!valid) throw new ServiceError('INVALID_SPEAKING_DIRECT_TICKET')
    if (!allowExpired && payload.expires_at <= now()) throw new ServiceError('SPEAKING_DIRECT_TICKET_EXPIRED')
    return payload
  }

  async function requireSession(event, requestContext, expectedKind) {
    if (!boundedString(hmacKey, 16, 512) || !boundedString(event.session_token, 1, 512)) {
      throw new ServiceError('UNAUTHORIZED')
    }
    const hash = tokenHash(event.session_token, hmacKey)
    const session = await store.getSession(hash)
    const expiresAt = session?.expires_at instanceof Date ? session.expires_at.getTime() : Date.parse(session?.expires_at)
    if (!session || session.caller_id !== requestContext.callerId || !Number.isFinite(expiresAt) || expiresAt <= now()
      || !['formal', 'test'].includes(session.data_kind) || (expectedKind && session.data_kind !== expectedKind)) {
      throw new ServiceError('UNAUTHORIZED')
    }
    if (session.data_kind === 'formal') assertFormalEntry(requestContext, session)
    return { ...session, token_hash: session.token_hash || hash }
  }

  async function requireTestSession(event, requestContext) {
    return requireSession(event, requestContext, 'test')
  }

  async function createDirectUploadProbe(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    const request = event.request
    if (!request || !Number.isInteger(request.byte_length)
      || !DIRECT_UPLOAD_PROBE_ALLOWED_BYTES.has(request.byte_length)
      || !SHA256_PATTERN.test(request.sha256 || '')
      || request.content_type !== 'audio/wav') throw new ServiceError('INVALID_DIRECT_UPLOAD_PROBE')
    if (!directUploadProbeStore) throw new ServiceError('SIGNING_UNAVAILABLE')
    const probeId = randomProbeId()
    if (!/^[A-Za-z0-9_-]{8,80}$/.test(probeId)) throw new ServiceError('SIGNING_UNAVAILABLE')
    const objectKey = `${DIRECT_UPLOAD_PROBE_PREFIX}/${probeId}.wav`
    let upload
    try {
      upload = await directUploadProbeStore.issue(objectKey, {
        expiresIn: DIRECT_UPLOAD_PROBE_TTL_MS / 1000,
        contentType: request.content_type
      })
    } catch { throw new ServiceError('SIGNING_UNAVAILABLE') }
    if (!boundedString(upload?.upload_url, 1, 4096) || !upload.upload_url.startsWith('https://')
      || !fileIdMatchesPath(upload?.file_id, objectKey)
      || upload.expires_in !== DIRECT_UPLOAD_PROBE_TTL_MS / 1000) throw new ServiceError('SIGNING_UNAVAILABLE')
    const timestamp = now()
    const payload = {
      v: 1,
      owner: directUploadProbeOwner(session, requestContext),
      object_key: objectKey,
      file_id: upload.file_id,
      byte_length: request.byte_length,
      sha256: request.sha256,
      content_type: request.content_type,
      issued_at: timestamp,
      expires_at: timestamp + DIRECT_UPLOAD_PROBE_TTL_MS
    }
    return {
      ok: true,
      data_kind: 'test',
      upload_url: upload.upload_url,
      object_key: objectKey,
      file_id: upload.file_id,
      byte_length: request.byte_length,
      expires_at: new Date(payload.expires_at).toISOString(),
      ticket: signDirectUploadTicket(payload)
    }
  }

  async function removeDirectUploadProbe(fileId) {
    try {
      await directUploadProbeStore.remove(fileId)
      return true
    } catch {
      return false
    }
  }

  async function verifyDirectUploadProbe(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    if (!directUploadProbeStore) throw new ServiceError('SIGNING_UNAVAILABLE')
    const payload = readDirectUploadTicket(event.ticket, session, requestContext)
    let bytes
    try { bytes = await directUploadProbeStore.download(payload.file_id) } catch {
      await removeDirectUploadProbe(payload.file_id)
      throw new ServiceError('UPLOAD_OBJECT_MISSING')
    }
    let integrityError = ''
    if (!Buffer.isBuffer(bytes) || bytes.length !== payload.byte_length) integrityError = 'UPLOAD_SIZE_MISMATCH'
    else if (sha256Hex(bytes) !== payload.sha256) integrityError = 'UPLOAD_HASH_MISMATCH'
    const cleanedUp = await removeDirectUploadProbe(payload.file_id)
    if (!cleanedUp) throw new ServiceError('UPLOAD_CLEANUP_FAILED')
    if (integrityError) throw new ServiceError(integrityError)
    return {
      ok: true,
      data_kind: 'test',
      byte_length: bytes.length,
      sha256: payload.sha256,
      cleaned_up: true
    }
  }

  async function cancelDirectUploadProbe(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    if (!directUploadProbeStore) throw new ServiceError('SIGNING_UNAVAILABLE')
    const payload = readDirectUploadTicket(event.ticket, session, requestContext, { allowExpired: true })
    if (!(await removeDirectUploadProbe(payload.file_id))) throw new ServiceError('UPLOAD_CLEANUP_FAILED')
    return { ok: true, data_kind: 'test', cleaned_up: true }
  }

  function validateSpeakingDirectDeclaration(request) {
    if (!Number.isInteger(request.byte_length) || request.byte_length < 768 || request.byte_length > MAX_SPEAKING_WAV_BYTES
      || !SHA256_PATTERN.test(request.sha256 || '') || request.content_type !== 'audio/wav') {
      throw new ServiceError('INVALID_SPEAKING_DIRECT_UPLOAD')
    }
  }

  async function createSpeakingDirectUpload(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    if (!speakingDirectUploadEnabled) throw new ServiceError('SPEAKING_DIRECT_UPLOAD_DISABLED')
    if (!speakingDirectUploadStore) throw new ServiceError('SPEAKING_DIRECT_SIGNING_UNAVAILABLE')
    const request = event.request
    const { course, takeId } = resolveSpeakingTake(session, request)
    if (course?.publication_status === 'test') throw new ServiceError('COURSE_NOT_FORMAL')
    validateSpeakingDirectDeclaration(request)
    const objectKey = speakingDirectUploadPath(session, request, requestContext)
    let upload
    try {
      upload = await speakingDirectUploadStore.issue(objectKey, {
        expiresIn: SPEAKING_DIRECT_UPLOAD_TTL_MS / 1000,
        contentType: request.content_type
      })
    } catch { throw new ServiceError('SPEAKING_DIRECT_SIGNING_UNAVAILABLE') }
    if (!boundedString(upload?.upload_url, 1, 4096) || !upload.upload_url.startsWith('https://')
      || !fileIdMatchesPath(upload?.file_id, objectKey)
      || upload.expires_in !== SPEAKING_DIRECT_UPLOAD_TTL_MS / 1000) {
      throw new ServiceError('SPEAKING_DIRECT_SIGNING_UNAVAILABLE')
    }
    const timestamp = now()
    const payload = {
      v: 2,
      owner: speakingDirectUploadOwner(session, requestContext),
      data_kind: 'test',
      result_id: request.result_id,
      course_id: request.course_id,
      course_version: request.course_version,
      question_id: request.question_id,
      attempt: request.attempt,
      take_id: takeId,
      object_key: objectKey,
      file_id: upload.file_id,
      byte_length: request.byte_length,
      sha256: request.sha256,
      content_type: request.content_type,
      issued_at: timestamp,
      expires_at: timestamp + SPEAKING_DIRECT_UPLOAD_TTL_MS
    }
    await store.saveAudit({
      action: 'speaking_test_direct_upload_issued', caller_id: requestContext.callerId,
      course_id: request.course_id, question_id: request.question_id, take_id: takeId,
      occurred_at: new Date(timestamp), log_tag: 'sherlock-english'
    })
    return {
      ok: true,
      data_kind: 'test',
      upload_url: upload.upload_url,
      byte_length: request.byte_length,
      expires_at: new Date(payload.expires_at).toISOString(),
      ticket: signDirectUploadTicket(payload)
    }
  }

  async function removeSpeakingDirectObject(fileId) {
    try {
      await speakingDirectUploadStore.remove(fileId)
      return true
    } catch {
      return false
    }
  }

  function isPcmWav(bytes) {
    return Buffer.isBuffer(bytes) && bytes.length >= 44
      && bytes.subarray(0, 4).toString() === 'RIFF'
      && bytes.subarray(8, 12).toString() === 'WAVE'
  }

  async function scoreDirectUploadedSpeakingTake(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    if (!speakingDirectUploadEnabled) throw new ServiceError('SPEAKING_DIRECT_UPLOAD_DISABLED')
    if (!speakingDirectUploadStore) throw new ServiceError('SPEAKING_DIRECT_SIGNING_UNAVAILABLE')
    const request = event.request
    const { course, question, takeId } = resolveSpeakingTake(session, request)
    if (course?.publication_status === 'test') throw new ServiceError('COURSE_NOT_FORMAL')
    validateSpeakingDirectDeclaration(request)
    const payload = readSpeakingDirectUploadTicket(event.ticket, session, request, requestContext)
    let validationMs = 0
    const scoringStarted = monotonicNow()
    let response
    let scoreError
    try {
      response = await scorePreparedSpeakingTake(session, request, requestContext, question, takeId, async () => {
        const validationStarted = monotonicNow()
        let bytes
        try { bytes = await speakingDirectUploadStore.download(payload.file_id) } catch {
          throw new ServiceError('SPEAKING_DIRECT_OBJECT_MISSING')
        }
        if (!isPcmWav(bytes) || bytes.length !== payload.byte_length || sha256Hex(bytes) !== payload.sha256) {
          throw new ServiceError('SPEAKING_DIRECT_INTEGRITY_FAILED')
        }
        validationMs = Math.max(0, monotonicNow() - validationStarted)
        return bytes.toString('base64')
      })
    } catch (error) {
      scoreError = error
    }
    const scoringFinished = monotonicNow()
    const cleanupStarted = monotonicNow()
    const cleanedUp = await removeSpeakingDirectObject(payload.file_id)
    const cleanupFinished = monotonicNow()
    if (!cleanedUp) {
      await store.saveAudit({
        action: 'speaking_test_direct_upload_cleanup_failed', caller_id: requestContext.callerId,
        course_id: request.course_id, question_id: request.question_id, take_id: takeId,
        occurred_at: new Date(now()), log_tag: 'sherlock-english'
      })
    }
    if (scoreError) throw scoreError
    await store.saveAudit({
      action: 'speaking_test_direct_upload_scored', caller_id: requestContext.callerId,
      course_id: request.course_id, question_id: request.question_id, take_id: takeId,
      idempotent: response.idempotent === true, cleaned_up: cleanedUp,
      occurred_at: new Date(now()), log_tag: 'sherlock-english'
    })
    return {
      ...response,
      transport: 'direct',
      cleaned_up: cleanedUp,
      server_timing: {
        validation_ms: Math.round(validationMs),
        scoring_ms: Math.round(Math.max(0, scoringFinished - scoringStarted - validationMs)),
        cleanup_ms: Math.round(Math.max(0, cleanupFinished - cleanupStarted))
      }
    }
  }

  async function cancelSpeakingDirectUpload(event, requestContext) {
    const session = await requireTestSession(event, requestContext)
    if (!speakingDirectUploadStore) throw new ServiceError('SPEAKING_DIRECT_SIGNING_UNAVAILABLE')
    const payload = readSpeakingDirectUploadTicket(event.ticket, session, undefined, requestContext, { allowExpired: true })
    if (!(await removeSpeakingDirectObject(payload.file_id))) throw new ServiceError('SPEAKING_DIRECT_CLEANUP_FAILED')
    await store.saveAudit({
      action: 'speaking_test_direct_upload_cancelled', caller_id: requestContext.callerId,
      course_id: payload.course_id, question_id: payload.question_id, take_id: payload.take_id,
      occurred_at: new Date(now()), log_tag: 'sherlock-english'
    })
    return { ok: true, data_kind: 'test', cleaned_up: true }
  }

  async function startChildSession(_event, requestContext) {
    if (!formalEnabled) throw new ServiceError('FORMAL_DISABLED')
    if (!boundedString(hmacKey, 16, 512) || !boundedString(requestContext.callerId, 1, 512)) throw new ServiceError('CONFIG_ERROR')
    const entryChannel = assertFormalEntry(requestContext)
    const timestamp = now()
    const token = randomToken()
    const expiresAt = timestamp + sessionTtlMs
    await store.saveSession({
      token_hash: tokenHash(token, hmacKey), caller_id: requestContext.callerId, data_kind: 'formal',
      entry_channel: entryChannel,
      created_at: new Date(timestamp), expires_at: new Date(expiresAt)
    })
    await store.saveAudit({ action: 'formal_child_session_started', caller_id: requestContext.callerId, occurred_at: new Date(timestamp), log_tag: 'sherlock-english' })
    return { ok: true, session_token: token, expires_at: new Date(expiresAt).toISOString(), data_kind: 'formal' }
  }

  async function getFormalProgress(event, requestContext) {
    await requireSession(event, requestContext, 'formal')
    const rows = await store.listParentResults({ data_kind: 'formal' })
    const completed = { listening: new Set(), speaking: new Set() }
    for (const item of rows) {
      if (item?.student_id === 'sherlock' && item.data_kind === 'formal' && item.status === 'completed' && completed[item.module_type]) {
        completed[item.module_type].add(item.course_id)
      }
    }
    return {
      ok: true,
      completed_course_ids: {
        listening: [...completed.listening].sort(),
        speaking: [...completed.speaking].sort()
      }
    }
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
    const session = await requireSession(event, requestContext)
    validateResult(event.result)
    const resultId = crypto.randomUUID()
    const submitted = {
      result_id: resultId,
      student_id: event.result.student_id,
      module_type: event.result.module_type,
      course_id: event.result.course_id,
      ...(event.result.pair_id ? { pair_id: event.result.pair_id } : {}),
      data_kind: session.data_kind,
      course_version: event.result.course_version,
      started_at: new Date(event.result.started_at),
      submitted_at: new Date(event.result.submitted_at),
      duration_seconds: event.result.duration_seconds,
      device_info: event.result.device_info || {},
      payload: event.result.payload,
      formal_completion_eligible: session.data_kind === 'formal',
      created_at: new Date(now()),
      created_by_session: session.token_hash.slice(0, 16)
    }
    await store.saveResult(submitted)
    await store.saveAudit({ action: `${session.data_kind}_result_created`, caller_id: requestContext.callerId, result_id: resultId, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return { ok: true, result_id: resultId, data_kind: session.data_kind, formal_completion_eligible: session.data_kind === 'formal' }
  }

  async function submitListeningResult(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const requestedId = event.submission?.result_id
    if (!boundedString(requestedId, 1, 80)) throw new ServiceError('INVALID_LISTENING_RESULT')
    let loaded
    try {
      loaded = courseProvider.get(event.submission?.course_id)
    } catch {
      throw new ServiceError('COURSE_NOT_FOUND')
    }
    assertCourseAllowedForSession(loaded.course, session)
    const existing = await store.getResult(requestedId)
    if (existing) {
      if (!belongsToSession(existing, session, requestContext) || existing.module_type !== 'listening'
        || existing.data_kind !== session.data_kind || existing.course_id !== event.submission?.course_id) {
        throw new ServiceError('RESULT_ID_CONFLICT')
      }
      return {
        ok: true, result_id: existing.result_id, data_kind: session.data_kind, formal_completion_eligible: session.data_kind === 'formal',
        wrong_question_ids: (existing.wrong_answers || []).map((item) => item.id), idempotent: true
      }
    }
    let submitted
    try {
      submitted = scoreListeningSubmission(loaded.course, event.submission, loaded.version, session.data_kind)
    } catch {
      throw new ServiceError('INVALID_LISTENING_RESULT')
    }
    submitted.created_at = new Date(now())
    Object.assign(submitted, ownershipFields(session, requestContext))
    await store.saveResult(submitted)
    await store.saveAudit({ action: `listening_${session.data_kind}_result_created`, caller_id: requestContext.callerId, result_id: submitted.result_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return {
      ok: true, result_id: submitted.result_id, data_kind: session.data_kind, formal_completion_eligible: session.data_kind === 'formal',
      wrong_question_ids: submitted.wrong_answers.map((item) => item.id), idempotent: false
    }
  }

  function transcriptFor(course, question) {
    const section = course.sections.find((item) => item.id === question.section)
    const source = question.type === 'passage_judge' ? section?.passage_transcript : section?.questions.find((item) => item.id === question.id)?.transcript
    return Array.isArray(source) ? source.map((part) => Array.isArray(part) ? String(part[1]) : String(part)) : []
  }

  async function checkListeningCorrection(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const result = await store.getResult(event.result_id)
    if (!result || result.module_type !== 'listening' || result.data_kind !== session.data_kind) throw new ServiceError('RESULT_NOT_FOUND')
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

  function resolveSpeakingTake(session, request) {
    if (!request || !boundedString(request.result_id, 1, 80)
      || !boundedString(request.course_id, 1, 80) || !boundedString(request.course_version, 1, 40)
      || !Number.isInteger(request.question_id) || !Number.isInteger(request.attempt)
      || request.attempt < 1 || request.attempt > 3) {
      throw new ServiceError('INVALID_SPEAKING_TAKE')
    }
    let loaded
    try { loaded = speakingCourseProvider.get(request.course_id) } catch { throw new ServiceError('COURSE_NOT_FOUND') }
    assertCourseAllowedForSession(loaded.course, session)
    if (loaded.version !== request.course_version) throw new ServiceError('COURSE_VERSION_MISMATCH')
    const question = loaded.course.questions.find((item) => item.id === request.question_id)
    if (!question) throw new ServiceError('INVALID_SPEAKING_TAKE')
    return { course: loaded.course, question, takeId: speakingTakeId(session, request) }
  }

  async function scorePreparedSpeakingTake(session, request, requestContext, question, takeId, wavProvider) {
    const cached = typeof store.getSpeakingTake === 'function' ? await store.getSpeakingTake(takeId) : null
    if (cached) {
      if (!belongsToSession(cached, session, requestContext) || cached.data_kind !== session.data_kind) throw new ServiceError('RESULT_ID_CONFLICT')
      return { ...cached.response, idempotent: true }
    }
    if (typeof speakingScorer !== 'function') throw new ServiceError('SPEAKING_SCORE_UNAVAILABLE')
    const wavBase64 = await wavProvider()
    if (!boundedString(wavBase64, 1024, 900_000)) throw new ServiceError('INVALID_SPEAKING_TAKE')
    let scored
    try {
      scored = await speakingScorer({
        result_id: request.result_id, course_id: request.course_id, course_version: request.course_version,
        question_id: request.question_id, attempt: request.attempt,
        target_text: question.text || question.expected, wav_base64: wavBase64,
        session_marker: session.token_hash.slice(0, 16), data_kind: session.data_kind
      })
    } catch (error) {
      throw new ServiceError(safeSpeakingScoreError(error))
    }
    if (!scored || scored.course_id !== request.course_id || scored.course_version !== request.course_version
      || scored.question_id !== request.question_id || scored.attempt !== request.attempt || scored.data_kind !== session.data_kind
      || (!Number.isFinite(scored.total) && !scored.is_rejected)
      || !boundedString(scored.recording_path, 1, 512)) {
      throw new ServiceError('SPEAKING_SCORE_UNAVAILABLE')
    }
    const trusted = {
      course_id: request.course_id, course_version: request.course_version,
      question_id: request.question_id, attempt: request.attempt, data_kind: session.data_kind,
      total: scored.total ?? null, accuracy: scored.accuracy ?? null, fluency: scored.fluency ?? null,
      integrity: scored.integrity ?? null, is_rejected: Boolean(scored.is_rejected),
      words: Array.isArray(scored.words) ? scored.words.slice(0, 80) : [],
      recording_path: scored.recording_path,
      recording_file_id: boundedString(scored.recording_file_id, 1, 1024) ? scored.recording_file_id : scored.recording_path
    }
    const feedback = feedbackForTake(trusted)
    const stars = scoreToStars(trusted.total, trusted.is_rejected)
    await store.saveAudit({ action: `speaking_${session.data_kind}_take_scored`, caller_id: requestContext.callerId, course_id: request.course_id, question_id: request.question_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    const response = {
      ok: true, stars, child_feedback: feedback.child_feedback,
      weak_words: feedback.weak_words, word_lights: feedback.word_lights,
      proof: signTakeProof(trusted, hmacKey), can_retry: stars < 3 && request.attempt < 3,
      can_skip: stars < 3 && request.attempt >= 3
    }
    if (typeof store.saveSpeakingTake === 'function') {
      await store.saveSpeakingTake({ take_id: takeId, response, ...ownershipFields(session, requestContext), created_at: new Date(now()), data_kind: session.data_kind })
    }
    return { ...response, idempotent: false }
  }

  async function scoreSpeakingTake(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const request = event.request
    const { question, takeId } = resolveSpeakingTake(session, request)
    if (!boundedString(request.wav_base64, 1024, 900_000)) throw new ServiceError('INVALID_SPEAKING_TAKE')
    return scorePreparedSpeakingTake(session, request, requestContext, question, takeId, async () => request.wav_base64)
  }

  function validateChunkCommon(request) {
    if (!Number.isInteger(request.chunk_count) || request.chunk_count < 1 || request.chunk_count > MAX_SPEAKING_CHUNKS
      || !Number.isInteger(request.wav_byte_length) || request.wav_byte_length < 768 || request.wav_byte_length > MAX_SPEAKING_WAV_BYTES
      || !SHA256_PATTERN.test(request.wav_sha256 || '')) throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
  }

  async function uploadSpeakingChunk(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const request = event.request
    resolveSpeakingTake(session, request)
    validateChunkCommon(request)
    if (!speakingUploadStore || !Number.isInteger(request.chunk_index) || request.chunk_index < 0 || request.chunk_index >= request.chunk_count
      || !SHA256_PATTERN.test(request.chunk_sha256 || '')) throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
    const bytes = strictBase64(request.chunk_base64, 4, MAX_SPEAKING_CHUNK_BASE64)
    if (!bytes || sha256Hex(bytes) !== request.chunk_sha256) throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
    const path = speakingChunkPath(session, request, requestContext, request.chunk_index)
    let uploaded
    try { uploaded = await speakingUploadStore.upload(path, bytes) } catch { throw new ServiceError('SPEAKING_UPLOAD_FAILED') }
    if (!fileIdMatchesPath(uploaded?.fileID, path)) throw new ServiceError('SPEAKING_UPLOAD_FAILED')
    return { ok: true, chunk_index: request.chunk_index, file_id: uploaded.fileID }
  }

  async function scoreUploadedSpeakingTake(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const request = event.request
    const { question, takeId } = resolveSpeakingTake(session, request)
    validateChunkCommon(request)
    if (!speakingUploadStore || !Array.isArray(request.part_file_ids)
      || request.part_file_ids.length !== request.chunk_count) throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
    const expectedPaths = request.part_file_ids.map((_, index) => speakingChunkPath(session, request, requestContext, index))
    if (!request.part_file_ids.every((fileId, index) => fileIdMatchesPath(fileId, expectedPaths[index]))) {
      throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
    }
    const wavProvider = async () => {
      let parts
      try { parts = await Promise.all(request.part_file_ids.map((fileId) => speakingUploadStore.download(fileId))) } catch {
        throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
      }
      if (!parts.every(Buffer.isBuffer)) throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
      const wav = Buffer.concat(parts)
      if (wav.length !== request.wav_byte_length || wav.length > MAX_SPEAKING_WAV_BYTES || sha256Hex(wav) !== request.wav_sha256) {
        throw new ServiceError('SPEAKING_UPLOAD_INCOMPLETE')
      }
      return wav.toString('base64')
    }
    const response = await scorePreparedSpeakingTake(session, request, requestContext, question, takeId, wavProvider)
    try { await speakingUploadStore.remove(request.part_file_ids) } catch { /* best-effort temporary cleanup */ }
    return response
  }

  async function submitSpeakingResult(event, requestContext) {
    const session = await requireSession(event, requestContext)
    const requestedId = event.submission?.result_id
    if (!boundedString(requestedId, 1, 80)) throw new ServiceError('INVALID_SPEAKING_RESULT')
    let loaded
    try { loaded = speakingCourseProvider.get(event.submission?.course_id) } catch { throw new ServiceError('COURSE_NOT_FOUND') }
    assertCourseAllowedForSession(loaded.course, session)
    const existing = await store.getResult(requestedId)
    if (existing) {
      if (!belongsToSession(existing, session, requestContext) || existing.module_type !== 'speaking'
        || existing.data_kind !== session.data_kind || existing.course_id !== event.submission?.course_id) throw new ServiceError('RESULT_ID_CONFLICT')
      return { ok: true, result_id: existing.result_id, data_kind: session.data_kind, formal_completion_eligible: session.data_kind === 'formal', idempotent: true }
    }
    let submitted
    try { submitted = buildSpeakingResult(loaded.course, event.submission, loaded.version, hmacKey, session.data_kind) } catch { throw new ServiceError('INVALID_SPEAKING_RESULT') }
    submitted.created_at = new Date(now())
    Object.assign(submitted, ownershipFields(session, requestContext))
    await store.saveResult(submitted)
    await store.saveAudit({ action: `speaking_${session.data_kind}_result_created`, caller_id: requestContext.callerId, result_id: submitted.result_id, occurred_at: new Date(now()), log_tag: 'sherlock-english' })
    return { ok: true, result_id: submitted.result_id, data_kind: session.data_kind, formal_completion_eligible: session.data_kind === 'formal', idempotent: false }
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
      || (filters.course_id !== undefined && !PARENT_COURSE_ID.test(filters.course_id))
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
          ok: true, service: 'sherlock-api', stage: 'P5', formal_enabled: formalEnabled,
          writes: formalEnabled ? 'formal-and-test' : 'test-only',
          formal_entry_mode: formalEntryMode,
          speaking_direct_upload_test_enabled: speakingDirectUploadEnabled,
          speaking_course_versions: Object.fromEntries(speakingCourseProvider.catalog().map((item) => [item.course_id, item.course_version]))
        }
      }
      if (event.action === 'startChildSession') return startChildSession(event, requestContext)
      if (event.action === 'getFormalProgress') return getFormalProgress(event, requestContext)
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
      if (event.action === 'createDirectUploadProbe') return createDirectUploadProbe(event, requestContext)
      if (event.action === 'verifyDirectUploadProbe') return verifyDirectUploadProbe(event, requestContext)
      if (event.action === 'cancelDirectUploadProbe') return cancelDirectUploadProbe(event, requestContext)
      if (event.action === 'createSpeakingDirectUpload') return createSpeakingDirectUpload(event, requestContext)
      if (event.action === 'scoreDirectUploadedSpeakingTake') return scoreDirectUploadedSpeakingTake(event, requestContext)
      if (event.action === 'cancelSpeakingDirectUpload') return cancelSpeakingDirectUpload(event, requestContext)
      if (event.action === 'uploadSpeakingChunk') return uploadSpeakingChunk(event, requestContext)
      if (event.action === 'scoreUploadedSpeakingTake') return scoreUploadedSpeakingTake(event, requestContext)
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
