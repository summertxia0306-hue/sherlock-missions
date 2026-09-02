import { createHash, randomUUID } from 'node:crypto'
import { mkdir, readFile, readdir, rename, rm, stat, writeFile } from 'node:fs/promises'
import { basename, dirname, extname, join, relative, resolve, sep } from 'node:path'

const DEFAULT_MAX_BYTES = 2 * 1024 * 1024
const ALLOWED_EXTENSIONS = new Set(['.css', '.html', '.js', '.json', '.svg', '.webmanifest', '.woff2'])
const BLOCKED_SEGMENTS = new Set(['audio', 'private'])
const CONTENT_TYPES = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
  '.woff2': 'font/woff2'
}

function portablePath(path) {
  return path.split(sep).join('/')
}

async function collectFiles(sourceRoot, directory = sourceRoot) {
  const collected = []
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || BLOCKED_SEGMENTS.has(entry.name)) continue
    const absolute = join(directory, entry.name)
    if (entry.isDirectory()) {
      collected.push(...await collectFiles(sourceRoot, absolute))
      continue
    }
    if (!entry.isFile()) continue
    const extension = extname(entry.name).toLowerCase()
    if (!ALLOWED_EXTENSIONS.has(extension) || entry.name.endsWith('.map')) continue
    const relativePath = portablePath(relative(sourceRoot, absolute))
    if (!relativePath || relativePath.startsWith('../') || relativePath.includes('/../')) {
      throw new Error('DOMESTIC_RELEASE_PATH_INVALID')
    }
    collected.push({ absolute, relativePath, extension })
  }
  return collected.sort((a, b) => a.relativePath.localeCompare(b.relativePath))
}

async function collectAudio(sourceRoot) {
  const audioRoot = join(sourceRoot, 'audio')
  try {
    const entries = []
    async function walk(directory) {
      for (const entry of await readdir(directory, { withFileTypes: true })) {
        if (entry.name.startsWith('.')) continue
        const absolute = join(directory, entry.name)
        if (entry.isDirectory()) {
          await walk(absolute)
          continue
        }
        if (!entry.isFile() || extname(entry.name).toLowerCase() !== '.mp3') continue
        const relativePath = portablePath(relative(sourceRoot, absolute))
        if (!/^audio\/(?:listening|speaking)\/[A-Za-z0-9-]+\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+\.mp3$/.test(relativePath)) {
          throw new Error('DOMESTIC_RELEASE_AUDIO_PATH_INVALID')
        }
        entries.push({ relativePath, bytes: (await stat(absolute)).size })
      }
    }
    await walk(audioRoot)
    return entries.sort((a, b) => a.relativePath.localeCompare(b.relativePath))
  } catch (error) {
    if (error?.code === 'ENOENT') return []
    throw error
  }
}

export async function prepareDomesticGatewayRelease(source, target, options = {}) {
  const sourceRoot = resolve(source)
  const targetRoot = resolve(target)
  const sourceStats = await stat(sourceRoot)
  if (!sourceStats.isDirectory() || targetRoot === sourceRoot || targetRoot.startsWith(`${sourceRoot}${sep}`)) {
    throw new Error('DOMESTIC_RELEASE_PATH_INVALID')
  }

  const maxBytes = Number(options.maxBytes || DEFAULT_MAX_BYTES)
  const files = await collectFiles(sourceRoot)
  const audio = await collectAudio(sourceRoot)
  const prepared = []
  let totalBytes = 0
  for (const file of files) {
    const body = await readFile(file.absolute)
    totalBytes += body.byteLength
    if (totalBytes > maxBytes) throw new Error('DOMESTIC_RELEASE_TOO_LARGE')
    prepared.push({
      ...file,
      body,
      sha256: createHash('sha256').update(body).digest('hex')
    })
  }
  if (!prepared.some((file) => file.relativePath === 'index.html')) {
    throw new Error('DOMESTIC_RELEASE_INDEX_MISSING')
  }

  const temporaryRoot = join(dirname(targetRoot), `.${basename(targetRoot)}.tmp-${randomUUID()}`)
  await rm(temporaryRoot, { recursive: true, force: true })
  try {
    await mkdir(temporaryRoot, { recursive: true })
    const manifest = { version: 1, totalBytes, files: {}, audio: {} }
    for (const file of prepared) {
      const destination = join(temporaryRoot, ...file.relativePath.split('/'))
      await mkdir(dirname(destination), { recursive: true })
      await writeFile(destination, file.body)
      manifest.files[file.relativePath] = {
        contentType: CONTENT_TYPES[file.extension],
        bytes: file.body.byteLength,
        sha256: file.sha256
      }
    }
    for (const item of audio) manifest.audio[item.relativePath] = { bytes: item.bytes }
    await writeFile(join(temporaryRoot, 'static-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
    await rm(targetRoot, { recursive: true, force: true })
    await rename(temporaryRoot, targetRoot)
  } catch (error) {
    await rm(temporaryRoot, { recursive: true, force: true })
    throw error
  }
  return { fileCount: prepared.length, totalBytes }
}

if (process.argv[1] && resolve(process.argv[1]) === import.meta.filename) {
  const [, , source, target] = process.argv
  if (!source || !target) throw new Error('Usage: node prepare-domestic-gateway-release.mjs <source> <target>')
  const summary = await prepareDomesticGatewayRelease(source, target)
  process.stdout.write(`Domestic gateway release: ${summary.fileCount} files, ${summary.totalBytes} bytes\n`)
}
