'use strict'

const COS = require('cos-nodejs-sdk-v5')

function fileIdMatchesPath(fileId, path) {
  if (typeof fileId !== 'string' || fileId.length < 1 || fileId.length > 1024) return false
  try { return decodeURIComponent(fileId).endsWith(`/${path}`) } catch { return false }
}

function parseClassicCosTarget(urlValue, expectedPath) {
  let url
  try { url = new URL(urlValue) } catch { throw new Error('DIRECT_UPLOAD_METADATA_INVALID') }
  const host = url.hostname.toLowerCase()
  const match = /^(.+)\.cos\.([a-z0-9-]+)\.myqcloud\.com$/.exec(host)
  if (url.protocol !== 'https:' || !match) throw new Error('DIRECT_UPLOAD_METADATA_INVALID')
  const metadataPath = decodeURIComponent(url.pathname.replace(/^\/+/, ''))
  if (metadataPath && metadataPath !== expectedPath) throw new Error('DIRECT_UPLOAD_METADATA_INVALID')
  return { bucket: match[1], region: match[2], key: expectedPath }
}

function createRuntimeCosSigner(env = process.env) {
  const secretId = env.TENCENTCLOUD_SECRETID
  const secretKey = env.TENCENTCLOUD_SECRETKEY
  const securityToken = env.TENCENTCLOUD_SESSIONTOKEN
  if (!secretId || !secretKey || !securityToken) throw new Error('DIRECT_UPLOAD_SIGNER_UNAVAILABLE')
  const cos = new COS({ SecretId: secretId, SecretKey: secretKey, SecurityToken: securityToken })
  return ({ bucket, region, key, expiresIn, contentType }) => new Promise((resolve, reject) => {
    cos.getObjectUrl({
      Bucket: bucket,
      Region: region,
      Key: key,
      Method: 'PUT',
      Sign: true,
      Expires: expiresIn,
      Headers: { 'content-type': contentType }
    }, (error, data) => {
      if (error || typeof data?.Url !== 'string' || !data.Url.startsWith('https://')) {
        reject(new Error('DIRECT_UPLOAD_SIGNER_UNAVAILABLE'))
        return
      }
      resolve(data.Url)
    })
  })
}

function createDirectUploadProbeStore(app, options = {}) {
  let signPutUrl = options.signPutUrl
  return {
    async issue(path, { expiresIn, contentType }) {
      const response = await app.getUploadMetadata({ cloudPath: path })
      const data = response?.data
      if (!data || !fileIdMatchesPath(data.fileId, path)) throw new Error('DIRECT_UPLOAD_METADATA_INVALID')
      const target = parseClassicCosTarget(data.url, path)
      if (!signPutUrl) signPutUrl = createRuntimeCosSigner(options.env)
      const uploadUrl = await signPutUrl({ ...target, expiresIn, contentType })
      if (typeof uploadUrl !== 'string' || !uploadUrl.startsWith('https://')) throw new Error('DIRECT_UPLOAD_SIGNER_UNAVAILABLE')
      return { upload_url: uploadUrl, file_id: data.fileId, expires_in: expiresIn }
    },
    async download(fileId) {
      const response = await app.downloadFile({ fileID: fileId })
      if (!Buffer.isBuffer(response?.fileContent)) throw new Error('UPLOAD_OBJECT_MISSING')
      return response.fileContent
    },
    async remove(fileId) {
      await app.deleteFile({ fileList: [fileId] })
    }
  }
}

module.exports = { createDirectUploadProbeStore, createRuntimeCosSigner, parseClassicCosTarget }
