'use strict'

const cloudbase = require('@cloudbase/node-sdk')
const { createService, ServiceError } = require('./core')
const { createCloudbaseStore } = require('./store')
const { createSpeakingScorer, createRecordingUrlProvider } = require('./speaking-client')

const app = cloudbase.init({ env: cloudbase.SYMBOL_CURRENT_ENV })
const store = createCloudbaseStore(app.database())
const service = createService({
  store,
  passwordHash: process.env.PARENT_PASSWORD_SCRYPT,
  hmacKey: process.env.PARENT_SESSION_HMAC_KEY,
  sessionTtlSeconds: Number(process.env.SESSION_TTL_SECONDS || 7200),
  authWindowSeconds: Number(process.env.AUTH_WINDOW_SECONDS || 900),
  maxFailures: Number(process.env.AUTH_MAX_FAILURES || 5),
  speakingScorer: createSpeakingScorer(app, process.env.SPEAKING_INTERNAL_HMAC_KEY),
  speakingRecordingUrl: createRecordingUrlProvider(app)
})

function callerId(event, context) {
  const cloudContext = cloudbase.getCloudbaseContext(context)
  const identity = cloudContext.TCB_UUID
    || cloudContext.WX_OPENID
    || cloudContext.TCB_CUSTOM_USER_ID
    || event?.userInfo?.openId
  if (identity) {
    return `user:${identity}`
  }
  return `request:${context?.requestId || 'unknown'}`
}

exports.main = async (event, context) => {
  try {
    return await service.handle(event, { callerId: callerId(event, context) })
  } catch (error) {
    const code = error instanceof ServiceError ? error.code : 'INTERNAL_ERROR'
    if (!(error instanceof ServiceError)) {
      console.error('sherlock-api internal error', error?.name || 'Error')
    }
    const safeMessages = {
      AUTH_FAILED: '认证失败',
      RATE_LIMITED: '请求过于频繁',
      UNAUTHORIZED: '未授权',
      INVALID_RESULT: '结果格式无效',
      FORMAL_DISABLED: 'P1 正式入口未开放',
      UNKNOWN_ACTION: '未知操作',
      CONFIG_ERROR: '服务配置未完成',
      INVALID_SPEAKING_TAKE: '口语录音格式无效',
      COURSE_NOT_FOUND: '课程不存在',
      COURSE_VERSION_MISMATCH: '课程已更新，请重新进入',
      SPEAKING_SCORE_UNAVAILABLE: '评分暂不可用，请重试',
      INVALID_SPEAKING_RESULT: '口语结果格式无效',
      RESULT_ID_CONFLICT: '结果编号冲突',
      RECORDING_NOT_FOUND: '录音不存在',
      RECORDING_UNAVAILABLE: '录音暂不可播放',
      INVALID_FILTER: '查询条件无效'
    }
    return { ok: false, error: { code, message: safeMessages[code] || '服务暂不可用' } }
  }
}
