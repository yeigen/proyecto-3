export default function Leyenda() {
  return (
    <div className="leaflet-bottom leaflet-left">
      <div className="leaflet-control leaflet-bar bg-white dark:bg-slate-800 p-2 rounded shadow text-xs">
        <p className="font-semibold mb-1">CLIP</p>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: '#22c55e' }} />
          <span>Baja</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: '#eab308' }} />
          <span>Media</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-sm" style={{ background: '#ef4444' }} />
          <span>Alta</span>
        </div>
      </div>
    </div>
  )
}
