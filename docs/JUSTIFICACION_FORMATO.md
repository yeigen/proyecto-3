# Justificación del formato dual GeoTIFF + Zarr

## Decisión

El panel de datos satelitales se persiste en **dos formatos complementarios**:
1. **GeoTIFF** (Cloud Optimized) en `gs://fuentes-proyecto-3/{fuente}/raw/`
2. **Zarr v3** en `gs://fuentes-proyecto-3/{fuente}/{batch}.zarr/` y `panel.zarr/` (S2), compresión blosc/zstd/c5/bitshuffle

No es duplicación. Cada uno tiene un rol específico:

| Formato | Rol | Por qué |
|---|---|---|
| **GeoTIFF** | Source-of-truth y trazabilidad | Es el formato nativo entregado por Google Earth Engine. Auditable píxel-a-píxel contra la API original. Estándar OGC para datos raster geoespaciales. |
| **Zarr** | Vista analítica para Situaciones 2 y 3 | Chunking N-dimensional permite acceso eficiente a series temporales (`pixel[t, :]`) sin abrir todos los archivos. Necesario para ConvLSTM y Kriging Espacio-Temporal. |

## El cambio NO es una recompresión

Recomprimir sería convertir un `.zip` a `.gz`: mismo dato, distinto algoritmo, sin beneficio.

Reformatear (lo que hacemos) es cambiar la **estructura de acceso** a los datos:

```
GeoTIFF: 1 archivo monolítico por (imagen, banda)
  → para leer pixel[200,200] de los 1552 timestamps,
    hay que abrir 1552 archivos secuencialmente

Zarr: chunks (time=5, band=13, y=974, x=974)
  → para leer pixel[200,200] de los 1552 timestamps,
    se leen ~310 chunks (uno por cada slice de 5 imágenes)
  → compresión blosc/zstd/c5/bitshuffle (mejor ratio que LZ4 sobre datos con NaN)
```

**El Zarr no comprime mejor que el GeoTIFF** — al contrario, los GeoTIFFs LZW de GEE comprimen excepcionalmente bien sobre datos sparse. El Zarr existe por la **estructura**, no por el peso.

## Cumplimiento del PDF

El PDF de la asignatura (Situación 1, p.4) lo pide explícitamente:

> *"Convertir las series temporales a formato Zarr (recomendado para arrays N-dimensionales con chunking espacio-temporal) o Parquet particionado por (año, mes, contaminante)."*

Sentinel-2 es naturalmente un array 4D `(time, band, y, x)` → Zarr es el formato apropiado.

## Costo del formato dual

- **Almacenamiento extra**: ~87 GB Zarr S2 (zstd/bitshuffle) sumados a los 77 GB GeoTIFF = ~164 GB total
- **Costo monetario**: $0.020/GB/mes en GCS Standard = $3.28/mes
- **Tiempo de cómputo de la conversión**: ~2.8 horas en una VM 4 vCPU/8 GB
- **Beneficio**: pipeline de Situaciones 2 y 3 viable (sin Zarr, abrir 1552 GeoTIFFs por consulta hace prohibitivos los modelos)

## Referencias

- [Zarr specification v3](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html)
- [Cloud Optimized GeoTIFF spec](https://www.cogeo.org/)
- [xarray + Zarr para teledetección](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr)
- [STAC + COG vs Zarr (Pangeo)](https://discourse.pangeo.io/)
- [Tutorial: GeoTIFF a Zarr con compresión](https://corteva.github.io/rioxarray/stable/examples/convert_to_raster.html)
- [PDF asignatura](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf), Situación 1, p. 4
