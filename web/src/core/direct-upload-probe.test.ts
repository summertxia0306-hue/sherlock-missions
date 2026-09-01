import { describe, expect, it, vi } from 'vitest'
import { DIRECT_UPLOAD_PROBE_OPTIONS, createDeterministicProbeWav, runDirectUploadProbe } from './direct-upload-probe'

describe('direct storage upload browser probe', () => {
  it('creates each fixed-size mono 16 kHz 16-bit PCM WAV without microphone input', () => {
    expect(DIRECT_UPLOAD_PROBE_OPTIONS).toEqual([
      { label: '150KiB', byteLength: 150 * 1024 },
      { label: '400KiB', byteLength: 400 * 1024 },
      { label: '700KB', byteLength: 700_000 }
    ])
    for (const option of DIRECT_UPLOAD_PROBE_OPTIONS) {
      const wav = createDeterministicProbeWav(option.byteLength)
      const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength)
      const ascii = (start: number, length: number) => String.fromCharCode(...wav.slice(start, start + length))

      expect(wav.byteLength).toBe(option.byteLength)
      expect(ascii(0, 4)).toBe('RIFF')
      expect(ascii(8, 4)).toBe('WAVE')
      expect(view.getUint16(22, true)).toBe(1)
      expect(view.getUint32(24, true)).toBe(16_000)
      expect(view.getUint16(34, true)).toBe(16)
      expect(view.getUint32(40, true)).toBe(wav.byteLength - 44)
    }
    expect(() => createDeterministicProbeWav(200 * 1024)).toThrow('INVALID_DIRECT_UPLOAD_PROBE_SIZE')
  })

  it('uploads one raw binary PUT, verifies server-side integrity, and reports phase timings', async () => {
    const api = {
      createDirectUploadProbe: vi.fn().mockResolvedValue({
        ok: true,
        data_kind: 'test',
        upload_url: 'https://storage.example.test/probe.wav?signed=1',
        object_key: 'sherlock-english/test/direct-upload-probe/probe.wav',
        file_id: 'cloud://bucket/sherlock-english/test/direct-upload-probe/probe.wav',
        byte_length: 400 * 1024,
        expires_at: '2026-08-31T12:02:00.000Z',
        ticket: 'opaque-ticket'
      }),
      verifyDirectUploadProbe: vi.fn().mockResolvedValue({
        ok: true, data_kind: 'test', byte_length: 400 * 1024, sha256: 'a'.repeat(64), cleaned_up: true
      }),
      cancelDirectUploadProbe: vi.fn()
    }
    const fetcher = vi.fn().mockResolvedValue({ ok: true, status: 200 })
    const ticks = [0, 5, 25, 40]

    const result = await runDirectUploadProbe(api as never, 'parent-token', 400 * 1024, {
      fetcher: fetcher as unknown as typeof fetch,
      now: () => ticks.shift() ?? 40
    })

    expect(api.createDirectUploadProbe).toHaveBeenCalledWith('parent-token', expect.objectContaining({
      byte_length: 400 * 1024,
      content_type: 'audio/wav',
      sha256: expect.stringMatching(/^[0-9a-f]{64}$/)
    }))
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher).toHaveBeenCalledWith('https://storage.example.test/probe.wav?signed=1', expect.objectContaining({
      method: 'PUT',
      credentials: 'omit',
      headers: { 'Content-Type': 'audio/wav' },
      body: expect.any(Uint8Array)
    }))
    expect(api.verifyDirectUploadProbe).toHaveBeenCalledWith('parent-token', 'opaque-ticket')
    expect(api.cancelDirectUploadProbe).not.toHaveBeenCalled()
    expect(result.byte_length).toBe(400 * 1024)
    expect(result.upload_ms).toBe(20)
    expect(result.verify_ms).toBe(15)
    expect(result.total_ms).toBe(40)
  })

  it('best-effort cancels the exact ticket after a CORS/network PUT failure', async () => {
    const api = {
      createDirectUploadProbe: vi.fn().mockResolvedValue({
        ok: true, data_kind: 'test', upload_url: 'https://storage.example.test/probe.wav',
        object_key: 'sherlock-english/test/direct-upload-probe/probe.wav', file_id: 'cloud://bucket/probe.wav',
        byte_length: 150 * 1024, expires_at: '2026-08-31T12:02:00.000Z', ticket: 'opaque-ticket'
      }),
      verifyDirectUploadProbe: vi.fn(),
      cancelDirectUploadProbe: vi.fn().mockResolvedValue({ ok: true, data_kind: 'test', cleaned_up: true })
    }
    const fetcher = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(runDirectUploadProbe(api as never, 'parent-token', 700_000, {
      fetcher: fetcher as unknown as typeof fetch
    })).rejects.toThrow('STORAGE_CORS_OR_NETWORK_BLOCKED')
    expect(api.cancelDirectUploadProbe).toHaveBeenCalledWith('parent-token', 'opaque-ticket')
    expect(api.verifyDirectUploadProbe).not.toHaveBeenCalled()
  })
})
