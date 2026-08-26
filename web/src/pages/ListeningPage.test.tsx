import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { SherlockApi } from '../core/cloudbase-api'
import { parseListeningCatalog, parseListeningCourse } from '../listening/course'
import { ListeningPage } from './ListeningPage'

const catalog = parseListeningCatalog([
  { course_id: 'W01D39', course_version: 'version1', title: 'Nanjing Road', course_type: 'training', week: 5, day: 4, visible: true },
  { course_id: 'W01D40', course_version: 'version2', title: 'Review', course_type: 'weekly_test', week: 5, day: 5, visible: true }
])

const api = {
  health: vi.fn(), authenticate: vi.fn(), submitResult: vi.fn(),
  submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(),
  scoreSpeakingTake: vi.fn(), submitSpeakingResult: vi.fn(), listSpeakingTestResults: vi.fn(), getSpeakingRecordingUrl: vi.fn(),
  listParentResults: vi.fn(), getParentRecordingUrl: vi.fn()
} as SherlockApi
const loadCatalog = async () => catalog

const course = parseListeningCourse({
  course_id: 'W01D39', course_version: 'version1', title: 'Nanjing Road', week: 5, day: 4,
  course_type: 'training', est_minutes: 20, test_audio_asset: 'audio/listening/W01D39/hello.mp3',
  sections: [
    { id: 'words', name: '听音选词', tip: '选词', max_plays: 2, questions: [
      { id: 1, type: 'word_choice', options: ['one', 'two'], audio_asset: 'audio/listening/W01D39/q01.mp3' }
    ] },
    { id: 'sentences', name: '听句判断', tip: '判断', max_plays: 2, questions: [
      { id: 2, type: 'sentence_judge', display: 'It is true.', audio_asset: 'audio/listening/W01D39/q02.mp3' }
    ] },
    { id: 'responses', name: '听问句选答语', tip: '选答语', max_plays: 2, questions: [
      { id: 3, type: 'question_response', options: ['Yes.', 'No.'], audio_asset: 'audio/listening/W01D39/q03.mp3' }
    ] },
    { id: 'dialogue', name: '听对话', tip: '选答案', max_plays: 2, questions: [
      { id: 4, type: 'dialogue_choice', question_text: 'Who?', options: ['Jill', 'Ben'], audio_asset: 'audio/listening/W01D39/q04.mp3' }
    ] },
    { id: 'passage', name: '听短文判断', tip: '判断短文', max_plays: 2, shared_audio: true,
      passage_audio_asset: 'audio/listening/W01D39/p01.mp3', questions: [
        { id: 5, type: 'passage_judge', statement: 'The story is true.' }
      ] }
  ]
})

class FakeAudio {
  listeners = new Map<string, () => void>()
  pause() {}
  addEventListener(type: string, listener: () => void) {
    this.listeners.set(type, listener)
  }
  async play() {
    queueMicrotask(() => this.listeners.get('ended')?.())
  }
}

class ControlledAudio {
  static instances: ControlledAudio[] = []
  listeners = new Map<string, () => void>()
  pause = vi.fn()

  constructor() {
    ControlledAudio.instances.push(this)
  }

  addEventListener(type: string, listener: () => void) {
    this.listeners.set(type, listener)
  }

  async play() {}

  emit(type: string) {
    this.listeners.get(type)?.()
  }
}

class OfflineAudio extends ControlledAudio {
  async play() {
    throw new Error('offline')
  }
}

afterEach(() => {
  ControlledAudio.instances = []
  vi.unstubAllGlobals()
})

describe('P2 listening page', () => {
  it('shows the first formal incomplete course and never treats test as completed', async () => {
    render(<MemoryRouter><ListeningPage api={api} sessionToken="token" loadCatalog={loadCatalog} /></MemoryRouter>)
    expect(await screen.findByText(/当前推荐.*W01D39/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '听力训练' })).toBeInTheDocument()
    expect(screen.getAllByText('未完成')).toHaveLength(2)
    expect(screen.getByRole('button', { name: /开始.*W01D39/ })).toBeEnabled()
  })

  it('requires an authenticated test session before a course can start', async () => {
    render(<MemoryRouter><ListeningPage api={api} sessionToken="" loadCatalog={loadCatalog} /></MemoryRouter>)
    expect(await screen.findByText('请先从家长验收完成认证，再进入听力 test。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /开始.*W01D39/ })).toBeDisabled()
  })

  it('waits for the complete trial and prevents overlapping question audio', async () => {
    vi.stubGlobal('Audio', ControlledAudio)
    render(<MemoryRouter><ListeningPage api={api} sessionToken="token" loadCatalog={loadCatalog} loadCourse={async () => course} /></MemoryRouter>)

    await userEvent.click(await screen.findByRole('button', { name: /开始.*W01D39/ }))
    await userEvent.click(screen.getByRole('button', { name: '播放试音' }))
    expect(screen.getByRole('button', { name: '开始做题' })).toBeDisabled()
    ControlledAudio.instances[0].emit('ended')
    expect(await screen.findByText('试音成功')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '开始做题' }))

    const playButtons = screen.getAllByRole('button', { name: /播放录音/ })
    await userEvent.click(playButtons[0])
    expect(playButtons[0]).toHaveTextContent('正在播放')
    expect(playButtons[1]).toBeDisabled()
    ControlledAudio.instances[1].emit('ended')
    await waitFor(() => expect(playButtons[1]).toBeEnabled())
  })

  it('shows an actionable offline audio error and allows a later retry', async () => {
    vi.stubGlobal('Audio', OfflineAudio)
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    render(<MemoryRouter><ListeningPage api={api} sessionToken="token" loadCatalog={loadCatalog} loadCourse={async () => course} /></MemoryRouter>)

    await userEvent.click(await screen.findByRole('button', { name: /开始.*W01D39/ }))
    await userEvent.click(screen.getByRole('button', { name: '播放试音' }))
    expect(await screen.findByText('当前离线且这段音频尚未缓存；联网后再点一次。')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '播放试音' })).toBeEnabled()
  })

  it('runs trial, all five types, idempotent submit, and transcript-only correction without a child score', async () => {
    sessionStorage.clear()
    vi.stubGlobal('Audio', FakeAudio)
    const submitListeningResult = vi.fn().mockResolvedValue({
      ok: true, result_id: '123e4567-e89b-42d3-a456-426614174000', data_kind: 'test',
      formal_completion_eligible: false, wrong_question_ids: [2], idempotent: false
    })
    const checkListeningCorrection = vi.fn()
      .mockResolvedValueOnce({ ok: true, correct: false, reveal_transcript: ['The private transcript.'], next_attempt: 2, done: false })
      .mockResolvedValueOnce({ ok: true, correct: true, marker: '✓²', done: true })
    const flowApi = { ...api, submitListeningResult, checkListeningCorrection }
    render(<MemoryRouter><ListeningPage api={flowApi} sessionToken="token" loadCatalog={loadCatalog} loadCourse={async () => course} /></MemoryRouter>)

    await userEvent.click(await screen.findByRole('button', { name: /开始.*W01D39/ }))
    await userEvent.click(await screen.findByRole('button', { name: '播放试音' }))
    await userEvent.click(await screen.findByRole('button', { name: '开始做题' }))

    const cards = document.querySelectorAll('.question-card')
    expect(cards).toHaveLength(5)
    for (const card of cards) {
      const radios = within(card as HTMLElement).getAllByRole('radio')
      await userEvent.click(radios[0])
      const play = within(card as HTMLElement).queryByRole('button', { name: /播放录音/ })
      if (play) await userEvent.click(play)
    }
    await userEvent.click(screen.getByRole('button', { name: '播放短文（还可 2 次）' }))
    await userEvent.click(screen.getByRole('button', { name: '全部完成，提交 TEST' }))
    await waitFor(() => expect(submitListeningResult).toHaveBeenCalledTimes(1))
    expect(screen.queryByText(/\d+\s*分/)).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /订正重听/ }))
    await userEvent.click(screen.getByRole('radio', { name: '✓ 一样 / 对' }))
    await userEvent.click(screen.getByRole('button', { name: '确认订正' }))
    expect(await screen.findByText('The private transcript.')).toBeInTheDocument()
    expect(screen.queryByText(/正确答案|你选了/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: '✗ 不一样 / 不对' }))
    await userEvent.click(screen.getByRole('button', { name: '确认订正' }))
    expect(await screen.findByRole('heading', { name: '完成啦' })).toBeInTheDocument()
    expect(screen.queryByText(/100|score|正确答案/)).not.toBeInTheDocument()
    expect(checkListeningCorrection).toHaveBeenCalledTimes(2)
  })
})
