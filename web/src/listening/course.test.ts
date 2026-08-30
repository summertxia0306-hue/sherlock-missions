import { describe, expect, it } from 'vitest'
import { loadListeningCourse, parseListeningCatalog, parseListeningCourse, resolveAudioUrl } from './course'

const childCourse = {
  course_id: 'W01D39',
  course_version: 'abc12345',
  title: '听力训练',
  week: 5,
  day: 4,
  course_type: 'training',
  est_minutes: 20,
  test_audio_asset: 'audio/listening/W01D39/hello.mp3',
  sections: [
    {
      id: 'word_discrimination', name: '听音选词', tip: '听录音', max_plays: 2,
      questions: [{ id: 1, type: 'word_choice', options: ['one', 'two'], audio_asset: 'audio/listening/W01D39/q01.mp3' }]
    },
    {
      id: 'sentence_meaning', name: '听句判断', tip: '听录音', max_plays: 2,
      questions: [{ id: 2, type: 'sentence_judge', display: 'It is true.', audio_asset: 'audio/listening/W01D39/q02.mp3' }]
    },
    {
      id: 'question_response', name: '听问句选答语', tip: '听录音', max_plays: 2,
      questions: [{ id: 3, type: 'question_response', options: ['Yes.', 'No.'], audio_asset: 'audio/listening/W01D39/q03.mp3' }]
    },
    {
      id: 'dialogue', name: '听对话', tip: '听录音', max_plays: 2,
      questions: [{ id: 4, type: 'dialogue_choice', question_text: 'Who?', options: ['Jill', 'Ben'], audio_asset: 'audio/listening/W01D39/q04.mp3' }]
    },
    {
      id: 'passage', name: '听短文判断', tip: '听短文', max_plays: 2, shared_audio: true,
      passage_audio_asset: 'audio/listening/W01D39/p01.mp3',
      questions: [{ id: 5, type: 'passage_judge', statement: 'It is true.' }]
    }
  ]
}

describe('P2 listening child course contract', () => {
  it('accepts the five supported shapes without answer material', () => {
    const parsed = parseListeningCourse(childCourse)
    expect(parsed.sections[0].questions[0].type).toBe('word_choice')
    expect(JSON.stringify(parsed)).not.toMatch(/answer|transcript|parent_note|tag/)
  })

  it('rejects answer, transcript, tag, and parent notes in child assets', () => {
    for (const key of ['answer', 'transcript', 'tag', 'parent_note']) {
      const leaked = structuredClone(childCourse) as Record<string, unknown>
      const sections = leaked.sections as Array<{ questions: Array<Record<string, unknown>> }>
      sections[0].questions[0][key] = key === 'answer' ? 0 : 'secret'
      expect(() => parseListeningCourse(leaked)).toThrow()
    }
  })

  it('keeps stable order and a bounded five-course formal window', () => {
    const catalog = parseListeningCatalog(Array.from({ length: 12 }, (_, index) => ({
      course_id: `W01D${String(index + 39).padStart(2, '0')}`,
      title: `Course ${index + 39}`,
      course_type: 'training', week: 6, day: index + 1, visible: true,
      course_version: `v${index}`
    })))
    expect(catalog.window(new Set(), 5).map((item) => item.course_id)).toEqual([
      'W01D39', 'W01D40', 'W01D41', 'W01D42', 'W01D43'
    ])
    expect(catalog.window(new Set(['W01D39', 'W01D40', 'W01D41', 'W01D42', 'W01D43']), 5)
      .map((item) => item.course_id)).toEqual(['W01D42', 'W01D43', 'W01D44', 'W01D45', 'W01D46'])
  })

  it('resolves only generated listening audio assets below the PWA base', () => {
    expect(resolveAudioUrl('audio/listening/W01D39/q01.mp3', '/sherlock-english/'))
      .toBe('/sherlock-english/audio/listening/W01D39/q01.mp3')
    expect(() => resolveAudioUrl('../secret', '/sherlock-english/')).toThrow()
  })

  it('accepts a paired term course and keeps test-only entries out of formal recommendation', async () => {
    const termCourse = structuredClone(childCourse)
    termCourse.course_id = 'L4A-T1-W01-D01'
    Object.assign(termCourse, { pair_id: '4A-T1-W01-D01', study_pack: '4A-T1-W01-D01' })
    termCourse.test_audio_asset = 'audio/listening/L4A-T1-W01-D01/hello.mp3'
    for (const section of termCourse.sections) {
      if ('passage_audio_asset' in section && section.passage_audio_asset) section.passage_audio_asset = section.passage_audio_asset.replace('W01D39', termCourse.course_id)
      for (const question of section.questions) {
        if ('audio_asset' in question && question.audio_asset) question.audio_asset = question.audio_asset.replace('W01D39', termCourse.course_id)
      }
    }
    expect(parseListeningCourse(termCourse).pair_id).toBe('4A-T1-W01-D01')

    const catalog = parseListeningCatalog([
      { course_id: 'W01D50', course_version: 'legacy-v', title: 'Summer', course_type: 'weekly_test', week: 6, day: 10, visible: true },
      { course_id: 'L4A-T1-W01-D02', course_version: 'term-v2', title: 'Term 2', course_type: 'training', week: 1, day: 2, visible: false, pair_id: '4A-T1-W01-D02', study_pack: '4A-T1-W01-D02' },
      { course_id: 'L4A-T1-W01-D01', course_version: 'term-v1', title: 'Term 1', course_type: 'training', week: 1, day: 1, visible: false, pair_id: '4A-T1-W01-D01', study_pack: '4A-T1-W01-D01' }
    ])
    expect(catalog.window(new Set(['W01D50'])).map((item) => item.course_id)).toEqual(['W01D50'])
    expect(catalog.firstFormalIncomplete(new Set(['W01D50']))).toBeUndefined()
    expect(catalog.testCourses().map((item) => item.course_id)).toEqual(['W01D50', 'L4A-T1-W01-D01', 'L4A-T1-W01-D02'])

    const fetcher = async () => ({ ok: true, json: async () => termCourse } as Response)
    await expect(loadListeningCourse('L4A-T1-W01-D01', fetcher as typeof fetch)).resolves.toMatchObject({ course_id: 'L4A-T1-W01-D01' })
  })
})
