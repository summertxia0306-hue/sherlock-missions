import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const expectedRoot = 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'
assert.equal(projectRoot.toLowerCase(), expectedRoot.toLowerCase(), 'unexpected project root')

const baseUrl = new URL('https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/')
const plan = JSON.parse(await readFile(path.join(projectRoot, 'content/drafts/4A-T1-W01/audio-generation-plan.json'), 'utf8'))

async function fetchBytes(relativePath, fresh = false) {
  const url = new URL(relativePath, baseUrl)
  if (fresh) url.searchParams.set('p6', Date.now().toString())
  const response = await fetch(url, { cache: 'no-store' })
  assert.equal(response.status, 200, `${relativePath} returned ${response.status}`)
  return Buffer.from(await response.arrayBuffer())
}

function assertChildSafe(value, location = '$') {
  const forbidden = new Set(['answer', 'transcript', 'passage_transcript', 'tag', 'parent_note', 'expected', 'question'])
  if (Array.isArray(value)) return value.forEach((item, index) => assertChildSafe(item, `${location}[${index}]`))
  if (!value || typeof value !== 'object') return
  for (const [key, child] of Object.entries(value)) {
    assert.ok(!forbidden.has(key), `forbidden child field ${location}.${key}`)
    assertChildSafe(child, `${location}.${key}`)
  }
}

for (const module of ['listening', 'speaking']) {
  const catalog = JSON.parse((await fetchBytes(`content/${module}/catalog.json`, true)).toString('utf8'))
  assert.equal(catalog.length, 18, `${module} catalog count`)
  const hidden = catalog.filter((course) => course.visible === false)
  assert.equal(hidden.length, 6, `${module} hidden course count`)
  for (const entry of hidden) {
    assert.equal(entry.pair_id, entry.course_id.slice(1))
    assert.equal(entry.study_pack, entry.pair_id)
    const child = JSON.parse((await fetchBytes(`content/${module}/${entry.course_id}.json`, true)).toString('utf8'))
    assertChildSafe(child)
  }
}

let next = 0
const items = plan.items
async function audioWorker() {
  while (next < items.length) {
    const item = items[next++]
    const local = await readFile(path.join(projectRoot, item.path))
    const publicPath = item.path.replace(/^static\//, '')
    assert.notEqual(publicPath, item.path, `unexpected repository audio path ${item.path}`)
    const online = await fetchBytes(publicPath)
    assert.equal(createHash('sha256').update(online).digest('hex'), createHash('sha256').update(local).digest('hex'), item.path)
  }
}

await Promise.all(Array.from({ length: 12 }, audioWorker))
console.log(`P6 online test assets verified: 12 hidden child-safe courses, ${items.length} exact audio hashes`)
