import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const expectedRoot = 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'
assert.equal(projectRoot.toLowerCase(), expectedRoot.toLowerCase(), 'unexpected project root')

const baseUrl = 'https://family24-d7gqb6r6m2d722f7a-1383960965.tcloudbaseapp.com/sherlock-english/'
const manifest = JSON.parse(await readFile(path.join(projectRoot, 'web/public/content/listening/audio-manifest.json'), 'utf8'))
const entries = Object.values(manifest.courses).flatMap((course) => Object.keys(course))

async function fetchOk(relativePath) {
  const response = await fetch(new URL(relativePath, baseUrl), { cache: 'no-store' })
  assert.equal(response.status, 200, `${relativePath} returned ${response.status}`)
  return response
}

const catalog = await (await fetchOk('content/listening/catalog.json')).json()
assert.equal(catalog.length, 12, 'online catalog must contain 12 courses')

const forbiddenKeys = new Set(['answer', 'transcript', 'tag', 'parent_note'])
function assertChildSafe(value, location = '$') {
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertChildSafe(item, `${location}[${index}]`))
    return
  }
  if (!value || typeof value !== 'object') return
  for (const [key, child] of Object.entries(value)) {
    assert.ok(!forbiddenKeys.has(key), `forbidden child field ${location}.${key}`)
    assertChildSafe(child, `${location}.${key}`)
  }
}

for (const { course_id: courseId } of catalog) {
  assert.match(courseId, /^W01D(?:39|4[0-9]|50)$/)
  const course = await (await fetchOk(`content/listening/${courseId}.json`)).json()
  assertChildSafe(course)
}

let nextIndex = 0
async function verifyAudioWorker() {
  while (nextIndex < entries.length) {
    const relativePath = entries[nextIndex++]
    const localBytes = await readFile(path.join(projectRoot, 'web/public', relativePath))
    const onlineBytes = Buffer.from(await (await fetchOk(relativePath)).arrayBuffer())
    const expectedHash = createHash('sha256').update(localBytes).digest('hex')
    const actualHash = createHash('sha256').update(onlineBytes).digest('hex')
    assert.equal(actualHash, expectedHash, `${relativePath} byte hash mismatch`)
  }
}

await Promise.all(Array.from({ length: 12 }, verifyAudioWorker))
console.log(`P2 online verification passed: ${catalog.length} child-safe courses, ${entries.length} audio hashes`)
