import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const expectedRoot = 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'
const envId = 'family24-d7gqb6r6m2d722f7a'
assert.equal(projectRoot.toLowerCase(), expectedRoot.toLowerCase(), 'unexpected project root')

const npxCli = path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npx-cli.js')
const commands = [
  { TableName: 'sherlock_results', CommandType: 'COMMAND', Command: JSON.stringify({ count: 'sherlock_results', query: { data_kind: 'formal' } }) },
  { TableName: 'sherlock_results', CommandType: 'COMMAND', Command: JSON.stringify({ count: 'sherlock_results', query: { module_type: 'listening', data_kind: 'test' } }) }
]
const run = spawnSync(process.execPath, [npxCli, '--yes', '--package=@cloudbase/cli@3.8.0', 'tcb', '-e', envId,
  'db', 'nosql', 'execute', '--command', JSON.stringify(commands), '--json'], { encoding: 'utf8', windowsHide: true })

assert.equal(run.status, 0, run.stderr || run.stdout || 'CloudBase CLI failed')
const start = run.stdout.indexOf('{')
assert.ok(start >= 0, 'CloudBase CLI did not return JSON')
const response = JSON.parse(run.stdout.slice(start))
assert.ok(!response.error, `${response.error?.code}: ${response.error?.message}`)
const results = response.data?.Results || response.data?.results || response.data
assert.ok(Array.isArray(results), `unexpected CloudBase response: ${JSON.stringify(response)}`)
assert.equal(results.length, 2, 'both result counts must be returned')

function parseCount(item) {
  let value = Array.isArray(item) ? item[0] : item
  const encoded = value?.Result || value?.result
  if (typeof encoded === 'string') value = JSON.parse(encoded)
  const count = value?.n?.$numberInt ?? value?.n
  assert.ok(Number.isInteger(Number(count)), `unexpected count result: ${JSON.stringify(item)}`)
  return Number(count)
}
const formal = parseCount(results[0])
const listeningTest = parseCount(results[1])
assert.equal(formal, 0, `formal results were found in P2: ${formal}`)
console.log(`P2 CloudBase result verification passed: formal=${formal}, listening-test=${listeningTest}`)
