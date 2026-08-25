import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { SherlockApi } from '../core/cloudbase-api'
import { ParentPage } from './ParentPage'

class FakeAudio {
  listeners = new Map<string, () => void>()
  addEventListener(name: string, listener: () => void) { this.listeners.set(name, listener) }
  play() { window.setTimeout(() => this.listeners.get('ended')?.(), 10); return Promise.resolve() }
}

function api(): SherlockApi {
  return {
    health: vi.fn(), submitResult: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(),
    authenticate: vi.fn(async () => ({ ok: true as const, session_token: 'token', expires_at: '2026-08-24T12:00:00.000Z', data_kind: 'test' as const })),
    listListeningTestResults: vi.fn(async () => ({ ok: true as const, data_kind: 'test' as const, results: [{
      result_id: 'l1', course_id: 'W01D39', data_kind: 'test' as const, score: 10, duration_seconds: 60,
      section_scores: {}, wrong_answers: [], corrections: {}, question_results: [], submitted_at: '2026-08-24T10:00:00Z'
    }] })),
    scoreSpeakingTake: vi.fn(), submitSpeakingResult: vi.fn(),
    listSpeakingTestResults: vi.fn(async () => ({ ok: true as const, data_kind: 'test' as const, results: [{
      result_id: 's1', course_id: 'S01D39', score: 78, stars_total: 22, stars_max: 24, duration_seconds: 120,
      question_results: [{ id: 1, text: 'It is bright.', stars: 3, take_stars: [2, 3], first_total: 60, last_total: 80, best_total: 80, weak_words: ['bright'], passed_by_safety: false }]
    }] })),
    getSpeakingRecordingUrl: vi.fn(async () => ({ ok: true as const, url: 'https://private.test/recording.wav', expires_in: 600 }))
  }
}

describe('P3 parent acceptance details', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('loads listening and numeric speaking detail, then obtains a temporary private recording URL', async () => {
    vi.stubGlobal('Audio', FakeAudio)
    const service = api()
    render(<MemoryRouter><ParentPage api={service} /></MemoryRouter>)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('家长验收密码'), 'parent-password')
    await user.click(screen.getByRole('button', { name: '进入 test 验收' }))
    await user.click(screen.getByRole('button', { name: '刷新听力 test 明细' }))
    expect(await screen.findByText('W01D39 · test · 10 分')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '刷新口语 test 明细' }))
    expect(await screen.findByText('S01D39 · test · 22/24 星 · 78 分')).toBeInTheDocument()
    expect(screen.getByText(/首 60 → 末 80/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '播放第 1 次' }))
    await waitFor(() => expect(service.getSpeakingRecordingUrl).toHaveBeenCalledWith('token', 's1', 1, 1))
    expect(await screen.findByText('录音播放完成。')).toBeInTheDocument()
  })
})
