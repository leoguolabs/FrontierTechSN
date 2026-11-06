import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { archiveApi, assetUrl, requestJson, upload } from './api'
import type { Result, Topic, TopicDetail } from './api'
import { dateOptions, filterLibrary, readFilters } from './filters'
import { SearchSelect } from './SearchSelect'

const dateFormat = new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium' })

type Section = 'topics' | 'results'

function DocumentDropzone({ disabled, onError }: { disabled: boolean; onError: (message: string) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const fileSize = file && (file.size < 1024 * 1024
    ? `${Math.max(1, Math.ceil(file.size / 1024))} KB`
    : `${(file.size / 1024 / 1024).toFixed(2)} MB`)

  function chooseFiles(files: File[], dropped = false) {
    if (disabled || !input.current) return
    const next = files[0]
    const message = files.length > 1 ? '每次只能上传一个 DOCX 文档。'
      : next && !next.name.toLowerCase().endsWith('.docx') ? '请选择 DOCX 格式的 Word 文档。'
      : next && next.size > 24 * 1024 * 1024 ? '文档大小不能超过 24 MB。'
      : next && next.size === 0 ? '文档为空，请重新选择。' : ''
    onError(message)
    if (message) {
      input.current.value = ''
      setFile(null)
      return
    }
    if (dropped) {
      const transfer = new DataTransfer()
      if (next) transfer.items.add(next)
      input.current.files = transfer.files
    }
    setFile(next ?? null)
  }

  return (
    <label className={`document-dropzone${dragging && !disabled ? ' is-dragging' : ''}${file ? ' has-file' : ''}`}
      onDragOver={(event) => { event.preventDefault(); if (!disabled) setDragging(true) }}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false) }}
      onDrop={(event) => {
        event.preventDefault()
        setDragging(false)
        chooseFiles(Array.from(event.dataTransfer.files), true)
      }}>
      <input ref={input} type="file" name="document" accept=".docx" required disabled={disabled}
        className="document-drop-input" aria-label="选择或拖拽 Word 文档" aria-describedby="document-drop-hint"
        onChange={(event) => chooseFiles(Array.from(event.currentTarget.files ?? []))} />
      <svg viewBox="0 0 32 32" width="36" height="36" aria-hidden="true"><path d="M19 3H8a2 2 0 0 0-2 2v22a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V10Zm0 0v7h7M16 23V14m-4 4 4-4 4 4" /></svg>
      <strong>{file ? file.name : dragging ? '松开即可选择文档' : '拖拽 Word 文档到这里'}</strong>
      <span id="document-drop-hint">{file ? `${fileSize} · 点击或拖拽可更换` : '或点击选择文件 · DOCX · 最大 24 MB'}</span>
    </label>
  )
}

function TopicUploadDialog({ onSaved, onClose }: { onSaved: (saved: Topic | Result) => void; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const element = dialog.current
    const overflow = document.body.style.overflow
    const previousFocus = document.activeElement
    element?.showModal()
    document.body.style.overflow = 'hidden'
    return () => {
      element?.close()
      document.body.style.overflow = overflow
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus()
    }
  }, [])

  return (
    <dialog ref={dialog} className="topic-upload-dialog" aria-labelledby="topic-upload-title"
      onCancel={(event) => { event.preventDefault(); onClose() }}>
      <button type="button" className="upload-dialog-close" aria-label="关闭上传选题" onClick={onClose}>×</button>
      <UploadForm section="topics" topics={[]} topicId="" onSaved={onSaved} onClose={onClose} />
    </dialog>
  )
}

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
  const [targetTopic, setTargetTopic] = useState(topicId)
  const controller = useRef<AbortController | null>(null)
  const isTopic = section === 'topics'
  const busy = progress !== null

  useEffect(() => () => controller.current?.abort(), [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    if (!isTopic && !targetTopic) { setError('请选择关联选题'); return }
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
      <h2 id={isTopic ? 'topic-upload-title' : undefined}>{isTopic ? '上传选题' : '保存成片与封面'}</h2>
      <fieldset disabled={busy}>
        {!isTopic && <SearchSelect label="关联选题" value={targetTopic} onChange={setTargetTopic}
          disabled={busy} placeholder="请选择已保存的选题" searchPlaceholder="搜索选题标题或文件名…"
          options={topics.map((topic) => ({ value: topic.id, label: topic.title, description: topic.document_name }))} />}
        <label>{isTopic ? '选题标题' : '成片标题'}<input name="title" placeholder="可留空，默认使用文件名" maxLength={240} /></label>
        {isTopic
          ? <DocumentDropzone disabled={busy} onError={setError} />
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
    <section className="archive-detail" aria-label="成片详情" tabIndex={0}>
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
  const isTopic = section === 'topics'
  const indexId = isTopic ? 'topic-index' : 'result-index'
  const indexPreference = `frontier-${indexId}-hidden`
  const [indexHidden, setIndexHidden] = useState(() => localStorage.getItem(indexPreference) === 'true')
  const filters = readFilters(params)
  const topicId = filters.topic
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
  const allRows: (Topic | Result)[] = isTopic ? topics : (resultQuery.data ?? [])
  const rows = filterLibrary(allRows, filters)
  const selected = rows.find(({ id }) => id === params.get('id')) ?? rows[0]
  const hasFilters = !!(filters.name || filters.date || (!isTopic && topicId))
  const invalidRange = filters.date === 'custom' && !!filters.from && !!filters.to && filters.from > filters.to
  const names = [...new Set(allRows.map((row) => row.title))]

  function updateFilters(updates: Record<string, string>) {
    const next = new URLSearchParams(params)
    next.delete('id')
    for (const [key, value] of Object.entries(updates)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    setParams(next)
  }

  function clearFilters() {
    const next = new URLSearchParams(params)
    for (const key of ['name', 'date', 'from', 'to', 'topic', 'id']) next.delete(key)
    setParams(next)
  }

  function select(id: string) {
    const next = new URLSearchParams(params)
    next.set('id', id)
    setParams(next)
  }

  function onSaved(saved: Topic | Result) {
    const next = new URLSearchParams(params)
    for (const key of ['name', 'date', 'from', 'to']) next.delete(key)
    next.set('id', saved.id)
    if (topicId && 'topic_id' in saved) next.set('topic', saved.topic_id)
    queryClient.setQueryData<(Topic | Result)[]>(['library', section], (items) => [saved, ...(items ?? [])])
    void queryClient.invalidateQueries({ queryKey: ['library', section] })
    setParams(next)
    setShowForm(false)
  }

  function toggleIndex() {
    localStorage.setItem(indexPreference, String(!indexHidden))
    setIndexHidden(!indexHidden)
  }

  return (
    <main className="archive-main" aria-label={isTopic ? '选题库' : '成片库'}>
      <div className="library-toolbar">
        {activeQuery.isSuccess && <section className="library-filters" aria-label="档案筛选">
          <div className={`library-filter-fields${isTopic ? ' topics-filters' : ''}`}>
            <SearchSelect label="上传日期" value={filters.date} options={dateOptions}
              onChange={(date) => updateFilters({ date, from: '', to: '' })} searchPlaceholder="搜索日期范围…" />
            <SearchSelect label="任务名称" value={filters.name} onChange={(name) => updateFilters({ name })}
              searchPlaceholder={isTopic ? '输入选题标题关键词…' : '输入成片标题关键词…'}
              options={[{ value: '', label: '全部任务' }, ...names.map((name) => ({ value: name, label: name }))]} />
            {!isTopic && <SearchSelect label="关联选题" value={topicId} onChange={(topic) => updateFilters({ topic })}
              searchPlaceholder="搜索选题标题或文件名…"
              options={[{ value: '', label: '全部选题' }, ...topics.map((topic) => ({ value: topic.id, label: topic.title, description: topic.document_name }))]} />}
            <button type="button" className="secondary clear-filters" onClick={clearFilters} disabled={!hasFilters}>清除筛选</button>
          </div>
          {filters.date === 'custom' && <div className="library-date-range">
            <label>开始日期<input type="date" aria-invalid={invalidRange} max={filters.to || undefined}
              value={filters.from} onChange={(event) => updateFilters({ from: event.target.value })} /></label>
            <span aria-hidden="true">—</span>
            <label>结束日期<input type="date" aria-invalid={invalidRange} min={filters.from || undefined}
              value={filters.to} onChange={(event) => updateFilters({ to: event.target.value })} /></label>
            <p className={invalidRange ? 'date-range-error' : ''} role={invalidRange ? 'alert' : undefined}>
              {invalidRange ? '开始日期不能晚于结束日期。' : '包含起止当天，可只填写一端。'}
            </p>
          </div>}
        </section>}
        <div className="archive-actions library-toolbar-actions">
          {activeQuery.isSuccess && <span className="library-filter-count" aria-live="polite">{rows.length} / {allRows.length} 项</span>}
          {activeQuery.isSuccess && (
            <button type="button" className="secondary" aria-controls={indexId} aria-expanded={!indexHidden} onClick={toggleIndex}>
              {indexHidden ? '显示索引' : '隐藏索引'}
            </button>
          )}
          {(!showForm || isTopic) && (isTopic || topics.length > 0
            ? <button type="button" className="primary" onClick={() => setShowForm(true)}>{isTopic ? '＋ 上传选题' : '＋ 上传成片'}</button>
            : <Link className="secondary" to="/topics">前往选题库</Link>)}
        </div>
      </div>

      {showForm && (isTopic
        ? <TopicUploadDialog onSaved={onSaved} onClose={() => setShowForm(false)} />
        : <UploadForm section={section} topics={topics} topicId={topicId} onSaved={onSaved} onClose={() => setShowForm(false)} />)}

      {!isTopic && topicQuery.isError && <p className="archive-error" role="alert">无法读取关联选题。<button className="text-button" onClick={() => void topicQuery.refetch()}>重试</button></p>}
      {activeQuery.isPending && <p className="archive-status" role="status">正在载入档案…</p>}
      {activeQuery.isError && <p className="archive-error" role="alert">{activeQuery.error.message} <button className="text-button" onClick={() => void activeQuery.refetch()}>重试</button></p>}
      {activeQuery.isSuccess && (
        <div className={indexHidden ? 'archive-grid index-hidden' : 'archive-grid'}>
          <section className="archive-list" id={indexId} hidden={indexHidden} aria-label={isTopic ? '选题列表' : '成片列表'}>
            <div className="list-label"><span>{isTopic ? '选题索引' : '成片索引'}</span><span>{rows.length} 项</span></div>
            {rows.length === 0 && <p className="archive-status">{hasFilters ? '没有符合筛选条件的档案。请调整条件或清除筛选。' : isTopic ? '还没有选题。上传一个 DOCX 即可开始。' : '当前没有归档的成片。'}</p>}
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
            : <div className="archive-empty"><span aria-hidden="true">{isTopic ? '01' : '02'}</span><p>{hasFilters ? '没有匹配的档案' : isTopic ? '文档预览将在这里显示' : '上传后可在这里播放成片'}</p>{hasFilters && <button type="button" className="secondary" onClick={clearFilters}>清除筛选，查看全部</button>}</div>}
        </div>
      )}
    </main>
  )
}
