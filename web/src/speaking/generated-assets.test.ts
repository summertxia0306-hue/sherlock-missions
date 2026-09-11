import { existsSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { parseSpeakingCatalog, parseSpeakingCourse } from './course'

const publicRoot = join(process.cwd(), 'public')
const contentRoot = join(publicRoot, 'content', 'speaking')

describe('generated speaking assets', () => {
  it('publishes S01D39-S01D50 followed by the fifteen current term courses', () => {
    const catalog = parseSpeakingCatalog(JSON.parse(readFileSync(join(contentRoot, 'catalog.json'), 'utf8')))
    expect(catalog.courses.map((course) => course.course_id)).toEqual(
      [
        ...Array.from({ length: 12 }, (_, index) => `S01D${index + 39}`),
        ...Array.from({ length: 15 }, (_, index) => `S4A-T1-W01-D${String(index + 1).padStart(2, '0')}`)
      ]
    )
    for (let day = 1; day <= 15; day += 1) {
      expect(existsSync(join(contentRoot, `S4A-T1-W01-D${String(day).padStart(2, '0')}.json`))).toBe(true)
    }
    for (let day = 16; day <= 20; day += 1) {
      expect(existsSync(join(contentRoot, `S4A-T1-W01-D${String(day).padStart(2, '0')}.json`))).toBe(false)
    }
    for (const entry of catalog.courses) {
      expect(() => parseSpeakingCourse(JSON.parse(readFileSync(join(contentRoot, `${entry.course_id}.json`), 'utf8')))).not.toThrow()
    }
  })

  it('publishes exactly the approved speaking audio set', () => {
    const manifest = JSON.parse(readFileSync(join(contentRoot, 'audio-manifest.json'), 'utf8')) as {
      courses: Record<string, Record<string, string>>
    }
    expect(Object.keys(manifest.courses)).toEqual([
      ...Array.from({ length: 12 }, (_, index) => `S01D${index + 39}`),
      ...Array.from({ length: 15 }, (_, index) => `S4A-T1-W01-D${String(index + 1).padStart(2, '0')}`)
    ])
    const assets = Object.values(manifest.courses).flatMap((course) => Object.keys(course))
    expect(assets).toHaveLength(216)
    for (const asset of assets) {
      const file = join(publicRoot, ...asset.split('/'))
      expect(existsSync(file), asset).toBe(true)
      expect(statSync(file).size, asset).toBeGreaterThan(0)
    }
  })
})
