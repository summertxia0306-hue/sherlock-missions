'use strict'

const cloudbase = require('@cloudbase/node-sdk')
const { createService, ScoreError } = require('./core')
const { evaluateRetry } = require('./ise-client')

const app = cloudbase.init({ env: cloudbase.SYMBOL_CURRENT_ENV })
const service = createService({
  internalKey: process.env.SPEAKING_INTERNAL_HMAC_KEY,
  evaluator: ({ text, pcm }) => evaluateRetry({
    appId: process.env.XF_APPID, apiKey: process.env.XF_API_KEY, apiSecret: process.env.XF_API_SECRET,
    text, pcm
  }),
  uploader: (cloudPath, fileContent) => app.uploadFile({ cloudPath, fileContent })
})

exports.main = async (event) => {
  try { return { ok: true, ...(await service.handle(event)) } } catch (error) {
    const code = error instanceof ScoreError ? error.code : 'INTERNAL_ERROR'
    if (!(error instanceof ScoreError)) console.error('score-speaking internal error', error?.name || 'Error')
    return { ok: false, error: { code, message: '评分暂不可用，请稍后重试' } }
  }
}
