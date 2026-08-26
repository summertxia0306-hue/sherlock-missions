import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { setRefreshReadyForTest } from './test/pwa-register'

const speakingApi = {
  scoreSpeakingTake: vi.fn(), submitSpeakingResult: vi.fn(), listSpeakingTestResults: vi.fn(), getSpeakingRecordingUrl: vi.fn(),
  listParentResults: vi.fn(async () => ({ ok: true as const, data_kind: 'formal' as const, summary: { result_count: 0, completed_course_count: 0, formal_completion_count: 0 }, results: [] })),
  getParentRecordingUrl: vi.fn()
}

describe('P4 application shell', () => {
  it('shows only the approved visible modules and keeps formal learning closed', () => {
    render(<MemoryRouter><App /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '本周任务' })).toBeInTheDocument()
    expect(screen.getByText('听力训练')).toBeInTheDocument()
    expect(screen.getByText('跟读口语')).toBeInTheDocument()
    expect(screen.getByText('家长端')).toBeInTheDocument()
    expect(screen.queryByText('单词训练')).not.toBeInTheDocument()
    expect(screen.getByText('P4 历史迁移 · formal/test 独立查询')).toBeInTheDocument()
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
    expect(screen.getByRole('link', { name: '进入听力 test 验收' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '进入口语 test 验收' })).toBeInTheDocument()
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

  it('keeps unauthenticated speaking behind parent acceptance and renders not-found', async () => {
    const { unmount } = render(<MemoryRouter initialEntries={['/speaking']}><App /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '跟读口语' })).toBeInTheDocument()
    expect(await screen.findByText(/正在加载课程|口语课程目录暂时无法加载/)).toBeInTheDocument()
    unmount()
    render(<MemoryRouter initialEntries={['/missing']}><App /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '页面不存在' })).toBeInTheDocument()
  })

  it('reports offline state and an available PWA update', () => {
    const online = vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    const { unmount } = render(<MemoryRouter><App /></MemoryRouter>)
    expect(screen.getByText(/当前离线/)).toBeInTheDocument()
    unmount()
    online.mockReturnValue(true)
    setRefreshReadyForTest(true)
    render(<MemoryRouter><App /></MemoryRouter>)
    expect(screen.getByText('新版本已就绪。')).toBeInTheDocument()
    online.mockRestore()
    setRefreshReadyForTest(false)
  })
})
