import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import type { SherlockApi } from './core/cloudbase-api'
import { cloudbaseApi } from './core/cloudbase-api'
import { createFormalSessionManager, type SessionRequestRunner } from './core/formal-session'
import { PwaStatus } from './components/PwaStatus'
import { HomePage } from './pages/HomePage'
import { ListeningPage } from './pages/ListeningPage'
import { ParentPage } from './pages/ParentPage'
import { SpeakingPage } from './pages/SpeakingPage'

const DOMESTIC_FORMAL_ENTRY = 'https://family24-d7gqb6r6m2d722f7a-1383960965.ap-shanghai.app.tcloudbase.com/sherlock-api/'

export function mergeCompleted(
  value: { listening: string[]; speaking: string[] }, module: 'listening' | 'speaking', courseId: string
) {
  return value[module].includes(courseId) ? value : { ...value, [module]: [...value[module], courseId].sort() }
}

function LearningRoutes({
  api, parentSessionToken, formalSessionToken, runFormalRequest, completed, formalMessage, formalEntryRequired, markCompleted, onParentAuthenticated
}: {
  api: SherlockApi
  parentSessionToken: string
  formalSessionToken: string
  runFormalRequest: SessionRequestRunner
  completed: { listening: string[]; speaking: string[] }
  formalMessage: string
  formalEntryRequired: boolean
  markCompleted: (module: 'listening' | 'speaking', courseId: string) => void
  onParentAuthenticated: (token: string) => void
}) {
  const location = useLocation()
  const testMode = new URLSearchParams(location.search).get('mode') === 'test'
  const dataKind = testMode ? 'test' as const : 'formal' as const
  const sessionToken = testMode ? parentSessionToken : formalSessionToken
  const listeningCompleted = testMode ? new Set<string>() : new Set(completed.listening)
  const speakingCompleted = testMode ? new Set<string>() : new Set(completed.speaking)
  return <>
    <header className="topbar">
      <Link className="brand" to="/" aria-label="返回首页"><span className="brand-mark">S</span><span>夏洛恪英语</span></Link>
      <span className="test-label">{testMode ? 'TEST' : 'FORMAL'}</span>
    </header>
    {!testMode && formalMessage && <p className="notice warning" role="status">
      {formalMessage}
      {formalEntryRequired && <> <a href={DOMESTIC_FORMAL_ENTRY}>打开腾讯云国内正式入口</a></>}
    </p>}
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/listening" element={<ListeningPage api={api} sessionToken={sessionToken} runSessionRequest={testMode ? undefined : runFormalRequest} dataKind={dataKind} completedCourseIds={listeningCompleted} onFormalCompleted={markCompleted.bind(null, 'listening')} />} />
      <Route path="/speaking" element={<SpeakingPage api={api} sessionToken={sessionToken} runSessionRequest={testMode ? undefined : runFormalRequest} dataKind={dataKind} completedCourseIds={speakingCompleted} onFormalCompleted={markCompleted.bind(null, 'speaking')} />} />
      <Route path="/parent" element={<ParentPage api={api} onAuthenticated={onParentAuthenticated} />} />
      <Route path="*" element={<main className="center-card"><h1>页面不存在</h1><Link to="/">返回首页</Link></main>} />
    </Routes>
  </>
}

export function App({ api = cloudbaseApi }: { api?: SherlockApi }) {
  const [parentSessionToken, setParentSessionToken] = useState('')
  const [formalSessionToken, setFormalSessionToken] = useState('')
  const [completed, setCompleted] = useState({ listening: [] as string[], speaking: [] as string[] })
  const [formalMessage, setFormalMessage] = useState('正在连接正式学习进度…')
  const [formalEntryRequired, setFormalEntryRequired] = useState(false)
  const formalSession = useMemo(() => createFormalSessionManager(api, {
    onSession: (session) => setFormalSessionToken(session.session_token)
  }), [api])

  const runFormalRequest = useCallback<SessionRequestRunner>(async (request, options) => {
    try {
      const result = await formalSession.run(request, {
        onRecovering: () => {
          setFormalMessage('正式会话正在自动恢复，当前学习状态仍保留…')
          options?.onRecovering?.()
        }
      })
      setFormalEntryRequired(false)
      setFormalMessage('')
      return result
    } catch (error) {
      const code = error instanceof Error ? error.message : ''
      if (code === 'FORMAL_ENTRY_REQUIRED') {
        setFormalEntryRequired(true)
        setFormalMessage('儿童正式入口已迁移。')
      } else if (code === 'FORMAL_SESSION_RECOVERY_FAILED') {
        setFormalMessage('正式会话自动恢复失败，当前学习状态仍保留；联网后可再次操作。')
      }
      throw error
    }
  }, [formalSession])

  useEffect(() => {
    let active = true
    runFormalRequest((token) => api.getFormalProgress(token)).then((progress) => {
      if (!active) return
      setCompleted(progress.completed_course_ids)
      setFormalEntryRequired(false)
      setFormalMessage('')
    }).catch((error: unknown) => {
      if (!active) return
      const code = error instanceof Error ? error.message : ''
      if (code === 'FORMAL_ENTRY_REQUIRED') {
        setFormalEntryRequired(true)
        setFormalMessage('儿童正式入口已迁移。')
      } else {
        setFormalEntryRequired(false)
        setFormalMessage(code === 'FORMAL_DISABLED' ? '正式入口尚未开放。' : '正式进度暂时无法连接，请稍后刷新。')
      }
    })
    return () => { active = false }
  }, [api, runFormalRequest])

  useEffect(() => {
    let active = true
    const refresh = () => {
      if (!active || document.visibilityState === 'hidden') return
      void formalSession.ensureFresh({
        onRecovering: () => setFormalMessage('正式会话正在自动恢复，当前学习状态仍保留…')
      }).then(() => {
        if (active) {
          setFormalEntryRequired(false)
          setFormalMessage('')
        }
      }).catch((error: unknown) => {
        if (!active) return
        if (error instanceof Error && error.message === 'FORMAL_ENTRY_REQUIRED') {
          setFormalEntryRequired(true)
          setFormalMessage('儿童正式入口已迁移。')
        } else {
          setFormalMessage('正式会话自动恢复失败，当前学习状态仍保留；联网后可再次操作。')
        }
      })
    }
    document.addEventListener('visibilitychange', refresh)
    window.addEventListener('pageshow', refresh)
    return () => {
      active = false
      document.removeEventListener('visibilitychange', refresh)
      window.removeEventListener('pageshow', refresh)
    }
  }, [formalSession])

  function markCompleted(module: 'listening' | 'speaking', courseId: string) {
    setCompleted((value) => mergeCompleted(value, module, courseId))
  }

  return (
    <div className="app-shell">
      <PwaStatus />
      <LearningRoutes api={api} parentSessionToken={parentSessionToken} formalSessionToken={formalSessionToken}
        runFormalRequest={runFormalRequest} completed={completed} formalMessage={formalMessage} formalEntryRequired={formalEntryRequired} markCompleted={markCompleted} onParentAuthenticated={setParentSessionToken} />
    </div>
  )
}
