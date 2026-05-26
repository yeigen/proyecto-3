import type { Stats } from '../types'

interface Props {
  stats: Stats
  contaminanteActivo: string
}

export default function StatsPanel({ stats, contaminanteActivo }: Props) {
  return (
    <div className="w-64 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 p-4 overflow-y-auto flex flex-col gap-4 text-sm">
      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">
          Promedios
        </p>
        {(['NO2', 'SO2', 'O3'] as const).map(c => (
          <div
            key={c}
            className={`flex justify-between py-1 ${contaminanteActivo === c ? 'font-bold' : ''}`}
          >
            <span>{c === 'NO2' ? 'NO₂' : c === 'SO2' ? 'SO₂' : 'O₃'}</span>
            <span>{stats.promedios[c]} µg/m³</span>
          </div>
        ))}
      </div>

      <div>
        <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">
          Cobertura anual
        </p>
        {Object.keys(stats.cobertura).length === 0 ? (
          <p className="text-xs text-slate-400 py-2">Cargando...</p>
        ) : (
          Object.entries(stats.cobertura).map(([anio, total]) => {
            const maxTotal = Math.max(...Object.values(stats.cobertura))
            const pct = (total / maxTotal) * 100
            return (
              <div key={anio} className="flex items-center gap-2 py-0.5">
                <span className="w-10 text-xs">{anio}</span>
                <div className="flex-1 h-2.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-xs w-8 text-right">{total.toLocaleString()}</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
