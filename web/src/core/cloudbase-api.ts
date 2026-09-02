import type { ResultSubmission } from './result-schema'
import type { ListeningPick, ListeningSubmission } from '../listening/session'
import { scoreSpeakingDirectFirst, type SpeakingTransportDiagnostics } from './speaking-direct-upload'

interface ApiErrorResult {
  ok: false
  error: { code: string; message: string }
}

export interface ParentAuthResult {
  ok: true
  session_token: string
  expires_at: string
  data_kind: 'test'
}

export interface ChildSessionResult {
  ok: true
  session_token: string
  expires_at: string
  data_kind: 'formal'
}

export interface FormalProgressResult {
  ok: true
  completed_course_ids: { listening: string[]; speaking: string[] }
}

interface SubmitResultResponse {
  ok: true
  result_id: string
  data_kind: 'formal' | 'test'
  formal_completion_eligible: boolean
}

export interface HealthResult {
  ok: true
  service: 'sherlock-api'
  stage: 'P5'
  formal_enabled: boolean
  writes: 'test-only' | 'formal-and-test'
  formal_entry_mode?: 'dual' | 'github-http-only' | 'cloudbase-event-only'
  speaking_direct_upload_test_enabled?: boolean
}

export interface DirectUploadProbeRequest {
  byte_length: number
  sha256: string
  content_type: 'audio/wav'
}

export interface DirectUploadProbeIssueResult {
  ok: true
  data_kind: 'test'
  upload_url: string
  object_key: string
  file_id: string
  byte_length: number
  expires_at: string
  ticket: string
}

export interface DirectUploadProbeVerifyResult {
  ok: true
  data_kind: 'test'
  byte_length: number
  sha256: string
  cleaned_up: boolean
}

export interface DirectUploadProbeCancelResult {
  ok: true
  data_kind: 'test'
  cleaned_up: boolean
}

export interface SherlockApi {
  health(): Promise<HealthResult>
  startChildSession(): Promise<ChildSessionResult>
  getFormalProgress(sessionToken: string): Promise<FormalProgressResult>
  authenticate(password: string): Promise<ParentAuthResult>
  createDirectUploadProbe(sessionToken: string, request: DirectUploadProbeRequest): Promise<DirectUploadProbeIssueResult>
  verifyDirectUploadProbe(sessionToken: string, ticket: string): Promise<DirectUploadProbeVerifyResult>
  cancelDirectUploadProbe(sessionToken: string, ticket: string): Promise<DirectUploadProbeCancelResult>
  submitResult(sessionToken: string, result: ResultSubmission): Promise<SubmitResultResponse>
  submitListeningResult(sessionToken: string, submission: ListeningSubmission): Promise<ListeningSubmitResponse>
  checkListeningCorrection(sessionToken: string, resultId: string, questionId: number, attempt: 1 | 2, pick: ListeningPick): Promise<ListeningCorrectionResponse>
  listListeningTestResults(sessionToken: string): Promise<ListeningResultsResponse>
  scoreSpeakingTake(sessionToken: string, request: SpeakingScoreRequest, dataKind: 'formal' | 'test'): Promise<SpeakingScoreResponse>
  submitSpeakingResult(sessionToken: string, submission: SpeakingSubmission): Promise<SpeakingSubmitResponse>
  listSpeakingTestResults(sessionToken: string): Promise<SpeakingResultsResponse>
  getSpeakingRecordingUrl(sessionToken: string, resultId: string, questionId: number, attempt: number): Promise<{ ok: true; url: string; expires_in: number }>
  listParentResults(sessionToken: string, filters: ParentResultFilters): Promise<ParentResultsResponse>
  getParentRecordingUrl(sessionToken: string, resultId: string, questionId: number, attempt: number): Promise<{ ok: true; url: string; expires_in: number }>
}

export class SherlockApiError extends Error {
  readonly code: string

  constructor(code: string) {
    super(code)
    this.name = 'SherlockApiError'
    this.code = code
  }
}

export function apiErrorCode(error: unknown): string {
  if (error instanceof SherlockApiError) return error.code
  if (error instanceof Error && /^[A-Z][A-Z0-9_]{1,79}$/.test(error.message)) return error.message
  return ''
}

export function isNetworkFailure(error: unknown): boolean {
  if (typeof navigator !== 'undefined' && navigator.onLine === false) return true
  if (error instanceof TypeError) return true
  return ['NETWORK_ERROR', 'CLOUDBASE_NETWORK_ERROR', 'NETWORK_TIMEOUT'].includes(apiErrorCode(error))
}

export interface SpeakingScoreRequest {
  result_id: string
  course_id: string
  course_version: string
  question_id: number
  attempt: number
  wav_base64: string
}

export interface SpeakingScoreResponse {
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

export interface SpeakingSubmission {
  result_id: string
  student_id: string
  course_id: string
  course_version: string
  started_at: string
  submitted_at: string
  duration_seconds: number
  questions: Array<{ id: number; proofs: string[]; passed_by_safety: boolean }>
}

export interface SpeakingSubmitResponse {
  ok: true
  result_id: string
  data_kind: 'formal' | 'test'
  formal_completion_eligible: boolean
  idempotent: boolean
}

export interface SpeakingResultDetail {
  result_id: string
  course_id: string
  score: number
  stars_total: number
  stars_max: number
  duration_seconds: number
  question_results: Array<{
    id: number; text: string; stars: number; take_stars: number[]; first_total: number | null
    last_total: number | null; best_total: number | null; weak_words: string[]; passed_by_safety: boolean
  }>
}

export interface ParentResultFilters {
  data_kind?: 'formal' | 'test'
  module_type?: 'listening' | 'speaking'
  course_id?: string
  date_from?: string
  date_to?: string
}

export interface ParentResultDetail {
  result_id: string
  course_id: string
  module_type: 'listening' | 'speaking'
  data_kind: 'formal' | 'test'
  status?: string
  score: number
  duration_seconds: number
  submitted_at: string
  section_scores?: Record<string, number>
  wrong_answers?: Array<Record<string, unknown>>
  corrections?: Record<string, unknown>
  stars_total?: number
  stars_max?: number
  question_results: Array<Record<string, unknown> & {
    id: number
    text?: string
    stars?: number
    take_stars?: number[]
    first_total?: number | null
    last_total?: number | null
    best_total?: number | null
    weak_words?: string[]
    passed_by_safety?: boolean
    recording_records?: Array<{ file_id?: string; data_kind?: 'formal' | 'test' }>
  }>
}

export interface ParentResultsResponse {
  ok: true
  data_kind: 'formal' | 'test'
  summary: { result_count: number; completed_course_count: number; formal_completion_count: number }
  results: ParentResultDetail[]
}

export interface SpeakingResultsResponse { ok: true; data_kind: 'test'; results: SpeakingResultDetail[] }

export interface ListeningSubmitResponse {
  ok: true
  result_id: string
  data_kind: 'formal' | 'test'
  formal_completion_eligible: boolean
  wrong_question_ids: number[]
  idempotent: boolean
}

export interface ListeningCorrectionResponse {
  ok: true
  correct: boolean
  marker?: '✓' | '✓²' | '✗'
  reveal_transcript?: string[]
  next_attempt?: 2
  done: boolean
}

export interface ListeningResultDetail {
  result_id: string
  course_id: string
  data_kind: 'test'
  score: number
  duration_seconds: number
  section_scores: Record<string, number>
  wrong_answers: Array<Record<string, unknown>>
  corrections: Record<string, unknown>
  question_results: Array<Record<string, unknown>>
  submitted_at: string
}

export interface ListeningResultsResponse {
  ok: true
  data_kind: 'test'
  results: ListeningResultDetail[]
}

interface CloudbaseAppLike {
  auth(options: { persistence: 'local' }): {
    hasLoginState(): unknown
    signInAnonymously(): Promise<{ error?: unknown }>
  } | undefined
  callFunction?(options: { name: string; data: Record<string, unknown> }): Promise<{ result: unknown }>
}

interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

interface HttpGatewayDependencies {
  fetcher?: typeof fetch
  storage?: StorageLike
  createClientId?: () => string
  directSpeakingUploadEnabled?: boolean
}

const HTTP_CLIENT_STORAGE_KEY = 'sherlock-http-client-id-v1'
const SPEAKING_CHUNK_BASE64_LENGTH = 65_536
const SPEAKING_UPLOAD_CONCURRENCY = 2
const SPEAKING_UPLOAD_RETRIES = 2

function defaultClientId(): string {
  if (typeof globalThis.crypto?.randomUUID === 'function') return globalThis.crypto.randomUUID()
  const bytes = new Uint8Array(16)
  globalThis.crypto.getRandomValues(bytes)
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('')
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

async function mapWithConcurrency<T, R>(items: T[], concurrency: number, worker: (item: T, index: number) => Promise<R>): Promise<R[]> {
  const results = new Array<R>(items.length)
  let nextIndex = 0
  async function run(): Promise<void> {
    while (nextIndex < items.length) {
      const index = nextIndex
      nextIndex += 1
      results[index] = await worker(items[index], index)
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, () => run()))
  return results
}

export function createHttpGatewayApp(endpoint: string, dependencies: HttpGatewayDependencies = {}): CloudbaseAppLike {
  const fetcher = dependencies.fetcher || globalThis.fetch.bind(globalThis)
  const storage = dependencies.storage || globalThis.localStorage
  const createClientId = dependencies.createClientId || defaultClientId
  const directSpeakingUploadEnabled = dependencies.directSpeakingUploadEnabled === true
  let clientId = storage.getItem(HTTP_CLIENT_STORAGE_KEY) || ''
  if (!/^[A-Za-z0-9_-]{16,128}$/.test(clientId)) {
    clientId = createClientId()
    if (!/^[A-Za-z0-9_-]{16,128}$/.test(clientId)) throw new Error('HTTP_CLIENT_ID_INVALID')
    storage.setItem(HTTP_CLIENT_STORAGE_KEY, clientId)
  }

  async function post(data: Record<string, unknown>): Promise<{ response: Response; result: any }> {
    const response = await fetcher(endpoint, {
      method: 'POST',
      credentials: 'omit',
      headers: {
        'Content-Type': 'application/json',
        'X-Sherlock-Client-Id': clientId
      },
      body: JSON.stringify(data)
    })
    const result = await response.json()
    return { response, result }
  }

  async function uploadChunk(data: Record<string, unknown>): Promise<string> {
    for (let retry = 0; retry <= SPEAKING_UPLOAD_RETRIES; retry += 1) {
      try {
        const { response, result } = await post(data)
        if (response.ok && result?.ok === true && typeof result.file_id === 'string') return result.file_id
        if (result?.ok === false && response.status < 500) throw new SherlockApiError(result.error?.code || 'SPEAKING_UPLOAD_FAILED')
        if (retry === SPEAKING_UPLOAD_RETRIES) throw new SherlockApiError('SPEAKING_UPLOAD_FAILED')
      } catch (error) {
        if (error instanceof SherlockApiError && error.code !== 'SPEAKING_UPLOAD_FAILED') throw error
        if (retry === SPEAKING_UPLOAD_RETRIES) throw new SherlockApiError('SPEAKING_UPLOAD_FAILED')
      }
    }
    throw new SherlockApiError('SPEAKING_UPLOAD_FAILED')
  }

  async function scoreSpeakingInChunks(data: Record<string, unknown>): Promise<{ result: unknown }> {
    const request = data.request
    if (!request || typeof request !== 'object' || Array.isArray(request)) throw new SherlockApiError('INVALID_SPEAKING_TAKE')
    const wavBase64 = (request as Record<string, unknown>).wav_base64
    if (typeof wavBase64 !== 'string') throw new SherlockApiError('INVALID_SPEAKING_TAKE')
    const chunks = Array.from(
      { length: Math.ceil(wavBase64.length / SPEAKING_CHUNK_BASE64_LENGTH) },
      (_, index) => wavBase64.slice(index * SPEAKING_CHUNK_BASE64_LENGTH, (index + 1) * SPEAKING_CHUNK_BASE64_LENGTH)
    )
    const wavBytes = base64Bytes(wavBase64)
    const common = {
      ...(request as Record<string, unknown>),
      wav_base64: undefined,
      chunk_count: chunks.length,
      wav_byte_length: wavBytes.byteLength,
      wav_sha256: await sha256Hex(wavBytes)
    }
    delete common.wav_base64
    const partFileIds = await mapWithConcurrency(chunks, SPEAKING_UPLOAD_CONCURRENCY, async (chunkBase64, chunkIndex) => {
      const chunkBytes = base64Bytes(chunkBase64)
      return uploadChunk({
        action: 'uploadSpeakingChunk',
        session_token: data.session_token,
        request: {
          ...common,
          chunk_index: chunkIndex,
          chunk_base64: chunkBase64,
          chunk_sha256: await sha256Hex(chunkBytes)
        }
      })
    })
    const { result } = await post({
      action: 'scoreUploadedSpeakingTake',
      session_token: data.session_token,
      request: { ...common, part_file_ids: partFileIds }
    })
    return { result }
  }

  async function actionResult<T>(data: Record<string, unknown>): Promise<T> {
    const { response, result } = await post(data)
    if (typeof result === 'object' && result !== null && result.ok === false) {
      throw new SherlockApiError(result.error?.code || 'SERVICE_ERROR')
    }
    if (!response.ok) throw new Error('HTTP_GATEWAY_ERROR')
    return result as T
  }

  return {
    auth: () => ({ hasLoginState: () => true, signInAnonymously: async () => ({}) }),
    callFunction: async ({ data }) => {
      if (data.action === 'scoreSpeakingTake') {
        if (!directSpeakingUploadEnabled || data.data_kind !== 'test') return scoreSpeakingInChunks(data)
        const request = data.request as SpeakingScoreRequest
        const result = await scoreSpeakingDirectFirst(String(data.session_token || ''), request, {
          fetcher,
          issue: (sessionToken, directRequest) => actionResult({
            action: 'createSpeakingDirectUpload', session_token: sessionToken, request: directRequest
          }),
          scoreDirect: (sessionToken, ticket, directRequest) => actionResult({
            action: 'scoreDirectUploadedSpeakingTake', session_token: sessionToken, ticket, request: directRequest
          }),
          cancelDirect: (sessionToken, ticket) => actionResult({
            action: 'cancelSpeakingDirectUpload', session_token: sessionToken, ticket
          }),
          fallback: async (sessionToken, fallbackRequest) => {
            const response = await scoreSpeakingInChunks({
              action: 'scoreSpeakingTake', session_token: sessionToken, request: fallbackRequest
            })
            const fallbackResult = response.result as SpeakingScoreResponse | ApiErrorResult
            if (typeof fallbackResult === 'object' && fallbackResult !== null && fallbackResult.ok === false) {
              throw new SherlockApiError(fallbackResult.error.code)
            }
            return fallbackResult as SpeakingScoreResponse
          }
        })
        return { result }
      }
      const { response, result } = await post(data)
      if (!response.ok && !(typeof result === 'object' && result !== null && 'ok' in result)) {
        throw new Error('HTTP_GATEWAY_ERROR')
      }
      return { result }
    }
  }
}

async function configuredApp(): Promise<CloudbaseAppLike> {
  const httpEndpoint = import.meta.env.VITE_SHERLOCK_API_URL?.trim()
  if (httpEndpoint) return createHttpGatewayApp(httpEndpoint, {
    directSpeakingUploadEnabled: import.meta.env.VITE_SPEAKING_DIRECT_UPLOAD_TEST === 'true'
  })
  const env = import.meta.env.VITE_CLOUDBASE_ENV_ID?.trim()
  if (!env) {
    throw new Error('CLOUDBASE_NOT_CONFIGURED')
  }
  const accessKey = import.meta.env.VITE_CLOUDBASE_ACCESS_KEY?.trim()
  const { default: cloudbase } = await import('@cloudbase/js-sdk')
  return cloudbase.init({ env, ...(accessKey ? { accessKey } : {}) })
}

export function createCloudbaseApi(
  app: CloudbaseAppLike | undefined,
  functionName = 'sherlock-api'
): SherlockApi {
  let anonymousReady: Promise<void> | undefined

  async function ensureAnonymousLogin(): Promise<void> {
    if (!app) {
      throw new Error('CLOUDBASE_NOT_CONFIGURED')
    }
    const auth = app.auth({ persistence: 'local' })
    if (!auth) {
      throw new Error('CLOUDBASE_AUTH_UNAVAILABLE')
    }
    if (auth.hasLoginState()) {
      return
    }
    anonymousReady ??= auth.signInAnonymously().then((response) => {
      if (response.error) {
        throw new Error('CLOUDBASE_ANONYMOUS_LOGIN_FAILED')
      }
    }).catch((error: unknown) => {
      anonymousReady = undefined
      throw error
    })
    return anonymousReady
  }

  async function call<T>(data: Record<string, unknown>): Promise<T> {
    await ensureAnonymousLogin()
    if (!app?.callFunction) {
      throw new Error('CLOUDBASE_FUNCTIONS_UNAVAILABLE')
    }
    const response = await app.callFunction({ name: functionName, data })
    const result = response.result as T | ApiErrorResult
    if (typeof result === 'object' && result !== null && 'ok' in result && result.ok === false) {
      throw new SherlockApiError(result.error.code)
    }
    return result as T
  }

  return {
    health: () => call<HealthResult>({ action: 'health' }),
    startChildSession: () => call<ChildSessionResult>({ action: 'startChildSession' }),
    getFormalProgress: (sessionToken) => call<FormalProgressResult>({ action: 'getFormalProgress', session_token: sessionToken }),
    authenticate: (password) => call<ParentAuthResult>({ action: 'parentAuth', password }),
    createDirectUploadProbe: (sessionToken, request) => call<DirectUploadProbeIssueResult>({
      action: 'createDirectUploadProbe', session_token: sessionToken, request
    }),
    verifyDirectUploadProbe: (sessionToken, ticket) => call<DirectUploadProbeVerifyResult>({
      action: 'verifyDirectUploadProbe', session_token: sessionToken, ticket
    }),
    cancelDirectUploadProbe: (sessionToken, ticket) => call<DirectUploadProbeCancelResult>({
      action: 'cancelDirectUploadProbe', session_token: sessionToken, ticket
    }),
    submitResult: (sessionToken, result) => call<SubmitResultResponse>({
      action: 'submitResult',
      session_token: sessionToken,
      result
    }),
    submitListeningResult: (sessionToken, submission) => call<ListeningSubmitResponse>({
      action: 'submitListeningResult', session_token: sessionToken, submission
    }),
    checkListeningCorrection: (sessionToken, resultId, questionId, attempt, pick) => call<ListeningCorrectionResponse>({
      action: 'checkListeningCorrection', session_token: sessionToken,
      result_id: resultId, question_id: questionId, attempt, pick
    }),
    listListeningTestResults: (sessionToken) => call<ListeningResultsResponse>({
      action: 'listListeningTestResults', session_token: sessionToken
    }),
    scoreSpeakingTake: (sessionToken, request, dataKind) => call<SpeakingScoreResponse>({
      action: 'scoreSpeakingTake', session_token: sessionToken, request, data_kind: dataKind
    }),
    submitSpeakingResult: (sessionToken, submission) => call<SpeakingSubmitResponse>({ action: 'submitSpeakingResult', session_token: sessionToken, submission }),
    listSpeakingTestResults: (sessionToken) => call<SpeakingResultsResponse>({ action: 'listSpeakingTestResults', session_token: sessionToken }),
    getSpeakingRecordingUrl: (sessionToken, resultId, questionId, attempt) => call({
      action: 'getSpeakingRecordingUrl', session_token: sessionToken, result_id: resultId, question_id: questionId, attempt
    }),
    listParentResults: (sessionToken, filters) => call<ParentResultsResponse>({ action: 'listParentResults', session_token: sessionToken, filters }),
    getParentRecordingUrl: (sessionToken, resultId, questionId, attempt) => call({
      action: 'getParentRecordingUrl', session_token: sessionToken, result_id: resultId, question_id: questionId, attempt
    })
  }
}

let defaultApiPromise: Promise<SherlockApi> | undefined

async function getDefaultApi(): Promise<SherlockApi> {
  defaultApiPromise ??= configuredApp().then((app) => createCloudbaseApi(
    app,
    import.meta.env.VITE_CLOUDBASE_FUNCTION_NAME || 'sherlock-api'
  )).catch((error: unknown) => {
    defaultApiPromise = undefined
    throw error
  })
  return defaultApiPromise
}

export const cloudbaseApi: SherlockApi = {
  health: async () => (await getDefaultApi()).health(),
  startChildSession: async () => (await getDefaultApi()).startChildSession(),
  getFormalProgress: async (sessionToken) => (await getDefaultApi()).getFormalProgress(sessionToken),
  authenticate: async (password) => (await getDefaultApi()).authenticate(password),
  createDirectUploadProbe: async (sessionToken, request) => (await getDefaultApi()).createDirectUploadProbe(sessionToken, request),
  verifyDirectUploadProbe: async (sessionToken, ticket) => (await getDefaultApi()).verifyDirectUploadProbe(sessionToken, ticket),
  cancelDirectUploadProbe: async (sessionToken, ticket) => (await getDefaultApi()).cancelDirectUploadProbe(sessionToken, ticket),
  submitResult: async (sessionToken, result) => (await getDefaultApi()).submitResult(sessionToken, result),
  submitListeningResult: async (sessionToken, submission) => (await getDefaultApi()).submitListeningResult(sessionToken, submission),
  checkListeningCorrection: async (sessionToken, resultId, questionId, attempt, pick) => (
    await getDefaultApi()).checkListeningCorrection(sessionToken, resultId, questionId, attempt, pick),
  listListeningTestResults: async (sessionToken) => (await getDefaultApi()).listListeningTestResults(sessionToken),
  scoreSpeakingTake: async (sessionToken, request, dataKind) => (
    await getDefaultApi()).scoreSpeakingTake(sessionToken, request, dataKind),
  submitSpeakingResult: async (sessionToken, submission) => (await getDefaultApi()).submitSpeakingResult(sessionToken, submission),
  listSpeakingTestResults: async (sessionToken) => (await getDefaultApi()).listSpeakingTestResults(sessionToken),
  getSpeakingRecordingUrl: async (sessionToken, resultId, questionId, attempt) => (await getDefaultApi()).getSpeakingRecordingUrl(sessionToken, resultId, questionId, attempt),
  listParentResults: async (sessionToken, filters) => (await getDefaultApi()).listParentResults(sessionToken, filters),
  getParentRecordingUrl: async (sessionToken, resultId, questionId, attempt) => (await getDefaultApi()).getParentRecordingUrl(sessionToken, resultId, questionId, attempt)
}
