'use strict'

const { createDirectUploadProbeStore } = require('./direct-upload-probe-store')

function createSpeakingDirectUploadStore(app, options = {}) {
  const store = createDirectUploadProbeStore(app, options)
  return {
    issue: store.issue,
    async download(fileId) {
      try {
        return await store.download(fileId)
      } catch {
        throw new Error('SPEAKING_DIRECT_OBJECT_MISSING')
      }
    },
    remove: store.remove
  }
}

module.exports = { createSpeakingDirectUploadStore }
