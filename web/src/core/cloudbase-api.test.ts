import { describe, expect, it, vi } from 'vitest'

vi.mock('@cloudbase/js-sdk', () => ({
  default: {
    init: () => ({
      auth: () => ({ hasLoginState: () => true, signInAnonymously: vi.fn() }),
      callFunction: async () => ({ result: { ok: true, service: 'sherlock-api', stage: 'P3', formal_enabled: false, writes: 'test-only' } })
    })
  }
}))

import { cloudbaseApi, createCloudbaseApi } from './cloudbase-api'

function fakeApp(options: { loggedIn?: boolean; authError?: boolean; result?: unknown; functions?: boolean } = {}) {
  const signInAnonymously = vi.fn().mockResolvedValue(options.authError ? { error: new Error('denied') } : {})
  const callFunction = vi.fn().mockResolvedValue({
    result: options.result ?? { ok: true, service: 'sherlock-api', stage: 'P3', formal_enabled: false, writes: 'test-only' }
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

  it('forwards P2 listening submit, correction, and authenticated parent detail actions', async () => {
    const fake = fakeApp({ loggedIn: true, result: { ok: true, results: [] } })
    const api = createCloudbaseApi(fake.app)
    const submission = {
      result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock', course_id: 'W01D39',
      course_version: 'version1', started_at: '2026-08-24T10:00:00.000Z',
      submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
      answers: { '1': 0 as const }, play_counts: { '1': 1 }, device_info: {}
    }
    await api.submitListeningResult('token', submission)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      data: { action: 'submitListeningResult', session_token: 'token', submission }
    }))
    await api.checkListeningCorrection('token', submission.result_id, 1, 1, 0)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      data: expect.objectContaining({ action: 'checkListeningCorrection', question_id: 1, attempt: 1 })
    }))
    await api.listListeningTestResults('token')
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      data: { action: 'listListeningTestResults', session_token: 'token' }
    }))
  })

  it('forwards P3 scoring, proof-only submission, parent detail, and recording URL actions', async () => {
    const fake = fakeApp({ loggedIn: true, result: { ok: true, proof: 'opaque', stars: 3 } })
    const api = createCloudbaseApi(fake.app)
    const request = { result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1, wav_base64: 'base64' }
    await api.scoreSpeakingTake('token', request)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({ data: { action: 'scoreSpeakingTake', session_token: 'token', request } }))
    const submission = { result_id: 'r1', student_id: 'sherlock', course_id: 'S01D39', course_version: 'version1', started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120, questions: [{ id: 1, proofs: ['opaque'], passed_by_safety: false }] }
    await api.submitSpeakingResult('token', submission)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({ data: { action: 'submitSpeakingResult', session_token: 'token', submission } }))
    await api.listSpeakingTestResults('token')
    await api.getSpeakingRecordingUrl('token', 'r1', 1, 1)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({ data: expect.objectContaining({ action: 'getSpeakingRecordingUrl', result_id: 'r1' }) }))
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
