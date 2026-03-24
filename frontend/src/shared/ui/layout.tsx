import { Link, NavLink, Outlet } from 'react-router-dom'
import { PageContainer } from './states'

const tabs = [
  { to: '/', label: 'Загрузка' },
  { to: '/normalize', label: 'Нормализация' },
  { to: '/topics', label: 'Темы' },
  { to: '/confirm', label: 'Подтверждение' }
]

export function AppLayout() {
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
