import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import type { SherlockApi } from '../core/cloudbase-api'

function errorMessage(error: unknown): string {
  const code = error instanceof Error ? error.message : 'UNKNOWN'
  const messages: Record<string, string> = {
    AUTH_FAILED: '密码不正确，请重试。',
    RATE_LIMITED: '尝试次数过多，请稍后再试。',
    CLOUDBASE_NOT_CONFIGURED: '站点尚未完成 CloudBase 公开配置。',
    CLOUDBASE_ANONYMOUS_LOGIN_FAILED: 'CloudBase 匿名登录尚未启用。',
    CONFIG_ERROR: '云函数的家长认证配置尚未完成。'
  }
  return messages[code] || '暂时无法完成操作，请稍后再试。'
}

export function ParentPage({ api, onAuthenticated = () => undefined }: { api: SherlockApi; onAuthenticated?: (token: string) => void }) {
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [results, setResults] = useState<Awaited<ReturnType<SherlockApi['listListeningTestResults']>>['results']>([])

  async function onLogin(event: FormEvent) {
    event.preventDefault()
    if (!password) {
      setMessage('请输入家长验收密码')
      return
    }
    setBusy(true)
    setMessage('')
    try {
      const result = await api.authenticate(password)
      setToken(result.session_token)
      onAuthenticated(result.session_token)
      setPassword('')
      setMessage('认证成功：当前会话只能写 test。')
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  async function refreshListeningResults() {
    setBusy(true)
    setMessage('')
    try {
      const response = await api.listListeningTestResults(token)
      setResults(response.results)
      setMessage(response.results.length ? '已刷新听力 test 明细。' : '目前还没有听力 test 记录。')
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="center-card parent-card">
      <p className="eyebrow">PARENT ACCEPTANCE · TEST ONLY</p>
      <h1>家长验收</h1>
      <p>此入口不会产生儿童完成状态。浏览器提交的 data_kind 将被服务端忽略并强制改为 test。</p>
      {!token ? (
        <form onSubmit={onLogin}>
          <label htmlFor="parent-password">家长验收密码</label>
          <input
            id="parent-password"
            type="password"
            autoComplete="current-password"
            maxLength={256}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <button type="submit" disabled={busy}>{busy ? '认证中…' : '进入 test 验收'}</button>
        </form>
      ) : (
        <div className="parent-actions">
          <Link className="primary-link" to="/listening">进入听力 test 验收</Link>
          <button type="button" disabled={busy} onClick={refreshListeningResults}>刷新听力 test 明细</button>
        </div>
      )}
      {message && <p className="form-message" role="status">{message}</p>}
      {results.map((result) => (
        <details className="parent-result" key={result.result_id}>
          <summary>{result.course_id} · test · {result.score} 分</summary>
          <dl>
            <dt>score</dt><dd>{result.score}</dd>
            <dt>section_scores</dt><dd><pre>{JSON.stringify(result.section_scores, null, 2)}</pre></dd>
            <dt>wrong_answers</dt><dd><pre>{JSON.stringify(result.wrong_answers, null, 2)}</pre></dd>
            <dt>corrections</dt><dd><pre>{JSON.stringify(result.corrections, null, 2)}</pre></dd>
            <dt>question_results</dt><dd><pre>{JSON.stringify(result.question_results, null, 2)}</pre></dd>
          </dl>
        </details>
      ))}
      <Link className="back-link" to="/">← 返回本周任务</Link>
    </main>
  )
}
