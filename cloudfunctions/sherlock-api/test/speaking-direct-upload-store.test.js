'use strict'

const { describe, it } = require('node:test')
const assert = require('node:assert/strict')
const { createSpeakingDirectUploadStore } = require('../speaking-direct-upload-store')

describe('speaking direct upload storage adapter', () => {
  it('signs one exact private COS object and exposes no long-lived credentials', async () => {
    const path = 'sherlock-english/tmp-speaking-direct/test/owner/take.wav'
    const signed = []
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
    const store = createSpeakingDirectUploadStore(app, {
      signPutUrl(input) {
        signed.push(input)
        return `https://upload.example.test/${input.key}?q-sign-time=1;121`
      }
    })

    const result = await store.issue(path, { expiresIn: 120, contentType: 'audio/wav' })

    assert.deepEqual(signed, [{
      bucket: '6661-family24-1383960965', region: 'ap-shanghai', key: path,
      expiresIn: 120, contentType: 'audio/wav'
    }])
    assert.deepEqual(result, {
      upload_url: `https://upload.example.test/${path}?q-sign-time=1;121`,
      file_id: `cloud://family24.bucket/${path}`,
      expires_in: 120
    })
    assert.equal(Object.hasOwn(result, 'secret_id'), false)
    assert.equal(Object.hasOwn(result, 'secret_key'), false)
    assert.equal(Object.hasOwn(result, 'security_token'), false)
  })

  it('downloads and removes only the exact private file id', async () => {
    const fileId = 'cloud://family24.bucket/sherlock-english/tmp-speaking-direct/test/owner/take.wav'
    const app = {
      async downloadFile(input) {
        assert.deepEqual(input, { fileID: fileId })
        return { fileContent: Buffer.from('wav') }
      },
      async deleteFile(input) {
        assert.deepEqual(input, { fileList: [fileId] })
      }
    }
    const store = createSpeakingDirectUploadStore(app, { signPutUrl() { throw new Error('unused') } })

    assert.deepEqual(await store.download(fileId), Buffer.from('wav'))
    await store.remove(fileId)
  })

  it('rejects non-COS metadata, mismatched paths, and non-buffer downloads', async () => {
    const path = 'sherlock-english/tmp-speaking-direct/test/owner/take.wav'
    for (const data of [
      { url: `https://evil.example.test/${path}`, fileId: `cloud://family24.bucket/${path}` },
      { url: `https://bucket.cos.ap-shanghai.myqcloud.com/${path}`, fileId: 'cloud://family24.bucket/other.wav' }
    ]) {
      const store = createSpeakingDirectUploadStore(
        { async getUploadMetadata() { return { data } } },
        { signPutUrl() { return 'https://unused.test' } }
      )
      await assert.rejects(store.issue(path, { expiresIn: 120, contentType: 'audio/wav' }), /DIRECT_UPLOAD_METADATA_INVALID/)
    }

    const store = createSpeakingDirectUploadStore(
      { async downloadFile() { return { fileContent: 'not-a-buffer' } } },
      { signPutUrl() { return 'https://unused.test' } }
    )
    await assert.rejects(store.download('cloud://family24.bucket/path.wav'), /SPEAKING_DIRECT_OBJECT_MISSING/)
  })
})
