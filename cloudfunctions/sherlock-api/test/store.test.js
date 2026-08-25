'use strict'

const assert = require('node:assert/strict')
const test = require('node:test')
const { createCloudbaseStore } = require('../store')

function createDatabaseMock() {
  const writes = new Map()
  const queries = []
  const session = { token_hash: 'hash', caller_id: 'user:test', data_kind: 'test' }

  return {
    writes,
    queries,
    db: {
      command: {
        gt(value) {
          return { operator: 'gt', value }
        }
      },
      collection(name) {
        return {
          async add(value) {
            const values = writes.get(name) || []
            values.push(value)
            writes.set(name, values)
          },
          where(filter) {
            queries.push({ name, filter })
            return {
              limit(limit) {
                assert.equal(limit, 1)
                return this
              },
              async get() {
                return { data: name === 'sherlock_parent_sessions' ? [session] : [] }
              },
              async remove() {}
            }
          },
          doc(id) {
            return {
              async set(value) {
                const values = writes.get(name) || []
                values.push(value)
                writes.set(name, values)
              },
              async get() { return { data: [] } },
              async update() {}
            }
          }
        }
      }
    }
  }
}

test('CloudBase writes documents at collection root instead of nesting under data', async () => {
  const mock = createDatabaseMock()
  const store = createCloudbaseStore(mock.db)
  const occurredAt = new Date('2026-08-24T00:00:00.000Z')
  const session = { token_hash: 'hash', caller_id: 'user:test', data_kind: 'test' }
  const result = { result_id: 'result-1', data_kind: 'test' }
  const audit = { action: 'test_result_created', caller_id: 'user:test' }

  await store.recordFailure('user:test', occurredAt.getTime())
  await store.saveSession(session)
  await store.saveResult(result)
  await store.saveAudit(audit)

  assert.deepEqual(mock.writes.get('sherlock_auth_attempts'), [
    { caller_id: 'user:test', occurred_at: occurredAt }
  ])
  assert.deepEqual(mock.writes.get('sherlock_parent_sessions'), [session])
  assert.deepEqual(mock.writes.get('sherlock_results'), [result])
  assert.deepEqual(mock.writes.get('sherlock_audit_logs'), [audit])
})

test('session lookup queries the same root-level fields that saveSession writes', async () => {
  const mock = createDatabaseMock()
  const store = createCloudbaseStore(mock.db)

  const session = await store.getSession('hash')

  assert.equal(session.token_hash, 'hash')
  assert.equal(mock.queries.length, 1)
  assert.equal(mock.queries[0].name, 'sherlock_parent_sessions')
  assert.equal(mock.queries[0].filter.token_hash, 'hash')
  assert.equal(mock.queries[0].filter.expires_at.operator, 'gt')
  assert.ok(mock.queries[0].filter.expires_at.value instanceof Date)
})

test('a first speaking take uses an empty-safe query instead of a missing document read', async () => {
  const mock = createDatabaseMock()
  const store = createCloudbaseStore(mock.db)

  const take = await store.getSpeakingTake('take-1')

  assert.equal(take, null)
  assert.equal(mock.queries.length, 1)
  assert.equal(mock.queries[0].name, 'sherlock_speaking_takes')
  assert.equal(mock.queries[0].filter.take_id, 'take-1')
})
