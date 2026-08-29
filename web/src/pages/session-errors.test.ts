import { afterEach, describe, expect, it, vi } from 'vitest'
import { SherlockApiError, apiErrorCode, isNetworkFailure } from '../core/cloudbase-api'
import { listeningRequestFailureMessage } from './ListeningPage'
import { scoreFailureMessage, speakingScoreFailureMessage, speakingSubmitFailureMessage } from './SpeakingPage'

afterEach(() => vi.restoreAllMocks())

describe('session-aware request messages', () => {
  it('keeps formal listening state and distinguishes test expiry', () => {
    expect(listeningRequestFailureMessage(new Error('UNAUTHORIZED'), 'formal', '提交')).toMatch(/答案和 result_id.*保留/)
    expect(listeningRequestFailureMessage(new Error('FORMAL_SESSION_RECOVERY_FAILED'), 'formal', '订正')).toMatch(/订正状态.*保留/)
    expect(listeningRequestFailureMessage(new Error('UNAUTHORIZED'), 'test', '提交')).toMatch(/家长 TEST 会话已失效/)
  })

  it('labels only actual transport failures as network failures', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true)
    expect(listeningRequestFailureMessage(new TypeError('fetch failed'), 'formal', '提交')).toMatch(/网络不可用/)
    expect(listeningRequestFailureMessage(new SherlockApiError('COURSE_VERSION_MISMATCH'), 'formal', '提交')).toMatch(/诊断码：COURSE_VERSION_MISMATCH/)
    expect(listeningRequestFailureMessage('unknown', 'formal', '提交')).toMatch(/诊断码：SERVICE_ERROR/)
    expect(isNetworkFailure(new Error('NETWORK_TIMEOUT'))).toBe(true)
    expect(isNetworkFailure(new Error('OTHER'))).toBe(false)
  })

  it('keeps speaking recordings and proofs across recovery and service failures', () => {
    expect(speakingScoreFailureMessage(new Error('UNAUTHORIZED'), 'formal')).toMatch(/录音仍保留/)
    expect(speakingScoreFailureMessage(new Error('UNAUTHORIZED'), 'test')).toMatch(/家长 TEST 会话已失效/)
    expect(speakingSubmitFailureMessage(new Error('FORMAL_SESSION_RECOVERY_FAILED'), 'formal')).toMatch(/全部口语过程仍保留/)
    expect(speakingSubmitFailureMessage(new Error('UNAUTHORIZED'), 'test')).toMatch(/重新认证/)
    expect(speakingSubmitFailureMessage(new SherlockApiError('INVALID_SPEAKING_RESULT'), 'formal')).toMatch(/诊断码：INVALID_SPEAKING_RESULT/)
  })

  it('preserves the existing safe speaking diagnostics', () => {
    expect(scoreFailureMessage('SILENT_AUDIO', 'formal')).toMatch(/没有录到/)
    expect(scoreFailureMessage('INVALID_AUDIO', 'formal')).toMatch(/录音格式/)
    expect(scoreFailureMessage('COURSE_VERSION_MISMATCH', 'formal')).toMatch(/课程刚刚更新/)
    expect(scoreFailureMessage('RECORDING_UPLOAD_FAILED', 'test')).toMatch(/测试录音保存失败/)
    expect(scoreFailureMessage('', 'formal')).toMatch(/NETWORK_OR_CLIENT/)
    expect(apiErrorCode(new SherlockApiError('UNAUTHORIZED'))).toBe('UNAUTHORIZED')
    expect(apiErrorCode(new Error('not a code'))).toBe('')
  })
})
