import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { setRefreshReadyForTest } from './test/pwa-register'

describe('P1 application shell', () => {
  it('shows only the approved visible modules and keeps formal learning closed', () => {
    render(<MemoryRouter><App /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '本周任务' })).toBeInTheDocument()
    expect(screen.getByText('听力训练')).toBeInTheDocument()
    expect(screen.getByText('跟读口语')).toBeInTheDocument()
    expect(screen.getByText('家长验收')).toBeInTheDocument()
    expect(screen.queryByText('单词训练')).not.toBeInTheDocument()
    expect(screen.getByText('P1 仅开放家长 test 验收')).toBeInTheDocument()
  })

  it('does not authenticate with an empty password', async () => {
    const authenticate = vi.fn()
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult: vi.fn(), health: vi.fn() }} />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '进入 test 验收' }))
    expect(authenticate).not.toHaveBeenCalled()
    expect(screen.getByText('请输入家长验收密码')).toBeInTheDocument()
  })

  it('authenticates a parent and submits a smoke result through the test session', async () => {
    const authenticate = vi.fn().mockResolvedValue({
      ok: true,
      session_token: 'session-token',
      expires_at: '2026-08-24T12:00:00.000Z',
      data_kind: 'test'
    })
    const submitResult = vi.fn().mockResolvedValue({
      ok: true,
      result_id: 'result-1',
      data_kind: 'test',
      formal_completion_eligible: false
    })
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult, health: vi.fn() }} />
      </MemoryRouter>
    )
    await userEvent.type(screen.getByLabelText('家长验收密码'), 'valid-password')
    await userEvent.click(screen.getByRole('button', { name: '进入 test 验收' }))
    expect(await screen.findByText('认证成功：当前会话只能写 test。')).toBeInTheDocument()
    expect(screen.queryByLabelText('家长验收密码')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '写入一条 test 验收记录' }))
    expect(await screen.findByText('test 写入成功：result-1')).toBeInTheDocument()
    expect(submitResult).toHaveBeenCalledWith(
      'session-token',
      expect.objectContaining({ course_id: 'P1-SMOKE', data_kind: 'formal' })
    )
  })

  it('shows a safe authentication error without leaking implementation details', async () => {
    const authenticate = vi.fn().mockRejectedValue(new Error('AUTH_FAILED'))
    render(
      <MemoryRouter initialEntries={['/parent']}>
        <App api={{ authenticate, submitResult: vi.fn(), health: vi.fn() }} />
      </MemoryRouter>
    )
    await userEvent.type(screen.getByLabelText('家长验收密码'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: '进入 test 验收' }))
    expect(await screen.findByText('密码不正确，请重试。')).toBeInTheDocument()
  })

  it('renders module placeholders and the not-found route', () => {
    const { unmount } = render(<MemoryRouter initialEntries={['/listening']}><App /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: '听力训练' })).toBeInTheDocument()
    expect(screen.getByText('formal 入口关闭')).toBeInTheDocument()
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
