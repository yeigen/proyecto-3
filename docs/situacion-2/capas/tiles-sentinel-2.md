# Tiles Sentinel-2

## Qué contiene

Tiles de 64×64 píxeles extraídos desde escenas Sentinel-2 del panel. Cada tile cubre aproximadamente 640×640 m a resolución de 10 m.

## Dataset

| Archivo | Forma | Peso |
|---|---:|---:|
| `tiles_train.npz` | `(5000, 13, 64, 64)` float32 | 229 MB |
| `tiles_meta.parquet` | 5,000 filas × 22 columnas | 0.3 MB |
| `scl_por_escena.csv` | 1,552 filas × 3 columnas | 0.1 MB |

## Clases

- `contaminacion_alta_NO2`
- `contaminacion_alta_SO2`
- `ozono_anomalo`
- `vegetacion_densa`
- `suelo_urbano`

Cada clase tiene 1,000 tiles.

## Evidencias relacionadas

- [Mapa de tiles y estaciones](../evidencias/muestreo/tiles/mapa_tiles_estaciones.png)
- [Separación NDVI/NDBI](../evidencias/muestreo/tiles/separacion-clases.png)
- [Diversidad temporal](../evidencias/muestreo/tiles/tiles_diversidad_temporal.png)
- [Ejemplos por clase](../evidencias/muestreo/tiles/tiles_ejemplos_por_clase.png)

## Referencias

- [Muestreo estratificado](../metodologia/muestreo.md)
- [Muestreo Sit 2 original](../MUESTREO_SIT2.md)
- [Sentinel-2 en Situación 1](../../situacion-1/fuentes/sentinel-2.md)
