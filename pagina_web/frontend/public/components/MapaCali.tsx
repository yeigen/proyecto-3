import { MapContainer, TileLayer, Rectangle, Popup, ImageOverlay, useMapEvents } from 'react-leaflet'
import type { Estacion, TileClip } from '../types'
import EstacionMarker from './EstacionMarker'
import Leyenda from './Leyenda'

export interface OverlayInfo {
  url: string
  bounds: [[number, number], [number, number]]  // [[lat_min, lon_min], [lat_max, lon_max]]
  opacidad: number
}

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
  overlayGradiente?: OverlayInfo | null
  overlayIncertidumbre?: OverlayInfo | null
}

const CLASE_COLOR: Record<number, string> = { 0: '#22c55e', 1: '#eab308', 2: '#ef4444' }

function MapaClickHandler({ onClick }: { onClick: (lat: number, lon: number) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng.lat, e.latlng.lng) })
  return null
}

export default function MapaCali({
  estaciones, tilesClip, contaminanteActivo,
  mostrarEstaciones, mostrarTiles,
  onMapaClick, prediccion, cargando, puntoClick,
  overlayGradiente, overlayIncertidumbre,
}: Props) {
  return (
    <MapContainer center={[3.45, -76.53]} zoom={11} className="w-full h-full" zoomControl={true}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />

      {onMapaClick && <MapaClickHandler onClick={onMapaClick} />}

      {/* Mapa de gradiente (predicción) como overlay georreferenciado */}
      {overlayGradiente && (
        <ImageOverlay url={overlayGradiente.url} bounds={overlayGradiente.bounds} opacity={overlayGradiente.opacidad} />
      )}
      {/* Capa de incertidumbre (σ) superpuesta */}
      {overlayIncertidumbre && (
        <ImageOverlay url={overlayIncertidumbre.url} bounds={overlayIncertidumbre.bounds} opacity={overlayIncertidumbre.opacidad} />
      )}

      {mostrarTiles && tilesClip.map(t => (
        <Rectangle
          key={t.tile_id}
          bounds={[[t.lat - 0.0018, t.lon - 0.0018], [t.lat + 0.0018, t.lon + 0.0018]]}
          pathOptions={{ color: CLASE_COLOR[t.clase], fillOpacity: (t.score || 0.4) * 0.4, weight: 1 }}
        />
      ))}

      {mostrarEstaciones && estaciones.map(e => (
        <EstacionMarker key={e.id} estacion={e} contaminanteActivo={contaminanteActivo} />
      ))}

      {prediccion && puntoClick && (
        <Popup position={[puntoClick.lat, puntoClick.lon]}>
          <div className="text-sm" style={{ minWidth: '210px' }}>
            <strong>{prediccion.contaminante} · {prediccion.horizonte}</strong>
            {prediccion.error ? (
              <p style={{ color: '#b45309', fontSize: '0.78rem', marginTop: 6 }}>{prediccion.error}</p>
            ) : (
              <>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0d9488', margin: '4px 0' }}>
                  {prediccion.valor} <span style={{ fontSize: '0.8rem', color: '#64748b' }}>± {prediccion.sigma} µg/m³</span>
                </div>
                <hr style={{ margin: '6px 0', border: 'none', borderTop: '1px solid #e2e8f0' }} />
                <table style={{ width: '100%', fontSize: '0.78rem' }}>
                  <tbody>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Varianza Kriging</td><td style={{ fontWeight: 600 }}>{prediccion.varianza}</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Celda más cercana</td><td style={{ fontWeight: 600 }}>{prediccion.dist_celda_km} km</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Latencia</td><td style={{ fontWeight: 600 }}>{prediccion.latencia_ms} ms</td></tr>
                  </tbody>
                </table>
              </>
            )}
          </div>
        </Popup>
      )}

      {cargando && puntoClick && (
        <Popup position={[puntoClick.lat, puntoClick.lon]}>
          <div style={{ textAlign: 'center', padding: '8px' }}>Procesando...</div>
        </Popup>
      )}

      <Leyenda />
    </MapContainer>
  )
}
