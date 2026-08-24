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

interface SubmitResultResponse {
  ok: true
  result_id: string
  data_kind: 'test'
  formal_completion_eligible: false
}

export interface HealthResult {
  ok: true
  service: 'sherlock-api'
  stage: 'P2'
  formal_enabled: false
  writes: 'test-only'
}

export interface SherlockApi {
  health(): Promise<HealthResult>
  authenticate(password: string): Promise<ParentAuthResult>
  submitResult(sessionToken: string, result: ResultSubmission): Promise<SubmitResultResponse>
  submitListeningResult(sessionToken: string, submission: ListeningSubmission): Promise<ListeningSubmitResponse>
  checkListeningCorrection(sessionToken: string, resultId: string, questionId: number, attempt: 1 | 2, pick: ListeningPick): Promise<ListeningCorrectionResponse>
  listListeningTestResults(sessionToken: string): Promise<ListeningResultsResponse>
}

export interface ListeningSubmitResponse {
  ok: true
  result_id: string
  data_kind: 'test'
  formal_completion_eligible: false
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
  authenticate: async (password) => (await getDefaultApi()).authenticate(password),
  submitResult: async (sessionToken, result) => (await getDefaultApi()).submitResult(sessionToken, result),
  submitListeningResult: async (sessionToken, submission) => (await getDefaultApi()).submitListeningResult(sessionToken, submission),
  checkListeningCorrection: async (sessionToken, resultId, questionId, attempt, pick) => (
    await getDefaultApi()).checkListeningCorrection(sessionToken, resultId, questionId, attempt, pick),
  listListeningTestResults: async (sessionToken) => (await getDefaultApi()).listListeningTestResults(sessionToken)
}
