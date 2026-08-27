import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { SherlockApi } from '../core/cloudbase-api'
import {
  loadListeningCatalog,
  loadListeningCourse,
  resolveAudioUrl,
  type ListeningCatalog,
  type ListeningCourse,
  type ListeningQuestion
} from '../listening/course'
import {
  answerQuestion,
  buildListeningSubmission,
  createCorrectionState,
  createListeningSession,
  recordPlay,
  resolveCorrectionResponse,
  type CorrectionState,
  type ListeningPick,
  type ListeningSession
} from '../listening/session'

interface ListeningPageProps {
  api: SherlockApi
  sessionToken: string
  dataKind?: 'formal' | 'test'
  completedCourseIds?: ReadonlySet<string>
  onFormalCompleted?: (courseId: string) => void
  loadCatalog?: () => Promise<ListeningCatalog>
  loadCourse?: (courseId: string) => Promise<ListeningCourse>
}

function newResultId(): string {
  return crypto.randomUUID?.() || '00000000-0000-4000-8000-000000000000'
}

function questionOptions(question: ListeningQuestion): Array<{ label: string; value: ListeningPick }> {
  if (question.type === 'sentence_judge') return [{ label: '✓ 一样 / 对', value: 'same' }, { label: '✗ 不一样 / 不对', value: 'different' }]
  if (question.type === 'passage_judge') return [{ label: '✓ 对', value: 'true' }, { label: '✗ 错', value: 'false' }]
  return question.options.map((option, index) => ({ label: `${String.fromCharCode(65 + index)}. ${option}`, value: index }))
}

type ActiveAudio = { id: string; phase: 'loading' | 'playing' } | null

function LimitedAudioButton({ audioId, maxPlays, used, onPlay, activeAudio, label = '播放录音' }: {
  audioId: string; maxPlays: number; used: number; onPlay: () => void; activeAudio: ActiveAudio; label?: string
}) {
  const ownAudio = activeAudio?.id === audioId ? activeAudio : null
  return (
    <div className="audio-action">
      <button type="button" onClick={onPlay} disabled={Boolean(activeAudio) || used >= maxPlays}>
        {ownAudio?.phase === 'loading' ? '正在加载…' : ownAudio?.phase === 'playing' ? '正在播放…' : used >= maxPlays ? '播放次数已用完' : `${label}（还可 ${maxPlays - used} 次）`}
      </button>
    </div>
  )
}

function QuestionChoices({ question, value, onChange }: {
  question: ListeningQuestion; value: ListeningPick | undefined; onChange: (pick: ListeningPick) => void
}) {
  return (
    <fieldset className="choice-list">
      <legend className="sr-only">第 {question.id} 题选项</legend>
      {questionOptions(question).map((option) => (
        <label key={String(option.value)}>
          <input type="radio" name={`q-${question.id}`} checked={value === option.value} onChange={() => onChange(option.value)} />
          <span>{option.label}</span>
        </label>
      ))}
    </fieldset>
  )
}

export function ListeningPage({
  api, sessionToken, dataKind = 'test', completedCourseIds = new Set<string>(), onFormalCompleted = () => undefined,
  loadCatalog = loadListeningCatalog, loadCourse = loadListeningCourse
}: ListeningPageProps) {
  const [catalog, setCatalog] = useState<ListeningCatalog>()
  const [course, setCourse] = useState<ListeningCourse>()
  const [session, setSession] = useState<ListeningSession>()
  const [trialDone, setTrialDone] = useState(false)
  const [trialHeard, setTrialHeard] = useState(false)
  const [trialPlaying, setTrialPlaying] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [wrongIds, setWrongIds] = useState<number[]>()
  const [correction, setCorrection] = useState<CorrectionState>()
  const [correctionPick, setCorrectionPick] = useState<ListeningPick>()
  const [correctionPlays, setCorrectionPlays] = useState<Record<string, number>>({})
  const [activeAudio, setActiveAudio] = useState<ActiveAudio>(null)
  const activeAudioRef = useRef<HTMLAudioElement | null>(null)
  const audioTimeoutRef = useRef<number | null>(null)

  function clearAudioTimeout() {
    if (audioTimeoutRef.current !== null) window.clearTimeout(audioTimeoutRef.current)
    audioTimeoutRef.current = null
  }

  function releaseAudio(audio: HTMLAudioElement) {
    if (activeAudioRef.current !== audio) return
    clearAudioTimeout()
    activeAudioRef.current = null
    setActiveAudio(null)
  }

  function failAudio(audio: HTMLAudioElement) {
    if (activeAudioRef.current !== audio) return
    audio.pause()
    releaseAudio(audio)
    setMessage(navigator.onLine
      ? '音频加载失败，请检查网络后再点一次。'
      : '当前离线且这段音频尚未缓存；联网后再点一次。')
  }

  async function playAudio(audioId: string, asset: string, onStarted?: () => void, onEnded?: () => void) {
    if (activeAudioRef.current) return
    setMessage('')
    const audio = new Audio(resolveAudioUrl(asset))
    activeAudioRef.current = audio
    setActiveAudio({ id: audioId, phase: 'loading' })
    audio.addEventListener('ended', () => {
      if (activeAudioRef.current !== audio) return
      releaseAudio(audio)
      onEnded?.()
    }, { once: true })
    audio.addEventListener('error', () => failAudio(audio), { once: true })
    audioTimeoutRef.current = window.setTimeout(() => failAudio(audio), 8000)
    try {
      await audio.play()
      if (activeAudioRef.current !== audio) return
      clearAudioTimeout()
      setActiveAudio({ id: audioId, phase: 'playing' })
      onStarted?.()
    } catch {
      failAudio(audio)
    }
  }

  useEffect(() => () => {
    clearAudioTimeout()
    activeAudioRef.current?.pause()
    activeAudioRef.current = null
  }, [])

  useEffect(() => {
    loadCatalog().then(setCatalog).catch(() => setMessage('课程目录暂时无法加载，请稍后重试。'))
  }, [loadCatalog])

  useEffect(() => {
    if (session) sessionStorage.setItem(`sherlock-listening-${dataKind}-${session.course_id}`, JSON.stringify(session))
  }, [dataKind, session])

  const shownCourses = catalog?.window(completedCourseIds, 5) || []
  const recommended = catalog?.firstFormalIncomplete(completedCourseIds)
  const allQuestions = useMemo(() => course?.sections.flatMap((section) => section.questions) || [], [course])
  const allAnswered = Boolean(session && allQuestions.length && allQuestions.every((question) => session.answers[String(question.id)] !== undefined))

  async function startCourse(courseId: string) {
    if (!sessionToken) return
    setBusy(true)
    setMessage('')
    try {
      const loaded = await loadCourse(courseId)
      setCourse(loaded)
      const stored = sessionStorage.getItem(`sherlock-listening-${dataKind}-${courseId}`)
      setSession(stored ? JSON.parse(stored) as ListeningSession : createListeningSession(courseId, newResultId()))
      setTrialDone(false)
      setTrialHeard(false)
      setWrongIds(undefined)
      setCorrection(undefined)
    } catch {
      setMessage('课程暂时无法打开，请稍后重试。')
    } finally {
      setBusy(false)
    }
  }

  async function playTrial() {
    if (!course || activeAudio) return
    setTrialPlaying(true)
    await playAudio('trial', course.test_audio_asset, undefined, () => {
      setTrialPlaying(false)
      setTrialHeard(true)
    })
    if (!activeAudioRef.current) setTrialPlaying(false)
  }

  async function submit() {
    if (!course || !session || !sessionToken || !allAnswered) return
    setBusy(true)
    setMessage('')
    try {
      const response = await api.submitListeningResult(sessionToken, buildListeningSubmission(session, course.course_version, new Date().toISOString(), {
        platform: navigator.platform || 'unknown', user_agent: navigator.userAgent
      }))
      setWrongIds(response.wrong_question_ids)
      setCorrection(createCorrectionState(response.wrong_question_ids))
      if (response.data_kind === 'formal') onFormalCompleted(course.course_id)
      const kindLabel = response.data_kind === 'formal' ? '正式' : 'TEST'
      setMessage(response.idempotent ? `已恢复此前提交的同一条${kindLabel}结果。` : `${kindLabel}结果已安全提交。`)
    } catch {
      setMessage('提交没有完成。网络恢复后可再次点击，系统会沿用同一 result_id 防止重复。')
    } finally {
      setBusy(false)
    }
  }

  function findQuestion(questionId: number) {
    for (const section of course?.sections || []) {
      const question = section.questions.find((item) => item.id === questionId)
      if (question) return { section, question }
    }
    return undefined
  }

  async function checkCorrection() {
    if (!sessionToken || !session || !correction || correction.phase === 'done' || correctionPick === undefined) return
    const questionId = correction.queue[correction.index]
    setBusy(true)
    try {
      const attempt = correction.phase === 'try1' ? 1 : 2
      const response = await api.checkListeningCorrection(sessionToken, session.result_id, questionId, attempt, correctionPick)
      setCorrection(resolveCorrectionResponse(correction, response))
      setCorrectionPick(undefined)
    } catch {
      setMessage('订正校验暂时失败，请重试。')
    } finally {
      setBusy(false)
    }
  }

  if (!catalog) return <main className="center-card"><h1>听力训练</h1><p>{message || '正在加载课程…'}</p></main>

  if (!course || !session) {
    return (
      <main>
        <section className="hero compact-hero">
          <p className="eyebrow">LISTENING · {dataKind === 'formal' ? 'FORMAL' : 'TEST ONLY'}</p>
          <h1>听力训练</h1>
          <p className="hero-copy">{dataKind === 'formal' ? '正式课程结果会保存并衔接既有学习进度。' : '家长验收只保存 test，不计入正式完成。'}</p>
          {recommended && <div className="stage-pill">当前推荐 · {recommended.course_id}</div>}
        </section>
        {!sessionToken && <p className="notice warning">{dataKind === 'formal' ? '正式入口正在连接，请稍后重试。' : '请先从家长验收完成认证，再进入听力 test。'}</p>}
        {message && <p className="notice" role="status">{message}</p>}
        <section className="course-list" aria-label="听力课程">
          {shownCourses.map((item) => (
            <article className={`course-row${completedCourseIds.has(item.course_id) ? ' course-completed' : ''}${item.course_id === recommended?.course_id ? ' course-recommended' : ''}`} key={item.course_id}>
              <div><div className="course-title-line"><strong>{item.title}</strong>{item.course_id === recommended?.course_id && <span className="recommendation-badge">推荐</span>}</div><small>{item.course_id} · 第 {item.week} 周第 {item.day} 天</small></div>
              <span className="course-state">{completedCourseIds.has(item.course_id) ? '已完成' : '未完成'}</span>
              <button type="button" disabled={!sessionToken || busy} onClick={() => startCourse(item.course_id)} aria-label={`开始 ${item.course_id}`}>开始</button>
            </article>
          ))}
        </section>
        <Link className="back-link" to="/">← 返回本周任务</Link>
      </main>
    )
  }

  if (wrongIds && correction && correction.phase !== 'done') {
    const currentId = correction.queue[correction.index]
    const found = findQuestion(currentId)
    if (!found) return null
    const asset = found.section.shared_audio ? found.section.passage_audio_asset! : ('audio_asset' in found.question ? found.question.audio_asset : '')
    const playKey = `${currentId}-${correction.phase}`
    return (
      <main className="exercise-shell">
        <p className="eyebrow">错题订正 · {correction.index + 1} / {correction.queue.length}</p>
        <h1 className="exercise-title">第 {currentId} 题</h1>
        {correction.phase === 'try1'
          ? <p className="notice">先不看原文，再听、再做一次。</p>
          : <div className="transcript-box"><strong>原文</strong>{correction.transcript?.map((line) => <p key={line}>{line}</p>)}</div>}
        <LimitedAudioButton audioId={`correction-${playKey}`} activeAudio={activeAudio} maxPlays={2} used={correctionPlays[playKey] || 0}
          onPlay={() => playAudio(
            `correction-${playKey}`,
            asset,
            () => setCorrectionPlays((value) => ({ ...value, [playKey]: Math.min(2, (value[playKey] || 0) + 1) }))
          )} label="订正重听" />
        {'display' in found.question && <p className="question-prompt">{found.question.display}</p>}
        {'statement' in found.question && <p className="question-prompt">{found.question.statement}</p>}
        {'question_text' in found.question && found.question.question_text && <p className="question-prompt">{found.question.question_text}</p>}
        <QuestionChoices question={found.question} value={correctionPick} onChange={setCorrectionPick} />
        <button type="button" disabled={busy || Boolean(activeAudio) || correctionPick === undefined} onClick={checkCorrection}>确认订正</button>
      </main>
    )
  }

  if (wrongIds) {
    return (
      <main className="center-card result-card">
        <p className="eyebrow">{dataKind === 'formal' ? 'FORMAL RESULT SAVED' : 'TEST RESULT SAVED'}</p>
        <h1>完成啦</h1>
        <p>{wrongIds.length ? '有几题需要以后再复习，本次订正已经记录。' : '本次全部答对。'}</p>
        <div className="stage-pill">{dataKind === 'formal' ? '正式结果已保存' : '只写 test · 不计正式完成'}</div>
        <button type="button" onClick={() => {
          sessionStorage.removeItem(`sherlock-listening-${dataKind}-${session.course_id}`)
          setCourse(undefined); setSession(undefined); setWrongIds(undefined)
        }}>返回课程列表</button>
      </main>
    )
  }

  if (!trialDone) {
    return (
      <main className="center-card">
        <p className="eyebrow">{course.course_id} · {dataKind === 'formal' ? 'FORMAL' : 'TEST'}</p>
        <h1>{course.title}</h1>
        <p>先试音。试音不限次数，听到声音后再开始答题。</p>
        <button type="button" disabled={Boolean(activeAudio)} onClick={playTrial}>{activeAudio?.id === 'trial' ? activeAudio.phase === 'loading' ? '正在加载…' : '正在播放…' : '播放试音'}</button>
        {trialHeard && <p>试音成功</p>}
        <button type="button" disabled={!trialHeard || trialPlaying || Boolean(activeAudio)} onClick={() => setTrialDone(true)}>开始做题</button>
        {message && <p className="notice" role="status">{message}</p>}
      </main>
    )
  }

  return (
    <main className="exercise-shell">
      <p className="eyebrow">{course.course_id} · {dataKind === 'formal' ? 'FORMAL' : 'TEST ONLY'}</p>
      <h1 className="exercise-title">{course.title}</h1>
      <p className="notice">交卷前不显示对错。短文四题共用同一个播放次数。</p>
      {course.sections.map((section, sectionIndex) => (
        <section className="question-section" key={section.id}>
          <header><span>第 {'一二三四五'[sectionIndex]}部分</span><h2>{section.name}</h2><p>{section.tip}</p></header>
          {section.shared_audio && <LimitedAudioButton audioId={`section-${section.id}`} activeAudio={activeAudio} maxPlays={section.max_plays}
            used={session.play_counts[section.id] || 0} onPlay={() => playAudio(`section-${section.id}`, section.passage_audio_asset!, () => setSession(recordPlay(session, section.id, section.max_plays)))} label="播放短文" />}
          {section.questions.map((question) => (
            <article className="question-card" key={question.id}>
              <strong>第 {question.id} 题</strong>
              {!section.shared_audio && 'audio_asset' in question && <LimitedAudioButton audioId={`question-${question.id}`} activeAudio={activeAudio} maxPlays={section.max_plays}
                used={session.play_counts[String(question.id)] || 0}
                onPlay={() => playAudio(`question-${question.id}`, question.audio_asset, () => setSession(recordPlay(session, String(question.id), section.max_plays)))} />}
              {'display' in question && <p className="question-prompt">{question.display}</p>}
              {'statement' in question && <p className="question-prompt">{question.statement}</p>}
              {'question_text' in question && question.question_text && <p className="question-prompt">{question.question_text}</p>}
              <QuestionChoices question={question} value={session.answers[String(question.id)]}
                onChange={(pick) => setSession(answerQuestion(session, question.id, pick))} />
            </article>
          ))}
        </section>
      ))}
      <button className="submit-course" type="button" disabled={!allAnswered || busy || Boolean(activeAudio)} onClick={submit}>
        {busy ? '正在安全提交…' : `全部完成，提交${dataKind === 'formal' ? '正式结果' : ' TEST'}`}
      </button>
      {!allAnswered && <p className="notice">答完全部题目后才能提交。</p>}
      {message && <p className="notice" role="status">{message}</p>}
    </main>
  )
}
