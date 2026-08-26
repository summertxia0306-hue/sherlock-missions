import { useEffect, useState } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import type { SherlockApi } from './core/cloudbase-api'
import { cloudbaseApi } from './core/cloudbase-api'
import { PwaStatus } from './components/PwaStatus'
import { HomePage } from './pages/HomePage'
import { ListeningPage } from './pages/ListeningPage'
import { ParentPage } from './pages/ParentPage'
import { SpeakingPage } from './pages/SpeakingPage'

export function mergeCompleted(
  value: { listening: string[]; speaking: string[] }, module: 'listening' | 'speaking', courseId: string
) {
  return value[module].includes(courseId) ? value : { ...value, [module]: [...value[module], courseId].sort() }
}

function LearningRoutes({
  api, parentSessionToken, formalSessionToken, completed, formalMessage, markCompleted, onParentAuthenticated
}: {
  api: SherlockApi
  parentSessionToken: string
  formalSessionToken: string
  completed: { listening: string[]; speaking: string[] }
  formalMessage: string
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
    {!testMode && formalMessage && <p className="notice warning" role="status">{formalMessage}</p>}
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/listening" element={<ListeningPage api={api} sessionToken={sessionToken} dataKind={dataKind} completedCourseIds={listeningCompleted} onFormalCompleted={markCompleted.bind(null, 'listening')} />} />
      <Route path="/speaking" element={<SpeakingPage api={api} sessionToken={sessionToken} dataKind={dataKind} completedCourseIds={speakingCompleted} onFormalCompleted={markCompleted.bind(null, 'speaking')} />} />
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

  useEffect(() => {
    let active = true
    api.startChildSession().then(async (session) => {
      const progress = await api.getFormalProgress(session.session_token)
      if (!active) return
      setFormalSessionToken(session.session_token)
      setCompleted(progress.completed_course_ids)
      setFormalMessage('')
    }).catch((error: unknown) => {
      if (!active) return
      const code = error instanceof Error ? error.message : ''
      setFormalMessage(code === 'FORMAL_DISABLED' ? '正式入口尚未开放。' : '正式进度暂时无法连接，请稍后刷新。')
    })
    return () => { active = false }
  }, [api])

  function markCompleted(module: 'listening' | 'speaking', courseId: string) {
    setCompleted((value) => mergeCompleted(value, module, courseId))
  }

  return (
    <div className="app-shell">
      <PwaStatus />
      <LearningRoutes api={api} parentSessionToken={parentSessionToken} formalSessionToken={formalSessionToken}
        completed={completed} formalMessage={formalMessage} markCompleted={markCompleted} onParentAuthenticated={setParentSessionToken} />
    </div>
  )
}
