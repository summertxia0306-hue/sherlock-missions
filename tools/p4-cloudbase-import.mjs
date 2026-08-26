import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { attachRecordingPlan, cloudResultDocument, compareMigratedDocuments, planResultImport, reconcileMigration, sha256 } from './p4-migration-lib.mjs'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const expectedRoot = 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'
const expectedEnv = 'family24-d7gqb6r6m2d722f7a'
assert.equal(projectRoot.toLowerCase(), expectedRoot.toLowerCase(), 'unexpected project root')

function argument(name) {
  const index = process.argv.indexOf(name)
  return index >= 0 ? process.argv[index + 1] : undefined
}

const planFile = path.resolve(argument('--plan') || '')
const envId = argument('--env') || expectedEnv
const execute = process.argv.includes('--execute')
const verifySamples = process.argv.includes('--verify-samples')
assert.equal(envId, expectedEnv, 'unexpected CloudBase environment')
assert.ok(fs.existsSync(planFile), 'migration plan not found')
const artifactRoot = path.dirname(planFile)
assert.ok(!artifactRoot.startsWith(`${projectRoot}${path.sep}`), 'private migration plan must stay outside the public repository')
const migration = JSON.parse(fs.readFileSync(planFile, 'utf8'))
assert.equal(migration.summary.anomalies.length, 0, 'source snapshot has anomalies')

function resolveTcbCli() {
  const npxRoot = path.join(process.env.LOCALAPPDATA || '', 'npm-cache', '_npx')
  for (const entry of fs.existsSync(npxRoot) ? fs.readdirSync(npxRoot) : []) {
    const packageRoot = path.join(npxRoot, entry, 'node_modules', '@cloudbase', 'cli')
    const packageFile = path.join(packageRoot, 'package.json')
    const cliFile = path.join(packageRoot, 'dist', 'standalone', 'cli.js')
    if (!fs.existsSync(packageFile) || !fs.existsSync(cliFile)) continue
    const packageJson = JSON.parse(fs.readFileSync(packageFile, 'utf8'))
    if (packageJson.version === '3.8.0') return cliFile
  }
  throw new Error('CloudBase CLI 3.8.0 is not available in the npm cache')
}

const tcbCli = resolveTcbCli()

function extractJson(output) {
  const start = output.indexOf('{')
  if (start < 0) throw new Error(`CloudBase CLI returned no JSON: ${output.slice(0, 500)}`)
  let depth = 0; let quoted = false; let escaped = false
  for (let index = start; index < output.length; index += 1) {
    const character = output[index]
    if (quoted) {
      if (escaped) escaped = false
      else if (character === '\\') escaped = true
      else if (character === '"') quoted = false
    } else if (character === '"') quoted = true
    else if (character === '{') depth += 1
    else if (character === '}' && --depth === 0) return JSON.parse(output.slice(start, index + 1))
  }
  throw new Error('CloudBase CLI JSON was incomplete')
}

function tcb(args) {
  const run = spawnSync(process.execPath, [tcbCli, '-e', envId, ...args], {
    encoding: 'utf8', windowsHide: true, maxBuffer: 64 * 1024 * 1024
  })
  if (run.status !== 0) {
    const diagnostic = String(run.stderr || run.stdout || '').replaceAll(/\s+/g, ' ').slice(-1200)
    throw new Error(`CloudBase CLI failed (exit=${run.status}): ${diagnostic || 'no diagnostic output'}`)
  }
  const parsed = extractJson(run.stdout)
  if (parsed.error) throw new Error(`${parsed.error.code}: ${parsed.error.message}`)
  return parsed.data
}

function unwrap(value) {
  if (Array.isArray(value)) return value.map(unwrap)
  if (value && typeof value === 'object') {
    if ('$numberInt' in value) return Number(value.$numberInt)
    if ('$numberLong' in value) return Number(value.$numberLong)
    if ('$numberDouble' in value) return Number(value.$numberDouble)
    if ('$date' in value) return typeof value.$date === 'string' ? value.$date : new Date(Number(value.$date.$numberLong)).toISOString()
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, unwrap(item)]))
  }
  return value
}

function queryAll(collection, filter = {}) {
  const commands = [{ TableName: collection, CommandType: 'QUERY', Command: JSON.stringify({ find: collection, filter, limit: 1000 }) }]
  const response = tcb(['db', 'nosql', 'execute', '--command', JSON.stringify(commands), '--json'])
  const results = response.results || response.Results || response
  return unwrap((Array.isArray(results) ? results : []).flat())
}

function storageList(prefix) {
  const response = tcb(['storage', 'list', prefix, '--json'])
  return Array.isArray(response) ? response : []
}

const existingResults = queryAll('sherlock_results')
const existingById = new Map(existingResults.map((item) => [item.result_id || item._id, item]))
const currentSpeaking = existingResults.find((item) => item.module_type === 'speaking' && item.data_kind === 'test')
let cloudPrefix = ''
for (const question of currentSpeaking?.question_results || []) {
  for (const record of question.recording_records || []) {
    if (typeof record.file_id === 'string' && record.file_id.includes('/sherlock-english/')) cloudPrefix ||= record.file_id.slice(0, record.file_id.indexOf('/sherlock-english/') + 1)
  }
}
assert.match(cloudPrefix, new RegExp(`^cloud://${envId.replaceAll('-', '\\-')}\\.[^/]+/$`), 'could not derive the private CloudBase file prefix')

for (const item of migration.recordings) {
  const bytes = fs.readFileSync(item.source_absolute_path)
  assert.equal(bytes.length, item.size, `recording size changed: ${item.legacy_path}`)
  assert.equal(sha256(bytes), item.legacy_sha256, `recording hash changed: ${item.legacy_path}`)
}
const resultsWithRecordings = attachRecordingPlan(migration.results, migration.recordings, (item) => `${cloudPrefix}${item.cloud_path}`)
  .map(cloudResultDocument)
const resultPlan = planResultImport(resultsWithRecordings, existingById)
if (resultPlan.anomalies.length) throw new Error(`result conflicts: ${JSON.stringify(resultPlan.anomalies)}`)

const existingStorage = new Map(storageList('sherlock-english/legacy/').map((item) => [item.key, Number(item.size)]))
const missingRecordings = []
const skippedRecordings = []
for (const item of migration.recordings) {
  const existingSize = existingStorage.get(item.cloud_path)
  if (existingSize === undefined) missingRecordings.push(item)
  else if (existingSize === item.size) skippedRecordings.push(item)
  else throw new Error(`cloud recording size conflict: ${item.cloud_path}`)
}

if (execute && missingRecordings.length) {
  const staging = path.join(artifactRoot, 'upload-staging')
  fs.mkdirSync(staging, { recursive: true })
  for (const item of missingRecordings) {
    const relative = item.cloud_path.slice('sherlock-english/legacy/'.length)
    const target = path.join(staging, ...relative.split('/'))
    fs.mkdirSync(path.dirname(target), { recursive: true })
    if (fs.existsSync(target)) assert.equal(sha256(fs.readFileSync(target)), item.legacy_sha256, `staging conflict: ${relative}`)
    else fs.copyFileSync(item.source_absolute_path, target)
  }
  const uploaded = tcb(['storage', 'upload', staging, 'sherlock-english/legacy', '--times', '3', '--json'])
  assert.equal(Number(uploaded.failedCount), 0, 'one or more recordings failed to upload')
}

if (execute && resultPlan.insert.length) {
  for (let start = 0; start < resultPlan.insert.length; start += 1) {
    const documents = resultPlan.insert.slice(start, start + 1)
    const commands = [{ TableName: 'sherlock_results', CommandType: 'INSERT', Command: JSON.stringify({ insert: 'sherlock_results', documents }) }]
    tcb(['db', 'nosql', 'execute', '--command', JSON.stringify(commands), '--json'])
    if ((start + 1) % 10 === 0 || start + 1 === resultPlan.insert.length) {
      console.error(`Imported legacy results: ${start + 1}/${resultPlan.insert.length}`)
    }
  }
}

const finalResults = execute ? queryAll('sherlock_results') : existingResults
const finalById = new Map(finalResults.map((item) => [item.result_id || item._id, item]))
const finalResultPlan = planResultImport(resultsWithRecordings, finalById)
const fieldReconciliation = compareMigratedDocuments(resultsWithRecordings, finalById)
const finalStorage = execute ? new Map(storageList('sherlock-english/legacy/').map((item) => [item.key, Number(item.size)])) : existingStorage
const storageVerified = migration.recordings.filter((item) => finalStorage.get(item.cloud_path) === item.size)
const recordingHashSamples = []
if (verifySamples) {
  const selected = []
  for (const dataKind of ['formal', 'test']) {
    const candidates = migration.recordings.filter((item) => item.data_kind === dataKind)
      .sort((left, right) => left.cloud_path.localeCompare(right.cloud_path))
    for (const index of [0, Math.floor((candidates.length - 1) / 2), candidates.length - 1]) {
      if (candidates[index] && !selected.some((item) => item.cloud_path === candidates[index].cloud_path)) selected.push(candidates[index])
    }
  }
  for (const item of selected) {
    const temporary = tcb(['storage', 'url', item.cloud_path, '--expires', '600', '--json'])
    assert.equal(typeof temporary.url, 'string', `temporary URL missing: ${item.cloud_path}`)
    const response = await fetch(temporary.url)
    assert.equal(response.ok, true, `sample download failed: ${item.cloud_path}`)
    const bytes = Buffer.from(await response.arrayBuffer())
    const downloadedSha256 = sha256(bytes)
    assert.equal(bytes.length, item.size, `sample size mismatch: ${item.cloud_path}`)
    assert.equal(downloadedSha256, item.legacy_sha256, `sample SHA-256 mismatch: ${item.cloud_path}`)
    recordingHashSamples.push({
      cloud_path: item.cloud_path,
      data_kind: item.data_kind,
      size: bytes.length,
      sha256: downloadedSha256,
      matches: true
    })
  }
}
const report = {
  mode: execute ? 'execute' : 'dry-run',
  batch_id: migration.summary.batch_id,
  source_commit: migration.summary.source_commit,
  cloud_file_prefix: cloudPrefix,
  results: execute
    ? reconcileMigration({ source: resultsWithRecordings.length, imported: resultPlan.insert.length, skipped: finalResultPlan.skip.length - resultPlan.insert.length, anomalies: finalResultPlan.anomalies.length })
    : { source: resultsWithRecordings.length, would_import: resultPlan.insert.length, would_skip: resultPlan.skip.length, anomalies: resultPlan.anomalies.length },
  result_fields: fieldReconciliation,
  live_result_totals: {
    all: finalResults.length,
    formal: finalResults.filter((item) => item.data_kind === 'formal').length,
    test: finalResults.filter((item) => item.data_kind === 'test').length
  },
  recordings: {
    source: migration.recordings.length,
    imported: execute ? missingRecordings.length : 0,
    skipped: skippedRecordings.length,
    verified_by_path_and_size: storageVerified.length,
    would_import: execute ? 0 : missingRecordings.length
  },
  recording_hash_samples: recordingHashSamples
}
if (execute) {
  assert.equal(finalResultPlan.insert.length, 0, 'some results were not imported')
  assert.equal(finalResultPlan.anomalies.length, 0, 'post-import result conflict')
  assert.equal(fieldReconciliation.anomalies.length, 0, 'post-import result field mismatch')
  assert.equal(storageVerified.length, migration.recordings.length, 'some recordings were not uploaded')
}
fs.writeFileSync(path.join(artifactRoot, `import-report-${execute ? 'execute' : 'dry-run'}.json`), `${JSON.stringify(report, null, 2)}\n`)
console.log(JSON.stringify(report, null, 2))
