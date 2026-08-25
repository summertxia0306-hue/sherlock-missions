import { afterEach, describe, expect, it, vi } from 'vitest'
import { encodePcm16Wav, peakAmplitude, resampleTo16k, SharedPcmRecorder } from './recorder'

describe('P3 iPad recording primitives', () => {
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })
  it('downsamples input and writes PCM 16k mono WAV', () => {
    const source = new Float32Array(48000).map((_, index) => Math.sin(index / 20) * 0.2)
    const samples = resampleTo16k(source, 48000)
    expect(samples.length).toBe(16000)
    const wav = encodePcm16Wav(samples)
    const view = new DataView(wav)
    expect(String.fromCharCode(...new Uint8Array(wav, 0, 4))).toBe('RIFF')
    expect(view.getUint16(22, true)).toBe(1)
    expect(view.getUint32(24, true)).toBe(16000)
    expect(view.getUint16(34, true)).toBe(16)
  })

  it('detects silent input before consuming provider quota', () => {
    expect(peakAmplitude(new Float32Array([0, 0.005, -0.009]))).toBeLessThan(0.01)
    expect(peakAmplitude(new Float32Array([0, 0.02]))).toBeGreaterThan(0.01)
  })

  it('reuses one healthy microphone stream and suspends one AudioContext between takes', async () => {
    vi.useFakeTimers()
    const stop = vi.fn()
    const track = { readyState: 'live', muted: false, stop }
    const getUserMedia = vi.fn(async () => ({ getAudioTracks: () => [track], getTracks: () => [track] }))
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } })
    const processors: Array<{ onaudioprocess: ((event: { inputBuffer: { getChannelData: () => Float32Array } }) => void) | null; connect: ReturnType<typeof vi.fn>; disconnect: ReturnType<typeof vi.fn> }> = []
    const resume = vi.fn(async () => undefined)
    const suspend = vi.fn(async () => undefined)
    class FakeContext {
      sampleRate = 48000
      destination = {}
      resume = resume
      suspend = suspend
      createMediaStreamSource() { return { connect: vi.fn(), disconnect: vi.fn() } }
      createScriptProcessor() {
        const node = { onaudioprocess: null, connect: vi.fn(), disconnect: vi.fn() }
        processors.push(node)
        return node
      }
      createGain() { return { gain: { value: 1 }, connect: vi.fn(), disconnect: vi.fn() } }
    }
    vi.stubGlobal('AudioContext', FakeContext)
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:recording') })
    const recorder = new SharedPcmRecorder()
    for (let take = 0; take < 2; take += 1) {
      const start = recorder.start(vi.fn(), vi.fn())
      await vi.runAllTimersAsync()
      await start
      const samples = new Float32Array(48000).map((_, index) => Math.sin(index / 8) * 0.2)
      processors[take].onaudioprocess?.({ inputBuffer: { getChannelData: () => samples } })
      const result = await recorder.stop()
      expect(result.peak).toBeGreaterThan(0.01)
      expect(result.wav.type).toBe('audio/wav')
    }
    expect(getUserMedia).toHaveBeenCalledTimes(1)
    expect(resume).toHaveBeenCalledTimes(2)
    expect(suspend).toHaveBeenCalledTimes(2)
    recorder.release()
    expect(stop).toHaveBeenCalledTimes(1)
  })
})
