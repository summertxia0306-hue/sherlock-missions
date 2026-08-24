import { describe, expect, it } from 'vitest'
import { resultSubmissionSchema } from './result-schema'

describe('result submission contract', () => {
  it('accepts a bounded test payload', () => {
    const parsed = resultSubmissionSchema.parse({
      student_id: 'sherlock',
      module_type: 'listening',
      course_id: 'W01D39',
      course_version: '1',
      started_at: '2026-08-24T10:00:00.000Z',
      submitted_at: '2026-08-24T10:02:00.000Z',
      duration_seconds: 120,
      data_kind: 'formal',
      payload: { score: 12 }
    })
    expect(parsed.data_kind).toBe('formal')
  })

  it('rejects oversized payloads and unknown modules', () => {
    expect(() => resultSubmissionSchema.parse({
      student_id: 'sherlock',
      module_type: 'admin',
      course_id: 'bad',
      course_version: '1',
      started_at: 'x',
      submitted_at: 'x',
      duration_seconds: -1,
      payload: {}
    })).toThrow()
  })
})

