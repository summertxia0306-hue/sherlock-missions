import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { App, mergeCompleted } from './App'
import { setRefreshReadyForTest } from './test/pwa-register'

const speakingApi = {
  startChildSession: vi.fn(async () => ({ ok: true as const, session_token: 'formal-token', expires_at: '2026-08-26T13:00:00.000Z', data_kind: 'formal' as const })),
  getFormalProgress: vi.fn(async () => ({ ok: true as const, completed_course_ids: { listening: ['W01D43'], speaking: ['S01D43'] } })),
  scoreSpeakingTake: vi.fn(), submitSpeakingResult: vi.fn(), listSpeakingTestResults: vi.fn(), getSpeakingRecordingUrl: vi.fn(),
  listParentResults: vi.fn(async () => ({ ok: true as const, data_kind: 'formal' as const, summary: { result_count: 0, completed_course_count: 0, formal_completion_count: 0 }, results: [] })),
  getParentRecordingUrl: vi.fn()
}

describe('P5 application shell', () => {
  it('loads the formal child session and migrated completion progress', async () => {
    const service = { authenticate: vi.fn(), submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }
    render(<MemoryRouter><App api={service} /></MemoryRouter>)
    await waitFor(() => expect(service.getFormalProgress).toHaveBeenCalledWith('formal-token'))
    expect(screen.queryByText('正在连接正式学习进度…')).not.toBeInTheDocument()
  })

  it('shows safe formal connection failures and keeps direct test mode isolated', async () => {
    const disabled = { authenticate: vi.fn(), submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi,
      startChildSession: vi.fn(async () => { throw new Error('FORMAL_DISABLED') }) }
    const first = render(<MemoryRouter><App api={disabled} /></MemoryRouter>)
    expect(await screen.findByText('正式入口尚未开放。')).toBeInTheDocument()
    first.unmount()
    const unavailable = { ...disabled, startChildSession: vi.fn(async () => { throw 'network' }) }
    const second = render(<MemoryRouter><App api={unavailable} /></MemoryRouter>)
    expect(await screen.findByText('正式进度暂时无法连接，请稍后刷新。')).toBeInTheDocument()
    second.unmount()
    render(<MemoryRouter initialEntries={['/listening?mode=test']}><App api={disabled} /></MemoryRouter>)
    expect(screen.getByText('TEST')).toBeInTheDocument()
  })

  it('merges a new formal completion once and preserves an existing completion', () => {
    const value = { listening: ['W01D43'], speaking: ['S01D43'] }
    const added = mergeCompleted(value, 'listening', 'W01D44')
    expect(added.listening).toEqual(['W01D43', 'W01D44'])
    expect(mergeCompleted(added, 'listening', 'W01D44')).toBe(added)
  })

  it('shows only the approved visible modules and opens formal learning', () => {
    render(<MemoryRouter><App api={{ authenticate: vi.fn(), submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }} /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '本周任务' })).toBeInTheDocument()
    expect(screen.getByText('听力训练')).toBeInTheDocument()
    expect(screen.getByText('跟读口语')).toBeInTheDocument()
    expect(screen.getByText('家长端')).toBeInTheDocument()
    expect(screen.queryByText('单词训练')).not.toBeInTheDocument()
    expect(screen.getByText('P5 正式入口 · 历史进度已衔接')).toBeInTheDocument()
    expect(screen.getByText('FORMAL')).toBeInTheDocument()
  })

  it('does not authenticate with an empty password', async () => {
    const authenticate = vi.fn()
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }} />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '进入家长端' }))
    expect(authenticate).not.toHaveBeenCalled()
    expect(screen.getByText('请输入家长验收密码')).toBeInTheDocument()
  })

  it('authenticates a parent and exposes both listening and speaking acceptance actions', async () => {
    const authenticate = vi.fn().mockResolvedValue({
      ok: true,
      session_token: 'session-token',
      expires_at: '2026-08-24T12:00:00.000Z',
      data_kind: 'test'
    })
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }} />
      </MemoryRouter>
    )
    await userEvent.type(screen.getByLabelText('家长验收密码'), 'valid-password')
    await userEvent.click(screen.getByRole('button', { name: '进入家长端' }))
    expect(await screen.findByText('没有符合条件的 formal 记录。')).toBeInTheDocument()
    expect(screen.queryByLabelText('家长验收密码')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: '进入听力 test 验收' })).toHaveAttribute('href', '/listening?mode=test')
    expect(screen.getByRole('link', { name: '进入口语 test 验收' })).toHaveAttribute('href', '/speaking?mode=test')
    expect(screen.getByRole('button', { name: '查询' })).toBeInTheDocument()
    expect(screen.queryByText(/smoke/i)).not.toBeInTheDocument()
  })

  it('shows a safe authentication error without leaking implementation details', async () => {
    const authenticate = vi.fn().mockRejectedValue(new Error('AUTH_FAILED'))
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }} />
      </MemoryRouter>
    )
    await userEvent.type(screen.getByLabelText('家长验收密码'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: '进入家长端' }))
    expect(await screen.findByText('密码不正确，请重试。')).toBeInTheDocument()
  })

  it('loads formal speaking without parent authentication and renders not-found', async () => {
    const service = { authenticate: vi.fn(), submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }
    const { unmount } = render(<MemoryRouter initialEntries={['/speaking']}><App api={service} /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '跟读口语' })).toBeInTheDocument()
    expect(await screen.findByText(/正在加载课程|口语课程目录暂时无法加载/)).toBeInTheDocument()
    unmount()
    render(<MemoryRouter initialEntries={['/missing']}><App api={service} /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '页面不存在' })).toBeInTheDocument()
  })

  it('reports offline state and an available PWA update', () => {
    const online = vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    const service = { authenticate: vi.fn(), submitResult: vi.fn(), health: vi.fn(), submitListeningResult: vi.fn(), checkListeningCorrection: vi.fn(), listListeningTestResults: vi.fn(), ...speakingApi }
    const { unmount } = render(<MemoryRouter><App api={service} /></MemoryRouter>)
    expect(screen.getByText(/当前离线/)).toBeInTheDocument()
    unmount()
    online.mockReturnValue(true)
    setRefreshReadyForTest(true)
    render(<MemoryRouter><App api={service} /></MemoryRouter>)
    expect(screen.getByText('新版本已就绪。')).toBeInTheDocument()
    online.mockRestore()
    setRefreshReadyForTest(false)
  })
})
