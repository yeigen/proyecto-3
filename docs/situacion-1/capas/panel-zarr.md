# Panel Zarr

## Qué contiene

El panel Zarr integra las fuentes satelitales, atmosféricas y terrestres en una estructura analítica reutilizable.

## Uso en la situación 1

La Situación 1 valida que las fuentes queden publicadas y trazables para consumo posterior en Kaggle y notebooks.

| Fuente | Shape Zarr | Periodo | Rol |
|---|---:|---|---|
| Sentinel-2 MSI L2A | `(1552, 13, 3897, 3897)` | 2021-2025 | Imagen óptica |
| Sentinel-5P NO2 | `(25592, 3, 36, 36)` | 2021-2025 | Columna de NO2 |
| Sentinel-5P SO2 | `(25829, 2, 36, 36)` | 2021-2025 | Columna de SO2 |
| Sentinel-5P O3 | `(25716, 2, 36, 36)` | 2021-2025 | Columna total de O3 |
| ERA5 horario | `(43824, 8, 2, 2)` | 2021-2025 | Meteorología |
| MODIS MAIAC | `(1826, 4, 43, 43)` | 2021-2025 | Aerosoles y vapor de agua |
| DAGMA/CVC | 107,291 filas | 2020-2024 | Verdad observada |

## Decisiones clave

- El BBox operativo es `[-76.65, 3.30, -76.30, 3.65]`.
- Sentinel-2 se exporta en grilla común de 10 m.
- MODIS confiable corresponde a la versión `panel_v3.zarr`.
- Kaggle es la fuente práctica para notebooks; GCS queda como upstream.

## Referencias

- [Datasets del proyecto](../../DATASETS.md)
- [Manifest técnico](../../../manifest/manifest_output/manifest.json)
- [Config de Google Earth](../../../google-earth/config.py)
- [GeoTIFF vs Zarr](../../conceptos/geotiff-vs-zarr.md)
