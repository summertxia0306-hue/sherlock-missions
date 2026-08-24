export type ListeningPick = number | 'same' | 'different' | 'true' | 'false'

export interface ListeningSession {
  course_id: string
  result_id: string
  started_at: string
  answers: Record<string, ListeningPick>
  play_counts: Record<string, number>
}

export function createListeningSession(courseId: string, resultId: string, startedAt = new Date().toISOString()): ListeningSession {
  return { course_id: courseId, result_id: resultId, started_at: startedAt, answers: {}, play_counts: {} }
}

export function recordPlay(state: ListeningSession, key: string, maxPlays: number): ListeningSession {
  const current = state.play_counts[key] || 0
  if (current >= maxPlays) return state
  return { ...state, play_counts: { ...state.play_counts, [key]: current + 1 } }
}

export function answerQuestion(state: ListeningSession, questionId: number, pick: ListeningPick): ListeningSession {
  return { ...state, answers: { ...state.answers, [String(questionId)]: pick } }
}

export interface ListeningSubmission {
  result_id: string
  student_id: string
  course_id: string
  course_version: string
  started_at: string
  submitted_at: string
  duration_seconds: number
  answers: Record<string, ListeningPick>
  play_counts: Record<string, number>
  device_info: Record<string, unknown>
}

export function buildListeningSubmission(
  state: ListeningSession,
  courseVersion: string,
  submittedAt = new Date().toISOString(),
  deviceInfo: Record<string, unknown> = {}
): ListeningSubmission {
  const duration = Math.max(0, Math.min(86_400, Math.floor((Date.parse(submittedAt) - Date.parse(state.started_at)) / 1000)))
  return {
    result_id: state.result_id,
    student_id: 'sherlock',
    course_id: state.course_id,
    course_version: courseVersion,
    started_at: state.started_at,
    submitted_at: submittedAt,
    duration_seconds: Number.isFinite(duration) ? duration : 0,
    answers: { ...state.answers },
    play_counts: { ...state.play_counts },
    device_info: deviceInfo
  }
}

export interface CorrectionState {
  queue: number[]
  index: number
  phase: 'try1' | 'try2' | 'done'
  transcript?: string[]
  log: Record<string, '✓' | '✓²' | '✗'>
}

export function createCorrectionState(wrongIds: number[]): CorrectionState {
  return { queue: [...wrongIds], index: 0, phase: wrongIds.length ? 'try1' : 'done', log: {} }
}

export function resolveCorrectionResponse(
  state: CorrectionState,
  response: { correct: boolean; reveal_transcript?: string[] }
): CorrectionState {
  if (state.phase === 'done') return state
  const questionId = state.queue[state.index]
  if (state.phase === 'try1' && !response.correct) {
    return { ...state, phase: 'try2', transcript: response.reveal_transcript || [] }
  }
  const marker = state.phase === 'try1' ? '✓' : (response.correct ? '✓²' : '✗')
  const nextIndex = state.index + 1
  return {
    ...state,
    index: nextIndex,
    phase: nextIndex >= state.queue.length ? 'done' : 'try1',
    transcript: undefined,
    log: { ...state.log, [String(questionId)]: marker }
  }
}
