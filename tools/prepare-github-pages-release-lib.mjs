import { createHash } from 'node:crypto'
import { copyFile, mkdir, readFile, readdir, rm, stat } from 'node:fs/promises'
import { basename, join, relative, resolve, sep } from 'node:path'

const requiredBuildFiles = [
  'index.html',
  'manifest.webmanifest',
  'sw.js',
  'listening/index.html',
  'speaking/index.html',
  'parent/index.html'
]

const textExtensions = new Set(['.css', '.html', '.js', '.json', '.svg', '.txt', '.webmanifest', '.xml'])
const sensitiveMarkers = [
  /PARENT_PASSWORD_SCRYPT\s*[=:]/i,
  /PARENT_SESSION_HMAC_KEY\s*[=:]/i,
  /SPEAKING_INTERNAL_HMAC_KEY\s*[=:]/i,
  /(?:XUNFEI|ISE)_(?:API_KEY|API_SECRET)\s*[=:]/i,
  /(?:CLOUDBASE|TENCENTCLOUD)_(?:SECRET_ID|SECRET_KEY)\s*[=:]/i
]

function slash(path) {
  return path.replaceAll('\\', '/')
}

function extension(path) {
  const name = basename(path)
  const index = name.lastIndexOf('.')
  return index < 0 ? '' : name.slice(index).toLowerCase()
}

function assertInside(parent, child, label) {
  const safeParent = resolve(parent) + sep
  const resolvedChild = resolve(child)
  if (!resolvedChild.startsWith(safeParent)) throw new Error(`unsafe ${label} path: ${resolvedChild}`)
}

async function exists(path) {
  try {
    await stat(path)
    return true
  } catch (error) {
    if (error?.code === 'ENOENT') return false
    throw error
  }
}

async function listFiles(root, options = {}) {
  const files = []
  const excludedTopLevel = new Set(options.excludedTopLevel || [])

  async function visit(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const absolute = join(directory, entry.name)
      const path = slash(relative(root, absolute))
      if (!path.includes('/') && excludedTopLevel.has(entry.name)) continue
      if (entry.isDirectory()) await visit(absolute)
      else if (entry.isFile()) files.push({ absolute, path })
    }
  }

  await visit(root)
  return files.sort((first, second) => first.path.localeCompare(second.path))
}

async function digest(path) {
  const content = await readFile(path)
  return createHash('sha256').update(content).digest('hex')
}

async function snapshotRoot(pagesDir, target) {
  const files = await listFiles(pagesDir, { excludedTopLevel: ['.git', target] })
  return new Map(await Promise.all(files.map(async (file) => [file.path, await digest(file.absolute)])))
}

function changedFiles(before, after) {
  return [...new Set([...before.keys(), ...after.keys()])]
    .filter((path) => before.get(path) !== after.get(path))
    .sort()
}

async function validateRepository(pagesDir, expectedRemote) {
  const configPath = join(pagesDir, '.git', 'config')
  if (!await exists(configPath)) throw new Error('Pages checkout is missing .git/config')
  const config = await readFile(configPath, 'utf8')
  if (!config.includes(expectedRemote)) throw new Error('Pages repository mismatch')
}

async function validateBuild(distDir) {
  for (const path of requiredBuildFiles) {
    if (!await exists(join(distDir, ...path.split('/')))) throw new Error(`required build file is missing: ${path}`)
  }

  const files = await listFiles(distDir)
  for (const file of files) {
    const lowerPath = file.path.toLowerCase()
    if (lowerPath === '.env' || lowerPath.startsWith('.env.') || lowerPath.startsWith('private/')
      || lowerPath.includes('/private/') || lowerPath.includes('student-records') || lowerPath.includes('school-evidence')) {
      throw new Error(`forbidden public path: ${file.path}`)
    }
    if (!textExtensions.has(extension(file.path))) continue
    const content = await readFile(file.absolute, 'utf8')
    if (sensitiveMarkers.some((pattern) => pattern.test(content))) {
      throw new Error(`sensitive value marker found in ${file.path}`)
    }
  }

  const index = await readFile(join(distDir, 'index.html'), 'utf8')
  const manifest = await readFile(join(distDir, 'manifest.webmanifest'), 'utf8')
  const serviceWorker = await readFile(join(distDir, 'sw.js'), 'utf8')
  for (const [label, content] of [['index.html', index], ['manifest.webmanifest', manifest], ['sw.js', serviceWorker]]) {
    if (!content.includes('/sherlock-english/')) throw new Error(`${label} does not use /sherlock-english/`)
  }
  return files
}

async function copyTree(source, destination) {
  for (const entry of await readdir(source, { withFileTypes: true })) {
    const sourcePath = join(source, entry.name)
    const destinationPath = join(destination, entry.name)
    if (entry.isDirectory()) {
      await mkdir(destinationPath, { recursive: true })
      await copyTree(sourcePath, destinationPath)
    } else if (entry.isFile()) {
      await copyFile(sourcePath, destinationPath)
    }
  }
}

export async function prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote, target = 'sherlock-english' }) {
  if (target !== 'sherlock-english') throw new Error(`unsupported Pages target: ${target}`)
  pagesDir = resolve(pagesDir)
  distDir = resolve(distDir)
  if (!await exists(pagesDir) || !await exists(distDir)) throw new Error('Pages checkout or build directory is missing')

  await validateRepository(pagesDir, expectedRemote)
  const buildFiles = await validateBuild(distDir)
  const before = await snapshotRoot(pagesDir, target)
  const targetDir = join(pagesDir, target)
  assertInside(pagesDir, targetDir, 'Pages target')

  await rm(targetDir, { recursive: true, force: true })
  await mkdir(targetDir, { recursive: true })
  await copyTree(distDir, targetDir)

  const after = await snapshotRoot(pagesDir, target)
  const changedRootFiles = changedFiles(before, after)
  if (changedRootFiles.length) throw new Error(`protected Pages root changed: ${changedRootFiles.join(', ')}`)

  const manifest = await Promise.all(buildFiles.map(async (file) => {
    const info = await stat(file.absolute)
    return { path: file.path, bytes: info.size, sha256: await digest(file.absolute) }
  }))
  return {
    target,
    files: manifest.length,
    bytes: manifest.reduce((total, file) => total + file.bytes, 0),
    changedRootFiles,
    manifest
  }
}
