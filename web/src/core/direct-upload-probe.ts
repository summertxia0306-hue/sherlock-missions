const PROBE_WAV_BYTES = 150 * 1024
const WAV_HEADER_BYTES = 44
const SAMPLE_RATE = 16_000

interface DirectUploadProbeApi {
  createDirectUploadProbe(sessionToken: string, request: {
    byte_length: number
    sha256: string
    content_type: 'audio/wav'
  }): Promise<{
    upload_url: string
    ticket: string
  }>
  verifyDirectUploadProbe(sessionToken: string, ticket: string): Promise<{
    byte_length: number
    sha256: string
    cleaned_up: boolean
  }>
  cancelDirectUploadProbe(sessionToken: string, ticket: string): Promise<unknown>
}

interface ProbeDependencies {
  fetcher?: typeof fetch
  now?: () => number
}

export interface DirectUploadProbeResult {
  byte_length: number
  sha256: string
  upload_ms: number
  verify_ms: number
  total_ms: number
  cleaned_up: boolean
}

function writeAscii(bytes: Uint8Array, offset: number, value: string): void {
  for (let index = 0; index < value.length; index += 1) bytes[offset + index] = value.charCodeAt(index)
}

export function createDeterministicProbeWav(): Uint8Array {
  const bytes = new Uint8Array(PROBE_WAV_BYTES)
  const view = new DataView(bytes.buffer)
  const dataBytes = bytes.byteLength - WAV_HEADER_BYTES
  writeAscii(bytes, 0, 'RIFF')
  view.setUint32(4, bytes.byteLength - 8, true)
  writeAscii(bytes, 8, 'WAVE')
  writeAscii(bytes, 12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, SAMPLE_RATE, true)
  view.setUint32(28, SAMPLE_RATE * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeAscii(bytes, 36, 'data')
  view.setUint32(40, dataBytes, true)
  for (let offset = WAV_HEADER_BYTES, sampleIndex = 0; offset + 1 < bytes.byteLength; offset += 2, sampleIndex += 1) {
    const sample = Math.round(Math.sin((sampleIndex / SAMPLE_RATE) * Math.PI * 2 * 440) * 2048)
    view.setInt16(offset, sample, true)
  }
  return bytes
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', Uint8Array.from(bytes).buffer)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, '0')).join('')
}

export async function runDirectUploadProbe(
  api: DirectUploadProbeApi,
  sessionToken: string,
  dependencies: ProbeDependencies = {}
): Promise<DirectUploadProbeResult> {
  const fetcher = dependencies.fetcher || globalThis.fetch.bind(globalThis)
  const now = dependencies.now || (() => globalThis.performance.now())
  const totalStarted = now()
  const wav = createDeterministicProbeWav()
  const hash = await sha256Hex(wav)
  let ticket = ''
  try {
    const issued = await api.createDirectUploadProbe(sessionToken, {
      byte_length: wav.byteLength,
      sha256: hash,
      content_type: 'audio/wav'
    })
    ticket = issued.ticket
    const uploadStarted = now()
    let response: Response
    try {
      response = await fetcher(issued.upload_url, {
        method: 'PUT',
        credentials: 'omit',
        headers: { 'Content-Type': 'audio/wav' },
        body: wav as BodyInit
      })
    } catch (error) {
      if (error instanceof TypeError) throw new Error('STORAGE_CORS_OR_NETWORK_BLOCKED')
      throw error
    }
    const uploadFinished = now()
    if (!response.ok) throw new Error(`STORAGE_UPLOAD_HTTP_${response.status}`)
    const verified = await api.verifyDirectUploadProbe(sessionToken, ticket)
    const verifyFinished = now()
    return {
      byte_length: verified.byte_length,
      sha256: hash,
      upload_ms: Math.round(uploadFinished - uploadStarted),
      verify_ms: Math.round(verifyFinished - uploadFinished),
      total_ms: Math.round(verifyFinished - totalStarted),
      cleaned_up: verified.cleaned_up
    }
  } catch (error) {
    if (ticket) {
      try { await api.cancelDirectUploadProbe(sessionToken, ticket) } catch { /* best-effort cleanup */ }
    }
    throw error
  }
}
