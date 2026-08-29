import { describe, expect, it, vi } from 'vitest'
import { createFormalSessionManager } from './formal-session'
import type { SherlockApi } from './cloudbase-api'

function apiWithSessions(tokens: string[]): SherlockApi {
  let index = 0
  return {
    startChildSession: vi.fn(async () => ({
      ok: true as const,
      session_token: tokens[index++] || tokens.at(-1) || 'formal-token',
      expires_at: new Date(1_000_000 + index * 7_200_000).toISOString(),
      data_kind: 'formal' as const
    }))
  } as unknown as SherlockApi
}

describe('formal session manager', () => {
  it('renews before expiry and retries an unauthorized request at most once', async () => {
    const api = apiWithSessions(['token-1', 'token-2', 'token-3'])
    const manager = createFormalSessionManager(api, { now: () => 1_000_000, renewBeforeMs: 300_000 })
    const operation = vi.fn(async (token: string) => {
      if (token === 'token-1') throw new Error('UNAUTHORIZED')
      return token
    })

    await expect(manager.run(operation)).resolves.toBe('token-2')
    expect(operation.mock.calls.map(([token]) => token)).toEqual(['token-1', 'token-2'])
    expect(api.startChildSession).toHaveBeenCalledTimes(2)

    const alwaysUnauthorized = vi.fn(async () => { throw new Error('UNAUTHORIZED') })
    await expect(manager.run(alwaysUnauthorized)).rejects.toThrow('UNAUTHORIZED')
    expect(alwaysUnauthorized).toHaveBeenCalledTimes(2)
  })

  it('uses one renewal for concurrent requests and exposes background freshness checks', async () => {
    const api = apiWithSessions(['token-1', 'token-2'])
    const now = { value: 1_000_000 }
    const manager = createFormalSessionManager(api, { now: () => now.value, renewBeforeMs: 300_000 })

    await manager.ensureFresh()
    now.value = 8_000_001
    const [first, second] = await Promise.all([manager.ensureFresh(), manager.ensureFresh()])
    expect(first).toBe('token-2')
    expect(second).toBe('token-2')
    expect(api.startChildSession).toHaveBeenCalledTimes(2)
  })

  it('announces recovery without losing the original request closure', async () => {
    const api = apiWithSessions(['token-1', 'token-2'])
    const recovering = vi.fn()
    const manager = createFormalSessionManager(api, { now: () => 1_000_000 })
    const logicalRequest = { result_id: 'same-result', answers: { '1': 0 } }
    const seen: unknown[] = []

    await manager.run(async (token) => {
      seen.push({ token, logicalRequest })
      if (token === 'token-1') throw new Error('UNAUTHORIZED')
      return true
    }, { onRecovering: recovering })

    expect(recovering).toHaveBeenCalledTimes(1)
    expect((seen[0] as { logicalRequest: unknown }).logicalRequest).toBe(logicalRequest)
    expect((seen[1] as { logicalRequest: unknown }).logicalRequest).toBe(logicalRequest)
  })

  it('reports a failed renewal without retrying the original request indefinitely', async () => {
    const api = apiWithSessions(['token-1'])
    vi.mocked(api.startChildSession)
      .mockResolvedValueOnce({ ok: true, session_token: 'token-1', expires_at: new Date(8_200_000).toISOString(), data_kind: 'formal' })
      .mockRejectedValueOnce(new TypeError('offline'))
    const manager = createFormalSessionManager(api, { now: () => 1_000_000 })
    const request = vi.fn(async () => { throw new Error('UNAUTHORIZED') })

    await expect(manager.run(request)).rejects.toThrow('FORMAL_SESSION_RECOVERY_FAILED')
    expect(request).toHaveBeenCalledTimes(1)
    expect(api.startChildSession).toHaveBeenCalledTimes(2)
  })
})
