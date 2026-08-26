import crypto from 'node:crypto'
import path from 'node:path'

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().filter((key) => value[key] !== undefined)
      .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

export function sha256(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === 'string' ? value : canonical(value), 'utf8')
  return crypto.createHash('sha256').update(bytes).digest('hex')
}

function moduleType(courseId, legacyModule) {
  if (legacyModule === 'speaking' || String(courseId).startsWith('S')) return 'speaking'
  if (legacyModule === 'listening' || String(courseId).startsWith('W')) return 'listening'
  throw new Error(`unknown legacy module: ${courseId}`)
}

function isoDate(value) {
  if (typeof value !== 'string' || !value.trim()) throw new Error('legacy completed_at is missing')
  const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(value.trim())
    ? `${value.trim().replace(' ', 'T')}:00+08:00`
    : value.trim()
  const date = new Date(normalized)
  if (!Number.isFinite(date.getTime())) throw new Error(`invalid legacy date: ${value}`)
  return date.toISOString()
}

function validatedOptions(options) {
  if (!options || !/^[a-f0-9]{40}$/i.test(options.sourceCommit)
    || !/^[a-f0-9]{64}$/i.test(options.sourceBlobSha256)
    || typeof options.batchId !== 'string' || !options.batchId) throw new Error('invalid migration options')
}

export function transformLegacyResults(rows, options) {
  validatedOptions(options)
  if (!Array.isArray(rows)) throw new Error('legacy results must be an array')
  const currentCourseIds = options.currentCourseIds || new Set()
  return rows.map((source, index) => {
    const row = structuredClone(source)
    const sourceRecordHash = sha256(source)
    const sourceIndex = index + 1
    const legacySourceId = `github:summertxia0306-hue/sherlock-results:results.json:${String(sourceIndex).padStart(6, '0')}:${sourceRecordHash}`
    const explicitKind = source.data_kind === 'formal' || source.data_kind === 'test' ? source.data_kind : null
    const dataKind = explicitKind || 'test'
    const submittedAt = isoDate(source.completed_at)
    const durationSeconds = Number.isInteger(source.duration_seconds) && source.duration_seconds >= 0 ? source.duration_seconds : 0
    const startedAt = new Date(new Date(submittedAt).getTime() - durationSeconds * 1000).toISOString()
    const courseId = String(source.course_id || '')
    if (!/^[WS]\d{2}D\d{2}$/.test(courseId)) throw new Error(`invalid legacy course id at row ${sourceIndex}`)
    delete row.module
    return {
      ...row,
      result_id: `legacy-${sha256(legacySourceId).slice(0, 48)}`,
      module_type: moduleType(courseId, source.module),
      course_id: courseId,
      legacy_course_id: courseId,
      course_scope: currentCourseIds.has(courseId) ? 'current-equivalent' : 'legacy-only',
      course_version: `legacy-streamlit@${options.sourceCommit.slice(0, 12)}`,
      data_kind: dataKind,
      data_kind_evidence: explicitKind ? 'explicit_source_field' : 'missing_default_test',
      formal_completion_eligible: dataKind === 'formal',
      confirmed_by_parent: dataKind === 'formal',
      attempt_kind: Number(source.attempt || 1) > 1 ? 'redo' : 'first',
      started_at: startedAt,
      submitted_at: submittedAt,
      created_at: submittedAt,
      legacy_source_id: legacySourceId,
      legacy_source_commit: options.sourceCommit,
      legacy_source_blob_sha256: options.sourceBlobSha256,
      legacy_source_record_sha256: sourceRecordHash,
      migration_batch_id: options.batchId,
      migration_mode: 'append-only'
    }
  })
}

function normalizedLegacyPath(value) {
  const normalized = String(value || '').replaceAll('\\', '/').replace(/^\.\//, '')
  if (!normalized.startsWith('recordings/') || normalized.includes('../')) throw new Error(`unsafe recording path: ${value}`)
  return normalized
}

export function collectRecordingReferences(results) {
  const references = new Map()
  for (const result of results) {
    const resultKind = result.data_kind === 'formal' ? 'formal' : 'test'
    for (const question of result.question_results || []) {
      for (const recording of question.recording_records || []) {
        const sourcePath = normalizedLegacyPath(recording.path)
        const kind = recording.data_kind === 'formal' || recording.data_kind === 'test' ? recording.data_kind : resultKind
        const current = references.get(sourcePath)
        if (current && current !== kind) throw new Error(`recording data_kind conflict: ${sourcePath}`)
        references.set(sourcePath, kind)
      }
    }
  }
  return references
}

export function buildRecordingPlan(files, metadata, references, options) {
  validatedOptions(options)
  return files.map((file) => {
    const sourcePath = normalizedLegacyPath(file.path)
    if (!/^[a-f0-9]{64}$/i.test(file.sha256) || !Number.isInteger(file.size) || file.size < 1) throw new Error(`invalid recording manifest row: ${sourcePath}`)
    const explicit = metadata?.[sourcePath]?.data_kind
    const referenced = references?.get(sourcePath)
    let dataKind = 'test'
    let evidence = 'missing_default_test'
    if (explicit === 'formal' || explicit === 'test') {
      dataKind = explicit
      evidence = 'explicit_recording_metadata'
    } else if (referenced === 'formal' || referenced === 'test') {
      dataKind = referenced
      evidence = 'explicit_result_reference'
    }
    if (explicit && referenced && explicit !== referenced) throw new Error(`recording identity conflict: ${sourcePath}`)
    const parts = sourcePath.split('/')
    const courseId = parts.length > 2 ? parts[1] : 'unlinked'
    return {
      legacy_path: sourcePath,
      legacy_sha256: file.sha256.toLowerCase(),
      size: file.size,
      course_id: courseId,
      data_kind: dataKind,
      data_kind_evidence: evidence,
      cloud_path: `sherlock-english/legacy/${dataKind}/${courseId}/${file.sha256.toLowerCase()}.wav`,
      migration_batch_id: options.batchId,
      legacy_source_commit: options.sourceCommit
    }
  })
}

export function attachRecordingPlan(results, recordingPlan, fileIdForPath = (item) => item.cloud_path) {
  const byPath = new Map(recordingPlan.map((item) => [item.legacy_path, item]))
  return results.map((result) => ({
    ...result,
    question_results: (result.question_results || []).map((question) => ({
      ...question,
      recordings: undefined,
      recording_records: (question.recording_records || []).map((recording) => {
        const legacyPath = normalizedLegacyPath(recording.path)
        const plan = byPath.get(legacyPath)
        if (!plan) throw new Error(`referenced recording missing from snapshot: ${legacyPath}`)
        return {
          legacy_path: legacyPath,
          legacy_sha256: plan.legacy_sha256,
          cloud_path: plan.cloud_path,
          file_id: fileIdForPath(plan),
          data_kind: plan.data_kind
        }
      })
    }))
  }))
}

export function reconcileMigration({ source, imported, skipped, anomalies }) {
  for (const [name, value] of Object.entries({ source, imported, skipped, anomalies })) {
    if (!Number.isInteger(value) || value < 0) throw new Error(`invalid reconcile value: ${name}`)
  }
  const accounted = imported + skipped + anomalies
  if (accounted !== source) throw new Error(`reconcile mismatch: source=${source}, accounted=${accounted}`)
  return { source, imported, skipped, anomalies, accounted, matches: true }
}

export function planResultImport(records, existingById) {
  const insert = []
  const skip = []
  const anomalies = []
  for (const record of records) {
    const existing = existingById.get(record.result_id)
    if (!existing) insert.push(record)
    else if (existing.legacy_source_record_sha256 === record.legacy_source_record_sha256) skip.push(record)
    else anomalies.push({ result_id: record.result_id, reason: 'RESULT_ID_CONFLICT' })
  }
  return { insert, skip, anomalies }
}

export function cloudResultDocument(record) {
  if (!record || typeof record.result_id !== 'string' || !record.result_id) throw new Error('invalid migrated result')
  const { result_text: _legacyDisplayText, ...document } = structuredClone(record)
  return { _id: document.result_id, ...document }
}

export function compareMigratedDocuments(expectedDocuments, actualById) {
  const anomalies = []
  let matched = 0
  for (const expected of expectedDocuments) {
    const resultId = expected.result_id || expected._id
    const actual = actualById.get(resultId)
    if (!actual) anomalies.push({ result_id: resultId, reason: 'MISSING' })
    else if (sha256(expected) !== sha256(actual)) anomalies.push({ result_id: resultId, reason: 'FIELD_MISMATCH' })
    else matched += 1
  }
  return { source: expectedDocuments.length, matched, anomalies }
}

export function basenameForManifest(filePath) {
  return path.posix.basename(normalizedLegacyPath(filePath))
}
