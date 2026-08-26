import type { ResultSubmission } from './result-schema'
import type { ListeningPick, ListeningSubmission } from '../listening/session'

interface ApiErrorResult {
  ok: false
  error: { code: string; message: string }
}

interface ParentAuthResult {
  ok: true
  session_token: string
  expires_at: string
  data_kind: 'test'
}

interface ChildSessionResult {
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
}

export interface SherlockApi {
  health(): Promise<HealthResult>
  startChildSession(): Promise<ChildSessionResult>
  getFormalProgress(sessionToken: string): Promise<FormalProgressResult>
  authenticate(password: string): Promise<ParentAuthResult>
  submitResult(sessionToken: string, result: ResultSubmission): Promise<SubmitResultResponse>
  submitListeningResult(sessionToken: string, submission: ListeningSubmission): Promise<ListeningSubmitResponse>
  checkListeningCorrection(sessionToken: string, resultId: string, questionId: number, attempt: 1 | 2, pick: ListeningPick): Promise<ListeningCorrectionResponse>
  listListeningTestResults(sessionToken: string): Promise<ListeningResultsResponse>
  scoreSpeakingTake(sessionToken: string, request: SpeakingScoreRequest): Promise<SpeakingScoreResponse>
  submitSpeakingResult(sessionToken: string, submission: SpeakingSubmission): Promise<SpeakingSubmitResponse>
  listSpeakingTestResults(sessionToken: string): Promise<SpeakingResultsResponse>
  getSpeakingRecordingUrl(sessionToken: string, resultId: string, questionId: number, attempt: number): Promise<{ ok: true; url: string; expires_in: number }>
  listParentResults(sessionToken: string, filters: ParentResultFilters): Promise<ParentResultsResponse>
  getParentRecordingUrl(sessionToken: string, resultId: string, questionId: number, attempt: number): Promise<{ ok: true; url: string; expires_in: number }>
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

async function configuredApp(): Promise<CloudbaseAppLike> {
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
      throw new Error(result.error.code)
    }
    return result as T
  }

  return {
    health: () => call<HealthResult>({ action: 'health' }),
    startChildSession: () => call<ChildSessionResult>({ action: 'startChildSession' }),
    getFormalProgress: (sessionToken) => call<FormalProgressResult>({ action: 'getFormalProgress', session_token: sessionToken }),
    authenticate: (password) => call<ParentAuthResult>({ action: 'parentAuth', password }),
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
    scoreSpeakingTake: (sessionToken, request) => call<SpeakingScoreResponse>({ action: 'scoreSpeakingTake', session_token: sessionToken, request }),
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
  submitResult: async (sessionToken, result) => (await getDefaultApi()).submitResult(sessionToken, result),
  submitListeningResult: async (sessionToken, submission) => (await getDefaultApi()).submitListeningResult(sessionToken, submission),
  checkListeningCorrection: async (sessionToken, resultId, questionId, attempt, pick) => (
    await getDefaultApi()).checkListeningCorrection(sessionToken, resultId, questionId, attempt, pick),
  listListeningTestResults: async (sessionToken) => (await getDefaultApi()).listListeningTestResults(sessionToken),
  scoreSpeakingTake: async (sessionToken, request) => (await getDefaultApi()).scoreSpeakingTake(sessionToken, request),
  submitSpeakingResult: async (sessionToken, submission) => (await getDefaultApi()).submitSpeakingResult(sessionToken, submission),
  listSpeakingTestResults: async (sessionToken) => (await getDefaultApi()).listSpeakingTestResults(sessionToken),
  getSpeakingRecordingUrl: async (sessionToken, resultId, questionId, attempt) => (await getDefaultApi()).getSpeakingRecordingUrl(sessionToken, resultId, questionId, attempt),
  listParentResults: async (sessionToken, filters) => (await getDefaultApi()).listParentResults(sessionToken, filters),
  getParentRecordingUrl: async (sessionToken, resultId, questionId, attempt) => (await getDefaultApi()).getParentRecordingUrl(sessionToken, resultId, questionId, attempt)
}
