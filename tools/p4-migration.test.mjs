import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import {
  attachRecordingPlan,
  buildRecordingPlan,
  cloudResultDocument,
  compareMigratedDocuments,
  planResultImport,
  reconcileMigration,
  transformLegacyResults
} from './p4-migration-lib.mjs'

const options = {
  sourceCommit: '16ca371ee0efdd2aa3d50e0b7be256aafba1f442',
  sourceBlobSha256: 'a'.repeat(64),
  batchId: 'p4-20260825-16ca371e',
  currentCourseIds: new Set(['W01D39', 'S01D39'])
}

describe('P4 legacy result conversion', () => {
  it('preserves explicit formal evidence and conservatively defaults missing data_kind to test', () => {
    const rows = [
      { student_id: 'sherlock', course_id: 'W01D39', data_kind: 'formal', status: 'completed', score: 90, duration_seconds: 60, completed_at: '2026-08-15 20:00', wrong_answers: [], section_scores: {}, corrections: {} },
      { student_id: 'sherlock', course_id: 'W01D02', status: 'completed', score: 80, duration_seconds: 70, completed_at: '2026-06-12 21:00', wrong_answers: [], section_scores: {}, corrections: {} }
    ]

    const converted = transformLegacyResults(rows, options)

    assert.equal(converted[0].data_kind, 'formal')
    assert.equal(converted[0].formal_completion_eligible, true)
    assert.equal(converted[0].data_kind_evidence, 'explicit_source_field')
    assert.equal(converted[0].course_scope, 'current-equivalent')
    assert.equal(converted[1].data_kind, 'test')
    assert.equal(converted[1].formal_completion_eligible, false)
    assert.equal(converted[1].data_kind_evidence, 'missing_default_test')
    assert.equal(converted[1].course_scope, 'legacy-only')
  })

  it('generates stable unique source and result identifiers across repeated runs', () => {
    const duplicate = { student_id: 'sherlock', course_id: 'S01D01', module: 'speaking', data_kind: 'formal', status: 'completed', score: 99, duration_seconds: 30, completed_at: '2026-06-27 15:01', question_results: [] }
    const first = transformLegacyResults([duplicate, duplicate], options)
    const second = transformLegacyResults([duplicate, duplicate], options)

    assert.deepEqual(first, second)
    assert.notEqual(first[0].legacy_source_id, first[1].legacy_source_id)
    assert.notEqual(first[0].result_id, first[1].result_id)
    assert.equal(first[0].migration_batch_id, options.batchId)
  })
})

describe('P4 recording classification and reconciliation', () => {
  it('uses explicit metadata or formal result evidence and defaults unclassified recordings to test', () => {
    const files = [
      { path: 'recordings/S01D01/formal.wav', sha256: '1'.repeat(64), size: 100 },
      { path: 'recordings/S01D02/ref-formal.wav', sha256: '2'.repeat(64), size: 200 },
      { path: 'recordings/smoke/unclassified.wav', sha256: '3'.repeat(64), size: 300 }
    ]
    const metadata = { 'recordings/S01D01/formal.wav': { data_kind: 'formal' } }
    const references = new Map([['recordings/S01D02/ref-formal.wav', 'formal']])

    const plan = buildRecordingPlan(files, metadata, references, options)

    assert.deepEqual(plan.map((item) => item.data_kind), ['formal', 'formal', 'test'])
    assert.equal(plan[0].data_kind_evidence, 'explicit_recording_metadata')
    assert.equal(plan[1].data_kind_evidence, 'explicit_result_reference')
    assert.equal(plan[2].data_kind_evidence, 'missing_default_test')
    assert.match(plan[0].cloud_path, /^sherlock-english\/legacy\/formal\/S01D01\/[a-f0-9]{64}\.wav$/)
    assert.match(plan[2].cloud_path, /^sherlock-english\/legacy\/test\/smoke\/[a-f0-9]{64}\.wav$/)
  })

  it('accounts for imported, skipped and anomalous items without hiding differences', () => {
    const report = reconcileMigration({ source: 143, imported: 140, skipped: 2, anomalies: 1 })
    assert.equal(report.accounted, 143)
    assert.equal(report.matches, true)
    assert.throws(() => reconcileMigration({ source: 143, imported: 140, skipped: 1, anomalies: 1 }), /reconcile/i)
  })

  it('rewrites private recording references and rejects a missing source file', () => {
    const results = [{ result_id: 'r1', question_results: [{ id: 1, recordings: ['old'], recording_records: [{ path: 'recordings/S01D01/formal.wav', data_kind: 'formal' }] }] }]
    const plan = [{ legacy_path: 'recordings/S01D01/formal.wav', legacy_sha256: '1'.repeat(64), cloud_path: 'sherlock-english/legacy/formal/S01D01/hash.wav', data_kind: 'formal' }]
    const rewritten = attachRecordingPlan(results, plan, () => 'cloud://private/formal.wav')
    assert.equal(rewritten[0].question_results[0].recordings, undefined)
    assert.equal(rewritten[0].question_results[0].recording_records[0].file_id, 'cloud://private/formal.wav')
    assert.throws(() => attachRecordingPlan(results, [], () => 'cloud://missing'), /missing from snapshot/)
  })

  it('plans only absent result inserts, skips byte-equivalent migrations and reports conflicts', () => {
    const records = [
      { result_id: 'new', legacy_source_record_sha256: '1'.repeat(64) },
      { result_id: 'same', legacy_source_record_sha256: '2'.repeat(64) },
      { result_id: 'conflict', legacy_source_record_sha256: '3'.repeat(64) }
    ]
    const existing = new Map([
      ['same', { result_id: 'same', legacy_source_record_sha256: '2'.repeat(64) }],
      ['conflict', { result_id: 'conflict', legacy_source_record_sha256: '9'.repeat(64) }]
    ])
    const importPlan = planResultImport(records, existing)
    assert.deepEqual(importPlan.insert.map((item) => item.result_id), ['new'])
    assert.deepEqual(importPlan.skip.map((item) => item.result_id), ['same'])
    assert.deepEqual(importPlan.anomalies.map((item) => item.result_id), ['conflict'])
  })

  it('keeps the exact source result in the snapshot but omits bulky legacy display text from CloudBase', () => {
    const source = {
      result_id: 'legacy-result',
      result_text: 'a large Streamlit-only rendering payload',
      wrong_answers: [{ question_id: 1 }],
      question_results: [{ question_id: 1, score: 88 }],
      legacy_source_record_sha256: '4'.repeat(64)
    }

    const document = cloudResultDocument(source)

    assert.equal(source.result_text, 'a large Streamlit-only rendering payload')
    assert.equal(document.result_text, undefined)
    assert.deepEqual(document.wrong_answers, source.wrong_answers)
    assert.deepEqual(document.question_results, source.question_results)
    assert.equal(document._id, source.result_id)
  })

  it('detects missing or changed CloudBase documents during field reconciliation', () => {
    const expected = [
      { _id: 'same', result_id: 'same', score: 90, data_kind: 'formal' },
      { _id: 'changed', result_id: 'changed', score: 80, data_kind: 'formal' },
      { _id: 'missing', result_id: 'missing', score: 70, data_kind: 'test' }
    ]
    const actual = new Map([
      ['same', { _id: 'same', result_id: 'same', score: 90, data_kind: 'formal' }],
      ['changed', { _id: 'changed', result_id: 'changed', score: 81, data_kind: 'formal' }]
    ])

    const comparison = compareMigratedDocuments(expected, actual)

    assert.equal(comparison.matched, 1)
    assert.deepEqual(comparison.anomalies, [
      { result_id: 'changed', reason: 'FIELD_MISMATCH' },
      { result_id: 'missing', reason: 'MISSING' }
    ])
  })
})
