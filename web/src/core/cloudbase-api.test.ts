import { describe, expect, it, vi } from 'vitest'

vi.mock('@cloudbase/js-sdk', () => ({
  default: {
    init: () => ({
      auth: () => ({ hasLoginState: () => true, signInAnonymously: vi.fn() }),
      callFunction: async () => ({ result: { ok: true, service: 'sherlock-api', stage: 'P1', formal_enabled: false, writes: 'test-only' } })
    })
  }
}))

import { cloudbaseApi, createCloudbaseApi } from './cloudbase-api'

function fakeApp(options: { loggedIn?: boolean; authError?: boolean; result?: unknown; functions?: boolean } = {}) {
  const signInAnonymously = vi.fn().mockResolvedValue(options.authError ? { error: new Error('denied') } : {})
  const callFunction = vi.fn().mockResolvedValue({
    result: options.result ?? { ok: true, service: 'sherlock-api', stage: 'P1', formal_enabled: false, writes: 'test-only' }
  })
  return {
    app: {
      auth: () => ({ hasLoginState: () => options.loggedIn, signInAnonymously }),
      ...(options.functions === false ? {} : { callFunction })
    },
    signInAnonymously,
    callFunction
  }
}

describe('CloudBase browser adapter', () => {
  it('requires public environment configuration', async () => {
    await expect(createCloudbaseApi(undefined).health()).rejects.toThrow('CLOUDBASE_NOT_CONFIGURED')
  })

  it('logs in anonymously once and calls the isolated function', async () => {
    const fake = fakeApp()
    const api = createCloudbaseApi(fake.app, 'sherlock-api')
    expect((await api.health()).formal_enabled).toBe(false)
    await api.authenticate('password')
    expect(fake.signInAnonymously).toHaveBeenCalledTimes(1)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      name: 'sherlock-api',
      data: { action: 'parentAuth', password: 'password' }
    }))
  })

  it('uses an existing login state and forwards result submission', async () => {
    const fake = fakeApp({ loggedIn: true, result: { ok: true, result_id: 'r1', data_kind: 'test', formal_completion_eligible: false } })
    const api = createCloudbaseApi(fake.app)
    const response = await api.submitResult('token', {
      student_id: 's', module_type: 'listening', course_id: 'c', course_version: '1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:00:00.000Z',
      duration_seconds: 0, payload: {}
    })
    expect(response.data_kind).toBe('test')
    expect(fake.signInAnonymously).not.toHaveBeenCalled()
  })

  it('maps authentication, capability, and service failures to stable codes', async () => {
    await expect(createCloudbaseApi(fakeApp({ authError: true }).app).health()).rejects.toThrow('CLOUDBASE_ANONYMOUS_LOGIN_FAILED')
    await expect(createCloudbaseApi(fakeApp({ loggedIn: true, functions: false }).app).health()).rejects.toThrow('CLOUDBASE_FUNCTIONS_UNAVAILABLE')
    await expect(createCloudbaseApi(fakeApp({ result: { ok: false, error: { code: 'RATE_LIMITED', message: 'hidden' } } }).app).health()).rejects.toThrow('RATE_LIMITED')
    await expect(createCloudbaseApi({ auth: () => undefined }).health()).rejects.toThrow('CLOUDBASE_AUTH_UNAVAILABLE')
  })

  it('lazily initializes the production adapter from public environment values', async () => {
    vi.stubEnv('VITE_CLOUDBASE_ENV_ID', 'test-env')
    expect((await cloudbaseApi.health()).writes).toBe('test-only')
    vi.unstubAllEnvs()
  })
})
