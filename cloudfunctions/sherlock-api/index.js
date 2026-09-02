'use strict'

const cloudbase = require('@cloudbase/node-sdk')
const { createService, ServiceError } = require('./core')
const { createCloudbaseStore } = require('./store')
const { createSpeakingScorer, createRecordingUrlProvider } = require('./speaking-client')
const { createSpeakingUploadStore } = require('./speaking-upload-store')
const { createDirectUploadProbeStore } = require('./direct-upload-probe-store')
const { createSpeakingDirectUploadStore } = require('./speaking-direct-upload-store')
const {
  HttpRequestError,
  createHttpResponse,
  isHttpGatewayEvent,
  parseHttpGatewayEvent
} = require('./http-adapter')

const app = cloudbase.init({ env: cloudbase.SYMBOL_CURRENT_ENV })
const store = createCloudbaseStore(app.database())
const service = createService({
  store,
  passwordHash: process.env.PARENT_PASSWORD_SCRYPT,
  hmacKey: process.env.PARENT_SESSION_HMAC_KEY,
  sessionTtlSeconds: Number(process.env.SESSION_TTL_SECONDS || 7200),
  authWindowSeconds: Number(process.env.AUTH_WINDOW_SECONDS || 900),
  maxFailures: Number(process.env.AUTH_MAX_FAILURES || 5),
  formalEnabled: String(process.env.FORMAL_ENABLED || '').toLowerCase() === 'true',
  formalEntryMode: process.env.FORMAL_ENTRY_MODE || 'dual',
  speakingScorer: createSpeakingScorer(app, process.env.SPEAKING_INTERNAL_HMAC_KEY),
  speakingRecordingUrl: createRecordingUrlProvider(app),
  speakingUploadStore: createSpeakingUploadStore(app),
  directUploadProbeStore: createDirectUploadProbeStore(app),
  speakingDirectUploadStore: createSpeakingDirectUploadStore(app),
  speakingDirectUploadEnabled: String(process.env.SPEAKING_DIRECT_UPLOAD_TEST_ENABLED || '').toLowerCase() === 'true'
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

async function handleServiceEvent(event, context, requestContext = {
  callerId: callerId(event, context),
  transport: 'cloudbase-event'
}) {
  try {
    return await service.handle(event, requestContext)
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
      FORMAL_DISABLED: '正式入口尚未开放',
      FORMAL_ENTRY_REQUIRED: '请从新的正式入口重新进入',
      UNKNOWN_ACTION: '未知操作',
      CONFIG_ERROR: '服务配置未完成',
      INVALID_SPEAKING_TAKE: '口语录音格式无效',
      COURSE_NOT_FOUND: '课程不存在',
      COURSE_VERSION_MISMATCH: '课程已更新，请重新进入',
      COURSE_NOT_FORMAL: '该课程尚未开放正式学习',
      SPEAKING_SCORE_UNAVAILABLE: '评分暂不可用，请重试',
      INVALID_SPEAKING_RESULT: '口语结果格式无效',
      RESULT_ID_CONFLICT: '结果编号冲突',
      RECORDING_NOT_FOUND: '录音不存在',
      RECORDING_UNAVAILABLE: '录音暂不可播放',
      SPEAKING_UPLOAD_FAILED: '录音上传未完成，请重试',
      SPEAKING_UPLOAD_INCOMPLETE: '录音分块不完整，请重试',
      INVALID_DIRECT_UPLOAD_PROBE: '直传测试文件参数无效',
      INVALID_DIRECT_UPLOAD_TICKET: '直传测试票据无效',
      SIGNING_UNAVAILABLE: '当前环境无法签发直传地址',
      UPLOAD_TICKET_EXPIRED: '直传测试票据已过期',
      UPLOAD_OBJECT_MISSING: '直传测试对象不存在',
      UPLOAD_SIZE_MISMATCH: '直传测试文件大小不一致',
      UPLOAD_HASH_MISMATCH: '直传测试文件校验失败',
      UPLOAD_CLEANUP_FAILED: '直传测试对象清理失败',
      SPEAKING_DIRECT_UPLOAD_DISABLED: '口语直传 TEST 尚未开启',
      INVALID_SPEAKING_DIRECT_UPLOAD: '口语直传参数无效',
      INVALID_SPEAKING_DIRECT_TICKET: '口语直传票据无效',
      SPEAKING_DIRECT_TICKET_EXPIRED: '口语直传票据已过期',
      SPEAKING_DIRECT_SIGNING_UNAVAILABLE: '口语直传地址暂不可用',
      SPEAKING_DIRECT_OBJECT_MISSING: '口语直传录音不存在',
      SPEAKING_DIRECT_INTEGRITY_FAILED: '口语直传录音校验失败',
      SPEAKING_DIRECT_CLEANUP_FAILED: '口语直传临时录音清理失败',
      INVALID_FILTER: '查询条件无效'
    }
    return { ok: false, error: { code, message: safeMessages[code] || '服务暂不可用' } }
  }
}

exports.main = async (event, context) => {
  if (!isHttpGatewayEvent(event)) return handleServiceEvent(event, context)

  try {
    const request = parseHttpGatewayEvent(event)
    if (request.kind === 'preflight') return request.response
    const result = await handleServiceEvent(request.payload, context, {
      callerId: request.callerId,
      transport: 'github-http'
    })
    return createHttpResponse(result)
  } catch (error) {
    if (!(error instanceof HttpRequestError)) throw error
    return createHttpResponse(
      { ok: false, error: { code: error.code, message: '请求不被允许' } },
      error.statusCode,
      error.code !== 'HTTP_ORIGIN_DENIED'
    )
  }
}
