'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createFileCourseProvider, scoreListeningSubmission, sanitizeCourse } = require('../listening-service')

function course() {
  return {
    course_id: 'W01D39', title: 'Course', week: 5, day: 4, course_type: 'training', est_minutes: 20,
    scoring: { per_question: 5, total: 10 }, test_audio: 'static/audio/listening/W01D39/hello.mp3',
    test_transcript: [['n', 'hello']],
    sections: [
      { id: 'word_discrimination', name: 'Words', tip: 'Listen', max_plays: 2, questions: [
        { id: 1, type: 'word_choice', options: ['one', 'two'], answer: 0, transcript: [['n', 'one']], audio: 'static/audio/listening/W01D39/q01.mp3', tag: 'secret' }
      ] },
      { id: 'passage', name: 'Passage', tip: 'Listen', max_plays: 2, shared_audio: true,
        passage_audio: 'static/audio/listening/W01D39/p01.mp3', passage_transcript: [['n', 'Story']], questions: [
          { id: 2, type: 'passage_judge', statement: 'True.', answer: 'true', tag: 'secret' }
        ] }
    ]
  }
}

describe('P2 listening service', () => {
  it('sanitizes every child course field and derives audio from the manifest', () => {
    const child = sanitizeCourse(course(), {
      'static/audio/listening/W01D39/hello.mp3': 'hash1',
      'static/audio/listening/W01D39/q01.mp3': 'hash2',
      'static/audio/listening/W01D39/p01.mp3': 'hash3'
    }, 'version1')
    assert.equal(child.test_audio_asset, 'audio/listening/W01D39/hello.mp3')
    assert.equal(child.sections[0].questions[0].audio_asset, 'audio/listening/W01D39/q01.mp3')
    assert.doesNotMatch(JSON.stringify(child), /answer|transcript|parent_note|tag/)
  })

  it('scores all five question contracts on the server and returns parent details', () => {
    const result = scoreListeningSubmission(course(), {
      result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock',
      course_id: 'W01D39', course_version: 'version1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z',
      duration_seconds: 120, answers: { '1': 0, '2': 'false' }, play_counts: { '1': 2, passage: 1 }
    }, 'version1')
    assert.equal(result.score, 5)
    assert.deepEqual(result.section_scores, { word_discrimination: 5, passage: 0 })
    assert.deepEqual(result.wrong_answers.map((item) => item.id), [2])
    assert.equal(result.question_results.length, 2)
    assert.equal(result.data_kind, 'test')
    assert.equal(result.formal_completion_eligible, false)
  })

  it('scores all 12 retained courses and all five question types from generated source copies', () => {
    const provider = createFileCourseProvider()
    for (let number = 39; number <= 50; number += 1) {
      const courseId = `W01D${number}`
      const { course: loaded, version } = provider.get(courseId)
      const answers = {}
      const playCounts = {}
      const types = new Set()
      for (const section of loaded.sections) {
        if (section.shared_audio) playCounts[section.id] = 1
        for (const question of section.questions) {
          answers[String(question.id)] = question.answer
          types.add(question.type)
          if (!section.shared_audio) playCounts[String(question.id)] = 1
        }
      }
      const result = scoreListeningSubmission(loaded, {
        result_id: `123e4567-e89b-42d3-a456-4266141740${String(number - 39).padStart(2, '0')}`,
        student_id: 'sherlock', course_id: courseId, course_version: version,
        started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z',
        duration_seconds: 120, answers, play_counts: playCounts
      }, version)
      assert.equal(result.score, 100)
      assert.equal(result.question_results.length, 20)
      assert.deepEqual([...types].sort(), ['dialogue_choice', 'passage_judge', 'question_response', 'sentence_judge', 'word_choice'])
    }
  })

  it('rejects incomplete answers and forged play counts', () => {
    const input = {
      result_id: '123e4567-e89b-42d3-a456-426614174000', student_id: 'sherlock',
      course_id: 'W01D39', course_version: 'version1',
      started_at: '2026-08-24T10:00:00.000Z', submitted_at: '2026-08-24T10:02:00.000Z',
      duration_seconds: 120, answers: { '1': 0 }, play_counts: { '1': 99 }
    }
    assert.throws(() => scoreListeningSubmission(course(), input, 'version1'), /INVALID_LISTENING_RESULT/)
  })
})
