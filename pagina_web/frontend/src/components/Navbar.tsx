import { Link, useLocation } from 'react-router-dom'
import { Sun, Moon, Globe2 } from 'lucide-react'
import { useTheme } from '../theme/ThemeContext'

export default function Navbar() {
  const { pathname } = useLocation()
  const { darkMode, toggleDarkMode } = useTheme()

  const links = [
    { to: '/', label: 'Inicio' },
    { to: '/mapa', label: 'Mapa' },
    { to: '/acerca', label: 'Acerca' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md bg-blue-950/30 dark:bg-slate-950/50 border-b border-cyan-400/10">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight bg-gradient-to-r from-cyan-300 to-emerald-300 bg-clip-text text-transparent">
          <Globe2 size={20} className="text-cyan-300" />
          GeoVision-CLIP
        </Link>
        <div className="flex items-center gap-6">
          {links.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm transition-colors ${
                pathname === l.to
                  ? 'text-cyan-300 font-semibold'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              {l.label}
            </Link>
          ))}
          <button
            onClick={toggleDarkMode}
            aria-label={darkMode ? 'Activar modo claro' : 'Activar modo oscuro'}
            className="ml-2 inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 transition-colors text-slate-100"
          >
            {darkMode ? <Sun size={14} /> : <Moon size={14} />}
            {darkMode ? 'Claro' : 'Oscuro'}
          </button>
        </div>
      </div>
    </nav>
  )
}
