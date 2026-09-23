import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parseListeningCatalog, parseListeningCourse } from './course'

const publicRoot = join(process.cwd(), 'public')
const contentRoot = join(publicRoot, 'content', 'listening')

function audioFiles(root: string): string[] {
  return readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const path = join(root, entry.name)
    return entry.isDirectory() ? audioFiles(path) : [relative(publicRoot, path).replaceAll('\\', '/')]
  })
}

describe('generated listening assets', () => {
  it('publishes only the approved W01D39-W01D50 history and current formal courses', () => {
    const rawCatalog = JSON.parse(readFileSync(join(contentRoot, 'catalog.json'), 'utf8'))
    const catalog = parseListeningCatalog(rawCatalog)
    expect(catalog.courses.map((course) => course.course_id)).toEqual(
      [
        ...Array.from({ length: 12 }, (_, index) => `W01D${index + 39}`),
        ...Array.from({ length: 25 }, (_, index) => `L4A-T1-W01-D${String(index + 1).padStart(2, '0')}`)
      ]
    )
    expect(catalog.testCourses().filter((course) => !course.visible)).toEqual([])
    for (let day = 1; day <= 25; day += 1) {
      expect(existsSync(join(contentRoot, `L4A-T1-W01-D${String(day).padStart(2, '0')}.json`))).toBe(true)
    }
    for (const entry of catalog.testCourses()) {
      const raw = readFileSync(join(contentRoot, `${entry.course_id}.json`), 'utf8')
      const course = parseListeningCourse(JSON.parse(raw))
      const questionCount = course.sections.flatMap((section) => section.questions).length
      expect([20, 25]).toContain(questionCount)
      expect(raw).not.toMatch(/"answer"|"transcript"|"tag"|"parent_note"/)
    }
  })

  it('accounts for every generated audio asset through the public manifest', () => {
    const manifest = JSON.parse(readFileSync(join(contentRoot, 'audio-manifest.json'), 'utf8')) as {
      courses: Record<string, Record<string, string>>
    }
    const assets = Object.values(manifest.courses).flatMap((course) => Object.keys(course))
    expect(assets.sort()).toEqual(audioFiles(join(publicRoot, 'audio', 'listening')).sort())
    for (const asset of assets) {
      const file = join(publicRoot, ...asset.split('/'))
      expect(existsSync(file), asset).toBe(true)
      expect(statSync(file).size, asset).toBeGreaterThan(0)
    }
  })
})
