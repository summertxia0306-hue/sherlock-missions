import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
assert.equal(root.toLowerCase(), 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'.toLowerCase())

const revision = '5ba77dd641dfb21a954feff731484950637097f0'
const base = `https://gcore.jsdelivr.net/gh/summertxia0306-hue/sherlock-missions@${revision}/`
const plan = JSON.parse(await readFile(join(root, 'content/drafts/4A-T1-W01-UNIT3/audio-generation-plan.json'), 'utf8'))
const manifests = Object.fromEntries(await Promise.all(['listening', 'speaking'].map(async (module) => [
  module, JSON.parse(await readFile(join(root, `static/audio/${module}/manifest.json`), 'utf8'))
])))
assert.equal(plan.items.length, 154)

function hash(bytes) { return createHash('sha256').update(bytes).digest('hex') }

let next = 0
let verified = 0
async function worker() {
  while (next < plan.items.length) {
    const item = plan.items[next++]
    assert.ok(manifests[item.module]?.courses?.[item.course_id]?.[item.path], `Manifest missing ${item.path}`)
    const local = await readFile(join(root, item.path))
    assert.ok(local.length > 0, `Empty local audio ${item.path}`)
    let lastError
    for (let attempt = 0; attempt < 3; attempt += 1) {
      try {
        const response = await fetch(new URL(item.path, base), { signal: AbortSignal.timeout(20000) })
        assert.equal(response.status, 200, `${item.path}: HTTP ${response.status}`)
        const online = Buffer.from(await response.arrayBuffer())
        assert.equal(hash(online), hash(local), `SHA-256 mismatch ${item.path}`)
        lastError = null
        break
      } catch (error) {
        lastError = error
      }
    }
    if (lastError) throw lastError
    verified += 1
  }
}

await Promise.all(Array.from({ length: 8 }, worker))
assert.equal(verified, 154)
console.log(`Unit 3 audio online verified: ${verified}/154 SHA-256 matches at ${revision}`)
