'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const {
  createFileSpeakingCourseProvider,
  sanitizeSpeakingCourse,
  scoreToStars,
  feedbackForTake,
  signTakeProof,
  verifyTakeProof,
  buildSpeakingResult
} = require('../speaking-service')

function fixtureCourse() {
  return {
    course_id: 'S01D39', title: 'Speaking', week: 5, day: 4,
    course_type: 'training', est_minutes: 10,
    questions: Array.from({ length: 8 }, (_, index) => index < 6
      ? { id: index + 1, type: 'repeat', text: `It is bright ${index + 1}.`, audio: `static/audio/speaking/S01D39/q0${index + 1}.mp3`, tag: 'tag', parent_note: 'note' }
      : { id: index + 1, type: 'qa', question: 'What is it?', expected: 'It is bright.', hint: '用英语说：它很明亮。', audio: `static/audio/speaking/S01D39/q0${index + 1}.mp3`, tag: 'tag' })
  }
}

function take(questionId, attempt, total, overrides = {}) {
  return {
    course_id: 'S01D39', course_version: 'version1', question_id: questionId, attempt,
    data_kind: 'test',
    total, accuracy: total - 2, fluency: total - 1, integrity: total,
    is_rejected: false, words: [{ word: 'bright', score: total }],
    recording_path: `sherlock-english/test/test/S01D39/r1/q${questionId}-take${attempt}.wav`,
    ...overrides
  }
}

describe('P3 speaking service contract', () => {
  it('publishes only child-safe course fields', () => {
    const child = sanitizeSpeakingCourse(fixtureCourse(), 'version1')
    assert.equal(child.questions.length, 8)
    assert.equal(child.questions[0].text, 'It is bright 1.')
    assert.equal(child.questions[6].hint, '用英语说：它很明亮。')
    assert.equal(JSON.stringify(child).includes('expected'), false)
    assert.equal(JSON.stringify(child).includes('parent_note'), false)
    assert.equal(JSON.stringify(child).includes('tag'), false)
    assert.equal(child.questions[0].audio_asset, 'audio/speaking/S01D39/q01.mp3')
  })

  it('keeps thresholds and feedback consistent without numeric child text', () => {
    assert.deepEqual([49, 50, 74, 75].map((value) => scoreToStars(value, false)), [1, 2, 2, 3])
    assert.equal(scoreToStars(99, true), 0)
    const weak = feedbackForTake({ total: 60, is_rejected: false, words: [{ word: 'bright', score: 20 }] })
    assert.deepEqual(weak.weak_words, ['bright'])
    assert.match(weak.child_feedback, /bright/)
    assert.doesNotMatch(weak.child_feedback, /60|分/)
    assert.doesNotMatch(weak.child_feedback, /真棒/)
    assert.match(feedbackForTake({ total: null, is_rejected: true, words: [] }).child_feedback, /没有听清/)
    assert.match(feedbackForTake({ total: 80, is_rejected: false, words: [] }).child_feedback, /真棒/)
    assert.match(feedbackForTake({ total: 60, is_rejected: false, words: [] }).child_feedback, /连贯/)
    const missed = feedbackForTake({ total: 20, is_rejected: false, words: [{ word: 'one', score: 0 }, { word: 'two', score: 20 }, { word: 'three', score: 80 }] })
    assert.deepEqual(missed.word_lights.map((item) => item.light), ['miss', 'weak', 'good'])
  })

  it('signs trusted takes and rejects tampering', () => {
    const original = take(1, 1, 80)
    const proof = signTakeProof(original, '1234567890abcdef')
    assert.equal(verifyTakeProof(proof, '1234567890abcdef').total, 80)
    const parts = proof.split('.')
    parts[3] = `${parts[3].startsWith('A') ? 'B' : 'A'}${parts[3].slice(1)}`
    const tampered = parts.join('.')
    assert.throws(() => verifyTakeProof(tampered, '1234567890abcdef'))
    assert.throws(() => signTakeProof(original, 'short'))
  })

  it('requires every question to satisfy the three-star or third-valid-take gate', () => {
    const course = fixtureCourse()
    const good = signTakeProof(take(1, 1, 80), '1234567890abcdef')
    const low = [1, 2, 3].map((attempt) => signTakeProof(take(2, attempt, 60), '1234567890abcdef'))
    const rest = Array.from({ length: 6 }, (_, index) => ({ id: index + 3, proofs: [signTakeProof(take(index + 3, 1, 80), '1234567890abcdef')], passed_by_safety: false }))
    const result = buildSpeakingResult(course, {
      result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock',
      course_id: 'S01D39', course_version: 'version1', started_at: '2026-08-24T10:00:00.000Z',
      submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
      questions: [{ id: 1, proofs: [good], passed_by_safety: false }, { id: 2, proofs: low, passed_by_safety: true }, ...rest]
    }, 'version1', '1234567890abcdef')
    assert.equal(result.module_type, 'speaking')
    assert.equal(result.data_kind, 'test')
    assert.equal(result.formal_completion_eligible, false)
    assert.equal(result.question_results[0].stars, 3)
    assert.equal(result.question_results[1].passed_by_safety, true)
    assert.deepEqual(result.question_results[1].take_stars, [2, 2, 2])
    assert.equal(result.question_results[1].first_total, 60)
    assert.equal(result.question_results[1].last_total, 60)
    assert.equal(result.question_results[1].best_total, 60)
    assert.throws(() => buildSpeakingResult(course, {
      result_id: 'r2', student_id: 'sherlock', course_id: 'S01D39', course_version: 'version1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z', duration_seconds: 120,
      questions: [{ id: 1, proofs: [good], passed_by_safety: false }, { id: 2, proofs: low.slice(0, 2), passed_by_safety: true }, ...rest]
    }, 'version1', '1234567890abcdef'))
  })

  it('loads the 12 retained speaking courses with six repeat and two QA questions', () => {
    const provider = createFileSpeakingCourseProvider()
    const ids = provider.catalog().map((item) => item.course_id)
    assert.deepEqual(ids, Array.from({ length: 12 }, (_, index) => `S01D${index + 39}`))
    for (const id of ids) {
      const loaded = provider.get(id)
      assert.equal(loaded.course.questions.filter((item) => item.type === 'repeat').length, 6)
      assert.equal(loaded.course.questions.filter((item) => item.type === 'qa').length, 2)
    }
  })
})
