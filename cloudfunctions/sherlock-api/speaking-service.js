'use strict'

const crypto = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')

const COURSE_ID = /^(?:S\d{2}D\d{2}|S[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})$/
const AUDIO_PATH = /^static\/audio\/speaking\/(?:S\d{2}D\d{2}|S[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})\/q\d{2}\.mp3$/

function fail() { throw new Error('INVALID_SPEAKING_DATA') }

function stableVersion(course) {
  return crypto.createHash('sha256').update(JSON.stringify(course)).digest('hex').slice(0, 16)
}

function validateCourse(course) {
  if (!course || !COURSE_ID.test(course.course_id) || !Array.isArray(course.questions) || course.questions.length !== 8) fail()
  course.questions.forEach((question, index) => {
    if (question.id !== index + 1 || !['repeat', 'qa'].includes(question.type)
      || !AUDIO_PATH.test(question.audio) || !question.audio.includes(`/${course.course_id}/`)) fail()
    if (question.type === 'repeat' && (typeof question.text !== 'string' || !question.text.trim())) fail()
    if (question.type === 'qa' && (![question.question, question.expected, question.hint].every((value) => typeof value === 'string' && value.trim()))) fail()
  })
  if (course.questions.filter((item) => item.type === 'repeat').length !== 6
    || course.questions.filter((item) => item.type === 'qa').length !== 2) fail()
  return course
}

function sanitizeSpeakingCourse(course, version = stableVersion(course)) {
  validateCourse(course)
  return {
    course_id: course.course_id,
    ...(course.pair_id ? { pair_id: course.pair_id } : {}),
    ...(course.study_pack ? { study_pack: course.study_pack } : {}),
    course_version: version,
    title: String(course.title || course.course_id),
    week: Number(course.week || 0),
    day: Number(course.day || 0),
    course_type: course.course_type === 'weekly_review' ? 'weekly_review' : 'training',
    est_minutes: Number(course.est_minutes || 10),
    questions: course.questions.map((question) => ({
      id: question.id,
      type: question.type,
      ...(question.type === 'repeat' ? { text: question.text } : { hint: question.hint }),
      audio_asset: question.audio.replace(/^static\//, '')
    }))
  }
}

function createFileSpeakingCourseProvider(directory = path.join(__dirname, 'content', 'speaking')) {
  function get(courseId) {
    if (!COURSE_ID.test(courseId)) fail()
    const filename = path.join(directory, `${courseId}.json`)
    const course = validateCourse(JSON.parse(fs.readFileSync(filename, 'utf8')))
    return { course, version: stableVersion(course), child: sanitizeSpeakingCourse(course) }
  }
  return {
    get,
    catalog() {
      return fs.readdirSync(directory).filter((name) => /^(?:S\d{2}D\d{2}|S[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})\.json$/.test(name)).sort()
        .map((name) => {
          const loaded = get(name.slice(0, -5))
          return { course_id: loaded.course.course_id, title: loaded.course.title, course_type: loaded.course.course_type, week: loaded.course.week, day: loaded.course.day, visible: loaded.course.publication_status !== 'test', course_version: loaded.version }
        })
    }
  }
}

function scoreToStars(total, rejected = false) {
  if (rejected || !Number.isFinite(total)) return 0
  if (total >= 75) return 3
  if (total >= 50) return 2
  return 1
}

function wordLights(value) {
  return Array.isArray(value?.words) ? value.words.slice(0, 80).map((entry) => ({
    word: String(entry.word || '').slice(0, 80),
    light: !Number.isFinite(entry.score) || entry.score < 5 ? 'miss' : entry.score < 40 ? 'weak' : 'good'
  })).filter((entry) => entry.word) : []
}

function feedbackForTake(value) {
  const lights = wordLights(value)
  const missed = lights.filter((item) => item.light === 'miss').map((item) => item.word)
  const weak = lights.filter((item) => item.light === 'weak').map((item) => item.word)
  if (value?.is_rejected || !Number.isFinite(value?.total)) {
    return { child_feedback: '好像没有听清。先听一遍示范，再大声读一次吧！', weak_words: [], word_lights: lights }
  }
  if (missed.length || weak.length) {
    const parts = []
    if (missed.length) parts.push(`这些单词没读到：${missed.join('、')}`)
    if (weak.length) parts.push(`这些单词再练一遍：${weak.join('、')}`)
    return { child_feedback: `${parts.join('。')}。再听示范，重录试试！`, weak_words: [...missed, ...weak], word_lights: lights }
  }
  if (scoreToStars(value.total, value.is_rejected) >= 3) {
    return { child_feedback: '读得真棒！每个单词都很清楚！', weak_words: [], word_lights: lights }
  }
  const lowest = (Array.isArray(value.words) ? value.words : []).filter((item) => Number.isFinite(item.score))
    .sort((a, b) => a.score - b.score).slice(0, 2).map((item) => String(item.word))
  return {
    child_feedback: lowest.length ? `还差一点点！把这些单词读得更清楚、更响亮：${lowest.join('、')}。` : '单词都读对了！整句再读得连贯、响亮一点。',
    weak_words: lowest,
    word_lights: lights
  }
}

function proofKey(secret) {
  if (typeof secret !== 'string' || secret.length < 16) fail()
  return crypto.createHash('sha256').update(`speaking-proof:${secret}`).digest()
}

function signTakeProof(value, secret) {
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv('aes-256-gcm', proofKey(secret), iv)
  const body = Buffer.from(JSON.stringify(value), 'utf8')
  const encrypted = Buffer.concat([cipher.update(body), cipher.final()])
  return `v1.${iv.toString('base64url')}.${encrypted.toString('base64url')}.${cipher.getAuthTag().toString('base64url')}`
}

function verifyTakeProof(proof, secret) {
  try {
    const [version, iv, encrypted, tag] = String(proof).split('.')
    if (version !== 'v1' || !iv || !encrypted || !tag) fail()
    const decipher = crypto.createDecipheriv('aes-256-gcm', proofKey(secret), Buffer.from(iv, 'base64url'))
    decipher.setAuthTag(Buffer.from(tag, 'base64url'))
    return JSON.parse(Buffer.concat([decipher.update(Buffer.from(encrypted, 'base64url')), decipher.final()]).toString('utf8'))
  } catch { fail() }
}

function validIso(value) { return typeof value === 'string' && Number.isFinite(Date.parse(value)) }

function buildSpeakingResult(course, submission, expectedVersion, secret, dataKind = 'test') {
  validateCourse(course)
  if (!['formal', 'test'].includes(dataKind)) fail()
  if (!submission || submission.course_id !== course.course_id || submission.course_version !== expectedVersion
    || typeof submission.result_id !== 'string' || submission.result_id.length > 80
    || typeof submission.student_id !== 'string' || !submission.student_id
    || !validIso(submission.started_at) || !validIso(submission.submitted_at)
    || !Number.isInteger(submission.duration_seconds) || submission.duration_seconds < 0 || submission.duration_seconds > 86400
    || !Array.isArray(submission.questions) || submission.questions.length !== course.questions.length) fail()

  const questionResults = course.questions.map((question) => {
    const state = submission.questions.find((item) => item.id === question.id)
    if (!state || !Array.isArray(state.proofs) || state.proofs.length < 1 || state.proofs.length > 3) fail()
    const takes = state.proofs.map((proof, index) => {
      const value = verifyTakeProof(proof, secret)
      if (value.course_id !== course.course_id || value.course_version !== expectedVersion || value.question_id !== question.id || value.attempt !== index + 1 || value.data_kind !== dataKind) fail()
      return value
    })
    const stars = takes.map((item) => scoreToStars(item.total, item.is_rejected))
    const bestIndex = stars.reduce((best, value, index) => value > stars[best] ? index : best, 0)
    const best = takes[bestIndex]
    const achieved = stars[bestIndex] >= 3
    const safety = state.passed_by_safety === true
    if ((!achieved && !(safety && takes.length === 3)) || (achieved && safety)) fail()
    const validScores = takes.filter((item) => Number.isFinite(item.total) && !item.is_rejected)
    const feedback = feedbackForTake(best)
    return {
      id: question.id, type: question.type, text: question.text || question.expected,
      stars: stars[bestIndex], best_total: best.total ?? null,
      first_total: validScores.length ? Math.round(validScores[0].total) : null,
      last_total: validScores.length ? Math.round(validScores.at(-1).total) : null,
      passed_by_safety: safety,
      accuracy: best.accuracy ?? null, fluency: best.fluency ?? null, integrity: best.integrity ?? null,
      take_stars: stars, is_rejected: Boolean(best.is_rejected), takes: takes.length,
      weak_words: feedback.weak_words,
      recordings: takes.map((item) => item.recording_path).filter(Boolean),
      recording_records: takes.filter((item) => item.recording_path).map((item) => ({ path: item.recording_path, file_id: item.recording_file_id || item.recording_path, data_kind: dataKind })),
      tag: question.tag || ''
    }
  })
  const scored = questionResults.filter((item) => Number.isFinite(item.best_total))
  return {
    result_id: submission.result_id, student_id: submission.student_id, module_type: 'speaking', module: 'speaking',
    course_id: course.course_id, data_kind: dataKind, course_version: expectedVersion, status: 'completed',
    ...(course.pair_id ? { pair_id: course.pair_id } : {}),
    ...(course.study_pack ? { study_pack: course.study_pack } : {}),
    score: scored.length ? Math.round(scored.reduce((sum, item) => sum + item.best_total, 0) / scored.length) : 0,
    stars_total: questionResults.reduce((sum, item) => sum + item.stars, 0), stars_max: questionResults.length * 3,
    question_results: questionResults, duration_seconds: submission.duration_seconds,
    started_at: new Date(submission.started_at), submitted_at: new Date(submission.submitted_at),
    section_scores: {}, wrong_answers: [], play_counts: {}, formal_completion_eligible: dataKind === 'formal'
  }
}

module.exports = {
  stableVersion, createFileSpeakingCourseProvider, sanitizeSpeakingCourse, scoreToStars, wordLights,
  feedbackForTake, signTakeProof, verifyTakeProof, buildSpeakingResult
}
