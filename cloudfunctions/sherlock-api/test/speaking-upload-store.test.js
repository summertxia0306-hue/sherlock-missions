'use strict'

const test = require('node:test')
const assert = require('node:assert/strict')
const { createSpeakingUploadStore } = require('../speaking-upload-store')

test('keeps speaking chunks in private CloudBase storage and supports merge cleanup', async () => {
  const calls = []
  const app = {
    async uploadFile(input) {
      calls.push(['upload', input])
      return { fileID: `cloud://test.bucket/${input.cloudPath}` }
    },
    async downloadFile(input) {
      calls.push(['download', input])
      return { fileContent: Buffer.from('chunk') }
    },
    async deleteFile(input) {
      calls.push(['delete', input])
      return { fileList: input.fileList }
    }
  }
  const store = createSpeakingUploadStore(app)
  const uploaded = await store.upload('sherlock-english/tmp-speaking/test/part-00.bin', Buffer.from('chunk'))
  const downloaded = await store.download(uploaded.fileID)
  await store.remove([uploaded.fileID])
  await store.remove([])

  assert.equal(downloaded.toString(), 'chunk')
  assert.equal(calls.filter(([kind]) => kind === 'upload').length, 1)
  assert.equal(calls.filter(([kind]) => kind === 'download').length, 1)
  assert.equal(calls.filter(([kind]) => kind === 'delete').length, 1)
})

test('rejects a CloudBase download without binary file content', async () => {
  const store = createSpeakingUploadStore({
    async uploadFile() { return {} },
    async downloadFile() { return { fileContent: 'not-binary' } },
    async deleteFile() {}
  })
  await assert.rejects(store.download('cloud://test.bucket/missing'), /SPEAKING_UPLOAD_INCOMPLETE/)
})
