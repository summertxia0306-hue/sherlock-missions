export interface DirectSpeakingRequest {
  result_id: string
  course_id: string
  course_version: string
  question_id: number
  attempt: number
  wav_base64: string
}

export interface DirectSpeakingResponse {
  ok: true
  stars: 0 | 1 | 2 | 3
  proof: string
  child_feedback: string
  weak_words: string[]
  word_lights: Array<{ word: string; light: 'good' | 'weak' | 'miss' }>
  can_retry: boolean
  can_skip: boolean
  idempotent?: boolean
  transport_diagnostics?: SpeakingTransportDiagnostics
}

interface DirectRequestWithoutAudio {
  result_id: string
  course_id: string
  course_version: string
  question_id: number
  attempt: number
  byte_length: number
  sha256: string
  content_type: 'audio/wav'
}

interface DirectScoreResponse extends DirectSpeakingResponse {
  transport: 'direct'
  cleaned_up: boolean
  server_timing: { validation_ms: number; scoring_ms: number; cleanup_ms: number }
}

export interface SpeakingTransportDiagnostics {
  mode: 'direct' | 'chunk-fallback'
  hash_ms: number
  ticket_ms: number
  upload_ms: number
  validation_ms: number
  scoring_ms: number
  cleanup_ms: number
  total_ms: number
  cleaned_up: boolean
  direct_error_code?: string
}

export interface DirectSpeakingTransportDependencies {
  fetcher: typeof fetch
  issue(sessionToken: string, request: DirectRequestWithoutAudio): Promise<{ upload_url: string; ticket: string }>
  scoreDirect(sessionToken: string, ticket: string, request: DirectRequestWithoutAudio): Promise<DirectScoreResponse>
  cancelDirect(sessionToken: string, ticket: string): Promise<unknown>
  fallback(sessionToken: string, request: DirectSpeakingRequest): Promise<DirectSpeakingResponse>
  now?: () => number
}

const SAFE_ISSUE_FALLBACK = new Set(['SPEAKING_DIRECT_UPLOAD_DISABLED', 'SPEAKING_DIRECT_SIGNING_UNAVAILABLE'])
const SAFE_SCORE_FALLBACK = new Set([
  'SPEAKING_DIRECT_UPLOAD_DISABLED',
  'SPEAKING_DIRECT_OBJECT_MISSING',
  'SPEAKING_DIRECT_INTEGRITY_FAILED',
  'SPEAKING_DIRECT_TICKET_EXPIRED'
])

function errorCode(error: unknown): string {
  return error instanceof Error && /^[A-Z][A-Z0-9_]{1,79}$/.test(error.message) ? error.message : ''
}

function isAmbiguousNetworkError(error: unknown): boolean {
  return error instanceof TypeError || ['NETWORK_ERROR', 'CLOUDBASE_NETWORK_ERROR', 'NETWORK_TIMEOUT'].includes(errorCode(error))
}

function base64Bytes(value: string): Uint8Array {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index)
  return bytes
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes as BufferSource)
  return Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, '0')).join('')
}

export async function scoreSpeakingDirectFirst(
  sessionToken: string,
  request: DirectSpeakingRequest,
  dependencies: DirectSpeakingTransportDependencies
): Promise<DirectSpeakingResponse> {
  const now = dependencies.now || (() => globalThis.performance.now())
  const started = now()
  const wav = base64Bytes(request.wav_base64)
  const hashStarted = now()
  const hash = await sha256Hex(wav)
  const hashFinished = now()
  const directRequest: DirectRequestWithoutAudio = {
    result_id: request.result_id,
    course_id: request.course_id,
    course_version: request.course_version,
    question_id: request.question_id,
    attempt: request.attempt,
    byte_length: wav.byteLength,
    sha256: hash,
    content_type: 'audio/wav'
  }
  let ticket = ''
  let ticketMs = 0
  let uploadMs = 0

  async function fallback(code: string): Promise<DirectSpeakingResponse> {
    const response = await dependencies.fallback(sessionToken, request)
    return {
      ...response,
      transport_diagnostics: {
        mode: 'chunk-fallback',
        hash_ms: Math.round(Math.max(0, hashFinished - hashStarted)),
        ticket_ms: Math.round(ticketMs),
        upload_ms: Math.round(uploadMs),
        validation_ms: 0,
        scoring_ms: 0,
        cleanup_ms: 0,
        total_ms: Math.round(Math.max(0, now() - started)),
        cleaned_up: true,
        direct_error_code: code
      }
    }
  }

  let issued
  const ticketStarted = now()
  try {
    issued = await dependencies.issue(sessionToken, directRequest)
    ticket = issued.ticket
  } catch (error) {
    ticketMs = Math.max(0, now() - ticketStarted)
    const code = errorCode(error)
    if (SAFE_ISSUE_FALLBACK.has(code) || isAmbiguousNetworkError(error)) return fallback(code || 'DIRECT_ISSUE_NETWORK_ERROR')
    throw error
  }
  ticketMs = Math.max(0, now() - ticketStarted)

  const uploadStarted = now()
  try {
    const response = await dependencies.fetcher(issued.upload_url, {
      method: 'PUT',
      credentials: 'omit',
      headers: { 'Content-Type': 'audio/wav' },
      body: wav as BodyInit
    })
    uploadMs = Math.max(0, now() - uploadStarted)
  } catch {
    uploadMs = Math.max(0, now() - uploadStarted)
  }

  let direct
  try {
    direct = await dependencies.scoreDirect(sessionToken, ticket, directRequest)
  } catch (firstError) {
    if (isAmbiguousNetworkError(firstError)) {
      try {
        direct = await dependencies.scoreDirect(sessionToken, ticket, directRequest)
      } catch (secondError) {
        if (isAmbiguousNetworkError(secondError)) throw new Error('SPEAKING_DIRECT_STATUS_UNKNOWN')
        const code = errorCode(secondError)
        if (!SAFE_SCORE_FALLBACK.has(code)) throw secondError
        try { await dependencies.cancelDirect(sessionToken, ticket) } catch { /* best-effort cleanup */ }
        return fallback(code)
      }
    } else {
      const code = errorCode(firstError)
      if (!SAFE_SCORE_FALLBACK.has(code)) throw firstError
      try { await dependencies.cancelDirect(sessionToken, ticket) } catch { /* best-effort cleanup */ }
      return fallback(code)
    }
  }

  return {
    ...direct,
    transport_diagnostics: {
      mode: 'direct',
      hash_ms: Math.round(Math.max(0, hashFinished - hashStarted)),
      ticket_ms: Math.round(ticketMs),
      upload_ms: Math.round(uploadMs),
      validation_ms: Math.round(Math.max(0, direct.server_timing.validation_ms)),
      scoring_ms: Math.round(Math.max(0, direct.server_timing.scoring_ms)),
      cleanup_ms: Math.round(Math.max(0, direct.server_timing.cleanup_ms)),
      total_ms: Math.round(Math.max(0, now() - started)),
      cleaned_up: direct.cleaned_up
    }
  }
}
