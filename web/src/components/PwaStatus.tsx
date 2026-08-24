import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

export function PwaStatus() {
  const [online, setOnline] = useState(() => navigator.onLine)
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker
  } = useRegisterSW()

  useEffect(() => {
    const markOnline = () => setOnline(true)
    const markOffline = () => setOnline(false)
    window.addEventListener('online', markOnline)
    window.addEventListener('offline', markOffline)
    return () => {
      window.removeEventListener('online', markOnline)
      window.removeEventListener('offline', markOffline)
    }
  }, [])

  if (!online) {
    return <div className="status-banner" role="status">当前离线：已缓存页面仍可打开，提交需恢复网络。</div>
  }
  if (needRefresh) {
    return (
      <div className="status-banner" role="status">
        新版本已就绪。
        <button type="button" onClick={() => updateServiceWorker(true)}>立即更新</button>
        <button type="button" className="quiet" onClick={() => setNeedRefresh(false)}>稍后</button>
      </div>
    )
  }
  return null
}

