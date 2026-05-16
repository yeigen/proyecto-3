# Justificaciones técnicas — GeoVision-CLIP Cali

Decisiones de arquitectura que el reviewer debe poder defender, con números medidos sobre el bucket [`gs://fuentes-proyecto-3`](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3).

---

## Formato dual GeoTIFF + Zarr

El panel se persiste en **dos formatos complementarios**, no en uno: GeoTIFF como source-of-truth y Zarr como vista analítica. Cada uno tiene un rol:

| Formato | Rol | Por qué |
|---|---|---|
| **GeoTIFF** (COG) | Source-of-truth y trazabilidad | Formato nativo de GEE. Auditable píxel-a-píxel contra la API original. Estándar OGC. |
| **Zarr v2** | Vista analítica para Situaciones 2 y 3 | Chunking N-dimensional permite acceso eficiente a series temporales `pixel[t, :]` sin abrir todos los archivos. Necesario para ConvLSTM y Kriging Espacio-Temporal. |

### El cambio no es una recompresión, es una reestructuración

```
GeoTIFF: 1 archivo monolítico por (imagen, banda)
  → leer pixel[200,200] de 1552 timestamps abre 1552 archivos secuencialmente

Zarr: chunks (time=5, band=13, y=974, x=974)
  → leer el mismo pixel toca ~312 chunks (uno por slice de 5 imágenes)
  → compresión blosc/zstd/c5/bitshuffle
```

El Zarr **no comprime mejor** que el GeoTIFF — al contrario, el LZW de GEE comprime excepcionalmente bien sobre datos sparse. El Zarr existe por la **estructura**, no por el peso.

### Cumplimiento del PDF

PDF Situación 1, p.4: *"Convertir las series temporales a formato Zarr (recomendado para arrays N-dimensionales con chunking espacio-temporal) o Parquet particionado por (año, mes, contaminante)."*

Sentinel-2 es naturalmente un array 4D `(time, band, y, x)` → Zarr es la opción técnicamente correcta. Parquet forzaría un esquema tabular sobre algo que no lo es.

Detalle profundo del diseño de chunks `(5, 13, 974, 974)` en [`conceptos/geotiff-vs-zarr.md`](conceptos/geotiff-vs-zarr.md).

---

## Método de exportación: `xee` sobre `toCloudStorage`

Para las 5 fuentes pequeñas (S5P × 3 + ERA5 + MODIS) usamos `xee` (Xarray Earth Engine), no `ee.batch.Export.image.toCloudStorage()`.

### Por qué no `toCloudStorage`

| Problema | Detalle |
|---|---|
| No produce Zarr | Genera GeoTIFFs que luego requieren conversión a Zarr — agrega un paso completo de post-procesamiento |
| Una tarea por imagen | ERA5 (43,824 imágenes) → 43,824 tareas. GEE limita a ~3,000 concurrentes y cada una tarda 30 s – 2 min. Tiempo: 12–48 h solo en submit+poll |
| Cuotas | ~3,000 tasks/día en cuenta gratuita, ~10,000 en registradas. Excede para MODIS (151K) o S5P (25K+) |
| Orquestación compleja | Submit + monitor + reintentos + esperar completación + descargar + convertir |
| Resolución obligada | No permite reescalar — usa la grilla nativa del pixel grid de GEE |
| Sin beneficio para datos pequeños | ERA5 sobre Cali son ~11 MB. El overhead de submit es órdenes de magnitud mayor |

### Por qué `xee`

`xee` abre ImageCollections directamente como `xarray.Dataset`:

- Sin descarga intermedia. Lee directo desde servidores GEE vía API, convierte a xarray on-the-fly.
- Un solo paso: `open_dataset` → `to_zarr`. Sin GeoTIFFs, sin conversión manual.
- Chunking nativo con `io_chunks` para controlar tamaño Dask/lazy.
- `to_zarr` permite `encoding`, `dtype`, `consolidated` — todo configurable.

### Pipeline por fuente

| Fuente | Método | Justificación |
|---|---|---|
| ERA5 | `xee` directo → `panel.zarr` | 11 MB total. Cabe en RAM en un solo paso. |
| S5P NO₂/SO₂/O₃ | `xee` directo → `panel.zarr` | ~200-270 MB por fuente. Cabe en RAM con Dask. |
| MODIS | `xee` streaming → `panel.zarr` | ~9 GB. Streaming con `io_chunks` y `to_zarr(mode='a')`. |
| Sentinel-2 | Pipeline propio (`getDownloadURL` por banda) | 77 GB en GeoTIFFs, luego append-by-batch a Zarr. `xee` no es viable: `getDownloadURL` maneja bandas individuales y resolución 10 m forzada. |

### Benchmark estimado ERA5

- `getDownloadURL`: ~7 h para 43K imágenes (50 por batch).
- `xee`: 5–15 minutos.
- `toCloudStorage`: ~30 días (absurdo para 11 MB de datos).

---

## Pesos del panel — análisis por etapa

Análisis del peso en cada etapa del pipeline: **crudo teórico → GeoTIFF (LZW) → Zarr (Zstd/bitshuffle)**.

### Resumen ejecutivo

| Etapa | S2 | S5P (×3) | ERA5 | MODIS | **Total panel** |
|---|---|---|---|---|---|
| Crudo teórico (sin compresión, BBox) | ~612 GB | ~2.5 GB | ~5 MB | ~2.4 GB | **~617 GB** |
| GeoTIFF + LZW (medido) | 76.99 GB | 0.14 GB | 0.085 GB | 0.022 GB | **77.23 GB** |
| Zarr + Zstd/bitshuffle (proyectado/medido) | ~87 GB | 0.07 GB | 0.008 GB | 0.009 GB | **~87 GB** |

- GeoTIFF LZW: **8× sobre crudo** (617 → 77 GB).
- Zarr Zstd: similar ratio al LZW; el cambio es estructura, no compresión.
- **Umbral del proyecto ≥ 50 GB** ✅ cumplido con margen del **54 %** sobre solo el GeoTIFF.

### Detalle por fuente

**Sentinel-2** domina el peso (99 %).

- BBox `[-76.65, 3.30, -76.30, 3.65]` = 0.35° × 0.35° ≈ 38.9 × 38.9 km.
- Resolución forzada a 10 m → 3,897 × 3,897 = 15.18 M píxeles por banda.
- 13 bandas × uint16 (2 bytes) → 394.7 MB por imagen sin compresión.
- 1,552 escenas → **612 GB crudos**, **76.99 GB tras LZW** (ratio 7.95×).
- LZW comprime tanto porque: (1) imágenes en bordes de swath tienen 70-95 % `_FillValue=0`; (2) redundancia espacial en cuerpos de agua/vegetación; (3) coherencia inter-banda en red edge.

**Sentinel-5P** (NO₂/SO₂/O₃).

- Resolución L3: 1113 m → 36 × 35 píxeles dentro del BBox.
- float64 (8 bytes) — el dataset GEE entrega así por precisión.
- ~25K imágenes × 20–30 KB → 2.5 GB crudos → 0.14 GB en GeoTIFF (ratio 17.9× porque float64 sparse comprime extremo bien).

**ERA5 atmosférico horario**.

- Resolución 27.8 km → 2 × 2 píxeles (overshoot a 0.5° × 0.5°, grilla nativa 0.25°).
- 8 bandas × float32 → 128 bytes por imagen.
- 43,824 horas × 128 B = **4.4 MB crudos**.
- GeoTIFF medido 85 MB: mayoritariamente **overhead de headers** (cada archivo ~2 KB de metadata, dominante sobre los 128 B de datos reales).

**MODIS MAIAC**.

- Resolución 927 m → 43 × 43 píxeles.
- 4 bandas × int32 → 30 KB por imagen.
- ~80K gránulos × 30 KB = 2.4 GB crudos → 0.022 GB tras LZW (90 % de los gránulos son bordes vacíos que comprimen a 600 B solo del header).

### Por qué Zarr Zstd/bitshuffle comprime diferente

Benchmark medido sobre `20210106T...__T18NUJ__spectral.tif` (12 bandas densas):

| Codec | Tamaño | Ratio |
|---|---|---|
| Sin compresión | 347.6 MB | 1.0× |
| GeoTIFF + LZW | 408.6 MB | **0.85×** (¡peor!) |
| Zarr + LZ4 (Blosc lvl 5) | 197 MB | 1.77× |
| Zarr + Zstd (Blosc lvl 5, bitshuffle) | 131 MB | **2.65×** |

Y sobre `__B4.tif` individual (datos sparse de borde de swath):

| Codec | Tamaño | Ratio |
|---|---|---|
| Sin compresión | 28.97 MB | 1.0× |
| GeoTIFF + LZW | 1.99 MB | **14.6×** |
| Zarr + Zstd (bitshuffle) | 2.31 MB | 12.6× |
| Zarr + LZ4 | 3.97 MB | 7.3× |

LZW de GEE es **excepcional sobre datos sparse**. Zstd+bitshuffle es óptimo sobre **datos densos float32 con NaN**: bitshuffle explota el orden de exponentes IEEE 754, zstd comprime las runs resultantes.

---

## Cobertura temporal verificada (2021-01-01 → 2026-01-01)

| Fuente | Primer dato | Último dato | Archivos GCS |
|---|---|---|---:|
| Sentinel-2 | 2021-01-03 | 2025-12-31 | 20,176 |
| S5P NO₂ | 2020-12-31 | 2025-12-31 | 25,592 |
| S5P SO₂ | 2020-12-31 | 2025-12-31 | 25,829 |
| S5P O₃ | 2020-12-31 | 2025-12-31 | 25,716 |
| ERA5 horario | 2021-01-01 | 2025-12-31 | 43,824 |
| MODIS MAIAC | (DOY) | (DOY) | 151,558 |

- El **último dato es siempre 2025-12-31**: `ee.ImageCollection.filterDate(ini, fin)` excluye el fin. La ventana `("2021-01-01", "2026-01-01")` significa "desde 1-ene-2021 inclusive hasta 1-ene-2026 exclusive". Para incluir el 1-ene-2026 habría que poner `fin="2026-01-02"`. Diferencia <1 día, no afecta ninguna serie.
- **S2 empieza el 2021-01-03 y no el 01-01**: revisita de 5 días y la órbita no pasó por Cali los 2 primeros días del año.
- **MODIS** usa Day-of-Year en `system:index`; 151,558 archivos = múltiples gránulos/día (Terra + Aqua + swaths superpuestos).

## Coherencia lossless GeoTIFF ↔ Zarr

Verificado sobre la primera imagen del panel S2 (`20210103T152641_T18NUJ`):

| Banda | Píxeles válidos | `diff_max` | Resultado |
|---|---:|---:|---|
| B1 (60 m → 10 m bilinear) | 2,354,710 | **0.000000** | bit-perfect |
| B4 (10 m nativo) | 2,346,114 | **0.000000** | bit-perfect |
| B8 (10 m nativo) | 2,346,114 | **0.000000** | bit-perfect |
| SCL (20 m → 10 m) | 2,346,114 | **0.000000** | bit-perfect |

Verificaciones cruzadas en otras fuentes:

| Fuente | Imagen | `diff_max` |
|---|---|---:|
| S5P NO₂ | 20240715 | 2e-12 (ruido float64 → float32) |
| ERA5 | 20210211 | 0.000000 |

La conversión Zarr es lossless. Los `e-12` en S5P son ruido de precisión `float64 → float32`, no error de pipeline.

---

## Decisiones técnicas adicionales

| Decisión | Trade-off aceptado |
|---|---|
| **BBox `[-76.65, 3.30, -76.30, 3.65]`** (PDF pide `[-76.60, 3.30, -76.40, 3.55]`) | +35 % de área para capturar Yumbo + Acopi + cultivos de caña. Coherente con "corredor industrial Yumbo–Acopi" del PDF (p. 2) y "zona de cultivos de caña" (Situación 1). |
| **ERA5 horario (27.8 km) en lugar de ERA5-Land (9 km)** | ERA5-Land no contiene `boundary_layer_height` ni `relative_humidity`. El PDF las exige; ERA5-Land no las tiene. La elección preserva las variables solicitadas. |
| **S2 con 13 bandas (B1 + B2-B12 + SCL)** | PDF dice "13 bandas (B2-B12)" pero B2-B12 son 11. B1 (aerosol) y SCL (QA de escena) completan 13 sin ruido. |
| **S2 resampleado a 10 m (3897×3897)** | Tensor `(13, 3897, 3897)` uniforme para ViT-B/32 de Situación 2. Replicación bilineal de B1/B9 (60 m) y B5-B7/B8A/B11/B12 (20 m) — práctica estándar (RemoteCLIP, Prithvi). |
| **HARP saltado porque GEE L3 ya está pre-griddeado** | El paso 3 del PDF asume L2 + `harpconvert bin_spatial`, pero el dataset `COPERNICUS/S5P/OFFL/L3_*` ya es el output post-bin_spatial. Pedir L2 + HARP recrearía lo mismo. |
| **Chunks Zarr `(5, 13, 974, 974)`** | 4,992 data chunks (bajo el límite HF de 10K), 15–30 MB comprimido por chunk (sweet spot HTTP Range), 5 timestamps por chunk útil para ConvLSTM. |
| **`zstd c5 + bitshuffle` sobre LZ4** | 2.65× vs 1.77× sobre datos densos S2. Bitshuffle explota IEEE 754. 400-600 MB/s de escritura es suficiente. |
| **ThreadPoolExecutor en lugar de Dask explícito** | PDF dice "paralelizar por banda, fecha y tile". El cuello de botella real es `getDownloadURL` (50 MB/request) y la API GEE, no el cómputo local. Dask aquí solo agregaría complejidad. |

---

## Referencias

- [Zarr v3 specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html) (los stores usan `zarr_format=2` por compatibilidad amplia con xarray/dask).
- [Cloud Optimized GeoTIFF spec](https://www.cogeo.org/)
- [GDAL GeoTIFF driver](https://gdal.org/drivers/raster/gtiff.html)
- [Blosc compression library](https://www.blosc.org/)
- [Bitshuffle filter](https://github.com/kiyo-masui/bitshuffle)
- [Zstd](https://github.com/facebook/zstd)
- [xarray + Zarr integration](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr)
- [PDF asignatura](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf) — Situación 1, p. 3-4
- [`DATASETS.md`](DATASETS.md) — fuentes y bandas
- [`conceptos/geotiff-vs-zarr.md`](conceptos/geotiff-vs-zarr.md) — diseño detallado de chunks y benchmarks
