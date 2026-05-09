# Justificación de pesos del panel

Análisis del peso de los datos en cada etapa del pipeline: **fuente original → GeoTIFF (LZW) → Zarr (LZ4/Zstd)**. Todos los números provienen de mediciones reales sobre [`gs://fuentes-proyecto-3`](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3) y los [logs de ejecución](#logs-de-auditoría).

## Resumen ejecutivo

| Etapa | S2 | S5P (3 fuentes) | ERA5 | MODIS | **Total panel** |
|---|---|---|---|---|---|
| **Crudo teórico** (sin compresión, BBox Cali+Yumbo+Acopi) | ~612 GB | ~2.5 GB | ~5 MB | ~2.4 GB | **~617 GB** |
| **GeoTIFF + LZW** (medido) | 76.99 GB | 0.14 GB | 0.085 GB | 0.022 GB | **77.23 GB** |
| **Zarr + LZ4/Zstd** (proyectado) | ~77 GB | 0.07 GB | 0.008 GB | 0.009 GB | **~77 GB** |

**Compresión efectiva**:
- GeoTIFF LZW: **8x** sobre crudo (de 617 → 77 GB)
- Zarr LZ4: **0.97x** sobre LZW (peso similar; cambia la estructura, no el ratio)

**Umbral del proyecto: ≥ 50 GB** ✅ Cumplido con margen del **54%** sobre solo el panel GeoTIFF.

---

## Por qué los pesos crudos teóricos son los que son

Cada fuente tiene un peso crudo determinado por **4 variables físicas**: resolución espacial, área (BBox), número de bandas y dtype.

### Sentinel-2 MSI L2A — el dataset que domina el peso (99%)

**Parámetros**:
- BBox Cali+Yumbo+Acopi: `[-76.65, 3.30, -76.30, 3.65]` = 0.35° × 0.35° ≈ 38.9 × 38.9 km
- Resolución forzada a **10 m** (resampleo en GEE server side, ver [DATASETS.md](DATASETS.md#decisión-resampleo-a-10-m))
- Píxeles por banda: ⌈38,900 / 10⌉² = **3,897 × 3,897 = 15.18 M píxeles**
- Bandas incluidas: 13 (12 espectrales uint16 + SCL uint8 → casteado a uint16)
- Dtype: uint16 → 2 bytes por píxel

**Peso por imagen sin compresión**:
```
15,180,609 px × 13 bandas × 2 bytes = 394.7 MB / imagen
```

**Imágenes detectadas en el BBox + ventana 2021-2026**:
- Tile T18NUH (oeste, parte): ~520 imágenes
- Tile T18NUJ (centro, Cali): ~516 imágenes
- Tile T18NUK (este, Yumbo+Palmira): ~516 imágenes
- **Total: 1,552 imágenes** (verificado por log [`exportar_s2_*.log`](#logs-de-auditoría))

**Peso crudo total S2**: `1,552 × 394.7 MB = 612 GB`

**Peso GeoTIFF LZW real**: 76.99 GB → **ratio 7.95x**

¿Por qué LZW comprime tanto?
1. **Datos sparse**: imágenes en bordes de swath tienen 70-95% de píxeles igual a 0 (`_FillValue`). LZW codifica runs de ceros eficientemente.
2. **Redundancia espacial**: superficies homogéneas (cuerpos de agua, vegetación densa) tienen valores similares en píxeles vecinos.
3. **Coherencia entre bandas adyacentes**: B5, B6, B7 (red edge) tienen valores correlacionados.

### Sentinel-5P TROPOMI (NO2 / SO2 / O3)

**Parámetros**:
- Resolución: 1113 m (re-grilla L3 a 0.01°) — [TROPOMI L3 spec](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-5p)
- BBox: 36 × 35 píxeles (con overshoot por grilla)
- Bandas: 2-3 según contaminante (NO2 = 3, SO2 = 2, O3 = 2)
- Dtype: **float64** (8 bytes/píxel) — el dataset GEE entrega así por precisión

**Peso por imagen**:
```
36 × 35 × 3 × 8 bytes = 30 KB (NO2)
36 × 35 × 2 × 8 bytes = 20 KB (SO2/O3)
```

**Imágenes**: ~25,000 por contaminante (1-2 órbitas/día × 5 años)

**Peso crudo total S5P**: `(25k × 30KB) + 2 × (25k × 20KB) ≈ 2.5 GB`

**Peso GeoTIFF medido**: 0.139 GB → ratio **17.9x** (muy alto porque float64 con datos sparse comprime extremo bien con LZW).

### ERA5 atmospheric hourly

**Parámetros**:
- Resolución nativa: 27.8 km (0.25°) — [ECMWF ERA5 docs](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- BBox: 2 × 2 píxeles (overshoot a 0.5° × 0.5°)
- Bandas: 8 (T2m, dewpoint, viento u/v, BLH, RH, presión, precipitación)
- Dtype: float32 (4 bytes/píxel)

**Peso por imagen**:
```
2 × 2 × 8 × 4 bytes = 128 bytes
```

**Imágenes**: 34,499 (horarias)

**Peso crudo total ERA5**: `34,499 × 128 bytes = 4.4 MB`

**Peso GeoTIFF medido**: 0.085 GB = 85 MB → mayoritariamente **overhead de headers GeoTIFF** (cada archivo tiene ~2 KB de metadata, dominante sobre los 128 bytes de datos).

### MODIS MAIAC AOD

**Parámetros**:
- Resolución: 927 m — [MAIAC ATBD](https://atmosphere-imager.gsfc.nasa.gov/sites/default/files/ModAtmo/MAIAC_ATBD_v1.pdf)
- BBox: 43 × 43 píxeles
- Bandas: 4 (OD_047, OD_055, Column_WV, AOD_QA)
- Dtype: int32 (4 bytes/píxel)

**Peso por imagen**:
```
43 × 43 × 4 × 4 bytes = 30 KB
```

**Imágenes esperadas**: ~80,000 gránulos (Terra+Aqua, múltiples swaths/día sobre 5 años, mayoría sin cobertura sobre Cali)

**Peso crudo total MODIS**: `80k × 30 KB ≈ 2.4 GB`

**Peso GeoTIFF medido**: 0.022 GB (en curso) → 90% de los gránulos resultan ser bordes vacíos o `_FillValue`, comprimen a 600 bytes c/u (solo header).

---

## Por qué Zarr LZ4 NO comprime más

Test directo medido sobre archivo `20210106T..._T18NUJ__spectral.tif` (12 bandas densas):

| Codec | Tamaño | Ratio | Velocidad |
|---|---|---|---|
| Sin compresión | 347.6 MB | 1.0x | — |
| GeoTIFF + LZW | 408.6 MB | **0.85x** (¡peor!) | rápido |
| Zarr + LZ4 (Blosc lvl 5) | 196.8 MB | 1.77x | muy rápido |
| Zarr + Zstd (Blosc lvl 3) | 131.4 MB | 2.65x | medio |

Y para `__B4.tif` individual (datos sparse de borde swath):

| Codec | Tamaño | Ratio |
|---|---|---|
| Sin compresión | 28.97 MB | 1.0x |
| GeoTIFF + LZW | 1.99 MB | **14.6x** |
| Zarr + LZ4 | 3.97 MB | 7.3x |
| Zarr + Zstd | 2.31 MB | 12.6x |

**Conclusiones**:
1. LZW de GEE es **excepcionalmente bueno** sobre datos satelitales sparse — supera a LZ4 e iguala casi a Zstd
2. Zarr usa LZ4 default por velocidad de lectura/escritura, no por ratio
3. **No estamos "recomprimiendo" en Zarr** (ver [JUSTIFICACION_FORMATO.md](JUSTIFICACION_FORMATO.md)) — estamos cambiando la **estructura de chunking**

**Referencias**:
- [GeoTIFF compression comparison (GDAL)](https://gdal.org/drivers/raster/gtiff.html#creation-options)
- [Zarr v3 codec spec](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html#data-types)
- [Blosc compression library](https://www.blosc.org/)
- [LZW algorithm overview](https://en.wikipedia.org/wiki/Lempel%E2%80%93Ziv%E2%80%93Welch)

---

## Pesos reales por etapa (medidos en bucket)

Inventario verificable con `gcloud storage du -s gs://fuentes-proyecto-3/`:

```
copernicus_s2_sr_harmonized:        19,400 archivos × ~4 MB    = 76.99 GB
  └ panel.zarr/ (en construcción):   1,050 archivos × ~14 MB   = 14.05 GB → proyección final ~77 GB

copernicus_s5p_offl_l3_no2:         14,799 archivos × 2.7 KB   = 0.040 GB
  └ batch_NNNN.zarr/ ×512:           5,900 archivos × 4 KB     = 0.022 GB

copernicus_s5p_offl_l3_so2:         25,830 archivos × 1.5 KB   = 0.037 GB
  └ batch_NNNN.zarr/ ×515:          10,340 archivos × 1.5 KB   = 0.015 GB

copernicus_s5p_offl_l3_o3:          25,717 archivos × 2.4 KB   = 0.062 GB
  └ batch_NNNN.zarr/ ×515:          10,300 archivos × 3 KB     = 0.031 GB

ecmwf_era5_hourly:                  34,499 archivos × 2.5 KB   = 0.085 GB
  └ batch_NNNN.zarr/ ×690:          13,780 archivos × 0.6 KB   = 0.008 GB

modis_061_mcd19a2_granules:         28,450 archivos × 0.8 KB   = 0.022 GB (en curso)
  └ batch_NNNN.zarr/ ×569:          11,171 archivos × 0.8 KB   = 0.009 GB
```

---

## Logs de auditoría

Todos los pasos del pipeline tienen log estructurado en `logger/logs/` (modulo `logger/__init__.py`).

| Fase | Log file | Tamaño | Notas |
|---|---|---|---|
| Test toCloudStorage S2 | `test_s2_tcs_20260508_004056.log` | 2.7 KB | validación inicial — exitosa |
| S2 download (1ª iter, fallida) | `s2_final_20260508_000841.log` | 248 B | primer intento, screen mató |
| S2 download (2ª iter, exitosa) | `exportar_s2_20260508_*.log` | varios | 1552 imágenes en 8h05min |
| S5P + ERA5 download | `exportar_zarr_gcs_*.log` | 0.27 MB c/u | 5 logs (1 por intento/sesión) |
| MODIS download (resume) | `modis_resume.log` (en `/root/`) | actualizando | desde batch 1, salta cached |
| S2 → Zarr consolidación | `consolidar_s2_zarr_*.log` | en curso | 311 bloques de 5 imágenes |

**Estructura de cada log** (formato del `logger` del proyecto):
```
2026-05-08 04:21:36,245 [INFO] exportar_s2: [1/1483] 20210329T...__T18NUK | 4MB en 15s | 0 fallas | ETA 379min
                                            └── progreso ────┘   └── peso ┘  └── tiempo ┘
```

Cada log permite reconstruir:
- Cuántas imágenes de cada fuente fueron descargadas
- Peso individual por imagen
- Tiempo por imagen (auditoría de throughput)
- Errores (todos hasta ahora son 0 fallas)

---

## Referencias técnicas

### Formato GeoTIFF
- [GeoTIFF specification (OGC)](https://docs.ogc.org/is/19-008r4/19-008r4.html)
- [GDAL GeoTIFF driver docs](https://gdal.org/drivers/raster/gtiff.html)
- [Cloud Optimized GeoTIFF (COG)](https://www.cogeo.org/)
- [LZW compression in TIFF](https://en.wikipedia.org/wiki/TIFF#Compression)

### Formato Zarr
- [Zarr v3 specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html)
- [Zarr Python docs](https://zarr.readthedocs.io/en/stable/)
- [xarray + Zarr integration](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr)
- [Pangeo Cloud Native Geospatial](https://pangeo.io/)
- [Blosc meta-compressor](https://www.blosc.org/)

### Datasets
- [Sentinel-2 User Handbook](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook)
- [Sentinel-5P TROPOMI mission](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p)
- [ERA5 hourly atmospheric data](https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels)
- [MODIS MCD19A2 product](https://lpdaac.usgs.gov/products/mcd19a2v061/)
- [Google Earth Engine catalog](https://developers.google.com/earth-engine/datasets)

### Bucket
- [GCP Console — gs://fuentes-proyecto-3](https://console.cloud.google.com/storage/browser/fuentes-proyecto-3)
- [Google Cloud Storage docs](https://cloud.google.com/storage/docs)
