import { MapContainer, TileLayer, Rectangle, Popup, ImageOverlay, useMapEvents } from 'react-leaflet'
import { Trees, Building2, Factory, Sun, Car, MapPin } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Estacion, TileClip, Cobertura } from '../types'
import { useTheme } from '../theme/ThemeContext'
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
  cobertura?: Cobertura | null
  cargando?: boolean
  puntoClick?: { lat: number; lon: number } | null
  overlayGradiente?: OverlayInfo | null
  overlayIncertidumbre?: OverlayInfo | null
}

const CLASE_COLOR: Record<number, string> = { 0: '#22c55e', 1: '#eab308', 2: '#ef4444' }

// Basemap que reacciona al modo oscuro (CARTO voyager / dark_all).
function ThemedTileLayer() {
  const { darkMode } = useTheme()
  const url = darkMode
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
  return (
    <TileLayer
      key={darkMode ? 'dark' : 'light'}
      url={url}
      subdomains="abcd"
      maxZoom={20}
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
    />
  )
}

function iconoCobertura(clase: string | null): ReactNode {
  const c = clase || ''
  if (c.includes('vegetacion')) return <Trees size={15} color="#16a34a" />
  if (c.includes('urbano')) return <Building2 size={15} color="#b45309" />
  if (c.includes('SO2')) return <Factory size={15} color="#dc2626" />
  if (c.includes('NO2')) return <Car size={15} color="#dc2626" />
  if (c.includes('ozono')) return <Sun size={15} color="#d97706" />
  return <MapPin size={15} color="#64748b" />
}

function MapaClickHandler({ onClick }: { onClick: (lat: number, lon: number) => void }) {
  useMapEvents({ click: (e) => onClick(e.latlng.lat, e.latlng.lng) })
  return null
}

export default function MapaCali({
  estaciones, tilesClip, contaminanteActivo,
  mostrarEstaciones, mostrarTiles,
  onMapaClick, prediccion, cobertura, cargando, puntoClick,
  overlayGradiente, overlayIncertidumbre,
}: Props) {
  const mostrarPopup = !!puntoClick && !cargando && (!!prediccion || !!cobertura)

  return (
    <MapContainer center={[3.45, -76.53]} zoom={11} className="w-full h-full" zoomControl={true}>
      <ThemedTileLayer />

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

      {mostrarPopup && puntoClick && (
        <Popup position={[puntoClick.lat, puntoClick.lon]}>
          <div className="text-sm" style={{ minWidth: '220px' }}>
            <strong>{(prediccion?.contaminante) || contaminanteActivo} · {(prediccion?.horizonte) || ''}</strong>
            {prediccion?.error ? (
              <p style={{ color: '#b45309', fontSize: '0.78rem', marginTop: 6 }}>{prediccion.error}</p>
            ) : prediccion ? (
              <>
                <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0d9488', margin: '4px 0' }}>
                  {prediccion.valor} <span style={{ fontSize: '0.8rem', color: '#64748b' }}>± {prediccion.sigma} µg/m³</span>
                </div>
                <table style={{ width: '100%', fontSize: '0.78rem' }}>
                  <tbody>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Varianza Kriging</td><td style={{ fontWeight: 600 }}>{prediccion.varianza}</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Celda más cercana</td><td style={{ fontWeight: 600 }}>{prediccion.dist_celda_km} km</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Latencia</td><td style={{ fontWeight: 600 }}>{prediccion.latencia_ms} ms</td></tr>
                  </tbody>
                </table>
              </>
            ) : null}

            {cobertura && cobertura.clase_dominante && (
              <>
                <hr style={{ margin: '8px 0', border: 'none', borderTop: '1px solid #e2e8f0' }} />
                <p style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.04em', color: '#94a3b8', marginBottom: 4 }}>
                  Zona que ve el modelo
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                  {iconoCobertura(cobertura.clase_dominante)}
                  <span>{cobertura.etiqueta}</span>
                </div>
                <table style={{ width: '100%', fontSize: '0.74rem', marginTop: 4 }}>
                  <tbody>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>NDVI (vegetación)</td><td style={{ fontWeight: 600 }}>{cobertura.ndvi ?? '—'}</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>NDBI (urbano)</td><td style={{ fontWeight: 600 }}>{cobertura.ndbi ?? '—'}</td></tr>
                    <tr><td style={{ color: '#64748b', paddingRight: 8 }}>Tiles cercanos</td><td style={{ fontWeight: 600 }}>{cobertura.n_tiles}</td></tr>
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
