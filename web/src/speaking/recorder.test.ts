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

  it('uses a fresh processed microphone stream for every take and releases it immediately', async () => {
    vi.useFakeTimers()
    const stops = [vi.fn(), vi.fn()]
    let streamIndex = 0
    const getUserMedia = vi.fn(async () => {
      const stop = stops[streamIndex++]
      const track = { readyState: 'live', muted: false, stop }
      return { getAudioTracks: () => [track], getTracks: () => [track] }
    })
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
    expect(getUserMedia).toHaveBeenCalledTimes(2)
    expect(getUserMedia).toHaveBeenNthCalledWith(1, {
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    })
    expect(resume).toHaveBeenCalledTimes(2)
    expect(suspend).toHaveBeenCalledTimes(2)
    expect(stops[0]).toHaveBeenCalledTimes(1)
    expect(stops[1]).toHaveBeenCalledTimes(1)
    recorder.release()
    expect(stops[1]).toHaveBeenCalledTimes(1)
  })

  it('releases the iOS microphone indicator even when the take is silent', async () => {
    vi.useFakeTimers()
    const stop = vi.fn()
    const track = { readyState: 'live', muted: false, stop }
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: {
      getUserMedia: vi.fn(async () => ({ getAudioTracks: () => [track], getTracks: () => [track] }))
    } })
    let processor: { onaudioprocess: ((event: { inputBuffer: { getChannelData: () => Float32Array } }) => void) | null } | undefined
    class FakeContext {
      sampleRate = 48000
      destination = {}
      async resume() {}
      async suspend() {}
      createMediaStreamSource() { return { connect: vi.fn(), disconnect: vi.fn() } }
      createScriptProcessor() {
        processor = { onaudioprocess: null }
        return { ...processor, connect: vi.fn(), disconnect: vi.fn() }
      }
      createGain() { return { gain: { value: 1 }, connect: vi.fn(), disconnect: vi.fn() } }
    }
    vi.stubGlobal('AudioContext', FakeContext)
    const recorder = new SharedPcmRecorder()
    const start = recorder.start(vi.fn(), vi.fn())
    await vi.runAllTimersAsync()
    await start
    processor?.onaudioprocess?.({ inputBuffer: { getChannelData: () => new Float32Array(48000).fill(0.001) } })
    await expect(recorder.stop()).rejects.toThrow('SILENT_RECORDING')
    expect(stop).toHaveBeenCalledTimes(1)
  })

  it('releases an active microphone stream when the page is left mid-take', async () => {
    vi.useFakeTimers()
    const stop = vi.fn()
    const sourceDisconnect = vi.fn()
    const processorDisconnect = vi.fn()
    const track = { readyState: 'live', muted: false, stop }
    Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: {
      getUserMedia: vi.fn(async () => ({ getAudioTracks: () => [track], getTracks: () => [track] }))
    } })
    class FakeContext {
      sampleRate = 48000
      destination = {}
      async resume() {}
      async suspend() {}
      createMediaStreamSource() { return { connect: vi.fn(), disconnect: sourceDisconnect } }
      createScriptProcessor() { return { onaudioprocess: null, connect: vi.fn(), disconnect: processorDisconnect } }
      createGain() { return { gain: { value: 1 }, connect: vi.fn(), disconnect: vi.fn() } }
    }
    vi.stubGlobal('AudioContext', FakeContext)
    const recorder = new SharedPcmRecorder()
    const start = recorder.start(vi.fn(), vi.fn())
    await vi.runAllTimersAsync()
    await start
    recorder.release()
    expect(sourceDisconnect).toHaveBeenCalledTimes(1)
    expect(processorDisconnect).toHaveBeenCalledTimes(1)
    expect(stop).toHaveBeenCalledTimes(1)
  })
})
