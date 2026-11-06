import type { Result, Topic } from './api'

export type DateRange = '' | 'today' | '7d' | '30d' | 'custom'
export type LibraryFilters = { name: string; topic: string; date: DateRange; from: string; to: string }

export const dateOptions = [
  { value: '', label: '全部日期' },
  { value: 'today', label: '今天' },
  { value: '7d', label: '最近 7 天' },
  { value: '30d', label: '最近 30 天' },
  { value: 'custom', label: '自定义日期范围' },
] satisfies { value: DateRange; label: string }[]

// Use the same local calendar day as the dates displayed in the archive.
export function localDate(value: Date): string {
  return `${String(value.getFullYear()).padStart(4, '0')}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

function validDate(value: string): string {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return ''
  const date = new Date(`${value}T00:00:00`)
  return !Number.isNaN(date.getTime()) && localDate(date) === value ? value : ''
}

export function readFilters(params: URLSearchParams): LibraryFilters {
  const date = params.get('date') ?? ''
  return {
    name: params.get('name') ?? '',
    topic: params.get('topic') ?? '',
    date: dateOptions.some((option) => option.value === date) ? date as DateRange : '',
    from: validDate(params.get('from') ?? ''),
    to: validDate(params.get('to') ?? ''),
  }
}

export function filterLibrary<T extends Topic | Result>(items: T[], filters: LibraryFilters, now = new Date()): T[] {
  let from = filters.date === 'custom' ? filters.from : ''
  let to = filters.date === 'custom' ? filters.to : ''
  if (filters.date && filters.date !== 'custom') {
    const start = new Date(now)
    start.setDate(start.getDate() - (filters.date === '7d' ? 6 : filters.date === '30d' ? 29 : 0))
    from = localDate(start)
    to = localDate(now)
  }
  return items.filter((item) => {
    if (filters.name && item.title !== filters.name) return false
    if (filters.topic && 'topic_id' in item && item.topic_id !== filters.topic) return false
    const day = localDate(new Date(item.created_at))
    return (!from || day >= from) && (!to || day <= to)
  })
}
