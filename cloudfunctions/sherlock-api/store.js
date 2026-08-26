'use strict'

function createCloudbaseStore(db) {
  const command = db.command
  const collections = {
    sessions: db.collection('sherlock_parent_sessions'),
    results: db.collection('sherlock_results'),
    audits: db.collection('sherlock_audit_logs'),
    failures: db.collection('sherlock_auth_attempts'),
    speakingTakes: db.collection('sherlock_speaking_takes')
  }

  return {
    async getFailures(callerId) {
      const response = await collections.failures.where({ caller_id: callerId }).limit(100).get()
      return response.data.map((item) => item.occurred_at instanceof Date ? item.occurred_at.getTime() : Date.parse(item.occurred_at))
    },
    async recordFailure(callerId, occurredAt) {
      await collections.failures.add({ caller_id: callerId, occurred_at: new Date(occurredAt) })
    },
    async clearFailures(callerId) {
      await collections.failures.where({ caller_id: callerId }).remove()
    },
    async saveSession(value) {
      await collections.sessions.add(value)
    },
    async getSession(hash) {
      const response = await collections.sessions.where({ token_hash: hash, expires_at: command.gt(new Date()) }).limit(1).get()
      return response.data[0] || null
    },
    async saveResult(value) {
      if (value.result_id) {
        await collections.results.doc(value.result_id).set(value)
      } else {
        await collections.results.add(value)
      }
      return value.result_id
    },
    async getResult(resultId) {
      const response = await collections.results.doc(resultId).get()
      return response.data?.[0] || null
    },
    async updateResult(resultId, patch) {
      await collections.results.doc(resultId).update(patch)
    },
    async listResults(moduleType = 'listening') {
      const response = await collections.results.where({ data_kind: 'test', module_type: moduleType }).limit(50).get()
      return response.data
    },
    async listParentResults(filters) {
      const query = { data_kind: filters.data_kind }
      if (filters.module_type) query.module_type = filters.module_type
      if (filters.course_id) query.course_id = filters.course_id
      const rows = []
      for (let offset = 0; offset < 2000; offset += 100) {
        const response = await collections.results.where(query).skip(offset).limit(100).get()
        rows.push(...response.data)
        if (response.data.length < 100) break
      }
      return rows
    },
    async getSpeakingTake(takeId) {
      const response = await collections.speakingTakes.where({ take_id: takeId }).limit(1).get()
      return response.data?.[0] || null
    },
    async saveSpeakingTake(value) {
      await collections.speakingTakes.doc(value.take_id).set(value)
    },
    async saveAudit(value) {
      await collections.audits.add(value)
    }
  }
}

module.exports = { createCloudbaseStore }
