import { describe, expect, it, vi } from 'vitest'
import { loadSpeakingCatalog, loadSpeakingCourse, parseSpeakingCatalog, parseSpeakingCourse, resolveSpeakingAudioUrl } from './course'

const course = {
  course_id: 'S01D39', course_version: '12345678', title: '口语训练', week: 5, day: 4,
  course_type: 'training', est_minutes: 10,
  questions: Array.from({ length: 8 }, (_, index) => index < 6
    ? { id: index + 1, type: 'repeat', text: `Sentence ${index + 1}.`, audio_asset: `audio/speaking/S01D39/q0${index + 1}.mp3` }
    : { id: index + 1, type: 'qa', hint: '用英语说：答案。', audio_asset: `audio/speaking/S01D39/q0${index + 1}.mp3` })
}

describe('P3 speaking child course contract', () => {
  it('accepts six repeat plus two QA prompts without target answers or tags', () => {
    const parsed = parseSpeakingCourse(course)
    expect(parsed.questions.filter((item) => item.type === 'repeat')).toHaveLength(6)
    expect(parsed.questions.filter((item) => item.type === 'qa')).toHaveLength(2)
    expect(JSON.stringify(parsed)).not.toMatch(/"expected"|"question"|"parent_note"|"tag"/)
  })

  it('rejects leaked scoring or parent fields', () => {
    for (const key of ['expected', 'question', 'tag', 'parent_note', 'score']) {
      const leaked = structuredClone(course) as typeof course & { questions: Array<Record<string, unknown>> }
      leaked.questions[0][key] = 'secret'
      expect(() => parseSpeakingCourse(leaked)).toThrow()
    }
  })

  it('keeps the same bounded five-course window policy as listening', () => {
    const catalog = parseSpeakingCatalog(Array.from({ length: 12 }, (_, index) => ({
      course_id: `S01D${index + 39}`, course_version: `version${index}`, title: 'Course',
      course_type: 'training', week: 6, day: index + 1, visible: true
    })))
    expect(catalog.window(new Set(), 5).map((item) => item.course_id)).toEqual(['S01D39', 'S01D40', 'S01D41', 'S01D42', 'S01D43'])
  })

  it('resolves only generated speaking assets below the PWA base', () => {
    expect(resolveSpeakingAudioUrl('audio/speaking/S01D39/q01.mp3', '/sherlock-english/')).toBe('/sherlock-english/audio/speaking/S01D39/q01.mp3')
    expect(() => resolveSpeakingAudioUrl('../secret', '/sherlock-english/')).toThrow()
  })

  it('bypasses stale service-worker JSON when loading the catalog and course', async () => {
    const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => ({
      ok: true,
      json: async () => String(input).includes('catalog.json') ? [{
        course_id: 'S01D39', course_version: '12345678', title: 'Course',
        course_type: 'training', week: 5, day: 4, visible: true
      }] : course
    } as Response))
    await loadSpeakingCatalog(fetcher as typeof fetch)
    await loadSpeakingCourse('S01D39', fetcher as typeof fetch)
    expect(fetcher).toHaveBeenCalledTimes(2)
    for (const [url, init] of fetcher.mock.calls) {
      expect(String(url)).toMatch(/\?fresh=\d+$/)
      expect(init).toMatchObject({ cache: 'no-store' })
    }
  })

  it('accepts paired term courses and exposes hidden courses only to test selection', async () => {
    const termCourse = structuredClone(course)
    termCourse.course_id = 'S4A-T1-W01-D01'
    Object.assign(termCourse, { pair_id: '4A-T1-W01-D01', study_pack: '4A-T1-W01-D01' })
    for (const question of termCourse.questions) question.audio_asset = question.audio_asset.replace('S01D39', termCourse.course_id)
    expect(parseSpeakingCourse(termCourse).study_pack).toBe('4A-T1-W01-D01')

    const catalog = parseSpeakingCatalog([
      { course_id: 'S01D50', course_version: 'legacy-v', title: 'Summer', course_type: 'weekly_review', week: 6, day: 10, visible: true },
      { course_id: 'S4A-T1-W01-D01', course_version: 'term-v', title: 'Term', course_type: 'training', week: 1, day: 1, visible: false, pair_id: '4A-T1-W01-D01', study_pack: '4A-T1-W01-D01' }
    ])
    expect(catalog.window(new Set(['S01D50'])).map((item) => item.course_id)).toEqual(['S01D50'])
    expect(catalog.testCourses().map((item) => item.course_id)).toEqual(['S01D50', 'S4A-T1-W01-D01'])

    const fetcher = async () => ({ ok: true, json: async () => termCourse } as Response)
    await expect(loadSpeakingCourse('S4A-T1-W01-D01', fetcher as typeof fetch)).resolves.toMatchObject({ course_id: 'S4A-T1-W01-D01' })
  })
})
