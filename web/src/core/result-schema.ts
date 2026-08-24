import { z } from 'zod'

const jsonPayloadSchema = z.record(z.string(), z.unknown()).refine(
  (value) => new TextEncoder().encode(JSON.stringify(value)).byteLength <= 64 * 1024,
  '结果 payload 超过 64 KiB'
)

export const resultSubmissionSchema = z.object({
  student_id: z.string().min(1).max(80),
  module_type: z.enum(['listening', 'speaking', 'vocabulary']),
  course_id: z.string().min(1).max(80),
  pair_id: z.string().min(1).max(80).optional(),
  data_kind: z.enum(['formal', 'test']).optional(),
  course_version: z.string().min(1).max(40),
  started_at: z.iso.datetime(),
  submitted_at: z.iso.datetime(),
  duration_seconds: z.number().int().min(0).max(86_400),
  device_info: z.record(z.string(), z.unknown()).optional(),
  payload: jsonPayloadSchema
}).strict()

export type ResultSubmission = z.infer<typeof resultSubmissionSchema>

