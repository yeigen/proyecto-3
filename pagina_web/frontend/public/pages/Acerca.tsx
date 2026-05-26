export default function Acerca() {
  return (
    <div className="pt-20 pb-12 px-4 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-emerald-400">Acerca del proyecto</h1>

      <section id="datos" className="mb-8 p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-semibold mb-4">Datos y fuentes</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300 mb-4">
          El panel integra 6 fuentes satelitales con un total de 89.73 GB en formato Zarr.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-2">Fuente</th>
                <th className="text-left py-2">Resolución</th>
                <th className="text-left py-2">Periodicidad</th>
                <th className="text-left py-2">Peso</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['Sentinel-5P NO₂', '3.5×5.5 km', 'Diaria', '20.4 GB'],
                ['Sentinel-5P SO₂', '3.5×5.5 km', 'Diaria', '8.1 GB'],
                ['Sentinel-5P O₃', '3.5×5.5 km', 'Diaria', '14.8 GB'],
                ['Sentinel-2 MSI', '10/20/60 m', '5 días', '89.67 GB'],
                ['ERA5-Land', '9 km', 'Horaria', '4.7 GB'],
                ['MODIS MCD19A2', '1 km', 'Diaria', '16.0 GB'],
              ].map(([fuente, res, per, peso]) => (
                <tr key={fuente} className="border-b border-slate-100 dark:border-slate-700/50">
                  <td className="py-2">{fuente}</td>
                  <td className="py-2 text-slate-500">{res}</td>
                  <td className="py-2 text-slate-500">{per}</td>
                  <td className="py-2 text-slate-500">{peso}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-400 mt-3">10 estaciones DAGMA monitoreando NO₂, SO₂ y O₃ en Cali</p>
      </section>

      <section id="metodologia" className="mb-8 p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-semibold mb-4">Metodología</h2>
        <div className="space-y-4 text-sm text-slate-600 dark:text-slate-300">
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-100">Situación 1 — Panel espacio-temporal</p>
            <p>Construcción de un panel analítico de 89.73 GB integrando imágenes satelitales, datos meteorológicos y ground truth DAGMA en formato Zarr.</p>
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-100">Situación 2 — GeoVision-CLIP + SAE</p>
            <p>Modelo multimodal basado en CLIP fine-tuned con RemoteCLIP + Sparse Autoencoders. Recall@1: 0.483, Recall@5: 1.000. Validación psicométrica con AFE/AFC.</p>
          </div>
          <div>
            <p className="font-semibold text-slate-800 dark:text-slate-100">Situación 3 — ConvLSTM + ST-Kriging</p>
            <p>Pipeline de predicción espacio-temporal en 3 horizontes (T+1, T+3, T+7) para NO₂, SO₂ y O₃. Validación LOO-CV contra DAGMA + análisis de Moran y LISA.</p>
          </div>
        </div>
      </section>

      <section className="p-6 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-semibold mb-4">Indicadores de rendimiento</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Recall@1', value: '0.483' },
            { label: 'Recall@5', value: '1.000' },
            { label: 'Panel', value: '89 GB' },
            { label: 'Estaciones', value: '10' },
          ].map(metric => (
            <div key={metric.label} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-700 text-center">
              <p className="text-2xl font-bold text-emerald-500">{metric.value}</p>
              <p className="text-xs text-slate-500">{metric.label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
