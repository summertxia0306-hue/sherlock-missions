import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..', 'cloud-resources', 'formal-cutover-shell')

test('migration shell points only to the approved GitHub Pages entry', async () => {
  const html = await readFile(resolve(root, 'index.html'), 'utf8')
  assert.match(html, /https:\/\/summertxia0306-hue\.github\.io\/sherlock-english\//)
  assert.match(html, /serviceWorker\.register\('\.\/sw\.js'/)
  assert.doesNotMatch(html, /VITE_|PARENT_|API_SECRET|ACCESS_KEY/)
})

test('migration worker clears only Sherlock entries and never deletes whole shared caches', async () => {
  const worker = await readFile(resolve(root, 'sw.js'), 'utf8')
  assert.match(worker, /\/sherlock-english\//)
  assert.match(worker, /cache\.delete\(request\)/)
  assert.doesNotMatch(worker, /caches\.delete\(/)
  assert.match(worker, /skipWaiting\(\)/)
  assert.match(worker, /clients\.claim\(\)/)
})
