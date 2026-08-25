'use strict'

const crypto = require('node:crypto')

function canonicalJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => canonicalJson(item)).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().filter((key) => value[key] !== undefined)
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

function signature(payload, key) {
  if (typeof key !== 'string' || key.length < 16) throw new Error('SPEAKING_CLIENT_CONFIG')
  return crypto.createHmac('sha256', key).update(canonicalJson(payload)).digest('base64url')
}

function createSpeakingScorer(app, internalKey, functionName = 'score-speaking') {
  return async (payload) => {
    const response = await app.callFunction({ name: functionName, data: { payload, signature: signature(payload, internalKey) } }, { timeout: 60_000 })
    if (!response?.result?.ok) throw new Error(response?.result?.error?.code || 'SPEAKING_SCORE_UNAVAILABLE')
    const { ok, ...scored } = response.result
    return scored
  }
}

function createRecordingUrlProvider(app) {
  return async (fileID) => {
    const response = await app.getTempFileURL({ fileList: [{ fileID, maxAge: 600 }] })
    const item = response?.fileList?.[0]
    const url = item?.tempFileURL || item?.download_url || item?.downloadUrl
    if (typeof url !== 'string' || !url.startsWith('https://')) throw new Error('RECORDING_UNAVAILABLE')
    return url
  }
}

module.exports = { signature, createSpeakingScorer, createRecordingUrlProvider }
