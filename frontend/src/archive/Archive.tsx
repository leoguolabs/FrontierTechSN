import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { archiveApi, requestJson, sessionExpired } from './api'
import { Library } from './Library'

function Brand() {
  return <span className="archive-brand"><span className="brand-stamp" aria-hidden="true">FT</span>FrontierTechSN</span>
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const credentials = Object.fromEntries(new FormData(event.currentTarget))
    setBusy(true)
    setError('')
    try {
      await requestJson(`${archiveApi}/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(credentials),
      }, false)
      onLogin()
    } catch (reason) {
      setError((reason as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="signin">
      <div className="signin-cover">
        <Brand />
        <div className="signin-title"><p className="eyebrow">PRODUCTION ARCHIVE</p><h1>影片档案</h1></div>
        <div className="signin-index"><span>01 / 选题与脚本</span><span>02 / 成片与封面</span></div>
      </div>
      <section className="signin-panel" aria-label="登录">
        <form onSubmit={signIn} className="archive-form">
          <p className="eyebrow">PRIVATE WORKSPACE</p>
          <h2>登录工作台</h2>
          <label>用户名<input name="username" autoComplete="username" maxLength={100} required /></label>
          <label>密码<input name="password" type="password" autoComplete="current-password" maxLength={256} required /></label>
          <button className="primary" disabled={busy}>{busy ? '登录中…' : '进入档案库'}</button>
          {error && <p className="archive-error" role="alert">{error}</p>}
        </form>
      </section>
    </main>
  )
}

export default function Archive() {
  const client = useQueryClient()
  const [logoutError, setLogoutError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const session = useQuery({
    queryKey: ['session'],
    queryFn: ({ signal }) => requestJson<{ authenticated: boolean }>(`${archiveApi}/auth/session`, { signal }),
    staleTime: Infinity,
    refetchOnWindowFocus: 'always',
    refetchInterval: 60_000,
  })

  const updateSession = useCallback((authenticated: boolean) => {
    void client.cancelQueries({ queryKey: ['session'] })
    if (!authenticated) client.removeQueries({ queryKey: ['library'] })
    client.setQueryData(['session'], { authenticated })
  }, [client])

  useEffect(() => {
    const expire = () => updateSession(false)
    window.addEventListener(sessionExpired, expire)
    return () => window.removeEventListener(sessionExpired, expire)
  }, [updateSession])

  async function logout() {
    setLoggingOut(true)
    setLogoutError('')
    try {
      await requestJson(`${archiveApi}/auth/logout`, { method: 'POST' })
      updateSession(false)
    } catch (reason) {
      setLogoutError((reason as Error).message)
    } finally {
      setLoggingOut(false)
    }
  }

  if (session.isPending) return <main className="archive-status" role="status">正在连接档案库…</main>
  if (session.isError) return <main className="archive-status"><p role="alert">暂时无法连接档案库。</p><button onClick={() => void session.refetch()}>重试</button></main>
  if (!session.data.authenticated) return <Login onLogin={() => updateSession(true)} />

  return (
    <div className="archive-shell">
      <header className="archive-header">
        <Link to="/topics" aria-label="FrontierTechSN 首页"><Brand /></Link>
        <nav aria-label="档案导航">
          <NavLink to="/topics"><span>01</span> 选题库</NavLink>
          <NavLink to="/results"><span>02</span> 成片库</NavLink>
        </nav>
        <button type="button" className="text-button" onClick={() => void logout()} disabled={loggingOut}>退出登录</button>
      </header>
      {logoutError && <p className="archive-error" role="alert">{logoutError}</p>}
      <Routes>
        <Route path="/topics" element={<Library key="topics" section="topics" />} />
        <Route path="/results" element={<Library key="results" section="results" />} />
        <Route path="*" element={<Navigate to="/topics" replace />} />
      </Routes>
    </div>
  )
}
