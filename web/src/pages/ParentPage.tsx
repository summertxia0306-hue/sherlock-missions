import { useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import type { ParentResultDetail, ParentResultFilters, SherlockApi } from '../core/cloudbase-api'
import { DIRECT_UPLOAD_PROBE_OPTIONS, runDirectUploadProbe } from '../core/direct-upload-probe'

function errorMessage(error: unknown): string {
  const code = error instanceof Error ? error.message : 'UNKNOWN'
  const messages: Record<string, string> = {
    AUTH_FAILED: '密码不正确，请重试。', RATE_LIMITED: '尝试次数过多，请稍后再试。',
    CLOUDBASE_NOT_CONFIGURED: '站点尚未完成 CloudBase 公开配置。', CLOUDBASE_ANONYMOUS_LOGIN_FAILED: 'CloudBase 匿名登录尚未启用。',
    CONFIG_ERROR: '云函数的家长认证配置尚未完成。', INVALID_FILTER: '查询条件无效，请检查课程编号或日期。',
    SIGNING_UNAVAILABLE: '当前体验版环境无法签发直传地址。', STORAGE_CORS_OR_NETWORK_BLOCKED: '云存储跨域或网络连接被阻止。',
    UPLOAD_TICKET_EXPIRED: '直传测试票据已过期，请重新运行。', UPLOAD_OBJECT_MISSING: '云存储没有收到测试文件。',
    UPLOAD_SIZE_MISMATCH: '测试文件大小校验失败。', UPLOAD_HASH_MISMATCH: '测试文件完整性校验失败。',
    UPLOAD_CLEANUP_FAILED: '测试对象未能自动清理，请停止测试。'
  }
  if (/^STORAGE_UPLOAD_HTTP_\d{3}$/.test(code)) return `云存储上传失败（HTTP ${code.slice(-3)}）。`
  return messages[code] || '暂时无法完成操作，请稍后再试。'
}

const initialFilters: ParentResultFilters = { data_kind: 'formal' }

export function ParentPage({
  api,
  onAuthenticated = () => undefined,
  directUploadProbeEnabled = import.meta.env.VITE_DIRECT_UPLOAD_PROBE === 'true',
  probeRunner = runDirectUploadProbe
}: {
  api: SherlockApi
  onAuthenticated?: (token: string) => void
  directUploadProbeEnabled?: boolean
  probeRunner?: typeof runDirectUploadProbe
}) {
  const [password, setPassword] = useState('')
  const [token, setToken] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [filters, setFilters] = useState<ParentResultFilters>(initialFilters)
  const [results, setResults] = useState<ParentResultDetail[]>([])
  const [summary, setSummary] = useState({ result_count: 0, completed_course_count: 0, formal_completion_count: 0 })
  const playbackRef = useRef<HTMLAudioElement | null>(null)

  async function query(sessionToken: string, nextFilters: ParentResultFilters) {
    const response = await api.listParentResults(sessionToken, nextFilters)
    setResults(response.results)
    setSummary(response.summary)
    setMessage(response.results.length ? `已加载 ${response.data_kind} 历史记录。` : `没有符合条件的 ${response.data_kind} 记录。`)
  }

  async function onLogin(event: FormEvent) {
    event.preventDefault()
    if (!password) { setMessage('请输入家长验收密码'); return }
    setBusy(true); setMessage('')
    try {
      const result = await api.authenticate(password)
      setToken(result.session_token); onAuthenticated(result.session_token); setPassword('')
      await query(result.session_token, initialFilters)
    } catch (error) { setMessage(errorMessage(error)) }
    finally { setBusy(false) }
  }

  async function onQuery(event: FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('')
    try {
      const normalized: ParentResultFilters = {
        data_kind: filters.data_kind || 'formal',
        ...(filters.module_type ? { module_type: filters.module_type } : {}),
        ...(filters.course_id?.trim() ? { course_id: filters.course_id.trim().toUpperCase() } : {}),
        ...(filters.date_from ? { date_from: new Date(`${filters.date_from}T00:00:00+08:00`).toISOString() } : {}),
        ...(filters.date_to ? { date_to: new Date(`${filters.date_to}T23:59:59+08:00`).toISOString() } : {})
      }
      await query(token, normalized)
    } catch (error) { setMessage(errorMessage(error)) }
    finally { setBusy(false) }
  }

  async function playRecording(resultId: string, questionId: number, attempt: number) {
    if (playbackRef.current) return
    setBusy(true); setMessage('正在取得私有录音…')
    try {
      const response = await api.getParentRecordingUrl(token, resultId, questionId, attempt)
      const audio = new Audio(response.url); playbackRef.current = audio
      audio.addEventListener('ended', () => { playbackRef.current = null; setBusy(false); setMessage('录音播放完成。') }, { once: true })
      audio.addEventListener('error', () => { playbackRef.current = null; setBusy(false); setMessage('录音暂时无法播放。') }, { once: true })
      await audio.play(); setMessage('正在播放私有录音…')
    } catch (error) { playbackRef.current = null; setBusy(false); setMessage(errorMessage(error)) }
  }

  async function runProbe(byteLength: number, label: string) {
    setBusy(true); setMessage(`正在生成并上传${label}测试 WAV，不会启用麦克风…`)
    try {
      const result = await probeRunner(api, token, byteLength)
      setMessage(`直传成功：${result.byte_length} 字节｜上传 ${result.upload_ms}ms｜核验 ${result.verify_ms}ms｜总计 ${result.total_ms}ms｜${result.cleaned_up ? '对象已清理' : '对象未清理'}`)
    } catch (error) { setMessage(errorMessage(error)) }
    finally { setBusy(false) }
  }

  return (
    <main className="center-card parent-card">
      <p className="eyebrow">PARENT HISTORY · FORMAL / TEST ISOLATED</p>
      <h1>家长端</h1>
      <p>默认只查询正式记录；test 必须单独选择，永不计入正式完成和汇总。</p>
      {!token ? (
        <form onSubmit={onLogin}>
          <label htmlFor="parent-password">家长验收密码</label>
          <input id="parent-password" type="password" autoComplete="current-password" maxLength={256} value={password} onChange={(event) => setPassword(event.target.value)} />
          <button type="submit" disabled={busy}>{busy ? '认证中…' : '进入家长端'}</button>
        </form>
      ) : (
        <>
          <form className="parent-filters" onSubmit={onQuery}>
            <label htmlFor="parent-kind">数据类型</label>
            <select id="parent-kind" value={filters.data_kind} onChange={(event) => setFilters({ ...filters, data_kind: event.target.value as 'formal' | 'test' })}>
              <option value="formal">formal 正式</option><option value="test">test 测试</option>
            </select>
            <label htmlFor="parent-module">模块</label>
            <select id="parent-module" value={filters.module_type || ''} onChange={(event) => setFilters({ ...filters, module_type: (event.target.value || undefined) as ParentResultFilters['module_type'] })}>
              <option value="">全部</option><option value="listening">听力</option><option value="speaking">口语</option>
            </select>
            <label htmlFor="parent-course">课程</label>
            <input id="parent-course" placeholder="如 W01D49 或 L4A-T1-W01-D01" maxLength={18} value={filters.course_id || ''} onChange={(event) => setFilters({ ...filters, course_id: event.target.value })} />
            <label htmlFor="parent-from">开始日期</label><input id="parent-from" type="date" value={filters.date_from || ''} onChange={(event) => setFilters({ ...filters, date_from: event.target.value })} />
            <label htmlFor="parent-to">结束日期</label><input id="parent-to" type="date" value={filters.date_to || ''} onChange={(event) => setFilters({ ...filters, date_to: event.target.value })} />
            <button type="submit" disabled={busy}>查询</button>
          </form>
          <div className="parent-summary" aria-label="查询汇总">
            <strong>{filters.data_kind === 'test' ? '测试记录' : '正式记录'} {summary.result_count} 条</strong>
            <span>完成课程 {summary.completed_course_count} 门</span>
            <span>计入正式完成 {summary.formal_completion_count} 门</span>
          </div>
          <div className="parent-actions"><Link className="primary-link" to="/listening?mode=test">进入听力 test 验收</Link><Link className="primary-link" to="/speaking?mode=test">进入口语 test 验收</Link></div>
          {directUploadProbeEnabled && (
            <section className="parent-result" aria-label="云存储直传隔离测试">
              <strong>云存储直传隔离测试</strong>
              <p>按需生成150KiB、400KiB或700KB测试 WAV；不调用麦克风、不评分、不写学习记录，核验后立即删除。每次只运行一项。</p>
              {DIRECT_UPLOAD_PROBE_OPTIONS.map((option) => (
                <button type="button" disabled={busy} key={option.byteLength} onClick={() => runProbe(option.byteLength, option.label)}>
                  {busy ? '测试进行中…' : `运行${option.label}直传测试`}
                </button>
              ))}
            </section>
          )}
        </>
      )}
      {message && <p className="form-message" role="status">{message}</p>}
      {results.map((result) => result.module_type === 'listening' ? (
        <details className="parent-result" key={result.result_id}>
          <summary>{result.course_id} · {result.data_kind} · {result.score} 分</summary>
          <dl><dt>时间</dt><dd>{new Date(result.submitted_at).toLocaleString('zh-CN')}</dd><dt>section_scores</dt><dd><pre>{JSON.stringify(result.section_scores || {}, null, 2)}</pre></dd><dt>wrong_answers</dt><dd><pre>{JSON.stringify(result.wrong_answers || [], null, 2)}</pre></dd><dt>corrections</dt><dd><pre>{JSON.stringify(result.corrections || {}, null, 2)}</pre></dd></dl>
        </details>
      ) : (
        <details className="parent-result" key={result.result_id}>
          <summary>{result.course_id} · {result.data_kind} · {result.stars_total}/{result.stars_max} 星 · {result.score} 分</summary>
          {result.question_results.map((question) => {
            const takeStars = question.take_stars || []
            return <section className="parent-speaking-question" key={question.id}><strong>Q{question.id} · {question.text}</strong><p>{question.stars} 星｜各次 {takeStars.join('/')}｜首 {question.first_total ?? '-'} → 末 {question.last_total ?? '-'}｜最高 {question.best_total ?? '-'}{question.passed_by_safety ? '｜三次后先过' : ''}</p>{(question.weak_words || []).length > 0 && <p>弱词：{question.weak_words?.join('、')}</p>}<div className="recording-buttons">{takeStars.map((_, index) => <button type="button" disabled={busy} key={index} onClick={() => playRecording(result.result_id, question.id, index + 1)}>播放第 {index + 1} 次</button>)}</div></section>
          })}
        </details>
      ))}
      <Link className="back-link" to="/">← 返回本周任务</Link>
    </main>
  )
}
