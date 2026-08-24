import { z } from 'zod'

const courseSchema = z.object({
  course_id: z.string().min(1).max(80),
  module_type: z.enum(['listening', 'speaking', 'vocabulary']),
  title: z.string().min(1).max(120),
  visible: z.boolean().default(true)
}).strict()

export type CourseSummary = z.infer<typeof courseSchema>

export function parseCatalog(input: unknown): CourseSummary[] {
  return z.array(courseSchema).parse(input)
}

export function firstFormalIncomplete(
  courses: readonly CourseSummary[],
  formalCompletedCourseIds: ReadonlySet<string>
): CourseSummary | undefined {
  return courses.find((course) => course.visible && !formalCompletedCourseIds.has(course.course_id))
}

