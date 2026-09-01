import { describe, expect, it, vi } from 'vitest'
import { SherlockApiError } from './cloudbase-api'
import { scoreSpeakingDirectFirst, type DirectSpeakingTransportDependencies } from './speaking-direct-upload'

const request = {
  result_id: 'r1', course_id: 'S01D39', course_version: 'version1', question_id: 1, attempt: 1,
  wav_base64: Buffer.alloc(12_044, 7).toString('base64')
}

function response(proof = 'direct-proof') {
  return {
    ok: true as const, stars: 3 as const, proof, child_feedback: 'ok', weak_words: [], word_lights: [],
    can_retry: false, can_skip: false
  }
}

function dependencies(overrides: Partial<DirectSpeakingTransportDependencies> = {}): DirectSpeakingTransportDependencies {
  return {
    fetcher: vi.fn().mockResolvedValue({ ok: true, status: 200 }) as unknown as typeof fetch,
    issue: vi.fn().mockResolvedValue({
      upload_url: 'https://storage.example.test/take.wav?signed=1', ticket: 'opaque-ticket'
    }),
    scoreDirect: vi.fn().mockResolvedValue({
      ...response(), transport: 'direct' as const, cleaned_up: true,
      server_timing: { validation_ms: 12, scoring_ms: 800, cleanup_ms: 5 }
    }),
    cancelDirect: vi.fn().mockResolvedValue({ ok: true, cleaned_up: true }),
    fallback: vi.fn().mockResolvedValue(response('chunk-proof')),
    now: (() => { let value = 0; return () => { value += 10; return value } })(),
    ...overrides
  }
}

describe('speaking direct-first browser transport', () => {
  it('uploads one raw WAV PUT and returns phase diagnostics from the direct score', async () => {
    const deps = dependencies()

    const result = await scoreSpeakingDirectFirst('parent-token', request, deps)

    expect(deps.issue).toHaveBeenCalledWith('parent-token', expect.objectContaining({
      result_id: 'r1', question_id: 1, byte_length: 12_044,
      sha256: expect.stringMatching(/^[0-9a-f]{64}$/), content_type: 'audio/wav'
    }))
    expect(deps.fetcher).toHaveBeenCalledWith('https://storage.example.test/take.wav?signed=1', expect.objectContaining({
      method: 'PUT', credentials: 'omit', headers: { 'Content-Type': 'audio/wav' }, body: expect.any(Uint8Array)
    }))
    expect(deps.scoreDirect).toHaveBeenCalledWith('parent-token', 'opaque-ticket', expect.not.objectContaining({ wav_base64: expect.anything() }))
    expect(deps.fallback).not.toHaveBeenCalled()
    expect(result.transport_diagnostics).toEqual(expect.objectContaining({
      mode: 'direct', validation_ms: 12, scoring_ms: 800, cleanup_ms: 5, cleaned_up: true
    }))
  })

  it('falls back before upload when direct signing is disabled or unavailable', async () => {
    for (const code of ['SPEAKING_DIRECT_UPLOAD_DISABLED', 'SPEAKING_DIRECT_SIGNING_UNAVAILABLE']) {
      const deps = dependencies({ issue: vi.fn().mockRejectedValue(new SherlockApiError(code)) })
      const result = await scoreSpeakingDirectFirst('parent-token', request, deps)

      expect(deps.fetcher).not.toHaveBeenCalled()
      expect(deps.fallback).toHaveBeenCalledTimes(1)
      expect(result.proof).toBe('chunk-proof')
      expect(result.transport_diagnostics?.mode).toBe('chunk-fallback')
      expect(result.transport_diagnostics?.direct_error_code).toBe(code)
    }
  })

  it('checks the direct object after an ambiguous PUT failure before deciding to fall back', async () => {
    const deps = dependencies({
      fetcher: vi.fn().mockRejectedValue(new TypeError('Failed to fetch')) as unknown as typeof fetch
    })

    const result = await scoreSpeakingDirectFirst('parent-token', request, deps)

    expect(deps.scoreDirect).toHaveBeenCalledTimes(1)
    expect(deps.fallback).not.toHaveBeenCalled()
    expect(result.proof).toBe('direct-proof')
  })

  it('retries the same direct score once after an ambiguous response loss', async () => {
    const scoreDirect = vi.fn()
      .mockRejectedValueOnce(new TypeError('network'))
      .mockResolvedValueOnce({
        ...response(), idempotent: true, transport: 'direct', cleaned_up: true,
        server_timing: { validation_ms: 0, scoring_ms: 1, cleanup_ms: 1 }
      })
    const deps = dependencies({ scoreDirect })

    const result = await scoreSpeakingDirectFirst('parent-token', request, deps)

    expect(scoreDirect).toHaveBeenCalledTimes(2)
    expect(scoreDirect.mock.calls[0]).toEqual(scoreDirect.mock.calls[1])
    expect(deps.fallback).not.toHaveBeenCalled()
    expect(result.idempotent).toBe(true)
  })

  it('falls back with the same recording only after a deterministic unscored storage failure', async () => {
    for (const code of ['SPEAKING_DIRECT_OBJECT_MISSING', 'SPEAKING_DIRECT_INTEGRITY_FAILED', 'SPEAKING_DIRECT_TICKET_EXPIRED']) {
      const deps = dependencies({ scoreDirect: vi.fn().mockRejectedValue(new SherlockApiError(code)) })
      const result = await scoreSpeakingDirectFirst('parent-token', request, deps)

      expect(deps.cancelDirect).toHaveBeenCalledWith('parent-token', 'opaque-ticket')
      expect(deps.fallback).toHaveBeenCalledWith('parent-token', request)
      expect(result.proof).toBe('chunk-proof')
      expect(result.transport_diagnostics?.direct_error_code).toBe(code)
    }
  })

  it('never starts chunk scoring when two direct responses remain ambiguous', async () => {
    const deps = dependencies({ scoreDirect: vi.fn().mockRejectedValue(new TypeError('network')) })

    await expect(scoreSpeakingDirectFirst('parent-token', request, deps)).rejects.toThrow('SPEAKING_DIRECT_STATUS_UNKNOWN')
    expect(deps.scoreDirect).toHaveBeenCalledTimes(2)
    expect(deps.fallback).not.toHaveBeenCalled()
    expect(deps.cancelDirect).not.toHaveBeenCalled()
  })

  it('does not hide authentication, validation, or provider errors behind chunk fallback', async () => {
    for (const code of ['UNAUTHORIZED', 'INVALID_SPEAKING_DIRECT_TICKET', 'INVALID_AUDIO', 'ISE_TIMEOUT']) {
      const deps = dependencies({ scoreDirect: vi.fn().mockRejectedValue(new SherlockApiError(code)) })

      await expect(scoreSpeakingDirectFirst('parent-token', request, deps)).rejects.toThrow(code)
      expect(deps.fallback).not.toHaveBeenCalled()
    }
  })
})
