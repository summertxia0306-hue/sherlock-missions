import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, relative, resolve } from 'node:path'
import test from 'node:test'

import { prepareGitHubPagesRelease } from './prepare-github-pages-release-lib.mjs'

const expectedRemote = 'https://github.com/summertxia0306-hue/summertxia0306-hue.github.io.git'

async function write(path, content) {
  await mkdir(resolve(path, '..'), { recursive: true })
  await writeFile(path, content)
}

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'sherlock-pages-release-'))
  const pagesDir = join(root, 'pages')
  const distDir = join(root, 'dist')
  await mkdir(join(pagesDir, '.git'), { recursive: true })
  await write(join(pagesDir, '.git', 'config'), `[remote "origin"]\n\turl = ${expectedRemote}\n`)
  await write(join(pagesDir, 'index.html'), '<title>家庭 24 点</title>')
  await write(join(pagesDir, 'assets', 'family24.js'), 'family24-root-asset')
  await write(join(pagesDir, 'sherlock-english', 'old.js'), 'old release')

  await write(join(distDir, 'index.html'), '<script src="/sherlock-english/assets/app.js"></script>')
  await write(join(distDir, 'manifest.webmanifest'), '{"start_url":"/sherlock-english/","scope":"/sherlock-english/"}')
  await write(join(distDir, 'sw.js'), 'const scope = "/sherlock-english/"')
  await write(join(distDir, 'assets', 'app.js'), 'safe application bundle')
  for (const route of ['listening', 'speaking', 'parent']) {
    await write(join(distDir, route, 'index.html'), '<script src="/sherlock-english/assets/app.js"></script>')
  }
  await write(join(distDir, 'audio', 'listening', 'sample.mp3'), 'audio')
  return { root, pagesDir, distDir }
}

async function cleanup(root) {
  const safeRoot = resolve(tmpdir())
  assert.ok(resolve(root).startsWith(safeRoot), `unsafe cleanup path: ${root}`)
  await rm(root, { recursive: true, force: true })
}

test('replaces only sherlock-english and preserves every family24 root file', async () => {
  const { root, pagesDir, distDir } = await fixture()
  try {
    const result = await prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote })
    assert.equal(await readFile(join(pagesDir, 'index.html'), 'utf8'), '<title>家庭 24 点</title>')
    assert.equal(await readFile(join(pagesDir, 'assets', 'family24.js'), 'utf8'), 'family24-root-asset')
    await assert.rejects(readFile(join(pagesDir, 'sherlock-english', 'old.js')), /ENOENT/)
    assert.equal(await readFile(join(pagesDir, 'sherlock-english', 'assets', 'app.js'), 'utf8'), 'safe application bundle')
    assert.equal(result.target, 'sherlock-english')
    assert.equal(result.files, 8)
    assert.ok(result.bytes > 0)
    assert.deepEqual(result.changedRootFiles, [])
  } finally {
    await cleanup(root)
  }
})

test('refuses a pages checkout whose origin is not the protected repository', async () => {
  const { root, pagesDir, distDir } = await fixture()
  try {
    await write(join(pagesDir, '.git', 'config'), '[remote "origin"]\n\turl = https://github.com/example/wrong.git\n')
    await assert.rejects(
      prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote }),
      /Pages repository mismatch/
    )
  } finally {
    await cleanup(root)
  }
})

test('refuses an incomplete PWA build', async () => {
  const { root, pagesDir, distDir } = await fixture()
  try {
    await rm(join(distDir, 'sw.js'))
    await assert.rejects(
      prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote }),
      /required build file is missing: sw\.js/
    )
  } finally {
    await cleanup(root)
  }
})

test('refuses private paths and secret-like values in the public build', async () => {
  const { root, pagesDir, distDir } = await fixture()
  try {
    await write(join(distDir, 'private', 'student-records.txt'), 'must not publish')
    await assert.rejects(
      prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote }),
      /forbidden public path: private\/student-records\.txt/
    )
    await rm(join(distDir, 'private'), { recursive: true })
    await write(join(distDir, 'assets', 'leak.js'), 'PARENT_PASSWORD_SCRYPT=not-public')
    await assert.rejects(
      prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote }),
      /sensitive value marker found in assets\/leak\.js/
    )
  } finally {
    await cleanup(root)
  }
})

test('normalizes every reported path relative to the release directory', async () => {
  const { root, pagesDir, distDir } = await fixture()
  try {
    const result = await prepareGitHubPagesRelease({ pagesDir, distDir, expectedRemote })
    for (const file of result.manifest) {
      assert.equal(relative(distDir, join(distDir, file.path)).startsWith('..'), false)
      assert.equal(file.path.includes('\\'), false)
    }
  } finally {
    await cleanup(root)
  }
})
