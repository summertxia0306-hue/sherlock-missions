import { Link } from 'react-router-dom'
import { visibleModules } from '../core/modules'

export function HomePage() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">SHERLOCK · ENGLISH LAB</p>
        <h1>本周任务</h1>
        <p className="hero-copy">P4 正在迁移历史学习证据。家长端可独立查询 formal/test；儿童正式入口仍关闭，新操作只保存 test。</p>
        <div className="stage-pill">P4 历史迁移 · formal/test 独立查询</div>
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
