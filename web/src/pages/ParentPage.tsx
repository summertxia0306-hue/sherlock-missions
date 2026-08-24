import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import type { SherlockApi } from '../core/cloudbase-api'
import { resultSubmissionSchema } from '../core/result-schema'

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

export function ParentPage({ api }: { api: SherlockApi }) {
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

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
      setPassword('')
      setMessage('认证成功：当前会话只能写 test。')
    } catch (error) {
      setMessage(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  async function writeSmokeResult() {
    setBusy(true)
    setMessage('')
    const now = new Date().toISOString()
    const result = resultSubmissionSchema.parse({
      student_id: 'p1-parent-acceptance',
      module_type: 'listening',
      course_id: 'P1-SMOKE',
      course_version: 'p1',
      started_at: now,
      submitted_at: now,
      duration_seconds: 0,
      data_kind: 'formal',
      device_info: { platform: navigator.platform || 'unknown' },
      payload: { check: 'p1-cloudbase-test-write' }
    })
    try {
      const response = await api.submitResult(token, result)
      setMessage(`test 写入成功：${response.result_id}`)
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
        <button type="button" disabled={busy} onClick={writeSmokeResult}>
          {busy ? '写入中…' : '写入一条 test 验收记录'}
        </button>
      )}
      {message && <p className="form-message" role="status">{message}</p>}
      <Link className="back-link" to="/">← 返回本周任务</Link>
    </main>
  )
}

