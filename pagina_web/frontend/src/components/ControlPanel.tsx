import type { FuenteInfo } from '../types'

interface Props {
  contaminanteActivo: string
  fuenteActiva: string
  horizonteActivo: string
  mostrarEstaciones: boolean
  mostrarTiles: boolean
  fuentes: FuenteInfo[]
  onChangeContaminante: (v: string) => void
  onChangeHorizonte: (v: string) => void
  onChangeFuente: (v: string) => void
  onChangeEstaciones: (v: boolean) => void
  onChangeTiles: (v: boolean) => void
}

export default function ControlPanel({
  contaminanteActivo, fuenteActiva, horizonteActivo,
  mostrarEstaciones, mostrarTiles, fuentes,
  onChangeContaminante, onChangeHorizonte, onChangeFuente,
  onChangeEstaciones, onChangeTiles,
}: Props) {
  return (
    <div className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 p-4 overflow-y-auto flex flex-col gap-5 text-sm">
      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">Contaminante</p>
        <div className="flex gap-1">
          {['NO2', 'SO2', 'O3'].map(c => (
            <button
              key={c}
              onClick={() => onChangeContaminante(c)}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                contaminanteActivo === c
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              {c === 'NO2' ? 'NO₂' : c === 'SO2' ? 'SO₂' : 'O₃'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">Horizonte</p>
        <div className="flex gap-1">
          {['T+1', 'T+3', 'T+7'].map(h => (
            <button
              key={h}
              onClick={() => onChangeHorizonte(h)}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                horizonteActivo === h
                  ? 'bg-emerald-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              {h}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">Fuente</p>
        <select
          value={fuenteActiva}
          onChange={e => onChangeFuente(e.target.value)}
          className="w-full px-2 py-1.5 rounded text-xs bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600"
        >
          {fuentes.map(f => (
            <option key={f.id} value={f.id}>{f.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">Capas</p>
        <label className="flex items-center gap-2 py-1 cursor-pointer">
          <input type="checkbox" checked={mostrarEstaciones} onChange={e => onChangeEstaciones(e.target.checked)} className="accent-emerald-500" />
          <span>Estaciones DAGMA</span>
        </label>
        <label className="flex items-center gap-2 py-1 cursor-pointer">
          <input type="checkbox" checked={mostrarTiles} onChange={e => onChangeTiles(e.target.checked)} className="accent-emerald-500" />
          <span>Tiles CLIP</span>
        </label>
      </div>

      <div className="mt-auto pt-2 border-t border-slate-200 dark:border-slate-700">
        <p className="text-xs text-slate-400 text-center py-2">
          🚧 Predicciones próximamente
        </p>
      </div>
    </div>
  )
}
