'use strict'

const crypto = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')

const COURSE_ID = /^(?:W\d{2}D\d{2}|L[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})$/
const RESULT_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const CHOICE_TYPES = new Set(['word_choice', 'question_response', 'dialogue_choice'])

function assetPath(repoPath) {
  if (typeof repoPath !== 'string' || !/^static\/audio\/listening\/(?:W\d{2}D\d{2}|L[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})\/(?:hello|q\d{2}|p\d{2})\.mp3$/.test(repoPath)) {
    throw new Error('INVALID_AUDIO_ASSET')
  }
  return repoPath.replace(/^static\//, '')
}

function sanitizeCourse(course, manifestCourse, version) {
  function checkedAsset(repoPath) {
    if (!Object.prototype.hasOwnProperty.call(manifestCourse, repoPath)) throw new Error('AUDIO_NOT_IN_MANIFEST')
    return assetPath(repoPath)
  }
  return {
    course_id: course.course_id,
    ...(course.pair_id ? { pair_id: course.pair_id } : {}),
    ...(course.study_pack ? { study_pack: course.study_pack } : {}),
    course_version: version,
    title: course.title,
    week: course.week,
    day: course.day,
    course_type: course.course_type,
    est_minutes: course.est_minutes || 20,
    test_audio_asset: checkedAsset(course.test_audio),
    sections: course.sections.map((section) => ({
      id: section.id,
      name: section.name,
      tip: section.tip,
      max_plays: section.max_plays,
      ...(section.shared_audio ? {
        shared_audio: true,
        passage_audio_asset: checkedAsset(section.passage_audio)
      } : {}),
      questions: section.questions.map((question) => ({
        id: question.id,
        type: question.type,
        ...(question.options ? { options: question.options } : {}),
        ...(question.display ? { display: question.display } : {}),
        ...(question.statement ? { statement: question.statement } : {}),
        ...(question.question_text ? { question_text: question.question_text } : {}),
        ...(!section.shared_audio ? { audio_asset: checkedAsset(question.audio) } : {})
      }))
    }))
  }
}

function pickLabel(question, pick) {
  if (pick === undefined || pick === null) return '未答'
  if (CHOICE_TYPES.has(question.type)) return Number.isInteger(pick) ? String.fromCharCode(65 + pick) : String(pick)
  if (question.type === 'sentence_judge') return pick === 'same' ? '√' : '×'
  return pick === 'true' ? '√' : '×'
}

function validateSubmission(course, submission, version) {
  if (!submission || !RESULT_ID.test(submission.result_id) || submission.course_id !== course.course_id
    || submission.course_version !== version || typeof submission.student_id !== 'string' || submission.student_id.length < 1
    || !Number.isFinite(Date.parse(submission.started_at)) || !Number.isFinite(Date.parse(submission.submitted_at))
    || !Number.isInteger(submission.duration_seconds) || submission.duration_seconds < 0 || submission.duration_seconds > 86400
    || !submission.answers || typeof submission.answers !== 'object' || Array.isArray(submission.answers)
    || !submission.play_counts || typeof submission.play_counts !== 'object' || Array.isArray(submission.play_counts)) {
    throw new Error('INVALID_LISTENING_RESULT')
  }
}

function scoreListeningSubmission(course, submission, version, dataKind = 'test') {
  validateSubmission(course, submission, version)
  if (!['formal', 'test'].includes(dataKind)) throw new Error('INVALID_LISTENING_RESULT')
  if (submission.student_id !== 'sherlock') throw new Error('INVALID_LISTENING_RESULT')
  const per = course.scoring.per_question
  const sectionScores = {}
  const wrongAnswers = []
  const questionResults = []
  for (const section of course.sections) {
    sectionScores[section.id] = 0
    for (const question of section.questions) {
      const pick = submission.answers[String(question.id)]
      const validPick = CHOICE_TYPES.has(question.type)
        ? Number.isInteger(pick) && pick >= 0 && pick < question.options.length
        : question.type === 'sentence_judge'
          ? pick === 'same' || pick === 'different'
          : pick === 'true' || pick === 'false'
      const playValue = Number(submission.play_counts[section.shared_audio ? section.id : String(question.id)] || 0)
      if (!validPick || !Number.isInteger(playValue) || playValue < 0 || playValue > section.max_plays) {
        throw new Error('INVALID_LISTENING_RESULT')
      }
      const correct = pick === question.answer
      if (correct) sectionScores[section.id] += per
      const playKey = section.shared_audio ? section.id : String(question.id)
      const detail = {
        id: question.id,
        section: section.id,
        type: question.type,
        picked: pickLabel(question, pick),
        correct: pickLabel(question, question.answer),
        is_correct: correct,
        play_count: playValue
      }
      questionResults.push(detail)
      if (!correct) wrongAnswers.push({ ...detail, tag: question.tag })
    }
  }
  return {
    result_id: submission.result_id,
    student_id: submission.student_id,
    module_type: 'listening',
    course_id: course.course_id,
    ...(course.pair_id ? { pair_id: course.pair_id } : {}),
    ...(course.study_pack ? { study_pack: course.study_pack } : {}),
    data_kind: dataKind,
    course_version: version,
    started_at: new Date(submission.started_at),
    submitted_at: new Date(submission.submitted_at),
    duration_seconds: submission.duration_seconds,
    device_info: submission.device_info || {},
    status: 'completed',
    score: Object.values(sectionScores).reduce((sum, value) => sum + value, 0),
    section_scores: sectionScores,
    wrong_answers: wrongAnswers,
    play_counts: submission.play_counts,
    corrections: {},
    question_results: questionResults,
    formal_completion_eligible: dataKind === 'formal'
  }
}

function courseVersion(raw) {
  return crypto.createHash('sha256').update(raw).digest('hex').slice(0, 16)
}

function createFileCourseProvider(root = path.join(__dirname, 'content', 'listening')) {
  return {
    get(courseId) {
      if (!COURSE_ID.test(courseId)) throw new Error('COURSE_NOT_FOUND')
      const file = path.join(root, `${courseId}.json`)
      const raw = fs.readFileSync(file)
      return { course: JSON.parse(raw.toString('utf8')), version: courseVersion(raw) }
    }
  }
}

module.exports = { createFileCourseProvider, sanitizeCourse, scoreListeningSubmission }
