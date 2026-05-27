import { Link } from 'react-router-dom'
import { Map as MapIcon, BarChart3, FlaskConical } from 'lucide-react'
import Clouds from '../components/Clouds'

export default function Inicio() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-950 via-slate-900 to-emerald-950 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.16)_0%,transparent_70%)]" />
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl" />
      <Clouds className="opacity-70" />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 text-center">
        <h1 className="text-6xl md:text-7xl font-bold mb-4 bg-gradient-to-r from-cyan-300 via-sky-300 to-emerald-300 bg-clip-text text-transparent">
          GeoVision-CLIP
        </h1>
        <p className="text-lg md:text-xl text-slate-300 max-w-2xl mb-8">
          Estimación de contaminación atmosférica en puntos no muestreados
          mediante Deep Learning + Estadística Geoespacial Avanzada
        </p>

        <Link
          to="/mapa"
          className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-600 hover:to-emerald-600 text-white font-semibold rounded-lg transition-colors shadow-lg shadow-cyan-500/25"
        >
          Ir al mapa interactivo
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-16 max-w-3xl w-full">
          <Link to="/mapa" className="p-4 rounded-lg bg-white/5 backdrop-blur border border-cyan-400/10 hover:bg-white/10 transition-colors text-left">
            <p className="flex items-center gap-2 font-semibold text-cyan-300 mb-1"><MapIcon size={18} /> Mapa interactivo</p>
            <p className="text-xs text-slate-400">Visualiza predicciones y estaciones en tiempo real</p>
          </Link>
          <Link to="/acerca#datos" className="p-4 rounded-lg bg-white/5 backdrop-blur border border-cyan-400/10 hover:bg-white/10 transition-colors text-left">
            <p className="flex items-center gap-2 font-semibold text-emerald-300 mb-1"><BarChart3 size={18} /> Datos y fuentes</p>
            <p className="text-xs text-slate-400">Satélites, estaciones DAGMA y más de 89 GB de datos</p>
          </Link>
          <Link to="/acerca#metodologia" className="p-4 rounded-lg bg-white/5 backdrop-blur border border-cyan-400/10 hover:bg-white/10 transition-colors text-left">
            <p className="flex items-center gap-2 font-semibold text-sky-300 mb-1"><FlaskConical size={18} /> Metodología</p>
            <p className="text-xs text-slate-400">CLIP, ConvLSTM, ST-Kriging y equidad espacial</p>
          </Link>
        </div>
      </div>

      <footer className="absolute bottom-4 left-0 right-0 text-center text-xs text-slate-500">
        Universidad Autónoma de Occidente · Analítica de Datos I · 2026
      </footer>
    </div>
  )
}
