import { z } from 'zod'
import { courseOrder, isCourseId, isPairId, pairIdForCourse } from '../core/course-id'

const listeningIdSchema = z.string().refine((value) => isCourseId(value, 'listening'), 'invalid listening course id')
const pairIdSchema = z.string().refine(isPairId, 'invalid study pair id')
const audioAssetSchema = z.string().refine((value) => {
  const match = /^audio\/listening\/([^/]+)\/(?:hello|q\d{2}|p\d{2})\.mp3$/.exec(value)
  return Boolean(match && isCourseId(match[1], 'listening'))
}, 'invalid listening audio asset')

const choiceQuestionSchema = z.object({
  id: z.number().int().positive(),
  type: z.enum(['word_choice', 'question_response', 'dialogue_choice']),
  options: z.array(z.string().min(1)).min(2).max(6),
  audio_asset: audioAssetSchema,
  question_text: z.string().min(1).optional()
}).strict()

const sentenceQuestionSchema = z.object({
  id: z.number().int().positive(),
  type: z.literal('sentence_judge'),
  display: z.string().min(1),
  audio_asset: audioAssetSchema
}).strict()

const passageQuestionSchema = z.object({
  id: z.number().int().positive(),
  type: z.literal('passage_judge'),
  statement: z.string().min(1)
}).strict()

export const listeningQuestionSchema = z.discriminatedUnion('type', [
  choiceQuestionSchema,
  sentenceQuestionSchema,
  passageQuestionSchema
])

const sectionSchema = z.object({
  id: z.string().min(1).max(80),
  name: z.string().min(1).max(120),
  tip: z.string().min(1).max(240),
  max_plays: z.number().int().min(1).max(9),
  shared_audio: z.boolean().optional(),
  passage_audio_asset: audioAssetSchema.optional(),
  questions: z.array(listeningQuestionSchema).min(1)
}).strict().superRefine((section, context) => {
  if (section.shared_audio && !section.passage_audio_asset) {
    context.addIssue({ code: 'custom', message: 'shared audio section needs passage_audio_asset' })
  }
  if (section.questions.some((question) => question.type === 'passage_judge') !== Boolean(section.shared_audio)) {
    context.addIssue({ code: 'custom', message: 'passage questions must use a shared audio section' })
  }
})

export const listeningCourseSchema = z.object({
  course_id: listeningIdSchema,
  pair_id: pairIdSchema.optional(),
  study_pack: pairIdSchema.optional(),
  course_version: z.string().min(8).max(64),
  title: z.string().min(1).max(160),
  week: z.number().int().positive(),
  day: z.number().int().positive(),
  course_type: z.enum(['diagnostic', 'training', 'weekly_test']),
  est_minutes: z.number().int().positive().max(120).default(20),
  test_audio_asset: audioAssetSchema,
  sections: z.array(sectionSchema).length(5)
}).strict().superRefine((course, context) => {
  const expected = pairIdForCourse(course.course_id)
  if (expected && (course.pair_id !== expected || course.study_pack !== expected)) {
    context.addIssue({ code: 'custom', message: 'term course must match pair_id and study_pack' })
  }
})

export type ListeningCourse = z.infer<typeof listeningCourseSchema>
export type ListeningQuestion = z.infer<typeof listeningQuestionSchema>

const catalogEntrySchema = z.object({
  course_id: listeningIdSchema,
  pair_id: pairIdSchema.optional(),
  study_pack: pairIdSchema.optional(),
  course_version: z.string().min(1).max(64),
  title: z.string().min(1).max(160),
  course_type: z.enum(['diagnostic', 'training', 'weekly_test']),
  week: z.number().int().positive(),
  day: z.number().int().positive(),
  visible: z.boolean()
}).strict()

export type ListeningCatalogEntry = z.infer<typeof catalogEntrySchema>

export interface ListeningCatalog {
  courses: readonly ListeningCatalogEntry[]
  testCourses(): ListeningCatalogEntry[]
  firstFormalIncomplete(formalCompleted: ReadonlySet<string>): ListeningCatalogEntry | undefined
  window(formalCompleted: ReadonlySet<string>, limit?: number): ListeningCatalogEntry[]
}

export function parseListeningCourse(input: unknown): ListeningCourse {
  return listeningCourseSchema.parse(input)
}

export function parseListeningCatalog(input: unknown): ListeningCatalog {
  const allCourses = z.array(catalogEntrySchema).parse(input)
    .sort((left, right) => courseOrder(left.course_id, right.course_id))
  const courses = allCourses.filter((course) => course.visible)
  return {
    courses,
    testCourses: () => [...allCourses],
    firstFormalIncomplete(formalCompleted) {
      return courses.find((course) => !formalCompleted.has(course.course_id))
    },
    window(formalCompleted, limit = 5) {
      if (limit < 1) return []
      const incompleteIndex = courses.findIndex((course) => !formalCompleted.has(course.course_id))
      const anchor = incompleteIndex < 0 ? Math.max(0, courses.length - 1) : incompleteIndex
      const before = Math.min(2, anchor)
      const start = Math.min(Math.max(0, anchor - before), Math.max(0, courses.length - limit))
      return courses.slice(start, start + limit)
    }
  }
}

export function resolveAudioUrl(asset: string, base = import.meta.env.BASE_URL): string {
  const parsed = audioAssetSchema.parse(asset)
  const safeBase = `/${base.split('/').filter(Boolean).join('/')}/`
  return `${safeBase}${parsed}`
}

export async function loadListeningCatalog(fetcher: typeof fetch = fetch): Promise<ListeningCatalog> {
  const response = await fetcher(`${import.meta.env.BASE_URL}content/listening/catalog.json`)
  if (!response.ok) throw new Error('LISTENING_CATALOG_UNAVAILABLE')
  return parseListeningCatalog(await response.json())
}

export async function loadListeningCourse(courseId: string, fetcher: typeof fetch = fetch): Promise<ListeningCourse> {
  if (!isCourseId(courseId, 'listening')) throw new Error('INVALID_COURSE_ID')
  const response = await fetcher(`${import.meta.env.BASE_URL}content/listening/${courseId}.json`)
  if (!response.ok) throw new Error('LISTENING_COURSE_UNAVAILABLE')
  return parseListeningCourse(await response.json())
}
