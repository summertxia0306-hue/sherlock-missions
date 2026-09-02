const DEFAULT_APP_BASE = '/sherlock-english/'
const SAFE_APP_BASE = /^\/[A-Za-z0-9_-]+\/$/

export function resolveAppBase(value: string | undefined): string {
  const candidate = value?.trim() || DEFAULT_APP_BASE
  if (!SAFE_APP_BASE.test(candidate) || candidate.includes('..') || candidate.includes('\\')) {
    throw new Error('INVALID_APP_BASE')
  }
  return candidate
}

export function createAudioPathPattern(value: string): RegExp {
  const appBase = resolveAppBase(value)
  return new RegExp(`^${appBase}audio/(?:listening|speaking)/`)
}
