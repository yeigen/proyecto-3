import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './theme/ThemeContext'
import Navbar from './components/Navbar'
import Inicio from './pages/Inicio'
import Mapa from './pages/Mapa'
import Acerca from './pages/Acerca'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/mapa" element={<Mapa />} />
          <Route path="/acerca" element={<Acerca />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
