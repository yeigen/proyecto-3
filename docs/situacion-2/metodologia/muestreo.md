# Muestreo estratificado

## Qué contiene

Método para generar 5,000 pares imagen-texto balanceados desde el panel satelital.

## Diseño

| Clase | Técnica | Guía |
|---|---|---|
| `contaminacion_alta_NO2` | Muestreo guiado por percentil | S5P NO2 > p90 |
| `contaminacion_alta_SO2` | Muestreo guiado por percentil | S5P SO2 > p90 |
| `ozono_anomalo` | Muestreo guiado por percentil | S5P O3 > p95 |
| `vegetacion_densa` | Aleatorio + filtro NDVI | NDVI > 0.6 |
| `suelo_urbano` | Proximidad a estaciones | DAGMA + NDVI < 0.3 |

## Decisiones clave

- 1,000 tiles por clase.
- Tile de 64×64×13.
- Filtro SCL mínimo de 0.3.
- Escenas Sentinel-2 prefiltradas por SCL para mejorar aceptación.
- O3 se relajó de p99 a p95 por su naturaleza episódica.

## Evidencias relacionadas

- [Mapa de tiles](../evidencias/muestreo/tiles/mapa_tiles_estaciones.png)
- [Separación de clases](../evidencias/muestreo/tiles/separacion-clases.png)
- [Diversidad temporal](../evidencias/muestreo/tiles/tiles_diversidad_temporal.png)

## Referencias

- [Muestreo Sit 2 original](../MUESTREO_SIT2.md)
- [Tiles Sentinel-2](../capas/tiles-sentinel-2.md)
- [Pseudo-labels S5P](../capas/pseudo-labels-s5p.md)
- [NDVI original Rouse et al.](https://ntrs.nasa.gov/citations/19740022614)
