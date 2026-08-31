import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { SherlockApi, SpeakingScoreResponse } from '../core/cloudbase-api'
import { parseSpeakingCatalog, parseSpeakingCourse } from '../speaking/course'
import type { PcmRecorder } from '../speaking/recorder'
import { SpeakingPage } from './SpeakingPage'

const catalog = parseSpeakingCatalog([{ course_id: 'S01D39', course_version: 'version1', title: 'Speaking', course_type: 'training', week: 5, day: 4, visible: true }])
const course = parseSpeakingCourse({
  course_id: 'S01D39', course_version: 'version1', title: 'Speaking', course_type: 'training', week: 5, day: 4, est_minutes: 10,
  questions: Array.from({ length: 8 }, (_, index) => index < 6
    ? { id: index + 1, type: 'repeat', text: `Sentence ${index + 1}.`, audio_asset: `audio/speaking/S01D39/q0${index + 1}.mp3` }
    : { id: index + 1, type: 'qa', hint: `用英语说：答案 ${index + 1}。`, audio_asset: `audio/speaking/S01D39/q0${index + 1}.mp3` })
})

class FakeAudio {
  listeners = new Map<string, () => void>()
  addEventListener(name: string, listener: () => void) { this.listeners.set(name, listener) }
  play() { queueMicrotask(() => this.listeners.get('ended')?.()); return Promise.resolve() }
  pause() {}
}

function fakeRecorder(): PcmRecorder {
  return {
    start: vi.fn(async (_auto, countdown) => { countdown?.(3); countdown?.(2); countdown?.(1); countdown?.(0) }),
    stop: vi.fn(async () => ({ wav: new Blob([new Uint8Array(9000)], { type: 'audio/wav' }), url: 'blob:test', peak: 0.2, seconds: 1 })),
    release: vi.fn()
  }
}

function api(score: (request: { question_id: number; attempt: number }) => Promise<SpeakingScoreResponse>): SherlockApi {
  return {
    startChildSession: vi.fn(), getFormalProgress: vi.fn(),
    health: vi.fn(), authenticate: vi.fn(), submitResult: vi.fn(), submitListeningResult: vi.fn(),
    checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(),
    scoreSpeakingTake: vi.fn((_token, request) => score(request)),
    submitSpeakingResult: vi.fn(async () => ({ ok: true as const, result_id: 'r1', data_kind: 'test' as const, formal_completion_eligible: false as const, idempotent: false })),
    listSpeakingTestResults: vi.fn(), getSpeakingRecordingUrl: vi.fn(), listParentResults: vi.fn(), getParentRecordingUrl: vi.fn(),
    createDirectUploadProbe: vi.fn(), verifyDirectUploadProbe: vi.fn(), cancelDirectUploadProbe: vi.fn()
  }
}

const scored = (stars: 1 | 2 | 3, question: number, attempt: number): SpeakingScoreResponse => ({
  ok: true, stars, proof: `proof-${question}-${attempt}`, child_feedback: stars === 3 ? '读得真棒！' : '请再读一次 bright。',
  weak_words: stars === 3 ? [] : ['bright'], word_lights: [{ word: 'bright', light: stars === 3 ? 'good' : 'weak' }],
  can_retry: stars < 3 && attempt < 3, can_skip: stars < 3 && attempt === 3
})

describe('P3 speaking page', () => {
  beforeEach(() => {
    vi.stubGlobal('Audio', FakeAudio)
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:test') })
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() })
    sessionStorage.clear()
  })
  afterEach(() => vi.unstubAllGlobals())

  async function finishTrial(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByRole('button', { name: '🎙️ 开始试录' }))
    await user.click(await screen.findByRole('button', { name: '停止录音' }))
    await user.click(screen.getByRole('button', { name: '▶ 回放试音' }))
    await waitFor(() => expect(screen.getByRole('button', { name: '声音正常，开始题目' })).toBeEnabled())
    await user.click(screen.getByRole('button', { name: '声音正常，开始题目' }))
  }

  async function recordAndScore(user: ReturnType<typeof userEvent.setup>) {
    await user.click(screen.getByRole('button', { name: /开始录音|重新录音/ }))
    await user.click(await screen.findByRole('button', { name: '■ 读完了' }))
    await user.click(screen.getByRole('button', { name: '就用这个，开始评分' }))
  }

  it('shows the five-course formal window around the first incomplete migrated course', async () => {
    const formalCatalog = parseSpeakingCatalog(Array.from({ length: 8 }, (_, index) => ({
      course_id: `S01D${index + 39}`, course_version: `version-${index}`, title: `Course ${index + 39}`,
      course_type: 'training', week: 5, day: index + 1, visible: true
    })))
    render(<MemoryRouter><SpeakingPage api={api(async (request) => scored(3, request.question_id, request.attempt))}
      sessionToken="formal-token" dataKind="formal" completedCourseIds={new Set(['S01D39', 'S01D40', 'S01D41', 'S01D42', 'S01D43'])}
      loadCatalog={async () => formalCatalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    expect(await screen.findByText(/当前推荐.*S01D44/)).toBeInTheDocument()
    const courseList = screen.getByRole('region', { name: '口语课程' })
    for (const id of ['S01D42', 'S01D43', 'S01D44', 'S01D45', 'S01D46']) expect(within(courseList).getByText(new RegExp(id))).toBeInTheDocument()
    expect(screen.getAllByText('已完成')).toHaveLength(2)
    expect(screen.getAllByText('未完成')).toHaveLength(3)
    expect(within(courseList).getByText('推荐')).toBeInTheDocument()
    expect(within(courseList).getByText('Course 42').closest('.course-row')).toHaveClass('course-completed')
    expect(within(courseList).getByText('Course 44').closest('.course-row')).toHaveClass('course-recommended')
  })

  it('keeps unauthenticated access read-only', async () => {
    render(<MemoryRouter><SpeakingPage api={api(async (request) => scored(3, request.question_id, request.attempt))} sessionToken="" loadCatalog={async () => catalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    expect(await screen.findByText(/请先从家长验收/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始' })).toBeDisabled()
  })

  it('enforces three valid low takes, then completes eight proof-only questions', async () => {
    const user = userEvent.setup()
    const service = api(async (request) => scored(request.question_id === 1 ? 2 : 3, request.question_id, request.attempt))
    render(<MemoryRouter><SpeakingPage api={service} sessionToken="token" loadCatalog={async () => catalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    await user.click(await screen.findByRole('button', { name: '开始' }))
    await finishTrial(user)
    expect(screen.getByText('Sentence 1.')).toBeInTheDocument()
    for (let attempt = 0; attempt < 3; attempt += 1) await recordAndScore(user)
    expect(screen.queryByText(/80|accuracy|total/i)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '先过这题' }))
    await user.click(screen.getByRole('button', { name: '下一题' }))
    for (let question = 2; question <= 8; question += 1) {
      await recordAndScore(user)
      if (question < 8) await user.click(screen.getByRole('button', { name: '下一题' }))
    }
    await user.click(screen.getByRole('button', { name: '全部完成，提交 TEST' }))
    expect(await screen.findByRole('heading', { name: '完成啦' })).toBeInTheDocument()
    expect(service.submitSpeakingResult).toHaveBeenCalledTimes(1)
    const submission = vi.mocked(service.submitSpeakingResult).mock.calls[0][1]
    expect(JSON.stringify(submission)).not.toMatch(/score|total|accuracy|fluency|integrity/)
    await user.click(screen.getByRole('button', { name: '返回课程列表' }))
    expect(await screen.findByRole('heading', { name: '跟读口语' })).toBeInTheDocument()
  })

  it('keeps the local recording when scoring fails so the retry does not consume a take', async () => {
    const user = userEvent.setup()
    let calls = 0
    const service = api(async (request) => { calls += 1; if (calls === 1) throw new Error('SPEAKING_SCORE_UNAVAILABLE'); return scored(3, request.question_id, request.attempt) })
    render(<MemoryRouter><SpeakingPage api={service} sessionToken="token" loadCatalog={async () => catalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    await user.click(await screen.findByRole('button', { name: '开始' }))
    await finishTrial(user)
    await recordAndScore(user)
    expect(await screen.findByText(/本次不计次数，录音仍保留/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '就用这个，开始评分' }))
    expect(await screen.findByLabelText('3 星')).toBeInTheDocument()
    expect(vi.mocked(service.scoreSpeakingTake).mock.calls[1][1].attempt).toBe(1)
  })

  it('shows a safe diagnostic code when test scoring fails immediately', async () => {
    const user = userEvent.setup()
    const service = api(async () => { throw new Error('ISE_10163') })
    render(<MemoryRouter><SpeakingPage api={service} sessionToken="token" loadCatalog={async () => catalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    await user.click(await screen.findByRole('button', { name: '开始' }))
    await finishTrial(user)
    await recordAndScore(user)
    expect(await screen.findByText(/诊断码：ISE_10163/)).toBeInTheDocument()
  })

  it('distinguishes a chunk upload failure from an ISE scoring failure', async () => {
    const user = userEvent.setup()
    const service = api(async () => { throw new Error('SPEAKING_UPLOAD_FAILED') })
    render(<MemoryRouter><SpeakingPage api={service} sessionToken="token" loadCatalog={async () => catalog} loadCourse={async () => course} recorder={fakeRecorder()} /></MemoryRouter>)
    await user.click(await screen.findByRole('button', { name: '开始' }))
    await finishTrial(user)
    await recordAndScore(user)
    expect(await screen.findByText(/录音上传没有完成.*直接再次评分/)).toBeInTheDocument()
  })
})
