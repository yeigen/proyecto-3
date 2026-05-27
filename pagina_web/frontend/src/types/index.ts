export interface Estacion {
  id: string
  nombre: string
  lat: number
  lon: number
  altitud: number
  contaminantes: string[]
  no2_avg?: number
  so2_avg?: number
  o3_avg?: number
}

export interface TileClip {
  tile_id: string
  lat: number
  lon: number
  clase: 0 | 1 | 2
  score: number
  fecha: string
}

export interface Stats {
  promedios: { NO2: number; SO2: number; O3: number }
  cobertura: Record<string, number>
}

export interface FuenteInfo {
  id: string
  nombre: string
  periodo: string
  peso_gb: number
}

export interface PrediccionPunto {
  lat: number
  lon: number
  horizonte: string
  contaminante: string
  valor: number
  varianza: number
  latencia_ms: number
}

export interface CeldaGrid {
  lat: number
  lon: number
  valor: number
  varianza: number
}

export interface Cobertura {
  lat: number
  lon: number
  radio_km: number
  n_tiles: number
  clase_dominante: string | null
  etiqueta: string
  descripcion: string
  ndvi: number | null
  ndbi: number | null
  clases: Record<string, number>
}
