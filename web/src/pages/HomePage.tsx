import { Link } from 'react-router-dom'
import { visibleModules } from '../core/modules'

export function HomePage() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">SHERLOCK · ENGLISH LAB</p>
        <h1>本周任务</h1>
        <p className="hero-copy">跟读口语正在 P3 验收。听力继续可用，本阶段仍只保存 test，不写正式学习记录。</p>
        <div className="stage-pill">P3 口语 · 仅开放家长 test 验收</div>
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
