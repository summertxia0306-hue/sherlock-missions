import { describe, expect, it } from 'vitest'
import { addScoredTake, buildSpeakingSubmission, createSpeakingSession, markSafetyPass } from './session'

const response = (stars: 0 | 1 | 2 | 3, proof: string) => ({
  ok: true as const, stars, proof, child_feedback: '再读一次', weak_words: [], word_lights: [],
  can_retry: stars < 3, can_skip: false
})

describe('P3 speaking session gate', () => {
  it('unlocks next only at three stars', () => {
    let state = createSpeakingSession('S01D39', 'r1')
    state = addScoredTake(state, 1, response(2, 'p1'))
    expect(state.questions['1'].complete).toBe(false)
    state = addScoredTake(state, 1, response(3, 'p2'))
    expect(state.questions['1'].complete).toBe(true)
    expect(state.questions['1'].proofs).toEqual(['p1', 'p2'])
  })

  it('offers safety pass only after three valid low takes', () => {
    let state = createSpeakingSession('S01D39', 'r1')
    state = addScoredTake(state, 1, response(1, 'p1'))
    state = addScoredTake(state, 1, response(2, 'p2'))
    expect(() => markSafetyPass(state, 1)).toThrow()
    state = addScoredTake(state, 1, response(2, 'p3'))
    state = markSafetyPass(state, 1)
    expect(state.questions['1'].complete).toBe(true)
    expect(state.questions['1'].passed_by_safety).toBe(true)
  })

  it('builds proof-only test submission without numeric scores', () => {
    let state = createSpeakingSession('S01D39', 'r1', '2026-08-24T10:00:00.000Z')
    for (let id = 1; id <= 8; id += 1) state = addScoredTake(state, id, response(3, `p${id}`))
    const submission = buildSpeakingSubmission(state, 'version1', '2026-08-24T10:02:00.000Z')
    expect(submission.questions).toHaveLength(8)
    expect(JSON.stringify(submission)).not.toMatch(/score|total|accuracy|fluency|integrity/)
    expect(submission.duration_seconds).toBe(120)
  })
})
