import { useState, useEffect } from 'react'
import MapaCali, { type OverlayInfo } from '../components/MapaCali'
import ControlPanel from '../components/ControlPanel'
import StatsPanel from '../components/StatsPanel'
import { fuentes, CONTAMINANTES, HORIZONTES, GASES_CON_MAPA } from '../data/constantes'
import type { Estacion, Stats, TileClip } from '../types'

const API = '/api'

export default function Mapa() {
  const [contaminanteActivo, setContaminanteActivo] = useState<string>('SO2')
  const [horizonteActivo, setHorizonteActivo] = useState<string>(HORIZONTES[0])
  const [fuenteActiva, setFuenteActiva] = useState<string>(fuentes[0].id)
  const [mostrarEstaciones, setMostrarEstaciones] = useState(true)
  const [mostrarTiles, setMostrarTiles] = useState(false)
  const [mostrarGradiente, setMostrarGradiente] = useState(true)
  const [mostrarIncertidumbre, setMostrarIncertidumbre] = useState(false)

  const [estaciones, setEstaciones] = useState<Estacion[]>([])
  const [tilesClip, setTilesClip] = useState<TileClip[]>([])
  const [stats, setStats] = useState<Stats | null>(null)

  const [prediccion, setPrediccion] = useState<any>(null)
  const [cargando, setCargando] = useState(false)
  const [puntoClick, setPuntoClick] = useState<{ lat: number; lon: number } | null>(null)

  const [boundsMapa, setBoundsMapa] = useState<[[number, number], [number, number]] | null>(null)

  useEffect(() => {
    fetch(`${API}/estaciones`)
      .then(r => r.json())
      .then(geo => {
        const apiEstaciones: Estacion[] = (geo?.features || []).map((f: any) => ({
          id: String(f.properties.id),
          nombre: f.properties.nombre,
          lat: f.geometry.coordinates[1],
          lon: f.geometry.coordinates[0],
          altitud: f.properties.altitud,
          contaminantes: f.properties.contaminantes || [],
        }))
        setEstaciones(apiEstaciones)
      })
      .catch(() => console.warn('API no disponible'))

    fetch(`${API}/estaciones/promedios`)
      .then(r => r.json())
      .then(promData => {
        if (!promData || Object.keys(promData).length === 0) return
        setEstaciones(prev => prev.map(e => {
          const p = promData[e.id]
          if (!p) return e
          return { ...e, no2_avg: p.NO2, so2_avg: p.SO2, o3_avg: p.O3 }
        }))
        const prom = (gas: string) => {
          const vals = Object.values(promData).map((p: any) => p[gas]).filter((v: any) => v != null)
          return vals.length ? +(vals.reduce((a: number, b: number) => a + b, 0) / vals.length).toFixed(2) : 0
        }
        setStats(s => ({ promedios: { NO2: prom('NO2'), SO2: prom('SO2'), O3: prom('O3') }, cobertura: s?.cobertura || {} }))
      })
      .catch(() => {})

    fetch(`${API}/estaciones/cobertura`)
      .then(r => r.json())
      .then(cov => { if (cov && Object.keys(cov).length) setStats(prev => prev ? { ...prev, cobertura: cov } : { promedios: { NO2: 0, SO2: 0, O3: 0 }, cobertura: cov }) })
      .catch(() => {})

    fetch(`${API}/tiles-clip?limite=1500`)
      .then(r => r.json())
      .then(geo => {
        if (geo?.features?.length > 0) {
          setTilesClip(geo.features.map((f: any, i: number) => ({
            tile_id: String(i),
            lat: f.geometry.coordinates[1],
            lon: f.geometry.coordinates[0],
            clase: (f.properties.clase?.includes('vegetacion') ? 0 : f.properties.clase?.includes('urbano') ? 1 : 2) as 0 | 1 | 2,
            score: 0.5,
            fecha: '2021-2024',
          })))
        }
      })
      .catch(() => {})
  }, [])

  // Cargar bounds del overlay al cambiar gas/horizonte
  useEffect(() => {
    if (!GASES_CON_MAPA.includes(contaminanteActivo)) { setBoundsMapa(null); return }
    fetch(`${API}/grids/bounds/${contaminanteActivo}/${encodeURIComponent(horizonteActivo)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.bounds) {
          const [latMin, lonMin, latMax, lonMax] = d.bounds
          setBoundsMapa([[latMin, lonMin], [latMax, lonMax]])
        }
      })
      .catch(() => setBoundsMapa(null))
  }, [contaminanteActivo, horizonteActivo])

  const handleMapaClick = async (lat: number, lon: number) => {
    setPuntoClick({ lat, lon })
    if (!GASES_CON_MAPA.includes(contaminanteActivo)) {
      setPrediccion({ contaminante: contaminanteActivo, horizonte: horizonteActivo,
        error: 'NO₂ no tiene mapa de predicción (solo 2 estaciones DAGMA).' })
      return
    }
    setCargando(true); setPrediccion(null)
    try {
      const res = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lon, contaminante: contaminanteActivo, horizonte: horizonteActivo }),
      })
      setPrediccion(await res.json())
    } catch (e) { console.error('Error en prediccion:', e) }
    setCargando(false)
  }

  const handleDescargarCSV = async () => {
    const res = await fetch(`${API}/predict/grid?contaminante=${contaminanteActivo}&horizonte=${encodeURIComponent(horizonteActivo)}`)
    const d = await res.json()
    if (!d?.celdas) return
    const filas = ['lat,lon,valor,varianza', ...d.celdas.map((c: any) => `${c.lat},${c.lon},${c.valor},${c.varianza}`)]
    const blob = new Blob([filas.join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `prediccion_${contaminanteActivo}_${horizonteActivo}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const overlayGradiente: OverlayInfo | null = (mostrarGradiente && boundsMapa && GASES_CON_MAPA.includes(contaminanteActivo))
    ? { url: `${API}/grids/${contaminanteActivo}/${encodeURIComponent(horizonteActivo)}/pred`, bounds: boundsMapa, opacidad: 0.6 }
    : null
  const overlayIncertidumbre: OverlayInfo | null = (mostrarIncertidumbre && boundsMapa && GASES_CON_MAPA.includes(contaminanteActivo))
    ? { url: `${API}/grids/${contaminanteActivo}/${encodeURIComponent(horizonteActivo)}/sigma`, bounds: boundsMapa, opacidad: 0.45 }
    : null

  return (
    <div className="pt-14 flex h-[calc(100vh-3.5rem)]">
      <ControlPanel
        contaminanteActivo={contaminanteActivo}
        fuenteActiva={fuenteActiva}
        horizonteActivo={horizonteActivo}
        mostrarEstaciones={mostrarEstaciones}
        mostrarTiles={mostrarTiles}
        mostrarGradiente={mostrarGradiente}
        mostrarIncertidumbre={mostrarIncertidumbre}
        fuentes={fuentes}
        onChangeContaminante={setContaminanteActivo}
        onChangeHorizonte={setHorizonteActivo}
        onChangeFuente={setFuenteActiva}
        onChangeEstaciones={setMostrarEstaciones}
        onChangeTiles={setMostrarTiles}
        onChangeGradiente={setMostrarGradiente}
        onChangeIncertidumbre={setMostrarIncertidumbre}
        onDescargarCSV={handleDescargarCSV}
      />

      <main className="flex-1 relative">
        <MapaCali
          estaciones={estaciones}
          tilesClip={tilesClip}
          contaminanteActivo={contaminanteActivo}
          mostrarEstaciones={mostrarEstaciones}
          mostrarTiles={mostrarTiles}
          onMapaClick={handleMapaClick}
          prediccion={prediccion}
          cargando={cargando}
          puntoClick={puntoClick}
          overlayGradiente={overlayGradiente}
          overlayIncertidumbre={overlayIncertidumbre}
        />
      </main>

      {stats && <StatsPanel stats={stats} contaminanteActivo={contaminanteActivo} />}
    </div>
  )
}
