import { describe, expect, it, vi } from 'vitest'

vi.mock('@cloudbase/js-sdk', () => ({
  default: {
    init: () => ({
      auth: () => ({ hasLoginState: () => true, signInAnonymously: vi.fn() }),
      callFunction: async () => ({ result: { ok: true, service: 'sherlock-api', stage: 'P4', formal_enabled: false, writes: 'test-only' } })
    })
  }
}))

import { cloudbaseApi, createCloudbaseApi, createHttpGatewayApp } from './cloudbase-api'

function fakeApp(options: { loggedIn?: boolean; authError?: boolean; result?: unknown; functions?: boolean } = {}) {
  const signInAnonymously = vi.fn().mockResolvedValue(options.authError ? { error: new Error('denied') } : {})
  const callFunction = vi.fn().mockResolvedValue({
    result: options.result ?? { ok: true, service: 'sherlock-api', stage: 'P4', formal_enabled: false, writes: 'test-only' }
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
  it('uses a stable client id and exact JSON request for the HTTP gateway transport', async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true, service: 'sherlock-api', stage: 'P5', formal_enabled: true, writes: 'formal-and-test' })
    })
    const values = new Map<string, string>()
    const storage = {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => { values.set(key, value) }
    }
    const endpoint = 'https://family24.example.app.tcloudbase.com/sherlock-api'
    const app = createHttpGatewayApp(endpoint, {
      fetcher: fetcher as unknown as typeof fetch,
      storage,
      createClientId: () => '123e4567-e89b-42d3-a456-426614174000'
    })
    const api = createCloudbaseApi(app)

    await api.health()
    await api.authenticate('password')

    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(fetcher).toHaveBeenLastCalledWith(endpoint, expect.objectContaining({
      method: 'POST',
      credentials: 'omit',
      headers: expect.objectContaining({
        'Content-Type': 'application/json',
        'X-Sherlock-Client-Id': '123e4567-e89b-42d3-a456-426614174000'
      }),
      body: JSON.stringify({ action: 'parentAuth', password: 'password' })
    }))
  })

  it('splits a normal 12-second speaking WAV into bounded HTTP requests', async () => {
    const calls: Array<{ body: string; payload: Record<string, any> }> = []
    let activeUploads = 0
    let maximumActiveUploads = 0
    const fetcher = vi.fn().mockImplementation(async (_url: string, init: RequestInit) => {
      const body = String(init.body)
      const payload = JSON.parse(body) as Record<string, any>
      calls.push({ body, payload })
      if (payload.action === 'uploadSpeakingChunk') {
        activeUploads += 1
        maximumActiveUploads = Math.max(maximumActiveUploads, activeUploads)
        await new Promise((resolve) => setTimeout(resolve, 2))
        activeUploads -= 1
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ok: true,
            chunk_index: payload.request.chunk_index,
            file_id: `cloud://test.bucket/tmp/part-${payload.request.chunk_index}.bin`
          })
        }
      }
      if (payload.action === 'scoreUploadedSpeakingTake') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ok: true, stars: 3, proof: 'opaque', child_feedback: 'ok', weak_words: [],
            word_lights: [], can_retry: false, can_skip: false
          })
        }
      }
      throw new Error(`unexpected action ${payload.action}`)
    })
    const storage = { getItem: () => '123e4567-e89b-42d3-a456-426614174000', setItem: vi.fn() }
    const api = createCloudbaseApi(createHttpGatewayApp('https://example.test/sherlock-api', {
      fetcher: fetcher as unknown as typeof fetch,
      storage
    }))
    const wavBase64 = Buffer.alloc(384_044, 7).toString('base64')

    const response = await api.scoreSpeakingTake('token', {
      result_id: 'r1', course_id: 'S01D39', course_version: 'version1',
      question_id: 1, attempt: 1, wav_base64: wavBase64
    })

    expect(response.proof).toBe('opaque')
    const uploads = calls.filter(({ payload }) => payload.action === 'uploadSpeakingChunk')
    expect(uploads).toHaveLength(8)
    expect(calls.at(-1)?.payload.action).toBe('scoreUploadedSpeakingTake')
    expect(calls.some(({ payload }) => payload.action === 'scoreSpeakingTake')).toBe(false)
    expect(Math.max(...calls.map(({ body }) => new TextEncoder().encode(body).byteLength))).toBeLessThan(75 * 1024)
    expect(maximumActiveUploads).toBe(2)
  })

  it('retries only a failed speaking chunk before final scoring', async () => {
    const attempts = new Map<number, number>()
    const fetcher = vi.fn().mockImplementation(async (_url: string, init: RequestInit) => {
      const payload = JSON.parse(String(init.body)) as Record<string, any>
      if (payload.action === 'uploadSpeakingChunk') {
        const index = payload.request.chunk_index as number
        attempts.set(index, (attempts.get(index) || 0) + 1)
        if (index === 0 && attempts.get(index) === 1) {
          return { ok: false, status: 503, json: async () => ({ ok: false, error: { code: 'TEMPORARY' } }) }
        }
        return { ok: true, status: 200, json: async () => ({ ok: true, chunk_index: index, file_id: `cloud://test.bucket/part-${index}` }) }
      }
      return {
        ok: true, status: 200,
        json: async () => ({ ok: true, stars: 3, proof: 'retry-proof', child_feedback: 'ok', weak_words: [], word_lights: [], can_retry: false, can_skip: false })
      }
    })
    const app = createHttpGatewayApp('https://example.test/sherlock-api', {
      fetcher: fetcher as unknown as typeof fetch,
      storage: { getItem: () => '123e4567-e89b-42d3-a456-426614174000', setItem: vi.fn() }
    })
    const response = await createCloudbaseApi(app).scoreSpeakingTake('token', {
      result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
      wav_base64: Buffer.alloc(60_000, 5).toString('base64')
    })
    expect(response.proof).toBe('retry-proof')
    expect(attempts.get(0)).toBe(2)
    expect(attempts.get(1)).toBe(1)
  })

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

  it('forwards isolated P4 parent filters and temporary legacy recording URL actions', async () => {
    const fake = fakeApp({ loggedIn: true, result: { ok: true, results: [], summary: { result_count: 0, completed_course_count: 0, formal_completion_count: 0 } } })
    const api = createCloudbaseApi(fake.app)
    const filters = { data_kind: 'formal' as const, module_type: 'speaking' as const, course_id: 'S01D01' }

    await api.listParentResults('token', filters)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      data: { action: 'listParentResults', session_token: 'token', filters }
    }))
    await api.getParentRecordingUrl('token', 'legacy-result', 1, 2)
    expect(fake.callFunction).toHaveBeenLastCalledWith(expect.objectContaining({
      data: { action: 'getParentRecordingUrl', session_token: 'token', result_id: 'legacy-result', question_id: 1, attempt: 2 }
    }))
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
    await cloudbaseApi.listParentResults('token', { data_kind: 'formal' })
    await cloudbaseApi.getParentRecordingUrl('token', 'legacy-result', 1, 1)
    vi.unstubAllEnvs()
  })
})
