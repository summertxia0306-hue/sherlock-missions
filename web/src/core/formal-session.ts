import { apiErrorCode, type ChildSessionResult, type SherlockApi } from './cloudbase-api'

export interface FormalRequestOptions {
  onRecovering?: () => void
}

export type SessionRequestRunner = <T>(
  request: (sessionToken: string) => Promise<T>,
  options?: FormalRequestOptions
) => Promise<T>

export interface FormalSessionManager {
  ensureFresh(options?: FormalRequestOptions): Promise<string>
  run<T>(request: (sessionToken: string) => Promise<T>, options?: FormalRequestOptions): Promise<T>
  current(): ChildSessionResult | undefined
}

export class FormalSessionRecoveryError extends Error {
  constructor(cause?: unknown) {
    super('FORMAL_SESSION_RECOVERY_FAILED', { cause })
    this.name = 'FormalSessionRecoveryError'
  }
}

export function createFormalSessionManager(
  api: Pick<SherlockApi, 'startChildSession'>,
  options: { now?: () => number; renewBeforeMs?: number; onSession?: (session: ChildSessionResult) => void } = {}
): FormalSessionManager {
  const now = options.now || Date.now
  const renewBeforeMs = options.renewBeforeMs ?? 5 * 60 * 1000
  let session: ChildSessionResult | undefined
  let renewal: Promise<ChildSessionResult> | undefined

  function isFresh(value: ChildSessionResult | undefined): value is ChildSessionResult {
    const expiresAt = Date.parse(value?.expires_at || '')
    return Boolean(value?.session_token) && Number.isFinite(expiresAt) && expiresAt - now() > renewBeforeMs
  }

  async function renew(recoveryOptions?: FormalRequestOptions, recovery = true): Promise<string> {
    if (recovery) recoveryOptions?.onRecovering?.()
    renewal ??= api.startChildSession().then((next) => {
      session = next
      options.onSession?.(next)
      return next
    }).catch((error: unknown) => {
      throw recovery ? new FormalSessionRecoveryError(error) : error
    }).finally(() => {
      renewal = undefined
    })
    return (await renewal).session_token
  }

  async function ensureFresh(recoveryOptions?: FormalRequestOptions): Promise<string> {
    return isFresh(session) ? session.session_token : renew(recoveryOptions, Boolean(session))
  }

  async function run<T>(request: (sessionToken: string) => Promise<T>, requestOptions?: FormalRequestOptions): Promise<T> {
    const token = await ensureFresh(requestOptions)
    try {
      return await request(token)
    } catch (error) {
      if (apiErrorCode(error) !== 'UNAUTHORIZED') throw error
      if (session?.session_token === token) session = undefined
      const retryToken = isFresh(session) ? session.session_token : await renew(requestOptions, true)
      return request(retryToken)
    }
  }

  return { ensureFresh, run, current: () => session }
}
