export type CourseModule = 'listening' | 'speaking'

const legacyListening = /^W\d{2}D\d{2}$/
const legacySpeaking = /^S\d{2}D\d{2}$/
const termPair = /^[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2}$/

export function isPairId(value: string): boolean {
  return termPair.test(value)
}

export function isCourseId(value: string, module: CourseModule): boolean {
  if (module === 'listening') return legacyListening.test(value) || (value.startsWith('L') && isPairId(value.slice(1)))
  return legacySpeaking.test(value) || (value.startsWith('S') && isPairId(value.slice(1)))
}

export function pairIdForCourse(value: string): string | undefined {
  const pair = value.slice(1)
  return isPairId(pair) && /^[LS]/.test(value) ? pair : undefined
}

export function courseOrder(left: string, right: string): number {
  const leftTerm = left.includes('-')
  const rightTerm = right.includes('-')
  if (leftTerm !== rightTerm) return leftTerm ? 1 : -1
  return left.localeCompare(right)
}
