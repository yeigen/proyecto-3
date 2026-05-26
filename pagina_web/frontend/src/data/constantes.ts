import type { FuenteInfo } from '../types'

export const CONTAMINANTES = ['NO2', 'SO2', 'O3']
export const HORIZONTES = ['T+1', 'T+3', 'T+7']

// Gases con mapa de Kriging (NO2 excluido: solo 2 estaciones DAGMA)
export const GASES_CON_MAPA = ['SO2', 'O3']

export const fuentes: FuenteInfo[] = [
  { id: 's5p_no2', nombre: 'Sentinel-5P NO₂', periodo: '2021-2026', peso_gb: 0.09 },
  { id: 's5p_so2', nombre: 'Sentinel-5P SO₂', periodo: '2021-2026', peso_gb: 0.04 },
  { id: 's5p_o3', nombre: 'Sentinel-5P O₃', periodo: '2021-2026', peso_gb: 0.07 },
  { id: 's2', nombre: 'Sentinel-2 MSI', periodo: '2021-2026', peso_gb: 97.61 },
  { id: 'era5', nombre: 'ERA5 hourly', periodo: '2021-2026', peso_gb: 0.11 },
  { id: 'modis', nombre: 'MODIS MAIAC AOD', periodo: '2021-2026', peso_gb: 0.18 },
]
