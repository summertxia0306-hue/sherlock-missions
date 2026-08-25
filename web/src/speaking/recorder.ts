export function peakAmplitude(samples: Float32Array): number {
  let peak = 0
  for (const sample of samples) peak = Math.max(peak, Math.abs(sample))
  return peak
}

export function resampleTo16k(input: Float32Array, sourceRate: number): Float32Array {
  if (!Number.isFinite(sourceRate) || sourceRate < 16000 || input.length === 0) throw new Error('INVALID_RECORDING')
  if (sourceRate === 16000) return input.slice()
  const ratio = sourceRate / 16000
  const output = new Float32Array(Math.floor(input.length / ratio))
  for (let index = 0; index < output.length; index += 1) {
    const start = Math.floor(index * ratio)
    const end = Math.min(input.length, Math.floor((index + 1) * ratio))
    let sum = 0
    for (let source = start; source < end; source += 1) sum += input[source]
    output[index] = sum / Math.max(1, end - start)
  }
  return output
}

export function encodePcm16Wav(samples: Float32Array): ArrayBuffer {
  const output = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(output)
  const text = (offset: number, value: string) => [...value].forEach((char, index) => view.setUint8(offset + index, char.charCodeAt(0)))
  text(0, 'RIFF'); view.setUint32(4, 36 + samples.length * 2, true); text(8, 'WAVE'); text(12, 'fmt ')
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true)
  view.setUint32(24, 16000, true); view.setUint32(28, 32000, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true)
  text(36, 'data'); view.setUint32(40, samples.length * 2, true)
  samples.forEach((sample, index) => view.setInt16(44 + index * 2, Math.round(Math.max(-1, Math.min(1, sample)) * (sample < 0 ? 32768 : 32767)), true))
  return output
}

export interface RecordedAudio { wav: Blob; url: string; peak: number; seconds: number }
export interface PcmRecorder {
  start(onAutoStop: () => void, onCountdown?: (value: number) => void): Promise<void>
  stop(): Promise<RecordedAudio>
  release(): void
}

export class SharedPcmRecorder implements PcmRecorder {
  private context?: AudioContext
  private stream?: MediaStream
  private source?: MediaStreamAudioSourceNode
  private processor?: ScriptProcessorNode
  private mute?: GainNode
  private chunks: Float32Array[] = []
  private sourceRate = 0
  private startedAt = 0
  private timer?: number

  private healthyStream(): boolean {
    return Boolean(this.stream?.getAudioTracks().some((track) => track.readyState === 'live' && !track.muted))
  }

  async start(onAutoStop: () => void, onCountdown?: (value: number) => void): Promise<void> {
    if (this.processor) throw new Error('RECORDER_BUSY')
    if (!this.healthyStream()) {
      this.stream?.getTracks().forEach((track) => track.stop())
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false } })
    }
    this.context ??= new AudioContext()
    await this.context.resume()
    for (const value of [3, 2, 1]) {
      onCountdown?.(value)
      await new Promise((done) => window.setTimeout(done, 700))
    }
    onCountdown?.(0)
    this.chunks = []
    this.sourceRate = this.context.sampleRate
    this.source = this.context.createMediaStreamSource(this.stream!)
    this.processor = this.context.createScriptProcessor(4096, 1, 1)
    this.mute = this.context.createGain(); this.mute.gain.value = 0
    this.processor.onaudioprocess = (event) => this.chunks.push(event.inputBuffer.getChannelData(0).slice())
    this.source.connect(this.processor); this.processor.connect(this.mute); this.mute.connect(this.context.destination)
    this.startedAt = performance.now()
    // Leave one second of headroom for the final ScriptProcessor buffer so
    // Safari recordings stay inside the server's 20-second WAV limit.
    this.timer = window.setTimeout(onAutoStop, 19_000)
  }

  async stop(): Promise<RecordedAudio> {
    if (!this.processor || !this.context) throw new Error('RECORDER_NOT_ACTIVE')
    if (this.timer) window.clearTimeout(this.timer)
    this.source?.disconnect(); this.processor.disconnect(); this.mute?.disconnect(); this.processor.onaudioprocess = null
    this.source = undefined; this.processor = undefined; this.mute = undefined
    await this.context.suspend()
    const length = this.chunks.reduce((sum, chunk) => sum + chunk.length, 0)
    const joined = new Float32Array(length)
    let offset = 0
    for (const chunk of this.chunks) { joined.set(chunk, offset); offset += chunk.length }
    const peak = peakAmplitude(joined)
    if (peak < 0.01) {
      this.stream?.getTracks().forEach((track) => track.stop()); this.stream = undefined
      throw new Error('SILENT_RECORDING')
    }
    const wav = new Blob([encodePcm16Wav(resampleTo16k(joined, this.sourceRate))], { type: 'audio/wav' })
    return { wav, url: URL.createObjectURL(wav), peak, seconds: Math.max(0, (performance.now() - this.startedAt) / 1000) }
  }

  release(): void {
    if (this.timer) window.clearTimeout(this.timer)
    this.stream?.getTracks().forEach((track) => track.stop())
    this.stream = undefined
  }
}

export const sharedPcmRecorder = new SharedPcmRecorder()
