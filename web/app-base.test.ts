import { describe, expect, it } from 'vitest'
import { createAudioPathPattern, resolveAppBase } from './app-base'

describe('resolveAppBase', () => {
  it('preserves the existing GitHub and CloudBase static default', () => {
    expect(resolveAppBase(undefined)).toBe('/sherlock-english/')
    expect(resolveAppBase('')).toBe('/sherlock-english/')
  })

  it('accepts the exact domestic gateway application path', () => {
    expect(resolveAppBase('/sherlock-api/')).toBe('/sherlock-api/')
  })

  it.each([
    'sherlock-api/',
    '/sherlock-api',
    'https://example.com/sherlock-api/',
    '/sherlock-api/../private/',
    '/sherlock-api\\private/',
    '//evil.example/'
  ])('rejects an unsafe or ambiguous application base: %s', (value) => {
    expect(() => resolveAppBase(value)).toThrow('INVALID_APP_BASE')
  })
})

describe('createAudioPathPattern', () => {
  it('matches only same-app listening and speaking audio paths without a runtime closure', () => {
    const pattern = createAudioPathPattern('/sherlock-api/')
    expect(pattern).toBeInstanceOf(RegExp)
    expect(pattern.test('/sherlock-api/audio/listening/W01D50/q1.mp3')).toBe(true)
    expect(pattern.test('/sherlock-api/audio/speaking/S01D50/q1.mp3')).toBe(true)
    expect(pattern.test('/sherlock-english/audio/listening/W01D50/q1.mp3')).toBe(false)
    expect(pattern.source).not.toContain('appBase')
  })
})
