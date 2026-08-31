'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createDirectUploadProbeStore } = require('../direct-upload-probe-store')

describe('direct upload probe storage adapter', () => {
  it('turns CloudBase metadata into an exact short-lived COS PUT URL', async () => {
    const calls = []
    const path = 'sherlock-english/test/direct-upload-probe/probe-id-1234.wav'
    const app = {
      async getUploadMetadata(input) {
        assert.deepEqual(input, { cloudPath: path })
        return {
          data: {
            url: `https://6661-family24-1383960965.cos.ap-shanghai.myqcloud.com/${path}`,
            fileId: `cloud://family24.bucket/${path}`
          }
        }
      }
    }
    const store = createDirectUploadProbeStore(app, {
      signPutUrl(input) {
        calls.push(input)
        return `https://upload.example.test/${input.key}?q-sign-time=1;121`
      }
    })

    const result = await store.issue(path, { expiresIn: 120, contentType: 'audio/wav' })

    assert.deepEqual(calls, [{
      bucket: '6661-family24-1383960965',
      region: 'ap-shanghai',
      key: path,
      expiresIn: 120,
      contentType: 'audio/wav'
    }])
    assert.deepEqual(result, {
      upload_url: `https://upload.example.test/${path}?q-sign-time=1;121`,
      file_id: `cloud://family24.bucket/${path}`,
      expires_in: 120
    })
  })

  it('downloads and removes only through the private CloudBase file id', async () => {
    const fileId = 'cloud://family24.bucket/sherlock-english/test/direct-upload-probe/p.wav'
    const app = {
      async downloadFile(input) {
        assert.deepEqual(input, { fileID: fileId })
        return { fileContent: Buffer.from('probe') }
      },
      async deleteFile(input) {
        assert.deepEqual(input, { fileList: [fileId] })
      }
    }
    const store = createDirectUploadProbeStore(app, { signPutUrl() { throw new Error('unused') } })
    assert.deepEqual(await store.download(fileId), Buffer.from('probe'))
    await store.remove(fileId)
  })

  it('rejects non-COS metadata, mismatched paths, and non-buffer downloads', async () => {
    const path = 'sherlock-english/test/direct-upload-probe/probe.wav'
    for (const data of [
      { url: `https://evil.example.test/${path}`, fileId: `cloud://family24.bucket/${path}` },
      { url: `https://bucket.cos.ap-shanghai.myqcloud.com/${path}`, fileId: 'cloud://family24.bucket/other.wav' }
    ]) {
      const store = createDirectUploadProbeStore({ async getUploadMetadata() { return { data } } }, { signPutUrl() { return 'https://unused.test' } })
      await assert.rejects(store.issue(path, { expiresIn: 120, contentType: 'audio/wav' }), /DIRECT_UPLOAD_METADATA_INVALID/)
    }

    const downloadStore = createDirectUploadProbeStore({
      async downloadFile() { return { fileContent: 'not-a-buffer' } }
    }, { signPutUrl() { return 'https://unused.test' } })
    await assert.rejects(downloadStore.download('cloud://family24.bucket/probe.wav'), /UPLOAD_OBJECT_MISSING/)
  })
})
