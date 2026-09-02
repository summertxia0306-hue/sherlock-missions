import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { prepareDomesticGatewayRelease } from './prepare-domestic-gateway-release.mjs'

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), 'sherlock-domestic-release-'))
  const source = join(root, 'dist')
  const target = join(root, 'public-app')
  await mkdir(join(source, 'assets'), { recursive: true })
  await mkdir(join(source, 'content', 'listening'), { recursive: true })
  await mkdir(join(source, 'audio', 'listening', 'W01D50'), { recursive: true })
  await mkdir(join(source, 'private'), { recursive: true })
  await writeFile(join(source, 'index.html'), '<!doctype html><script src="/sherlock-api/assets/app.js"></script>')
  await writeFile(join(source, 'assets', 'app.js'), 'console.info("ok")')
  await writeFile(join(source, 'assets', 'app.js.map'), '{"secret":"source"}')
  await writeFile(join(source, 'content', 'listening', 'catalog.json'), '[{"course_id":"W01D50"}]')
  await writeFile(join(source, 'sw.js'), 'self.skipWaiting()')
  await writeFile(join(source, 'audio', 'listening', 'W01D50', 'q01.mp3'), 'audio-bytes')
  await writeFile(join(source, 'private', 'student.json'), '{"student":"secret"}')
  await writeFile(join(source, '.env'), 'SECRET=value')
  return { root, source, target }
}

test('copies only the bounded non-audio PWA allowlist and writes a hashed manifest', async () => {
  const { root, source, target } = await fixture()
  try {
    const summary = await prepareDomesticGatewayRelease(source, target)
    assert.equal(summary.fileCount, 4)
    assert.ok(summary.totalBytes < 1024 * 1024)

    const manifest = JSON.parse(await readFile(join(target, 'static-manifest.json'), 'utf8'))
    assert.deepEqual(Object.keys(manifest.files).sort(), [
      'assets/app.js',
      'content/listening/catalog.json',
      'index.html',
      'sw.js'
    ])
    assert.equal(manifest.files['index.html'].contentType, 'text/html; charset=utf-8')
    assert.match(manifest.files['assets/app.js'].sha256, /^[a-f0-9]{64}$/)
    assert.deepEqual(Object.keys(manifest.audio), ['audio/listening/W01D50/q01.mp3'])
    assert.equal(manifest.audio['audio/listening/W01D50/q01.mp3'].bytes, 11)
    await assert.rejects(readFile(join(target, 'audio', 'listening', 'W01D50', 'q01.mp3')))
    await assert.rejects(readFile(join(target, 'private', 'student.json')))
    await assert.rejects(readFile(join(target, '.env')))
    await assert.rejects(readFile(join(target, 'assets', 'app.js.map')))
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})

test('refuses an oversized non-audio function package instead of producing a partial target', async () => {
  const { root, source, target } = await fixture()
  try {
    await writeFile(join(source, 'assets', 'oversized.js'), Buffer.alloc(2 * 1024 * 1024 + 1))
    await assert.rejects(
      prepareDomesticGatewayRelease(source, target, { maxBytes: 2 * 1024 * 1024 }),
      /DOMESTIC_RELEASE_TOO_LARGE/
    )
    await assert.rejects(readFile(join(target, 'static-manifest.json')))
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})
