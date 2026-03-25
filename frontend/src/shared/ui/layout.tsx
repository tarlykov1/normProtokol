import { Link, NavLink, Outlet } from 'react-router-dom'
import { FormEvent, useState } from 'react'
import { PageContainer } from './states'

const tabs = [
  { to: '/', label: 'Загрузка' },
  { to: '/normalize', label: 'Нормализация' },
  { to: '/topics', label: 'Темы' },
  { to: '/confirm', label: 'Подтверждение' }
]

export function AppLayout() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isUnlocked, setIsUnlocked] = useState(() => sessionStorage.getItem('normprotokol-gate') === 'ok')

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (password === '2156') {
      sessionStorage.setItem('normprotokol-gate', 'ok')
      setIsUnlocked(true)
      setError('')
      return
    }
    setError('Неверный пароль')
  }

  if (!isUnlocked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-3 rounded border bg-white p-4">
          <h1 className="text-lg font-semibold">Вход</h1>
          <p className="text-xs text-slate-500">Простая защита от случайного доступа (не полноценная авторизация).</p>
          <input type="password" className="w-full rounded border p-2" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Введите пароль" />
          {error && <p className="text-xs text-red-600">{error}</p>}
          <button type="submit" className="w-full rounded bg-slate-900 p-2 text-white">Открыть приложение</button>
        </form>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b bg-white">
        <PageContainer>
          <div className="flex flex-col gap-3 py-1 md:flex-row md:items-center md:justify-between">
            <Link to="/" className="text-lg font-semibold">Нормализатор протоколов</Link>
            <nav className="flex flex-wrap gap-2 text-sm">
              {tabs.map((t) => <NavLink key={t.to} to={t.to} className={({ isActive }) => `rounded px-3 py-1 ${isActive ? 'bg-slate-900 text-white' : 'bg-slate-200'}`}>{t.label}</NavLink>)}
            </nav>
          </div>
        </PageContainer>
      </header>
      <PageContainer><Outlet /></PageContainer>
    </div>
  )
}
