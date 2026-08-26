import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  buildRecordingPlan,
  collectRecordingReferences,
  sha256,
  transformLegacyResults
} from './p4-migration-lib.mjs'

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const expectedRoot = 'D:\\ObsidianVaults\\Education\\Sherlock\\English-Learning'
assert.equal(projectRoot.toLowerCase(), expectedRoot.toLowerCase(), 'unexpected project root')

function argument(name) {
  const index = process.argv.indexOf(name)
  return index >= 0 ? process.argv[index + 1] : undefined
}

const sourceRoot = path.resolve(argument('--source') || '')
const outputRoot = path.resolve(argument('--output') || '')
const trackedManifest = path.resolve(argument('--tracked-manifest') || path.join(projectRoot, 'docs', 'P4_旧库SHA256清单_2026-08-25.tsv'))
const trackedCourseMap = path.resolve(argument('--tracked-course-map') || path.join(projectRoot, 'docs', 'P4_课程映射_2026-08-25.tsv'))
assert.ok(fs.existsSync(path.join(sourceRoot, '.git')), 'legacy source must be a Git clone')
assert.ok(outputRoot && outputRoot !== projectRoot && !outputRoot.startsWith(`${projectRoot}${path.sep}`), 'snapshot output must remain outside the public repository')

const remote = execFileSync('git', ['-C', sourceRoot, 'remote', 'get-url', 'origin'], { encoding: 'utf8' }).trim()
assert.match(remote, /summertxia0306-hue\/sherlock-results(?:\.git)?$/i, 'unexpected legacy remote')
const sourceCommit = execFileSync('git', ['-C', sourceRoot, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()
assert.match(sourceCommit, /^[a-f0-9]{40}$/i)
assert.equal(execFileSync('git', ['-C', sourceRoot, 'status', '--porcelain'], { encoding: 'utf8' }).trim(), '', 'legacy source snapshot is dirty')

function filesUnder(directory) {
  const out = []
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === '.git') continue
    const absolute = path.join(directory, entry.name)
    if (entry.isDirectory()) out.push(...filesUnder(absolute))
    else if (entry.isFile()) out.push(absolute)
  }
  return out
}

const sourceFiles = filesUnder(sourceRoot).sort((a, b) => a.localeCompare(b, 'en'))
const manifest = sourceFiles.map((absolute) => {
  const bytes = fs.readFileSync(absolute)
  return {
    path: path.relative(sourceRoot, absolute).replaceAll('\\', '/'),
    size: bytes.length,
    sha256: sha256(bytes)
  }
})
const resultsFile = path.join(sourceRoot, 'results.json')
const metadataFile = path.join(sourceRoot, 'recording_metadata.json')
const sourceRows = JSON.parse(fs.readFileSync(resultsFile, 'utf8'))
const metadata = JSON.parse(fs.readFileSync(metadataFile, 'utf8'))
const currentCourseIds = new Set([
  ...fs.readdirSync(path.join(projectRoot, 'content', 'listening')).filter((name) => name.endsWith('.json')).map((name) => path.basename(name, '.json')),
  ...fs.readdirSync(path.join(projectRoot, 'content', 'speaking')).filter((name) => name.endsWith('.json')).map((name) => path.basename(name, '.json'))
])
const batchId = `p4-20260825-${sourceCommit.slice(0, 8)}`
const options = {
  sourceCommit,
  sourceBlobSha256: manifest.find((item) => item.path === 'results.json').sha256,
  batchId,
  currentCourseIds
}
const convertedResults = transformLegacyResults(sourceRows, options)
const references = collectRecordingReferences(sourceRows)
const recordingFiles = manifest.filter((item) => item.path.toLowerCase().endsWith('.wav'))
  .map((item) => ({ ...item, source_absolute_path: path.join(sourceRoot, ...item.path.split('/')) }))
const recordingPlan = buildRecordingPlan(recordingFiles, metadata, references, options)
  .map((item, index) => ({ ...item, source_absolute_path: recordingFiles[index].source_absolute_path }))

const countBy = (values, key) => Object.fromEntries([...new Set(values.map((item) => item[key]))].sort().map((value) => [value, values.filter((item) => item[key] === value).length]))
const summary = {
  batch_id: batchId,
  source_remote: 'summertxia0306-hue/sherlock-results',
  source_commit: sourceCommit,
  source_git_clean: true,
  source_files: manifest.length,
  source_bytes: manifest.reduce((sum, item) => sum + item.size, 0),
  source_manifest_sha256: sha256(manifest),
  results: convertedResults.length,
  results_by_data_kind: countBy(convertedResults, 'data_kind'),
  results_by_module: countBy(convertedResults, 'module_type'),
  recordings: recordingPlan.length,
  recording_bytes: recordingPlan.reduce((sum, item) => sum + item.size, 0),
  recordings_by_data_kind: countBy(recordingPlan, 'data_kind'),
  recording_references: references.size,
  metadata_entries: Object.keys(metadata).length,
  anomalies: []
}

fs.mkdirSync(path.join(outputRoot, 'raw'), { recursive: true })
fs.copyFileSync(resultsFile, path.join(outputRoot, 'raw', 'results.json'))
fs.copyFileSync(metadataFile, path.join(outputRoot, 'raw', 'recording_metadata.json'))
fs.writeFileSync(path.join(outputRoot, 'source-ref.json'), `${JSON.stringify({ remote, commit: sourceCommit }, null, 2)}\n`)
fs.writeFileSync(path.join(outputRoot, 'source-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
fs.writeFileSync(path.join(outputRoot, 'migration-plan.json'), `${JSON.stringify({ summary, results: convertedResults, recordings: recordingPlan }, null, 2)}\n`)
fs.writeFileSync(path.join(outputRoot, 'snapshot-summary.json'), `${JSON.stringify(summary, null, 2)}\n`)

const tsv = ['path\tsize\tsha256', ...manifest.map((item) => `${item.path}\t${item.size}\t${item.sha256}`)].join('\n') + '\n'
const courseIds = [...new Set(convertedResults.map((item) => item.course_id))].sort()
const courseMap = [
  'legacy_course_id\ttarget_course_id\tcourse_scope\tcourse_version\tresult_count\tformal_count\ttest_count',
  ...courseIds.map((courseId) => {
    const rows = convertedResults.filter((item) => item.course_id === courseId)
    const scope = rows[0].course_scope
    const targetCourseId = scope === 'current-equivalent' ? courseId : `legacy-streamlit/${courseId}`
    return [courseId, targetCourseId, scope, rows[0].course_version, rows.length,
      rows.filter((item) => item.data_kind === 'formal').length,
      rows.filter((item) => item.data_kind === 'test').length].join('\t')
  })
].join('\n') + '\n'
fs.writeFileSync(path.join(outputRoot, 'source-manifest.tsv'), tsv)
fs.writeFileSync(trackedManifest, tsv)
fs.writeFileSync(path.join(outputRoot, 'course-map.tsv'), courseMap)
fs.writeFileSync(trackedCourseMap, courseMap)
console.log(JSON.stringify({ outputRoot, trackedManifest, trackedCourseMap, summary }, null, 2))
