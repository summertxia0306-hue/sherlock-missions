import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
assert.equal(projectRoot.toLowerCase(), 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'.toLowerCase())

const revision = '5cc0978'
const baseUrl = `https://cdn.jsdelivr.net/gh/summertxia0306-hue/sherlock-missions@${revision}/`
const plan = JSON.parse(await readFile(path.join(projectRoot, 'content/drafts/4A-T1-W01-STARTER/audio-generation-plan.json'), 'utf8'))

let next = 0
let verified = 0
async function worker() {
  while (next < plan.items.length) {
    const item = plan.items[next++]
    const local = await readFile(path.join(projectRoot, item.path))
    const response = await fetch(new URL(item.path, baseUrl), { cache: 'no-store' })
    assert.equal(response.status, 200, item.path)
    const online = Buffer.from(await response.arrayBuffer())
    assert.equal(
      createHash('sha256').update(online).digest('hex'),
      createHash('sha256').update(local).digest('hex'),
      item.path,
    )
    verified += 1
  }
}

await Promise.all(Array.from({ length: 12 }, worker))
assert.equal(verified, 134)
console.log(`Starter audio online verified: ${verified}/134 SHA-256 matches at ${revision}`)
