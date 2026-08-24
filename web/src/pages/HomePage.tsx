import { Link } from 'react-router-dom'
import { visibleModules } from '../core/modules'

export function HomePage() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">SHERLOCK · ENGLISH LAB</p>
        <h1>本周任务</h1>
        <p className="hero-copy">新的学习空间正在搭建。本阶段只验证基础设施，不会写入正式学习记录。</p>
        <div className="stage-pill">P1 仅开放家长 test 验收</div>
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

