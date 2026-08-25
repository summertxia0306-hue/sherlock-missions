import { z } from 'zod'

const audioSchema = z.string().regex(/^audio\/speaking\/S01D(?:39|4\d|50)\/q\d{2}\.mp3$/)
const repeatSchema = z.object({
  id: z.number().int().min(1).max(8), type: z.literal('repeat'), text: z.string().min(1).max(500), audio_asset: audioSchema
}).strict()
const qaSchema = z.object({
  id: z.number().int().min(1).max(8), type: z.literal('qa'), hint: z.string().min(1).max(500), audio_asset: audioSchema
}).strict()

export const speakingQuestionSchema = z.discriminatedUnion('type', [repeatSchema, qaSchema])
export const speakingCourseSchema = z.object({
  course_id: z.string().regex(/^S01D(?:39|4\d|50)$/), course_version: z.string().min(8).max(64),
  title: z.string().min(1).max(160), week: z.number().int().positive(), day: z.number().int().positive(),
  course_type: z.enum(['training', 'weekly_review']), est_minutes: z.number().int().positive().max(60),
  questions: z.array(speakingQuestionSchema).length(8)
}).strict().superRefine((course, context) => {
  if (course.questions.some((item, index) => item.id !== index + 1)
    || course.questions.filter((item) => item.type === 'repeat').length !== 6
    || course.questions.filter((item) => item.type === 'qa').length !== 2) {
    context.addIssue({ code: 'custom', message: 'speaking question sequence must be 6 repeat + 2 qa' })
  }
  if (course.questions.some((item) => !item.audio_asset.includes(`/${course.course_id}/`))) {
    context.addIssue({ code: 'custom', message: 'audio must belong to course' })
  }
})

export type SpeakingCourse = z.infer<typeof speakingCourseSchema>
export type SpeakingQuestion = z.infer<typeof speakingQuestionSchema>

const catalogEntrySchema = z.object({
  course_id: z.string().regex(/^S01D(?:39|4\d|50)$/), course_version: z.string().min(1).max(64),
  title: z.string().min(1).max(160), course_type: z.enum(['training', 'weekly_review']),
  week: z.number().int().positive(), day: z.number().int().positive(), visible: z.boolean()
}).strict()
export type SpeakingCatalogEntry = z.infer<typeof catalogEntrySchema>
export interface SpeakingCatalog {
  courses: readonly SpeakingCatalogEntry[]
  firstFormalIncomplete(completed: ReadonlySet<string>): SpeakingCatalogEntry | undefined
  window(completed: ReadonlySet<string>, limit?: number): SpeakingCatalogEntry[]
}

export function parseSpeakingCourse(input: unknown): SpeakingCourse { return speakingCourseSchema.parse(input) }

export function parseSpeakingCatalog(input: unknown): SpeakingCatalog {
  const courses = z.array(catalogEntrySchema).parse(input).filter((item) => item.visible).sort((a, b) => a.course_id.localeCompare(b.course_id))
  return {
    courses,
    firstFormalIncomplete: (completed) => courses.find((item) => !completed.has(item.course_id)),
    window(completed, limit = 5) {
      if (limit < 1) return []
      const incomplete = courses.findIndex((item) => !completed.has(item.course_id))
      const anchor = incomplete < 0 ? Math.max(0, courses.length - 1) : incomplete
      const start = Math.min(Math.max(0, anchor - Math.min(2, anchor)), Math.max(0, courses.length - limit))
      return courses.slice(start, start + limit)
    }
  }
}

export function resolveSpeakingAudioUrl(asset: string, base = import.meta.env.BASE_URL): string {
  const parsed = audioSchema.parse(asset)
  return `/${base.split('/').filter(Boolean).join('/')}/${parsed}`
}

export async function loadSpeakingCatalog(fetcher: typeof fetch = fetch): Promise<SpeakingCatalog> {
  const response = await fetcher(`${import.meta.env.BASE_URL}content/speaking/catalog.json?fresh=${Date.now()}`, { cache: 'no-store' })
  if (!response.ok) throw new Error('SPEAKING_CATALOG_UNAVAILABLE')
  return parseSpeakingCatalog(await response.json())
}

export async function loadSpeakingCourse(courseId: string, fetcher: typeof fetch = fetch): Promise<SpeakingCourse> {
  if (!/^S01D(?:39|4\d|50)$/.test(courseId)) throw new Error('INVALID_COURSE_ID')
  const response = await fetcher(`${import.meta.env.BASE_URL}content/speaking/${courseId}.json?fresh=${Date.now()}`, { cache: 'no-store' })
  if (!response.ok) throw new Error('SPEAKING_COURSE_UNAVAILABLE')
  return parseSpeakingCourse(await response.json())
}
