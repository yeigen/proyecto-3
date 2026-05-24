import { Link, useLocation } from 'react-router-dom'

interface NavbarProps {
  darkMode: boolean
  toggleDarkMode: () => void
}

export default function Navbar({ darkMode, toggleDarkMode }: NavbarProps) {
  const { pathname } = useLocation()

  const links = [
    { to: '/', label: 'Inicio' },
    { to: '/mapa', label: 'Mapa' },
    { to: '/acerca', label: 'Acerca' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-black/20 dark:bg-black/40 border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="text-lg font-bold tracking-tight text-emerald-400">
          GeoVision-CLIP
        </Link>
        <div className="flex items-center gap-6">
          {links.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm transition-colors ${
                pathname === l.to
                  ? 'text-emerald-400 font-semibold'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              {l.label}
            </Link>
          ))}
          <button
            onClick={toggleDarkMode}
            className="ml-2 text-xs px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
          >
            {darkMode ? '☀️ Claro' : '🌙 Oscuro'}
          </button>
        </div>
      </div>
    </nav>
  )
}
