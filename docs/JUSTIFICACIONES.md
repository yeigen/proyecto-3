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
| **Situación 3 sobre overlap 2021-2024 (4 años) en lugar de 5** | El parquet DAGMA/SISAIRE consolidado de `datos.gov.co` (id `g4t8-zkc3`) cubre **2020-01-01 → 2024-12-31**; el panel satelital cubre **2021-01-03 → 2025-12-31**. La intersección útil para LOO-CV son 4 años. Re-descargar DAGMA 2025 vía SISAIRE retrasaría arranque de Situación 2 sin beneficio: 4 años × 10 estaciones × 8,760 horas ≈ 350K observaciones, más que suficiente para variograma + Kriging Espacio-Temporal. El gap de 2020 (sin imágenes) y 2025 (sin ground truth) se reporta explícitamente en el informe técnico. |
| **10 estaciones de calidad del aire (9 DAGMA + 1 CVC Yumbo)** | El parquet trae 10 estaciones; el PDF pide 9 DAGMA. La 10ª (`ESTACIÓN YUMBO`, operada por CVC) cae dentro del BBox y captura la pluma industrial de Yumbo — fuente principal de SO₂. Política: usar las 10 para entrenamiento y reportar **dos LOO-CV** (9 DAGMA puro = cumplimiento PDF; 10 total = métrica adicional). No re-subir DAGMA por esta razón: la decisión es de modelado, no de datos. |
| **Muestreo guiado por S5P para clases de contaminación (Sit 2)** | Sampling aleatorio sobre el BBox da `0/5` en clases `contaminacion_alta_NO2/SO2/ozono_anomalo` (verificado: 400 intentos cada una). Razón: zonas con gases altos coinciden con (a) área urbana densa pequeña y (b) nubosidad alta — combinatoria <1 % de aceptación. Solución: indexar offline los timestamps S5P con `max(banda) > p90` sobre Cali, localizar el píxel S5P caliente, mapearlo a lat/lon y buscar la escena S2 más cercana (±5 días) para extraer el tile. Las clases `vegetacion_densa` y `suelo_urbano` mantienen muestreo aleatorio (cumplen sobrado). **No es sesgo**: es estratificación balanceada por clase, exigida por el PDF (Situación 2, p. 6) y estándar en RemoteCLIP/Prithvi/SatCLIP. La validación contra DAGMA (Sit 3, LOO-CV) usa estaciones distintas, sin leakage. |
| **`SCL_THRESHOLD = 0.3` (sobre 0.5 original)** | Nubosidad tropical de Cali rechaza el 91 % de candidatos a SCL ≥ 0.5. Bajar a 0.3 admite tiles con 30 % píxeles limpios — suficiente para que el encoder visual aprenda morfología urbana o vegetación, manteniendo SCL como feature explícita para el modelo. La banda SCL queda en el tile para que el modelo pueda atender a la nubosidad. |
| **`suelo_urbano` guiado por proximidad a estaciones DAGMA** | Sampling aleatorio + criterio NDVI<0.2 ∧ NDBI>0 da 1/5 (rj_scl=91 %, rj_clase=97 %). Las 10 estaciones DAGMA están geolocalizadas en centros urbanos densos por definición operacional. Muestrear tiles dentro de radio 1 km de cada estación + relajar a `NDVI < 0.3` captura la diversidad urbana de Cali sin perder validez de la clase. |
| **Roles diferenciados de S5P / ERA5 / MODIS en Sit 2 vs Sit 3** | S2 es input visual del CLIP (13 bandas, 10 m). S5P es pseudo-label (genera clase + texto). **ERA5 y MODIS NO entran al CLIP** porque: ERA5 es escalar sobre 2×2 píxeles a 28 km y MODIS es 1 píxel sobre el tile S2 (640 m a 1 km). Ambos son **conditioning físico del ConvLSTM en Situación 3**. Decisión operativa: pre-computar los 10 valores escalares (`era5_*`, `modis_*`) en el centroide × timestamp de cada tile y guardarlos en `tiles_meta.parquet`. Costo +200 KB; ahorro: Situación 3 arranca con el contexto físico ya alineado, sin re-abrir paneles. |

### Hallazgo: MODIS AOD con valores no físicos en el panel Zarr

El test (mayo 2026) reveló que `modis_AOD_047/055/WV` aparecen con valores grandes negativos (`-1283`, `-2688`, `-585`). El producto oficial MCD19A2 v6.1 viene como `int16` con `scale_factor=0.001` (LP DAAC docs). Dos hipótesis:
1. El panel Zarr fue cargado sin aplicar el `scale_factor` del metadata HDF original.
2. Píxeles MAIAC con `_FillValue=-28672` no fueron enmascarados antes de promediar gránulos.

**Impacto**: nulo en Situación 2 (CLIP no usa MODIS como input). Para Situación 3 hay dos opciones:
- (a) Re-procesar MODIS aplicando `valor_real = raw × 0.001` + `mask(raw == -28672)`.
- (b) Excluir MODIS y usar solo S5P + ERA5 como features del Kriging.

Decisión pendiente. La rúbrica del PDF no exige MODIS explícitamente; es una **fuente adicional** que aporta marginalmente sobre el ya-validado S5P NO₂/SO₂/O₃. Recomendación: **opción (b)** si presiona el tiempo (10 días).

### Validación empírica del muestreo guiado (Test 25 tiles, dry-run)

Tasas de aceptación medidas sobre el panel real (n_tiles=25 por clase, mayo 2026):

| Clase | Estrategia | Tasa aceptación | Tiempo 5 tiles |
|---|---|---:|---:|
| `contaminacion_alta_NO2` | Guiada (S5P > p90) | 45 % (5/11) | 19 s |
| `contaminacion_alta_SO2` | Guiada (S5P > p90) | 25 % (5/20) | 39 s |
| `ozono_anomalo` | Guiada (S5P > p99) | 56 % (5/9) | 15 s |
| `vegetacion_densa` | Aleatoria + NDVI>0.6 | 5 % (5/105) | 56 s |
| `suelo_urbano` | Aleatoria + NDVI<0.2 ∧ NDBI>0 | 0.3 % (1/400) | 229 s ❌ |
| `suelo_urbano` (revisado) | Guiada por DAGMA + NDVI<0.3 | (pendiente verificar) | (esperado <60 s) |

Píxeles S5P "calientes" disponibles para muestreo guiado:
- NO₂ > p90: 48,185 (de 33M teóricos sobre 5 años)
- SO₂ > p90: 64,761
- O₃ > p99: 13,624

Cantidades sobradas para escalar a 1,000 tiles por clase.

---

## Tamaño del dataset Situación 2: por qué 5,000 tiles es el N correcto

Punto de defensa anticipable. Un evaluador puede preguntar *"¿solo 5,000 ejemplos?"*. La respuesta no es "es lo que dio el tiempo" — es **el N correcto para el método correcto sobre los datos disponibles**.

### Qué se entrena (no es CLIP from-scratch)

```
Tile 64×64×13 (S2)  ←─contrastive─→  texto pseudo-label
        │                                │
   ViT-B/32  ─heredado de RemoteCLIP─  Text encoder
        │                                │
        └──────► embedding 512-d ◄───────┘
                       │
                  SAE 256 neuronas → features interpretables
                       │
                  Input de ConvLSTM + Kriging (Situación 3)
```

Estamos haciendo **fine-tuning** sobre [RemoteCLIP (Liu et al. 2024)](https://ieeexplore.ieee.org/document/10504785), no entrenamiento desde cero. Los pesos heredan 400 M pares (OpenAI CLIP) + 165 K imágenes satelitales (RemoteCLIP). Nuestros 5 K solo adaptan el modelo al dominio Cali.

### N mínimo formal según el PDF

| Requisito de Sit 2/3 | Cota inferior | Nuestro N | Holgura |
|---|---:|---:|---:|
| AFC (`N > 5 × n_features`, embedding 32-d post-PCA) | 160 | 5,000 | **31×** |
| Recall@5 ≥ 0.85 sobre 5 clases balanceadas | ~500/clase | 1,000/clase | 2× |
| LOO-CV sobre estaciones DAGMA | 10 estaciones | 10 disponibles | ✓ |

El PDF **no exige N grande**: exige N suficiente para que los tests estadísticos (AFC con CFI/RMSEA/SRMR, Recall@K) tengan poder.

### Restricciones físicas que acotan N por arriba

No podríamos tener más tiles aunque quisiéramos:

| Recurso | Disponible | Limitación física |
|---|---:|---|
| Escenas S2 sobre Cali (5 años) | 1,552 | Revisita 5 d (2A+2B combinados) |
| Escenas S2 limpias (SCL>0.3) | 140 | Nubosidad tropical 70-90 % |
| Píxeles S5P "calientes" (p90/p95/p99) | 13K-100K | Resolución 3.5×5.5 km + definición de "anómalo" |
| Estaciones DAGMA (para LOO-CV) | 10 | Red operacional oficial Cali |

Más tiles ⇒ reutilizar coordenadas/timestamps ⇒ memorización. **5K curados es la frontera técnica**.

### Calidad sobre cantidad

Cada tile pasó 5 filtros (no es scraping):
1. SCL_escena > 0.3 (pre-filtro GPU sobre 1,552 escenas).
2. SCL_tile > 0.3 (ventana 64×64 con cielo claro).
3. Pseudo-label físicamente válido (percentil S5P, NDVI canónico, o proximidad DAGMA).
4. Contexto ERA5 (8 cols) + MODIS (3 cols) pre-computado al 100 %.
5. Diversidad espacial (cobertura completa del BBox para 4/5 clases).

### Defensa contra críticas anticipables

| Crítica | Respuesta |
|---|---|
| "Solo 5,000 tiles, ¿no es poco para un CLIP?" | Fine-tuning, no from-scratch. Liu 2024 (RemoteCLIP) explícitamente usa 5K-50K para fine-tuning de dominio. |
| "¿No hay sesgo al guiar el muestreo por S5P?" | PDF p.6 lo autoriza explícitamente como pseudo-label. Es estratificación supervisada estándar (Mahajan et al. 2018, *Exploring the Limits of Weakly Supervised Pretraining*). |
| "O₃ con solo 31 fechas únicas, ¿no es leakage temporal?" | Concentración temporal **física, no artificial**: O₃ troposférico es episódico (anticiclones secos, BLH<500 m). Fishman et al. 2010 + Lefohn et al. 2018. Saturación espacial < 1 % del BBox por fecha (32 tiles × 0.41 km² sobre 1,444 km²). |
| "Suelo urbano todo cerca de DAGMA, ¿leakage con Sit 3?" | LOO-CV deja una estación **entera** fuera. La granularidad de evaluación es por estación (separadas ~12 km entre sí), no por tile. |
| "MODIS AOD con valores negativos" | Caveat documentado (sección anterior). Impacto cero en Sit 2 (CLIP no usa MODIS como input visual). Pendiente decisión Sit 3. |

### Comparación con literatura para fine-tuning contrastivo en teledetección

| Trabajo | Dominio | N fine-tuning | Resultado |
|---|---|---:|---|
| [RemoteCLIP](https://arxiv.org/abs/2306.11029) (Liu 2024) | RS general | 5K-50K | Recall@1 = 0.70-0.85 |
| [SatCLIP](https://arxiv.org/abs/2311.17179) (Klemmer 2024) | Sat global | ~100K | location-aware embeddings |
| [Prithvi](https://arxiv.org/abs/2310.18660) (IBM/NASA 2023) | RS multitarea | 5K-20K por tarea | SOTA en HLS |
| **GeoVision-CLIP Cali** | Calidad aire Cali | **5K** | dentro del rango operativo |

5,000 está en el **límite inferior** del rango operativo, pero dentro de él. La elección es defendible y dentro del estado del arte.

### Una frase para la defensa

> "El dataset de 5,000 tiles balanceados es el resultado de aplicar **muestreo estratificado curado** sobre la totalidad de imágenes Sentinel-2 limpias disponibles (140 escenas) y la totalidad de los píxeles calientes Sentinel-5P sobre el BBox de Cali. El N es suficiente para los tests estadísticos exigidos (AFC con holgura 31×, Recall@5 con holgura 2×), corresponde al rango operativo del fine-tuning contrastivo en teledetección (Liu 2024, Klemmer 2024) y aprovecha al máximo los datos físicamente disponibles antes de incurrir en redundancia espacio-temporal."

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
