import assert from 'node:assert/strict'
import test from 'node:test'
import type { Result } from '../src/archive/api.ts'
import { filterLibrary, localDate, readFilters } from '../src/archive/filters.ts'

function result(id: string, createdAt: string, title = '机器人演示', topicId = 'robotics'): Result {
  return { id, title, created_at: createdAt, topic_id: topicId, topic_title: topicId, video_name: `${id}.mp4`, cover_name: `${id}.png` }
}

function ids(items: Result[], query: string, now = new Date(2026, 10, 6, 12)) {
  return filterLibrary(items, readFilters(new URLSearchParams(query)), now).map((item) => item.id)
}

test('date presets count calendar days, include today, and exclude future uploads', () => {
  const items = [
    result('future', '2026-11-07T00:00:00'), result('today-end', '2026-11-06T23:59:59'),
    result('today-start', '2026-11-06T00:00:00'), result('week-start', '2026-10-31T00:00:00'),
    result('before-week', '2026-10-30T23:59:59'), result('month-start', '2026-10-08T00:00:00'),
    result('before-month', '2026-10-07T23:59:59'),
  ]
  assert.deepEqual(ids(items, 'date=today'), ['today-end', 'today-start'])
  assert.deepEqual(ids(items, 'date=7d'), ['today-end', 'today-start', 'week-start'])
  assert.deepEqual(ids(items, 'date=30d'), ['today-end', 'today-start', 'week-start', 'before-week', 'month-start'])
})

test('custom dates include both boundaries, support one open end, and reject reversed ranges', () => {
  const items = [result('first', '2026-11-01T00:00:00'), result('last', '2026-11-06T23:59:59'), result('next', '2026-11-07T00:00:00')]
  assert.deepEqual(ids(items, 'date=custom&from=2026-11-01&to=2026-11-06'), ['first', 'last'])
  assert.deepEqual(ids(items, 'date=custom&from=2026-11-06'), ['last', 'next'])
  assert.deepEqual(ids(items, 'date=custom&to=2026-11-01'), ['first'])
  assert.deepEqual(ids(items, 'date=custom&from=2026-11-06&to=2026-11-01'), [])
  assert.deepEqual(ids(items, 'date=custom'), ['first', 'last', 'next'])
})

test('task title, linked topic, and upload date are intersected without dropping duplicate titles', () => {
  const items = [
    result('match-1', '2026-11-06T08:00:00'), result('match-2', '2026-11-06T09:00:00'),
    result('older', '2026-10-01T08:00:00'), result('other-title', '2026-11-06T08:00:00', '太空任务'),
    result('other-topic', '2026-11-06T08:00:00', '机器人演示', 'space'),
  ]
  assert.deepEqual(ids(items, new URLSearchParams({ name: '机器人演示', topic: 'robotics', date: 'today' }).toString()), ['match-1', 'match-2'])
  assert.deepEqual(ids(items, 'name=missing'), [])
  assert.equal(ids(items, '').length, items.length)
})

test('UTC timestamps are filtered by the same local date shown in the interface', () => {
  const timestamp = '2026-11-05T23:30:00Z'
  const day = localDate(new Date(timestamp))
  assert.deepEqual(ids([result('boundary', timestamp)], `date=custom&from=${day}&to=${day}`), ['boundary'])
  if (process.env.TZ === 'Asia/Singapore') assert.equal(day, '2026-11-06')
  if (process.env.TZ === 'America/New_York') assert.equal(day, '2026-11-05')
})

test('URL filters survive a round trip and malformed dates do not silently roll into another month', () => {
  const values = { name: 'AI & 太空 + 1', topic: 'space', date: 'custom', from: '2026-11-01', to: '2026-11-06' }
  assert.deepEqual(readFilters(new URLSearchParams(new URLSearchParams(values).toString())), values)
  assert.equal(readFilters(new URLSearchParams('date=custom&from=0002-11-06')).from, '0002-11-06')
  assert.deepEqual(readFilters(new URLSearchParams('date=unknown&from=2026-02-30&to=bad')), { name: '', topic: '', date: '', from: '', to: '' })
})
