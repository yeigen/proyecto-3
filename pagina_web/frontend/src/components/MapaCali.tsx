import { MapContainer, TileLayer, Rectangle, Popup, useMapEvents } from 'react-leaflet'
import type { Estacion, TileClip } from '../types'
import EstacionMarker from './EstacionMarker'
import Leyenda from './Leyenda'

interface Props {
  estaciones: Estacion[]
  tilesClip: TileClip[]
  contaminanteActivo: string
  mostrarEstaciones: boolean
  mostrarTiles: boolean
  onMapaClick?: (lat: number, lon: number) => void
  prediccion?: any
  cargando?: boolean
  puntoClick?: { lat: number; lon: number } | null
}

const CLASE_COLOR: Record<number, string> = { 0: '#22c55e', 1: '#eab308', 2: '#ef4444' }

function MapaClickHandler({ onClick }: { onClick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (e) => onClick(e.latlng.lat, e.latlng.lng),
  })
  return null
}

function getClaseColor(clase: string): string {
  if (clase.includes('NO2') || clase.includes('SO2') || clase.includes('ozono')) return '#ef4444'
  if (clase.includes('vegetacion')) return '#22c55e'
  return '#eab308'
}

export default function MapaCali({
  estaciones, tilesClip, contaminanteActivo,
  mostrarEstaciones, mostrarTiles,
  onMapaClick, prediccion, cargando, puntoClick,
}: Props) {
  return (
    <MapContainer
      center={[3.45, -76.53]}
      zoom={11}
      className="w-full h-full"
      zoomControl={true}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />

      {onMapaClick && <MapaClickHandler onClick={onMapaClick} />}

      {mostrarEstaciones && estaciones.map(e => (
        <EstacionMarker key={e.id} estacion={e} contaminanteActivo={contaminanteActivo} />
      ))}

      {mostrarTiles && tilesClip.map(t => (
        <Rectangle
          key={t.tile_id}
          bounds={[[t.lat - 0.0018, t.lon - 0.0018], [t.lat + 0.0018, t.lon + 0.0018]]}
          pathOptions={{
            color: CLASE_COLOR[t.clase],
            fillOpacity: t.score * 0.4,
            weight: 1,
          }}
        />
      ))}

      {prediccion && puntoClick && (
        <Popup position={[puntoClick.lat, puntoClick.lon]}>
          <div className="text-sm" style={{ minWidth: '200px' }}>
            <div
              className="w-3 h-3 rounded-full inline-block mr-1"
              style={{ background: getClaseColor(prediccion.clase) }}
            />
            <strong>{prediccion.clase}</strong>
            <p className="text-slate-500 text-xs mt-1 mb-2" style={{ color: '#64748b' }}>
              {prediccion.clase_descripcion}
            </p>
            <hr style={{ margin: '6px 0', border: 'none', borderTop: '1px solid #e2e8f0' }} />
            <table style={{ width: '100%', fontSize: '0.8rem' }}>
              <tbody>
                <tr><td style={{ color: '#64748b', paddingRight: 8 }}>NDVI</td><td style={{ fontWeight: 600 }}>{prediccion.ndvi}</td></tr>
                <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Tile ID</td><td style={{ fontWeight: 600 }}>{prediccion.tile_id}</td></tr>
                <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Coords tile</td><td style={{ fontWeight: 600 }}>{prediccion.tile_lat}, {prediccion.tile_lon}</td></tr>
                <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Latencia</td><td style={{ fontWeight: 600 }}>{prediccion.latencia_ms} ms</td></tr>
              </tbody>
            </table>
          </div>
        </Popup>
      )}

      {cargando && puntoClick && (
        <Popup position={[puntoClick.lat, puntoClick.lon]}>
          <div className="text-sm" style={{ textAlign: 'center', padding: '8px' }}>
            <p>Procesando...</p>
          </div>
        </Popup>
      )}

      <Leyenda />
    </MapContainer>
  )
}
