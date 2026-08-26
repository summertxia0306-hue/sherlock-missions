import { Link } from 'react-router-dom'
import { visibleModules } from '../core/modules'

export function HomePage() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">SHERLOCK · ENGLISH LAB</p>
        <h1>本周任务</h1>
        <p className="hero-copy">正式课程已迁移到当前地址；历史完成进度会自动衔接。家长验收入口继续独立保存 test。</p>
        <div className="stage-pill">P5 正式入口 · 历史进度已衔接</div>
      </section>
      <section className="module-grid" aria-label="功能模块">
        {visibleModules().map((module) => (
          <Link className={`module-card module-${module.id}`} to={module.route} key={module.id}>
            <span className="module-icon" aria-hidden="true">{module.icon}</span>
            <span>
              <strong>{module.title}</strong>
              <small>{module.description}</small>
            </span>
            <span className="arrow" aria-hidden="true">→</span>
          </Link>
        ))}
      </section>
    </main>
  )
}
