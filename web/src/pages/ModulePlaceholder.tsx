import { Link } from 'react-router-dom'

export function ModulePlaceholder({ title, phase }: { title: string; phase: string }) {
  return (
    <main className="center-card">
      <p className="eyebrow">基础入口已就绪</p>
      <h1>{title}</h1>
      <p>课程业务将在 {phase} 按原合同迁移。P1 不提前写入正式学习数据。</p>
      <div className="stage-pill">formal 入口关闭</div>
      <Link className="back-link" to="/">← 返回本周任务</Link>
    </main>
  )
}

