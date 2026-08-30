import './sync-p2-assets.mjs'
import { cp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises'
import { dirname, join, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const sourceContent = join(projectRoot, 'content', 'speaking')
const sourceAudio = join(projectRoot, 'static', 'audio', 'speaking')
const webContent = join(projectRoot, 'web', 'public', 'content', 'speaking')
const webAudio = join(projectRoot, 'web', 'public', 'audio', 'speaking')
const functionContent = join(projectRoot, 'cloudfunctions', 'sherlock-api', 'content', 'speaking')
const functionOnly = process.argv.includes('--function-only')
const require = createRequire(import.meta.url)
const { sanitizeSpeakingCourse, stableVersion } = require('../cloudfunctions/sherlock-api/speaking-service.js')

function assertTarget(target) {
  const normalized = resolve(target).toLowerCase()
  if (!normalized.startsWith(`${projectRoot}${sep}`.toLowerCase()) || ![
    webContent, webAudio, functionContent
  ].map((item) => resolve(item).toLowerCase()).includes(normalized)) throw new Error(`Unsafe generated target: ${target}`)
}

async function recreate(target) {
  assertTarget(target)
  await rm(target, { recursive: true, force: true })
  await mkdir(target, { recursive: true })
}

async function main() {
  const manifest = JSON.parse(await readFile(join(sourceAudio, 'manifest.json'), 'utf8'))
  const files = (await readdir(sourceContent)).filter((name) => /^(?:S\d{2}D\d{2}|S[1-9][A-Z]-T\d{1,2}-W\d{2}-D\d{2})\.json$/.test(name)).sort()
  await recreate(functionContent)
  if (!functionOnly) { await recreate(webContent); await recreate(webAudio) }
  const catalog = []
  const publicManifest = { courses: {} }
  for (const file of files) {
    const raw = await readFile(join(sourceContent, file))
    const course = JSON.parse(raw.toString('utf8'))
    const assets = manifest.courses?.[course.course_id]
    if (!assets || typeof assets !== 'object') throw new Error(`Manifest missing course ${course.course_id}`)
    const version = stableVersion(course)
    await cp(join(sourceContent, file), join(functionContent, file))
    if (!functionOnly) {
      const child = sanitizeSpeakingCourse(course, version)
      await writeFile(join(webContent, file), `${JSON.stringify(child, null, 2)}\n`, 'utf8')
      catalog.push({
        course_id: course.course_id, course_version: version, title: course.title,
        course_type: course.course_type, week: course.week, day: course.day,
        visible: course.publication_status !== 'test',
        ...(course.pair_id ? { pair_id: course.pair_id } : {}),
        ...(course.study_pack ? { study_pack: course.study_pack } : {})
      })
      publicManifest.courses[course.course_id] = {}
      for (const [repoPath, hash] of Object.entries(assets)) {
        const rel = repoPath.replace(/^static\/audio\/speaking\//, '')
        if (rel === repoPath || rel.includes('..')) throw new Error(`Invalid manifest path ${repoPath}`)
        const source = join(sourceAudio, ...rel.split('/'))
        if ((await stat(source)).size < 1) throw new Error(`Empty audio ${repoPath}`)
        const target = join(webAudio, ...rel.split('/'))
        await mkdir(dirname(target), { recursive: true })
        await cp(source, target)
        publicManifest.courses[course.course_id][`audio/speaking/${rel.replaceAll('\\', '/')}`] = hash
      }
    }
  }
  if (!functionOnly) {
    await writeFile(join(webContent, 'catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`, 'utf8')
    await writeFile(join(webContent, 'audio-manifest.json'), `${JSON.stringify(publicManifest, null, 2)}\n`, 'utf8')
  }
  process.stdout.write(`P3 speaking assets synchronized (${functionOnly ? 'function' : 'web+function'}): ${files.length} courses\n`)
}

await main()
