import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

interface ThemeCtx {
  darkMode: boolean
  toggleDarkMode: () => void
}

const ThemeContext = createContext<ThemeCtx>({ darkMode: false, toggleDarkMode: () => {} })

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('darkMode')
    return saved ? JSON.parse(saved) : false
  })

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode))
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  const toggleDarkMode = () => setDarkMode(prev => !prev)

  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
      {children}
    </ThemeContext.Provider>
  )
}

// Hook de acceso al tema (modo oscuro) desde cualquier componente.
export function useTheme() {
  return useContext(ThemeContext)
}
