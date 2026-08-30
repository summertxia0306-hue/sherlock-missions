import { describe, expect, it } from 'vitest'
import { courseOrder, isCourseId, isPairId } from './course-id'

describe('legacy and term course identifiers', () => {
  it('accepts retained summer ids and the approved 4A term ids', () => {
    expect(isCourseId('W01D50', 'listening')).toBe(true)
    expect(isCourseId('S01D50', 'speaking')).toBe(true)
    expect(isCourseId('L4A-T1-W01-D01', 'listening')).toBe(true)
    expect(isCourseId('S4A-T1-W01-D06', 'speaking')).toBe(true)
    expect(isPairId('4A-T1-W01-D06')).toBe(true)
  })

  it('rejects cross-module and malformed ids', () => {
    expect(isCourseId('S4A-T1-W01-D01', 'listening')).toBe(false)
    expect(isCourseId('L4A-T1-W01-D01', 'speaking')).toBe(false)
    expect(isCourseId('../L4A-T1-W01-D01', 'listening')).toBe(false)
    expect(isPairId('L4A-T1-W01-D01')).toBe(false)
  })

  it('orders the new term after retained summer courses', () => {
    const ids = ['L4A-T1-W01-D02', 'W01D50', 'L4A-T1-W01-D01', 'W01D49']
    expect(ids.sort(courseOrder)).toEqual(['W01D49', 'W01D50', 'L4A-T1-W01-D01', 'L4A-T1-W01-D02'])
  })
})
