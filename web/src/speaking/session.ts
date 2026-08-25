import type { SpeakingScoreResponse, SpeakingSubmission } from '../core/cloudbase-api'

export interface SpeakingQuestionState {
  proofs: string[]
  take_stars: Array<0 | 1 | 2 | 3>
  stars: 0 | 1 | 2 | 3
  child_feedback: string
  weak_words: string[]
  word_lights: Array<{ word: string; light: 'good' | 'weak' | 'miss' }>
  complete: boolean
  passed_by_safety: boolean
}

export interface SpeakingSession {
  course_id: string
  result_id: string
  started_at: string
  questions: Record<string, SpeakingQuestionState>
}

export function createSpeakingSession(courseId: string, resultId: string, startedAt = new Date().toISOString()): SpeakingSession {
  return { course_id: courseId, result_id: resultId, started_at: startedAt, questions: {} }
}

export function addScoredTake(state: SpeakingSession, questionId: number, response: SpeakingScoreResponse): SpeakingSession {
  const current = state.questions[String(questionId)] || { proofs: [], take_stars: [], stars: 0, child_feedback: '', weak_words: [], word_lights: [], complete: false, passed_by_safety: false }
  if (current.complete || current.proofs.length >= 3) throw new Error('SPEAKING_GATE_CLOSED')
  const next: SpeakingQuestionState = {
    proofs: [...current.proofs, response.proof], take_stars: [...current.take_stars, response.stars],
    stars: Math.max(current.stars, response.stars) as 0 | 1 | 2 | 3,
    child_feedback: response.child_feedback, weak_words: [...response.weak_words], word_lights: [...response.word_lights],
    complete: current.stars === 3 || response.stars === 3, passed_by_safety: false
  }
  return { ...state, questions: { ...state.questions, [String(questionId)]: next } }
}

export function markSafetyPass(state: SpeakingSession, questionId: number): SpeakingSession {
  const current = state.questions[String(questionId)]
  if (!current || current.complete || current.proofs.length !== 3 || current.stars === 3) throw new Error('SPEAKING_SAFETY_NOT_AVAILABLE')
  return { ...state, questions: { ...state.questions, [String(questionId)]: { ...current, complete: true, passed_by_safety: true } } }
}

export function buildSpeakingSubmission(state: SpeakingSession, version: string, submittedAt = new Date().toISOString()): SpeakingSubmission {
  const questions = Array.from({ length: 8 }, (_, index) => {
    const entry = state.questions[String(index + 1)]
    if (!entry?.complete) throw new Error('SPEAKING_INCOMPLETE')
    return { id: index + 1, proofs: [...entry.proofs], passed_by_safety: entry.passed_by_safety }
  })
  const duration = Math.max(0, Math.min(86400, Math.floor((Date.parse(submittedAt) - Date.parse(state.started_at)) / 1000)))
  return {
    result_id: state.result_id, student_id: 'sherlock', course_id: state.course_id, course_version: version,
    started_at: state.started_at, submitted_at: submittedAt, duration_seconds: Number.isFinite(duration) ? duration : 0, questions
  }
}
