import { createHash } from 'node:crypto'
import { cp, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises'
import { dirname, join, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const sourceContent = join(projectRoot, 'content', 'listening')
const sourceAudio = join(projectRoot, 'static', 'audio', 'listening')
const webContent = join(projectRoot, 'web', 'public', 'content', 'listening')
const webAudio = join(projectRoot, 'web', 'public', 'audio', 'listening')
const functionContent = join(projectRoot, 'cloudfunctions', 'sherlock-api', 'content', 'listening')
const functionOnly = process.argv.includes('--function-only')
const require = createRequire(import.meta.url)
const { sanitizeCourse } = require('../cloudfunctions/sherlock-api/listening-service.js')

function assertGeneratedTarget(target) {
  const normalizedRoot = `${projectRoot}${sep}`.toLowerCase()
  const normalized = resolve(target).toLowerCase()
  if (!normalized.startsWith(normalizedRoot) || ![
    resolve(webContent).toLowerCase(), resolve(webAudio).toLowerCase(), resolve(functionContent).toLowerCase()
  ].includes(normalized)) {
    throw new Error(`Unsafe generated target: ${target}`)
  }
}

async function recreate(target) {
  assertGeneratedTarget(target)
  await rm(target, { recursive: true, force: true })
  await mkdir(target, { recursive: true })
}

function versionOf(raw) {
  return createHash('sha256').update(raw).digest('hex').slice(0, 16)
}

async function main() {
  const manifest = JSON.parse(await readFile(join(sourceAudio, 'manifest.json'), 'utf8'))
  const files = (await readdir(sourceContent)).filter((name) => /^W\d{2}D\d{2}\.json$/.test(name)).sort()
  await recreate(functionContent)
  if (!functionOnly) {
    await recreate(webContent)
    await recreate(webAudio)
  }
  const catalog = []
  const publicManifest = { courses: {} }
  for (const file of files) {
    const raw = await readFile(join(sourceContent, file))
    const course = JSON.parse(raw.toString('utf8'))
    const assets = manifest.courses?.[course.course_id]
    if (!assets || typeof assets !== 'object') throw new Error(`Manifest missing course ${course.course_id}`)
    const version = versionOf(raw)
    await cp(join(sourceContent, file), join(functionContent, file))
    if (!functionOnly) {
      const child = sanitizeCourse(course, assets, version)
      await writeFile(join(webContent, file), `${JSON.stringify(child, null, 2)}\n`, 'utf8')
      catalog.push({
        course_id: course.course_id, course_version: version, title: course.title,
        course_type: course.course_type, week: course.week, day: course.day, visible: true
      })
      publicManifest.courses[course.course_id] = {}
      for (const [repoPath, hash] of Object.entries(assets)) {
        const rel = repoPath.replace(/^static\/audio\/listening\//, '')
        if (rel === repoPath || rel.includes('..')) throw new Error(`Invalid manifest path ${repoPath}`)
        const source = join(sourceAudio, ...rel.split('/'))
        if ((await stat(source)).size < 1) throw new Error(`Empty audio ${repoPath}`)
        const target = join(webAudio, ...rel.split('/'))
        await mkdir(dirname(target), { recursive: true })
        await cp(source, target)
        publicManifest.courses[course.course_id][`audio/listening/${rel.replaceAll('\\', '/')}`] = hash
      }
    }
  }
  if (!functionOnly) {
    await writeFile(join(webContent, 'catalog.json'), `${JSON.stringify(catalog, null, 2)}\n`, 'utf8')
    await writeFile(join(webContent, 'audio-manifest.json'), `${JSON.stringify(publicManifest, null, 2)}\n`, 'utf8')
  }
  const mode = functionOnly ? 'function' : 'web+function'
  process.stdout.write(`P2 assets synchronized (${mode}): ${files.length} courses\n`)
}

await main()
