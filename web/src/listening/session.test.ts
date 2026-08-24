import { describe, expect, it } from 'vitest'
import {
  answerQuestion,
  buildListeningSubmission,
  createCorrectionState,
  createListeningSession,
  recordPlay,
  resolveCorrectionResponse
} from './session'

describe('P2 listening session', () => {
  it('persists bounded play counts and shares passage plays', () => {
    let state = createListeningSession('W01D39', 'result-123', '2026-08-24T10:00:00.000Z')
    state = recordPlay(state, '1', 2)
    state = recordPlay(state, '1', 2)
    state = recordPlay(state, '1', 2)
    state = recordPlay(state, 'passage', 2)
    expect(state.play_counts).toEqual({ '1': 2, passage: 1 })
  })

  it('builds a stable idempotent submission without scores or answers keys', () => {
    let state = createListeningSession('W01D39', 'result-123', '2026-08-24T10:00:00.000Z')
    state = answerQuestion(state, 1, 0)
    state = answerQuestion(state, 2, 'same')
    const submission = buildListeningSubmission(state, 'v1', '2026-08-24T10:02:00.000Z', { platform: 'iPad' })
    expect(submission.result_id).toBe('result-123')
    expect(submission.answers).toEqual({ '1': 0, '2': 'same' })
    expect(submission.duration_seconds).toBe(120)
    expect(submission).not.toHaveProperty('score')
  })

  it('implements blind first correction and transcript-only second correction', () => {
    const initial = createCorrectionState([3])
    const retry = resolveCorrectionResponse(initial, { correct: false, reveal_transcript: ['Hello.'] })
    expect(retry.phase).toBe('try2')
    expect(retry.transcript).toEqual(['Hello.'])
    const done = resolveCorrectionResponse(retry, { correct: true })
    expect(done.log).toEqual({ '3': '✓²' })
    expect(done.phase).toBe('done')
  })
})
