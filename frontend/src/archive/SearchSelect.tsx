import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'

type Option = { value: string; label: string; description?: string; keywords?: string }

export function SearchSelect({
  label, value, options, onChange, placeholder = '请选择', searchPlaceholder = '输入关键词筛选…', disabled = false,
}: {
  label: string
  value: string
  options: Option[]
  onChange: (value: string) => void
  placeholder?: string
  searchPlaceholder?: string
  disabled?: boolean
}) {
  const id = useId()
  const root = useRef<HTMLDivElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const search = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeValue, setActiveValue] = useState<string | null>(null)
  const selected = options.find((option) => option.value === value)
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean)
  const filtered = options.filter((option) => {
    const text = `${option.label} ${option.description ?? ''} ${option.keywords ?? ''}`.toLocaleLowerCase()
    return terms.every((term) => text.includes(term))
  })
  const activeIndex = Math.max(0, filtered.findIndex((option) => option.value === activeValue))

  useEffect(() => {
    if (!open) return
    search.current?.focus()
    const outside = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])

  useEffect(() => {
    if (open) document.getElementById(`${id}-option-${activeIndex}`)?.scrollIntoView({ block: 'nearest' })
  }, [activeIndex, id, open])

  function expand() {
    setQuery('')
    setActiveValue(value)
    setOpen(true)
  }

  function choose(next: string) {
    onChange(next)
    setOpen(false)
    trigger.current?.focus()
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.nativeEvent.isComposing) return
    if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
      trigger.current?.focus()
    } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      const next = Math.min(Math.max(activeIndex + (event.key === 'ArrowDown' ? 1 : -1), 0), filtered.length - 1)
      setActiveValue(filtered[next]?.value ?? null)
    } else if (event.key === 'Enter') {
      event.preventDefault()
      if (filtered[activeIndex]) choose(filtered[activeIndex].value)
    }
  }

  return (
    <div className="archive-select" ref={root} onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false)
    }}>
      <label id={`${id}-label`} htmlFor={`${id}-trigger`} className="archive-select-label">{label}</label>
      <button ref={trigger} id={`${id}-trigger`} type="button" className="archive-select-trigger"
        aria-labelledby={`${id}-label ${id}-value`} aria-haspopup="listbox" aria-expanded={open}
        aria-controls={open ? `${id}-list` : undefined} disabled={disabled}
        onClick={() => open ? setOpen(false) : expand()}
        onKeyDown={(event) => {
          if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); expand() }
        }}>
        <span id={`${id}-value`} className={!selected ? 'archive-select-placeholder' : ''}>{selected?.label ?? (value || placeholder)}</span>
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="m4 6 4 4 4-4" /></svg>
      </button>
      {open && <div className="archive-select-popover">
        <div className="archive-select-search">
          <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" /><path d="m13 13 4 4" /></svg>
          <input ref={search} type="text" role="combobox" aria-label={`搜索${label}`} autoComplete="off"
            aria-expanded="true" aria-autocomplete="list" aria-controls={`${id}-list`}
            aria-activedescendant={filtered.length ? `${id}-option-${activeIndex}` : undefined}
            placeholder={searchPlaceholder} value={query} onKeyDown={onKeyDown}
            onChange={(event) => { setQuery(event.target.value); setActiveValue(null) }} />
          {query && <button type="button" aria-label={`清除${label}搜索`} onClick={() => {
            setQuery(''); setActiveValue(value); search.current?.focus()
          }}>×</button>}
        </div>
        <div id={`${id}-list`} role="listbox" aria-labelledby={`${id}-label`} className="archive-select-options">
          {filtered.map((option, index) => <div key={option.value} id={`${id}-option-${index}`} role="option"
            aria-selected={option.value === value} className={`archive-select-option${index === activeIndex ? ' is-active' : ''}`}
            onPointerDown={(event) => event.preventDefault()} onClick={() => choose(option.value)}>
            <span><strong>{option.label}</strong>{option.description && <small>{option.description}</small>}</span>
            {option.value === value && <span className="archive-select-check" aria-hidden="true">✓</span>}
          </div>)}
        </div>
        {filtered.length === 0 && <p className="archive-select-empty" role="status">没有匹配项，试试其他关键词。</p>}
        <div className="archive-select-footer" role="status">{filtered.length} 个选项<span>↑ ↓ 选择 · Enter 确认</span></div>
      </div>}
    </div>
  )
}
