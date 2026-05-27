import { Trees, Building2, Factory, Sun, Car, type LucideIcon } from 'lucide-react'
import type { Stats } from '../types'

interface Props {
  stats: Stats
  contaminanteActivo: string
  coberturaGlobal?: Record<string, number>
}

const COBERTURA_META: Record<string, { label: string; color: string; icon: LucideIcon }> = {
  vegetacion_densa: { label: 'Vegetación densa', color: '#16a34a', icon: Trees },
  suelo_urbano: { label: 'Suelo urbano', color: '#b45309', icon: Building2 },
  contaminacion_alta_NO2: { label: 'Contaminación NO₂', color: '#dc2626', icon: Car },
  contaminacion_alta_SO2: { label: 'Contaminación SO₂', color: '#b91c1c', icon: Factory },
  ozono_anomalo: { label: 'Ozono anómalo', color: '#d97706', icon: Sun },
}

export default function StatsPanel({ stats, contaminanteActivo, coberturaGlobal = {} }: Props) {
  const totalCob = Object.values(coberturaGlobal).reduce((a, b) => a + b, 0)

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

      {totalCob > 0 && (
        <div>
          <p className="font-semibold text-xs uppercase tracking-wider text-slate-500 mb-2">
            Cobertura del territorio
          </p>
          <p className="text-[0.68rem] text-slate-400 mb-2 -mt-1">Qué ve el modelo en los {totalCob.toLocaleString()} tiles</p>
          {Object.entries(coberturaGlobal)
            .sort((a, b) => b[1] - a[1])
            .map(([clase, n]) => {
              const meta = COBERTURA_META[clase] || { label: clase, color: '#64748b', icon: Trees }
              const Icon = meta.icon
              const pct = (n / totalCob) * 100
              return (
                <div key={clase} className="py-1">
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className="flex items-center gap-1.5">
                      <Icon size={13} color={meta.color} />
                      {meta.label}
                    </span>
                    <span className="text-slate-500">{pct.toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: meta.color }} />
                  </div>
                </div>
              )
            })}
        </div>
      )}

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
