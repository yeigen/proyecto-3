import type { FuenteInfo } from '../types'
import { GASES_CON_MAPA } from '../data/constantes'

interface Props {
  contaminanteActivo: string
  fuenteActiva: string
  horizonteActivo: string
  mostrarEstaciones: boolean
  mostrarTiles: boolean
  mostrarGradiente: boolean
  mostrarIncertidumbre: boolean
  fuentes: FuenteInfo[]
  onChangeContaminante: (v: string) => void
  onChangeHorizonte: (v: string) => void
  onChangeFuente: (v: string) => void
  onChangeEstaciones: (v: boolean) => void
  onChangeTiles: (v: boolean) => void
  onChangeGradiente: (v: boolean) => void
  onChangeIncertidumbre: (v: boolean) => void
  onDescargarCSV?: () => void
}

export default function ControlPanel({
  contaminanteActivo, fuenteActiva, horizonteActivo,
  mostrarEstaciones, mostrarTiles, mostrarGradiente, mostrarIncertidumbre, fuentes,
  onChangeContaminante, onChangeHorizonte, onChangeFuente,
  onChangeEstaciones, onChangeTiles, onChangeGradiente, onChangeIncertidumbre,
  onDescargarCSV,
}: Props) {
  const gasTieneMapa = GASES_CON_MAPA.includes(contaminanteActivo)

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
        {!gasTieneMapa && (
          <p className="text-[11px] text-amber-600 dark:text-amber-400 mt-1.5 leading-tight">
            NO₂ sin mapa de Kriging: solo 2 estaciones DAGMA lo miden (n&lt;3 para variograma).
          </p>
        )}
      </div>

      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">Horizonte temporal</p>
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
        <label className={`flex items-center gap-2 py-1 ${gasTieneMapa ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}>
          <input type="checkbox" checked={mostrarGradiente && gasTieneMapa} disabled={!gasTieneMapa} onChange={e => onChangeGradiente(e.target.checked)} className="accent-emerald-500" />
          <span>Mapa de gradiente</span>
        </label>
        <label className={`flex items-center gap-2 py-1 ${gasTieneMapa ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}>
          <input type="checkbox" checked={mostrarIncertidumbre && gasTieneMapa} disabled={!gasTieneMapa} onChange={e => onChangeIncertidumbre(e.target.checked)} className="accent-emerald-500" />
          <span>Incertidumbre (σ)</span>
        </label>
      </div>

      {onDescargarCSV && gasTieneMapa && (
        <button
          onClick={onDescargarCSV}
          className="w-full px-3 py-2 rounded text-xs font-medium bg-slate-700 text-white hover:bg-slate-600 transition-colors"
        >
          Descargar predicción CSV
        </button>
      )}

      <div className="mt-auto pt-2 border-t border-slate-200 dark:border-slate-700">
        <p className="text-[11px] text-slate-400 text-center py-1 leading-tight">
          Predicciones ConvLSTM + ST-Kriging<br />sobre malla pre-computada
        </p>
      </div>
    </div>
  )
}
