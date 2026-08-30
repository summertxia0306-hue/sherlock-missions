import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiErrorCode, isNetworkFailure, type SherlockApi } from '../core/cloudbase-api'
import type { SessionRequestRunner } from '../core/formal-session'
import { loadSpeakingCatalog, loadSpeakingCourse, resolveSpeakingAudioUrl, type SpeakingCatalog, type SpeakingCourse } from '../speaking/course'
import { addScoredTake, buildSpeakingSubmission, createSpeakingSession, markSafetyPass, type SpeakingSession } from '../speaking/session'
import { sharedPcmRecorder, type PcmRecorder, type RecordedAudio } from '../speaking/recorder'

type Activity = 'idle' | 'demo' | 'countdown' | 'recording' | 'replay' | 'scoring' | 'submitting'

function newResultId(): string { return crypto.randomUUID?.() || '00000000-0000-4000-8000-000000000000' }

async function blobBase64(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer())
  let binary = ''
  for (let offset = 0; offset < bytes.length; offset += 8192) binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192))
  return btoa(binary)
}

export function scoreFailureMessage(code: string, dataKind: 'formal' | 'test'): string {
  if (code === 'SILENT_AUDIO') return '没有录到清楚的声音，请重新录。'
  if (code === 'INVALID_AUDIO') return '录音格式没有通过检查，请重新录。'
  if (code === 'UNAUTHORIZED' || code === 'FORMAL_SESSION_RECOVERY_FAILED') return dataKind === 'formal' ? '正式会话自动恢复失败，录音仍保留；联网后可再次评分。' : '家长 TEST 会话已失效，请返回家长验收入口重新认证。'
  if (code === 'COURSE_VERSION_MISMATCH') return '课程刚刚更新，请返回列表后重新进入。'
  if (code === 'RECORDING_UPLOAD_FAILED') return `评分已返回，但${dataKind === 'formal' ? '正式' : '测试'}录音保存失败；本次不计次数，请重试。`
  const diagnostic = code || 'NETWORK_OR_CLIENT'
  return `评分暂时没有完成。本次不计次数，录音仍保留，可再次评分。（诊断码：${diagnostic}）`
}

export function speakingScoreFailureMessage(error: unknown, dataKind: 'formal' | 'test'): string {
  if (isNetworkFailure(error)) return '评分没有完成。当前网络不可用，本次不计次数，录音仍保留。'
  return scoreFailureMessage(apiErrorCode(error) || 'SERVICE_ERROR', dataKind)
}

export function speakingSubmitFailureMessage(error: unknown, dataKind: 'formal' | 'test'): string {
  const code = apiErrorCode(error)
  if (dataKind === 'formal' && (code === 'UNAUTHORIZED' || code === 'FORMAL_SESSION_RECOVERY_FAILED')) {
    return '正式会话自动恢复失败，全部口语过程仍保留；联网后可再次提交。'
  }
  if (dataKind === 'test' && code === 'UNAUTHORIZED') return '家长 TEST 会话已失效，请返回家长验收入口重新认证。'
  if (isNetworkFailure(error)) return '提交没有完成。当前网络不可用，恢复联网后可再次提交。'
  return `提交没有完成（诊断码：${code || 'SERVICE_ERROR'}）。全部口语过程仍保留，可再次提交。`
}

export function SpeakingPage({
  api, sessionToken, dataKind = 'test', completedCourseIds = new Set<string>(), onFormalCompleted = () => undefined,
  runSessionRequest, loadCatalog = loadSpeakingCatalog, loadCourse = loadSpeakingCourse, recorder = sharedPcmRecorder
}: {
  api: SherlockApi; sessionToken: string; dataKind?: 'formal' | 'test'; completedCourseIds?: ReadonlySet<string>;
  runSessionRequest?: SessionRequestRunner;
  onFormalCompleted?: (courseId: string) => void; loadCatalog?: () => Promise<SpeakingCatalog>; loadCourse?: (id: string) => Promise<SpeakingCourse>; recorder?: PcmRecorder
}) {
  const [catalog, setCatalog] = useState<SpeakingCatalog>()
  const [course, setCourse] = useState<SpeakingCourse>()
  const [session, setSession] = useState<SpeakingSession>()
  const [questionIndex, setQuestionIndex] = useState(0)
  const [trialDone, setTrialDone] = useState(false)
  const [trialReplayed, setTrialReplayed] = useState(false)
  const [recording, setRecording] = useState<RecordedAudio>()
  const [activity, setActivity] = useState<Activity>('idle')
  const [countdown, setCountdown] = useState(0)
  const [demoPlays, setDemoPlays] = useState<Record<string, number>>({})
  const [message, setMessage] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const recordingUrlRef = useRef('')

  function withSession<T>(request: (token: string) => Promise<T>, onRecovering?: () => void): Promise<T> {
    return runSessionRequest ? runSessionRequest(request, { onRecovering }) : request(sessionToken)
  }

  useEffect(() => { loadCatalog().then(setCatalog).catch(() => setMessage('口语课程目录暂时无法加载。')) }, [loadCatalog])
  useEffect(() => {
    if (session) sessionStorage.setItem(`sherlock-speaking-${dataKind}-${session.course_id}`, JSON.stringify(session))
  }, [dataKind, session])
  useEffect(() => () => {
    audioRef.current?.pause()
    recorder.release()
    if (recordingUrlRef.current) URL.revokeObjectURL(recordingUrlRef.current)
  }, [])

  function replaceRecording(next?: RecordedAudio) {
    if (recording) URL.revokeObjectURL(recording.url)
    recordingUrlRef.current = next?.url || ''
    setRecording(next)
    setTrialReplayed(false)
  }

  async function startCourse(courseId: string) {
    if (!sessionToken || activity !== 'idle') return
    setMessage('')
    try {
      const loaded = await loadCourse(courseId)
      const saved = sessionStorage.getItem(`sherlock-speaking-${dataKind}-${courseId}`)
      const restored = saved ? JSON.parse(saved) as SpeakingSession : createSpeakingSession(courseId, newResultId())
      setCourse(loaded); setSession(restored); setTrialDone(false); setSubmitted(false)
      setQuestionIndex(Math.min(7, Array.from({ length: 8 }, (_, index) => index).find((index) => !restored.questions[String(index + 1)]?.complete) ?? 0))
    } catch { setMessage('课程暂时无法打开，请稍后重试。') }
  }

  function playUrl(url: string, kind: 'demo' | 'replay', onEnded?: () => void) {
    if (activity !== 'idle') return
    const audio = new Audio(url)
    audioRef.current = audio
    setActivity(kind)
    audio.addEventListener('ended', () => { audioRef.current = null; setActivity('idle'); onEnded?.() }, { once: true })
    audio.addEventListener('error', () => {
      audioRef.current = null; setActivity('idle')
      setMessage(navigator.onLine ? '音频播放失败，请重试。' : '当前离线且音频尚未缓存；联网后再试。')
    }, { once: true })
    audio.play().catch(() => { audioRef.current = null; setActivity('idle'); setMessage('音频播放失败，请重试。') })
  }

  function playDemo() {
    if (!course || !trialDone || activity !== 'idle') return
    const question = course.questions[questionIndex]
    const used = demoPlays[String(question.id)] || 0
    if (used >= 2) return
    playUrl(resolveSpeakingAudioUrl(question.audio_asset), 'demo', () => setDemoPlays((value) => ({ ...value, [String(question.id)]: used + 1 })))
  }

  async function startRecording() {
    if (activity !== 'idle') return
    replaceRecording()
    setMessage('')
    setActivity('countdown')
    try {
      await recorder.start(() => { void stopRecording(true) }, (value) => { setCountdown(value); if (value === 0) setActivity('recording') })
    } catch (error) {
      setActivity('idle'); setCountdown(0)
      setMessage(error instanceof Error && error.message === 'NotAllowedError' ? '请允许麦克风权限后重试。' : '麦克风暂时不可用，请检查浏览器权限。')
    }
  }

  async function stopRecording(force = false) {
    if (!force && !['recording', 'countdown'].includes(activity)) return
    try {
      const captured = await recorder.stop()
      replaceRecording(captured)
      setMessage('录音完成。先回放确认，也可以直接评分。')
    } catch (error) {
      setMessage(error instanceof Error && error.message === 'SILENT_RECORDING' ? '没有录到清楚的声音，请靠近一点再录。' : '录音没有完成，请重试。')
    } finally { setActivity('idle'); setCountdown(0) }
  }

  async function scoreRecording() {
    if (!course || !session || !recording || activity !== 'idle') return
    const question = course.questions[questionIndex]
    const attempt = (session.questions[String(question.id)]?.proofs.length || 0) + 1
    setActivity('scoring'); setMessage('正在评分，请稍等…')
    try {
      const request = {
        result_id: session.result_id, course_id: course.course_id, course_version: course.course_version,
        question_id: question.id, attempt, wav_base64: await blobBase64(recording.wav)
      }
      const response = await withSession(
        (token) => api.scoreSpeakingTake(token, request),
        () => setMessage('正式会话已失效，正在自动恢复；本题录音和已完成评分均已保留…')
      )
      setSession(addScoredTake(session, question.id, response))
      replaceRecording()
      if (response.stars < 3) setDemoPlays((value) => ({ ...value, [String(question.id)]: 0 }))
      setMessage(response.child_feedback)
    } catch (error) {
      setMessage(speakingScoreFailureMessage(error, dataKind))
    } finally { setActivity('idle') }
  }

  function safetyPass() {
    if (!session || !course || activity !== 'idle') return
    setSession(markSafetyPass(session, course.questions[questionIndex].id))
    setMessage('已先过这题，家长端会保留三次记录。')
  }

  function nextQuestion() {
    if (!course || !session || activity !== 'idle') return
    const current = session.questions[String(course.questions[questionIndex].id)]
    if (!current?.complete) return
    replaceRecording()
    setMessage('')
    setQuestionIndex((value) => Math.min(course.questions.length - 1, value + 1))
  }

  async function submit() {
    if (!course || !session || activity !== 'idle') return
    setActivity('submitting')
    try {
      const submission = buildSpeakingSubmission(session, course.course_version)
      const response = await withSession(
        (token) => api.submitSpeakingResult(token, submission),
        () => setMessage('正式会话已失效，正在自动恢复；全部评分、星数、proof 和录音引用均已保留…')
      )
      setSubmitted(true); sessionStorage.removeItem(`sherlock-speaking-${dataKind}-${course.course_id}`)
      if (response.data_kind === 'formal') onFormalCompleted(course.course_id)
      setMessage(response.data_kind === 'formal' ? '正式结果已安全提交。' : 'TEST 结果已安全提交，不计正式完成。')
    } catch (error) {
      setMessage(speakingSubmitFailureMessage(error, dataKind))
    }
    finally { setActivity('idle') }
  }

  if (!catalog) return <main className="center-card"><h1>跟读口语</h1><p>{message || '正在加载课程…'}</p></main>
  const recommended = dataKind === 'formal' ? catalog.firstFormalIncomplete(completedCourseIds) : undefined
  const shownCourses = dataKind === 'test' ? catalog.testCourses() : catalog.window(completedCourseIds, 5)
  if (!course || !session) return (
    <main>
      <section className="hero compact-hero"><p className="eyebrow">SPEAKING · {dataKind === 'formal' ? 'FORMAL' : 'TEST ONLY'}</p><h1>跟读口语</h1><p className="hero-copy">{dataKind === 'formal' ? '正式课程结果和私有录音会保存并衔接既有学习进度。' : '家长验收只保存 test，不计入正式完成。'}</p>{recommended && <div className="stage-pill">当前推荐 · {recommended.course_id}</div>}</section>
      {!sessionToken && <p className="notice warning">{dataKind === 'formal' ? '正式入口正在连接，请稍后重试。' : '请先从家长验收完成认证，再进入口语 test。'}</p>}
      {message && <p className="notice" role="status">{message}</p>}
      <section className="course-list" aria-label="口语课程">{shownCourses.map((item) => {
        const completed = completedCourseIds.has(item.course_id)
        const isRecommended = item.course_id === recommended?.course_id
        return <article className={`course-row${completed ? ' course-completed' : ''}${isRecommended ? ' course-recommended' : ''}`} key={item.course_id}><div><div className="course-title-line"><strong>{item.title}</strong>{isRecommended && <span className="recommendation-badge">推荐</span>}</div><small>{item.course_id} · 第 {item.week} 周第 {item.day} 天</small></div><span className="course-state">{completed ? '已完成' : '未完成'}</span><button type="button" disabled={!sessionToken} onClick={() => startCourse(item.course_id)}>开始</button></article>
      })}</section><Link className="back-link" to="/">← 返回本周任务</Link>
    </main>
  )

  if (submitted) return <main className="center-card result-card"><p className="eyebrow">{dataKind === 'formal' ? 'FORMAL RESULT SAVED' : 'TEST RESULT SAVED'}</p><h1>完成啦</h1><p>{message}</p><button type="button" onClick={() => { setCourse(undefined); setSession(undefined); setSubmitted(false) }}>返回课程列表</button></main>

  if (!trialDone) return (
    <main className="center-card"><p className="eyebrow">{course.course_id} · 麦克风试音</p><h1>先试录</h1><p>每节课只申请一次麦克风权限。录一句、回放听清楚后再开始。</p>
      <button type="button" disabled={activity !== 'idle'} onClick={startRecording}>🎙️ 开始试录</button>
      {activity === 'countdown' && <p className="countdown">{countdown}</p>}
      {activity === 'recording' && <button type="button" onClick={() => { void stopRecording() }}>停止录音</button>}
      {recording && <button type="button" disabled={activity !== 'idle'} onClick={() => playUrl(recording.url, 'replay', () => setTrialReplayed(true))}>{activity === 'replay' ? '正在回放…' : '▶ 回放试音'}</button>}
      <button type="button" disabled={!trialReplayed || activity !== 'idle'} onClick={() => { setTrialDone(true); replaceRecording(); setMessage('') }}>声音正常，开始题目</button>
      {message && <p className="notice" role="status">{message}</p>}
    </main>
  )

  const question = course.questions[questionIndex]
  const questionState = session.questions[String(question.id)]
  const used = demoPlays[String(question.id)] || 0
  const allComplete = course.questions.every((item) => session.questions[String(item.id)]?.complete)
  return (
    <main className="exercise-shell speaking-shell"><p className="eyebrow">{course.course_id} · 第 {questionIndex + 1} / {course.questions.length} 题 · {dataKind === 'formal' ? 'FORMAL' : 'TEST'}</p><h1 className="exercise-title">{question.type === 'repeat' ? '跟着读' : '看提示回答'}</h1>
      <section className="speaking-card"><p className="speaking-prompt">{question.type === 'repeat' ? question.text : question.hint}</p>
        <button type="button" disabled={activity !== 'idle' || used >= 2} onClick={playDemo}>{activity === 'demo' ? '正在播放示范…' : `▶ 听示范（还可 ${2 - used} 次）`}</button>
        <button type="button" disabled={activity !== 'idle' || Boolean(questionState?.complete)} onClick={startRecording}>🎙️ {recording ? '重新录音' : '开始录音'}</button>
        {activity === 'countdown' && <div className="countdown" aria-live="polite">{countdown}</div>}
        {activity === 'recording' && <button type="button" onClick={() => { void stopRecording() }}>■ 读完了</button>}
        {recording && <div className="recording-actions"><button type="button" disabled={activity !== 'idle'} onClick={() => playUrl(recording.url, 'replay')}>▶ 回放我的录音</button><button type="button" disabled={activity !== 'idle' || Boolean(questionState?.complete)} onClick={scoreRecording}>{activity === 'scoring' ? '正在评分…' : '就用这个，开始评分'}</button></div>}
        {questionState && <div className="speaking-feedback"><div className="stars" aria-label={`${questionState.stars} 星`}>{'⭐'.repeat(questionState.stars) || '再试一次'}</div><p>{message || questionState.child_feedback}</p><div className="word-lights">{questionState.word_lights.map((item, index) => <span className={`word-${item.light}`} key={`${item.word}-${index}`}>{item.word}</span>)}</div><small>各次星级：{questionState.take_stars.map((value) => '⭐'.repeat(value) || '未识别').join(' / ')}</small></div>}
        {!questionState && message && <p className="notice" role="status">{message}</p>}
        {questionState && !questionState.complete && questionState.proofs.length === 3 && <button type="button" className="quiet-button" disabled={activity !== 'idle'} onClick={safetyPass}>先过这题</button>}
        {questionState?.complete && (questionIndex < 7 ? <button type="button" disabled={activity !== 'idle'} onClick={nextQuestion}>下一题</button> : <button type="button" disabled={!allComplete || activity !== 'idle'} onClick={submit}>全部完成，提交{dataKind === 'formal' ? '正式结果' : ' TEST'}</button>)}
      </section><p className="notice">播放、录音、评分时不能切题，避免两个声音叠加。</p>
    </main>
  )
}
