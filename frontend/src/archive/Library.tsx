import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { archiveApi, assetUrl, requestJson, upload } from './api'
import type { Result, Topic, TopicDetail } from './api'

const dateFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' })

type Section = 'topics' | 'results'

function UploadForm({
  section, topics, topicId, onSaved, onClose,
}: {
  section: Section
  topics: Topic[]
  topicId: string
  onSaved: (saved: Topic | Result) => void
  onClose: () => void
}) {
  const [progress, setProgress] = useState<number | null>(null)
  const [error, setError] = useState('')
  const controller = useRef<AbortController | null>(null)
  const isTopic = section === 'topics'
  const busy = progress !== null

  useEffect(() => () => controller.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const targetTopic = data.get('topic_id')
    data.delete('topic_id')
    const path = isTopic ? `${archiveApi}/topics` : `${archiveApi}/topics/${targetTopic}/results`
    const request = new AbortController()
    controller.current = request
    setProgress(0)
    setError('')
    try {
      const saved = await upload<Topic | Result>(path, data, setProgress, request.signal)
      onSaved(saved)
    } catch (reason) {
      if (!request.signal.aborted) setError((reason as Error).message)
    } finally {
      controller.current = null
      setProgress(null)
    }
  }

  return (
    <form className="archive-form upload-form" onSubmit={submit} aria-label={isTopic ? '上传选题' : '上传成片'}>
      <h2>{isTopic ? '保存新选题' : '保存成片与封面'}</h2>
      <fieldset disabled={busy}>
        {!isTopic && <label>关联选题<select name="topic_id" defaultValue={topicId} required>
          <option value="">请选择已保存的选题</option>
          {topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}
        </select></label>}
        <label>{isTopic ? '选题标题' : '成片标题'}<input name="title" placeholder="可留空，默认使用文件名" maxLength={240} /></label>
        {isTopic
          ? <label>Word 文档 <small>DOCX · 最大 24 MB</small><input type="file" name="document" accept=".docx" required /></label>
          : <>
              <label>视频文件 <small>MP4 / WebM · 最大 4 GB</small><input type="file" name="video" accept=".mp4,.webm" required /></label>
              <label>封面图片 <small>PNG / JPEG / WebP · 最大 16 MB</small><input type="file" name="cover" accept=".png,.jpg,.jpeg,.webp" required /></label>
            </>}
      </fieldset>
      {busy && <div className="archive-progress" role="status"><progress aria-label="上传进度" value={progress} max={100} /><span>{progress === 100 ? '正在保存…' : `已上传 ${progress}%`}</span></div>}
      {error && <p className="archive-error" role="alert">{error}</p>}
      <div className="archive-actions">
        <button type="submit" className="primary" disabled={busy}>上传并保存</button>
        <button type="button" className="secondary" onClick={() => { controller.current?.abort(); onClose() }}>取消</button>
      </div>
    </form>
  )
}

function DocumentView({ topic }: { topic: Topic }) {
  const detail = useQuery({
    queryKey: ['library', 'topic', topic.id],
    queryFn: ({ signal }) => requestJson<TopicDetail>(`${archiveApi}/topics/${topic.id}`, { signal }),
  })
  return (
    <section className="archive-detail" aria-label="选题详情" tabIndex={0}>
      <div className="detail-header">
        <div><p className="eyebrow">SOURCE DOCUMENT</p><h2>{topic.title}</h2><p className="file-name">{topic.document_name}</p></div>
        <div className="archive-actions">
          <a className="secondary" href={`${archiveApi}/topics/${topic.id}/document`}>下载原件</a>
          <Link className="secondary" to={`/results?topic=${topic.id}`}>查看关联成片</Link>
        </div>
      </div>
      {detail.isPending && <p className="archive-status" role="status">正在读取文档…</p>}
      {detail.isError && <p className="archive-error" role="alert">{detail.error.message}</p>}
      {detail.data && (detail.data.preview_html
        ? <article className="document-paper" aria-label="Word 正文" dangerouslySetInnerHTML={{ __html: detail.data.preview_html }} />
        : <p className="archive-status">此文档没有可显示的正文，可下载原件查阅。</p>)}
    </section>
  )
}

function ResultView({ result }: { result: Result }) {
  const [error, setError] = useState(false)
  return (
    <section className="archive-detail" aria-label="成片详情">
      <div className="detail-header">
        <div><p className="eyebrow">SCREENING ROOM</p><h2>{result.title}</h2>
          <Link className="source-link" to={`/topics?id=${result.topic_id}`}>{result.topic_title} ↗</Link>
        </div>
        <div className="archive-actions">
          <a className="secondary" href={`${assetUrl(result, 'video')}?download=1`}>下载视频</a>
          <a className="secondary" href={`${assetUrl(result, 'cover')}?download=1`}>下载封面</a>
        </div>
      </div>
      <video controls playsInline preload="metadata" poster={assetUrl(result, 'cover')} src={assetUrl(result, 'video')} onError={() => setError(true)} aria-label={result.title} />
      {error && <p className="archive-error" role="alert">无法播放该视频，可下载原片，或检查浏览器是否支持此编码。</p>}
      <p className="file-name">{result.video_name}</p>
    </section>
  )
}

export function Library({ section }: { section: Section }) {
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const [showForm, setShowForm] = useState(false)
  const [indexHidden, setIndexHidden] = useState(() => localStorage.getItem('frontier-topic-index-hidden') === 'true')
  const isTopic = section === 'topics'
  const topicId = params.get('topic') ?? ''
  const topicQuery = useQuery({
    queryKey: ['library', 'topics'],
    queryFn: ({ signal }) => requestJson<Topic[]>(`${archiveApi}/topics`, { signal }),
  })
  const resultQuery = useQuery({
    queryKey: ['library', 'results'],
    queryFn: ({ signal }) => requestJson<Result[]>(`${archiveApi}/results`, { signal }),
    enabled: !isTopic,
  })
  const topics = topicQuery.data ?? []
  const activeQuery = isTopic ? topicQuery : resultQuery
  const results = (resultQuery.data ?? []).filter((result) => !topicId || result.topic_id === topicId)
  const rows = isTopic ? topics : results
  const selected = rows.find(({ id }) => id === params.get('id')) ?? rows[0]

  function select(id: string) {
    const next = new URLSearchParams(params)
    next.set('id', id)
    setParams(next)
  }

  function onSaved(saved: Topic | Result) {
    const next = new URLSearchParams(params)
    next.set('id', saved.id)
    if (topicId && 'topic_id' in saved) next.set('topic', saved.topic_id)
    queryClient.setQueryData<(Topic | Result)[]>(['library', section], (items) => [saved, ...(items ?? [])])
    void queryClient.invalidateQueries({ queryKey: ['library', section] })
    setParams(next)
    setShowForm(false)
  }

  function toggleIndex() {
    localStorage.setItem('frontier-topic-index-hidden', String(!indexHidden))
    setIndexHidden(!indexHidden)
  }

  return (
    <main className={isTopic ? 'archive-main topic-library' : 'archive-main'}>
      <section className="library-heading">
        <div>
          <p className="eyebrow">{isTopic ? '01 / TOPIC LIBRARY' : '02 / FILM LIBRARY'}</p>
          <h1>{isTopic ? '选题库' : '成片库'}</h1>
          <p>{isTopic ? '保存研究材料与双语脚本，在网页上直接查阅 Word 正文。' : '把视频和封面归档到选题，按版本查找、播放与下载。'}</p>
        </div>
        <div className="archive-actions">
          {isTopic && activeQuery.isSuccess && (
            <button type="button" className="secondary" aria-controls="topic-index" aria-expanded={!indexHidden} onClick={toggleIndex}>
              {indexHidden ? '显示索引' : '隐藏索引'}
            </button>
          )}
          {!showForm && (isTopic || topics.length > 0
            ? <button type="button" className="primary" onClick={() => setShowForm(true)}>{isTopic ? '＋ 上传选题' : '＋ 上传成片'}</button>
            : <Link className="secondary" to="/topics">前往选题库</Link>)}
        </div>
      </section>

      {showForm && <UploadForm section={section} topics={topics} topicId={topicId} onSaved={onSaved} onClose={() => setShowForm(false)} />}

      {!isTopic && topicQuery.isError && <p className="archive-error" role="alert">无法读取关联选题。<button className="text-button" onClick={() => void topicQuery.refetch()}>重试</button></p>}
      {activeQuery.isPending && <p className="archive-status" role="status">正在载入档案…</p>}
      {activeQuery.isError && <p className="archive-error" role="alert">{activeQuery.error.message} <button className="text-button" onClick={() => void activeQuery.refetch()}>重试</button></p>}
      {activeQuery.isSuccess && (
        <div className={isTopic && indexHidden ? 'archive-grid index-hidden' : 'archive-grid'}>
          <section className="archive-list" id={isTopic ? 'topic-index' : undefined} hidden={isTopic && indexHidden} aria-label={isTopic ? '选题列表' : '成片列表'}>
            <div className="list-label"><span>{isTopic ? '选题索引' : '成片索引'}</span><span>{rows.length} 项</span></div>
            {!isTopic && <label className="archive-filter">筛选选题<select value={topicId} onChange={(event) => {
              const next = event.target.value
              setParams(next ? { topic: next } : {})
            }}>
              <option value="">全部选题</option>
              {topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}
            </select></label>}
            {rows.length === 0 && <p className="archive-status">{isTopic ? '还没有选题。上传一个 DOCX 即可开始。' : '当前没有归档的成片。'}</p>}
            <ul>
              {rows.map((row) => (
                <li key={row.id}><button className="archive-row" type="button" aria-pressed={row.id === selected?.id} onClick={() => select(row.id)}>
                  {'cover_name' in row && <img src={assetUrl(row, 'cover')} alt="" loading="lazy" />}
                  <span><strong>{row.title}</strong><small>{dateFormat.format(new Date(row.created_at))}</small></span>
                </button></li>
              ))}
            </ul>
          </section>
          {selected ? ('cover_name' in selected
            ? <ResultView key={selected.id} result={selected} />
            : <DocumentView key={selected.id} topic={selected} />)
            : <div className="archive-empty"><span aria-hidden="true">{isTopic ? '01' : '02'}</span><p>{isTopic ? '文档预览将在这里显示' : '上传后可在这里播放成片'}</p></div>}
        </div>
      )}
    </main>
  )
}
