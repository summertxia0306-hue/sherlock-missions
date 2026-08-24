import { existsSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parseListeningCatalog, parseListeningCourse } from './course'

const publicRoot = join(process.cwd(), 'public')
const contentRoot = join(publicRoot, 'content', 'listening')

describe('P2 generated listening assets', () => {
  it('publishes exactly W01D39-50 from one source and strips sensitive child fields', () => {
    const rawCatalog = JSON.parse(readFileSync(join(contentRoot, 'catalog.json'), 'utf8'))
    const catalog = parseListeningCatalog(rawCatalog)
    expect(catalog.courses.map((course) => course.course_id)).toEqual(
      Array.from({ length: 12 }, (_, index) => `W01D${index + 39}`)
    )
    for (const entry of catalog.courses) {
      const raw = readFileSync(join(contentRoot, `${entry.course_id}.json`), 'utf8')
      const course = parseListeningCourse(JSON.parse(raw))
      expect(course.sections.flatMap((section) => section.questions)).toHaveLength(20)
      expect(raw).not.toMatch(/"answer"|"transcript"|"tag"|"parent_note"/)
    }
  })

  it('accounts for every generated audio asset through the public manifest', () => {
    const manifest = JSON.parse(readFileSync(join(contentRoot, 'audio-manifest.json'), 'utf8')) as {
      courses: Record<string, Record<string, string>>
    }
    const assets = Object.values(manifest.courses).flatMap((course) => Object.keys(course))
    expect(assets).toHaveLength(216)
    for (const asset of assets) {
      const file = join(publicRoot, ...asset.split('/'))
      expect(existsSync(file), asset).toBe(true)
      expect(statSync(file).size, asset).toBeGreaterThan(0)
    }
  })
})
