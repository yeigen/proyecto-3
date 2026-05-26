import { useState, useEffect } from 'react'
import MapaCali from '../components/MapaCali'
import ControlPanel from '../components/ControlPanel'
import StatsPanel from '../components/StatsPanel'
import { fuentes, CONTAMINANTES, HORIZONTES } from '../data/mock'
import type { Estacion, Stats, TileClip } from '../types'

const API = '/api'

export default function Mapa() {
  const [contaminanteActivo, setContaminanteActivo] = useState<string>(CONTAMINANTES[0])
  const [horizonteActivo, setHorizonteActivo] = useState<string>(HORIZONTES[0])
  const [fuenteActiva, setFuenteActiva] = useState<string>(fuentes[0].id)
  const [mostrarEstaciones, setMostrarEstaciones] = useState(true)
  const [mostrarTiles, setMostrarTiles] = useState(true)

  const [estaciones, setEstaciones] = useState<Estacion[]>([])
  const [tilesClip, setTilesClip] = useState<TileClip[]>([])
  const [stats, setStats] = useState<Stats | null>(null)

  const [prediccion, setPrediccion] = useState<any>(null)
  const [cargando, setCargando] = useState(false)
  const [puntoClick, setPuntoClick] = useState<{ lat: number; lon: number } | null>(null)

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
          contaminantes: [],
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
          return {
            ...e,
            contaminantes: Object.keys(p),
            no2_avg: p.no2,
            so2_avg: p.so2,
            o3_avg: p.o3,
          }
        }))
        const allNo2 = Object.values(promData).map((p: any) => p.no2).filter(Boolean)
        const allSo2 = Object.values(promData).map((p: any) => p.so2).filter(Boolean)
        const allO3 = Object.values(promData).map((p: any) => p.o3).filter(Boolean)
        setStats({
          promedios: {
            NO2: allNo2.length ? +(allNo2.reduce((a: number, b: number) => a + b, 0) / allNo2.length).toFixed(2) : 0,
            SO2: allSo2.length ? +(allSo2.reduce((a: number, b: number) => a + b, 0) / allSo2.length).toFixed(2) : 0,
            O3: allO3.length ? +(allO3.reduce((a: number, b: number) => a + b, 0) / allO3.length).toFixed(2) : 0,
          },
          cobertura: {},
        })
      })
      .catch(() => {})

    fetch(`${API}/estaciones/cobertura`)
      .then(r => r.json())
      .then(cov => {
        if (cov && Object.keys(cov).length > 0) {
          setStats(prev => prev ? { ...prev, cobertura: cov } : null)
        }
      })
      .catch(() => {})

    fetch(`${API}/tiles-clip?limite=2000`)
      .then(r => r.json())
      .then(geo => {
        if (geo?.features?.length > 0) {
          setTilesClip(geo.features.map((f: any) => ({
            tile_id: f.properties.tile_id,
            lat: f.geometry.coordinates[1],
            lon: f.geometry.coordinates[0],
            clase: f.properties.clase as 0 | 1 | 2,
            score: f.properties.score,
            fecha: '2024',
          })))
        }
      })
      .catch(() => {})
  }, [])

  const handleMapaClick = async (lat: number, lon: number) => {
    setPuntoClick({ lat, lon })
    setCargando(true)
    setPrediccion(null)
    try {
      const res = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat,
          lon,
          contaminante: contaminanteActivo,
          horizonte: horizonteActivo,
        }),
      })
      const data = await res.json()
      setPrediccion(data)
    } catch (e) {
      console.error('Error en prediccion:', e)
    }
    setCargando(false)
  }

  return (
    <div className="pt-14 flex h-[calc(100vh-3.5rem)]">
      <ControlPanel
        contaminanteActivo={contaminanteActivo}
        fuenteActiva={fuenteActiva}
        horizonteActivo={horizonteActivo}
        mostrarEstaciones={mostrarEstaciones}
        mostrarTiles={mostrarTiles}
        fuentes={fuentes}
        onChangeContaminante={setContaminanteActivo}
        onChangeHorizonte={setHorizonteActivo}
        onChangeFuente={setFuenteActiva}
        onChangeEstaciones={setMostrarEstaciones}
        onChangeTiles={setMostrarTiles}
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
        />
      </main>

      {stats && (
        <StatsPanel
          stats={stats}
          contaminanteActivo={contaminanteActivo}
        />
      )}
    </div>
  )
}
