import { describe, expect, it } from 'vitest'
import { firstFormalIncomplete, parseCatalog } from './course-catalog'

describe('course catalog', () => {
  const catalog = parseCatalog([
    { course_id: 'W01D39', module_type: 'listening', title: 'Listening 39', visible: true },
    { course_id: 'W01D40', module_type: 'listening', title: 'Listening 40', visible: true },
    { course_id: 'W01D41', module_type: 'listening', title: 'Listening 41', visible: false }
  ])

  it('finds the first visible course missing from formal completion only', () => {
    expect(firstFormalIncomplete(catalog, new Set(['W01D39']))?.course_id).toBe('W01D40')
  })

  it('ignores test completion ids when the formal set is empty', () => {
    expect(firstFormalIncomplete(catalog, new Set())?.course_id).toBe('W01D39')
  })

  it('rejects invalid course data', () => {
    expect(() => parseCatalog([{ course_id: '', module_type: 'unknown' }])).toThrow()
  })
})

