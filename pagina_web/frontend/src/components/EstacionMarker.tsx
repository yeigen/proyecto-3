import { CircleMarker, Popup } from 'react-leaflet'
import type { Estacion } from '../types'

interface Props {
  estacion: Estacion
  contaminanteActivo: string
}

function getValor(estacion: Estacion, contaminante: string): number | null {
  if (contaminante === 'NO2') return estacion.no2_avg ?? null
  if (contaminante === 'SO2') return estacion.so2_avg ?? null
  if (contaminante === 'O3') return estacion.o3_avg ?? null
  return null
}

const UMBRALES: Record<string, [number, number, number]> = {
  NO2: [10, 20, 40],
  SO2: [5, 10, 20],
  O3: [30, 50, 80],
}

function getColor(contaminante: string, valor: number | null): string {
  if (valor === null) return '#6b7280'
  const [bajo, medio, alto] = UMBRALES[contaminante] || [10, 20, 40]
  if (valor < bajo) return '#22c55e'
  if (valor < medio) return '#eab308'
  if (valor < alto) return '#f97316'
  return '#ef4444'
}

export default function EstacionMarker({ estacion, contaminanteActivo }: Props) {
  const valor = getValor(estacion, contaminanteActivo)
  const color = getColor(contaminanteActivo, valor)

  return (
    <CircleMarker
      center={[estacion.lat, estacion.lon]}
      radius={8}
      pathOptions={{ color: '#fff', fillColor: color, fillOpacity: 0.8, weight: 2 }}
    >
      <Popup>
        <div className="text-sm">
          <p className="font-bold text-base">{estacion.nombre}</p>
          <p className="text-slate-500">{estacion.lat}°N, {Math.abs(estacion.lon)}°W</p>
          <p className="text-slate-500">Altitud: {estacion.altitud} m</p>
          <hr className="my-1" />
          {estacion.no2_avg !== undefined && (
            <p className={contaminanteActivo === 'NO2' ? 'font-bold text-rose-600' : ''}>
              NO₂: {estacion.no2_avg} µg/m³
            </p>
          )}
          {estacion.so2_avg !== undefined && (
            <p className={contaminanteActivo === 'SO2' ? 'font-bold text-amber-600' : ''}>
              SO₂: {estacion.so2_avg} µg/m³
            </p>
          )}
          {estacion.o3_avg !== undefined && (
            <p className={contaminanteActivo === 'O3' ? 'font-bold text-purple-600' : ''}>
              O₃: {estacion.o3_avg} µg/m³
            </p>
          )}
        </div>
      </Popup>
    </CircleMarker>
  )
}
