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
    startChildSession: vi.fn(), getFormalProgress: vi.fn(),
    health: vi.fn(), submitResult: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(),
    authenticate: vi.fn(async () => ({ ok: true as const, session_token: 'token', expires_at: '2026-08-24T12:00:00.000Z', data_kind: 'test' as const })),
    createDirectUploadProbe: vi.fn(), verifyDirectUploadProbe: vi.fn(), cancelDirectUploadProbe: vi.fn(),
    listListeningTestResults: vi.fn(async () => ({ ok: true as const, data_kind: 'test' as const, results: [{
      result_id: 'l1', course_id: 'W01D39', data_kind: 'test' as const, score: 10, duration_seconds: 60,
      section_scores: {}, wrong_answers: [], corrections: {}, question_results: [], submitted_at: '2026-08-24T10:00:00Z'
    }] })),
    scoreSpeakingTake: vi.fn(), submitSpeakingResult: vi.fn(),
    listSpeakingTestResults: vi.fn(async () => ({ ok: true as const, data_kind: 'test' as const, results: [{
      result_id: 's1', course_id: 'S01D39', score: 78, stars_total: 22, stars_max: 24, duration_seconds: 120,
      question_results: [{ id: 1, text: 'It is bright.', stars: 3, take_stars: [2, 3], first_total: 60, last_total: 80, best_total: 80, weak_words: ['bright'], passed_by_safety: false }]
    }] })),
    getSpeakingRecordingUrl: vi.fn(async () => ({ ok: true as const, url: 'https://private.test/recording.wav', expires_in: 600 })),
    listParentResults: vi.fn(), getParentRecordingUrl: vi.fn()
  }
}

function p4Api(): SherlockApi {
  const service = api()
  service.listParentResults = vi.fn(async (_token, filters) => ({
    ok: true as const,
    data_kind: filters.data_kind || 'formal',
    summary: { result_count: 1, completed_course_count: filters.data_kind === 'test' ? 0 : 1, formal_completion_count: filters.data_kind === 'test' ? 0 : 1 },
    results: filters.data_kind === 'test' ? [{
      result_id: 't1', course_id: 'W01D02', module_type: 'listening' as const, data_kind: 'test' as const,
      score: 80, duration_seconds: 70, submitted_at: '2026-06-12T13:00:00.000Z', section_scores: {}, wrong_answers: [], corrections: {}, question_results: []
    }] : [{
      result_id: 'f1', course_id: 'S01D01', module_type: 'speaking' as const, data_kind: 'formal' as const,
      score: 99, stars_total: 24, stars_max: 24, duration_seconds: 334, submitted_at: '2026-06-27T07:01:00.000Z',
      question_results: [{ id: 1, text: 'I have a little cat.', stars: 3, take_stars: [3], first_total: 99, last_total: 99, best_total: 99, weak_words: [], passed_by_safety: false }]
    }]
  }))
  service.getParentRecordingUrl = vi.fn(async () => ({ ok: true as const, url: 'https://private.test/history.wav', expires_in: 600 }))
  return service
}

describe('P4 parent history', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('shows formal by default and only includes test after the parent selects the test filter', async () => {
    vi.stubGlobal('Audio', FakeAudio)
    const service = p4Api()
    render(<MemoryRouter><ParentPage api={service} /></MemoryRouter>)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('家长验收密码'), 'parent-password')
    await user.click(screen.getByRole('button', { name: '进入家长端' }))

    expect(await screen.findByText('正式记录 1 条')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '运行150KiB直传测试' })).not.toBeInTheDocument()
    expect(screen.getByText('S01D01 · formal · 24/24 星 · 99 分')).toBeInTheDocument()
    expect(screen.queryByText(/W01D02/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '播放第 1 次' }))
    await waitFor(() => expect(service.getParentRecordingUrl).toHaveBeenCalledWith('token', 'f1', 1, 1))
    expect(await screen.findByText('录音播放完成。')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('数据类型'), 'test')
    await user.click(screen.getByRole('button', { name: '查询' }))
    expect(await screen.findByText('W01D02 · test · 80 分')).toBeInTheDocument()
    expect(service.listParentResults).toHaveBeenLastCalledWith('token', expect.objectContaining({ data_kind: 'test' }))
  })

  it('shows the isolated binary upload probe only when explicitly enabled and reports timings', async () => {
    const service = p4Api()
    const probeRunner = vi.fn().mockResolvedValue({
      byte_length: 150 * 1024,
      sha256: 'a'.repeat(64),
      upload_ms: 420,
      verify_ms: 180,
      total_ms: 640,
      cleaned_up: true
    })
    render(<MemoryRouter><ParentPage api={service} directUploadProbeEnabled probeRunner={probeRunner} /></MemoryRouter>)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('家长验收密码'), 'parent-password')
    await user.click(screen.getByRole('button', { name: '进入家长端' }))
    await user.click(await screen.findByRole('button', { name: '运行150KiB直传测试' }))

    await waitFor(() => expect(probeRunner).toHaveBeenCalledWith(service, 'token'))
    expect(await screen.findByText(/直传成功：153600 字节/)).toHaveTextContent('上传 420ms')
    expect(screen.getByText(/对象已清理/)).toBeInTheDocument()
  })
})
