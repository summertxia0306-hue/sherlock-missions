import { useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import type { SherlockApi } from './core/cloudbase-api'
import { cloudbaseApi } from './core/cloudbase-api'
import { PwaStatus } from './components/PwaStatus'
import { HomePage } from './pages/HomePage'
import { ListeningPage } from './pages/ListeningPage'
import { ModulePlaceholder } from './pages/ModulePlaceholder'
import { ParentPage } from './pages/ParentPage'

export function App({ api = cloudbaseApi }: { api?: SherlockApi }) {
  const [parentSessionToken, setParentSessionToken] = useState('')
  return (
    <div className="app-shell">
      <PwaStatus />
      <header className="topbar">
        <Link className="brand" to="/" aria-label="返回首页">
          <span className="brand-mark">S</span>
          <span>夏洛恪英语</span>
        </Link>
        <span className="test-label">TEST</span>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/listening" element={<ListeningPage api={api} sessionToken={parentSessionToken} />} />
        <Route path="/speaking" element={<ModulePlaceholder title="跟读口语" phase="P3" />} />
        <Route path="/parent" element={<ParentPage api={api} onAuthenticated={setParentSessionToken} />} />
        <Route path="*" element={<main className="center-card"><h1>页面不存在</h1><Link to="/">返回首页</Link></main>} />
      </Routes>
    </div>
  )
}
