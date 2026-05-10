# GeoTIFF vs Zarr: conceptos, comparación y justificación de chunks

## 1. Qué es GeoTIFF

GeoTIFF es un archivo TIFF estándar con etiquetas de georreferenciación embebidas (proyección, origen, resolución). Es el formato de facto para rasters geoespaciales.

### Estructura interna

```
archivo.tif
├── Header TIFF (8 bytes)
├── IFD — Image File Directory
│   ├── Tags de georreferenciación (ModelTiepointTag, ModelPixelScaleTag, GeoKeyDirectoryTag)
│   ├── Tags de imagen (Width, Height, BitsPerSample, Compression, TileOffsets, TileByteCounts)
│   └── Compresión: LZW, Deflate, JPEG, o sin compresión
├── Datos raster (stripes o tiles contiguos)
│   └── Cada tile: bloque NxN píxeles comprimido independientemente
└── (Opcional) Overviews piramidales
```

**Un GeoTIFF es un array 2D** (bandas × y × x). La dimensión temporal no existe dentro del archivo. Una "serie temporal" es literalmente N archivos GeoTIFF, uno por fecha.

### Cloud Optimized GeoTIFF (COG)

Un COG es un GeoTIFF donde los tiles internos están ordenados secuencialmente y las_overviews existen, permitiendo HTTP GET con Range requests (bytes=inicio-fin) sin descargar todo el archivo. GEE exporta COGs por defecto.

### Limitación fundamental para series temporales

Para responder una consulta como *"dame el valor del pixel (200, 300) en todas las 1552 fechas"*:

| Paso | GeoTIFF | Zarr |
|---|---|---|
| Apertura | Abrir 1552 archivos (open TIFF, parse IFD, seek) | Abrir 1 store (leer .zattrs, .zgroup) |
| Lectura | En cada archivo: seek al tile → decompress → extract 1 pixel | Leer 312 chunks (time=5) → decompress → extract 1 pixel |
| I/O total | 1552 requests HTTP, ~4 MB/archivo = ~6 GB leídos | ~312 × ~15 MB seleccionados × acceso parcial |
| Datos útiles | 1552 × 4 bytes = 6.2 KB | 1552 × 4 bytes = 6.2 KB (idéntico) |
| Overhead | 1552 × (metadata + seek + decompress tile completo) | 312 × (decompress chunk parcial) |

**El problema no es la compresión, es el patrón de acceso.** GeoTIFF fuerza 1552 seeks en N archivos para obtener 6.2 KB de señal. Zarr organiza el mismo dato para que el acceso temporal sea O(chunks_temporales) en vez de O(n_timestamps).

---

## 2. Qué es Zarr

Zarr es un formato de storage para arrays N-dimensionales que divide el array en **chunks** (bloques regulares), cada uno almacenado como un archivo separado y comprimido independientemente.

### Estructura interna

```
panel.zarr/
├── .zgroup              → {"zarr_format": 2}
├── .zattrs              → atributos globales (crs, bbox, fuente)
├── .zmetadata           → índice consolidado (1 lectura → todo el metadata)
├── data/
│   ├── .zarray          → {"shape": [1552, 13, 3897, 3897], "chunks": [5,13,974,974], "dtype": "<f4", ...}
│   ├── .zattrs          → atributos del array
│   ├── 0.0.0.0          → chunk (t=0-4, band=0-12, y=0-973, x=0-973) — comprimido con blosc/zstd
│   ├── 0.0.0.1          → chunk (t=0-4, band=0-12, y=0-973, x=974-1947)
│   ├── ...
│   ├── 311.0.3.3        → último chunk (t=1550-1551, band=0-12, y=2922-3896, x=2922-3896)
│   ├── band/
│   │   ├── .zarray
│   │   └── 0           → ["B1", "B2", ..., "SCL"]
│   └── time/            → coordinate arrays
├── y/
│   ├── .zarray
│   └── 0.0             → coordenadas Y comprimidas
└── x/
    ├── .zarray
    └── 0.0             → coordenadas X comprimidas
```

**Cada archivo `i.j.k.l` es auto-contenido**: un bloque comprimido con blosc que puedo leer sin tocar los demás. El nombre codifica la posición del chunk en el array N-dimensional.

### Propiedades clave

1. **N-dimensional por diseño**: `(time, band, y, x)` es una estructura de primera clase. No hay que abrir N archivos.
2. **Chunking explícito**: el usuario elige las dimensiones de cada bloque. Cambiar los chunks cambia radicalmente el rendimiento de acceso.
3. **Compresión por chunk**: cada bloque se comprime independientemente. Si un chunk tiene 90% NaN (nubes), zstd+bitshuffle lo comprime a casi nada.
4. **Consolidated metadata**: `.zmetadata` reúne todos los `.zarray` y `.zattrs` en un solo archivo. Una lectura HTTP para descubrir todo el layout.
5. **Append-friendly**: `mode='a', append_dim='time'` permite escribir batches sin reescribir todo el array.

---

## 3. Diferencias estructurales

### Anatomía de un dato: cómo se almacena un píxel

```
GeoTIFF (1 imagen, 1 banda):
┌──────────────────────────────────────────────────┐
│  Header + IFD + Tags + Tiles comprimidos (LZW)  │
│  Todo en 1 archivo. Para leer 1 píxel,          │
│  hay que localizar el tile y decomprimirlo.      │
└──────────────────────────────────────────────────┘
Peso: ~4-50 MB por archivo

Zarr (1 chunk, 5 timestamps × 13 bandas × 974×974):
┌──────────────────────────────────────────────────┐
│  Blosc header (16 bytes) + zstd compressed data  │
│  Archivo auto-contenido, leer solo este file.    │
└──────────────────────────────────────────────────┘
Peso: ~10-30 MB por chunk (depende de nubosidad)
```

### Patrones de acceso comparados

| Operación | GeoTIFF (1552 archivos) | Zarr (1 store, chunks 5,13,974,974) |
|---|---|---|
| **Serie temporal** de 1 pixel: `pixel[:, j, i]` | Abrir 1552 archivos, leer tile de cada uno → ~1552 I/O | Leer 312 chunks (1552/5) → 312 I/O, cada chunk tiene 5 timestamps contiguos |
| **1 imagen completa**: `imagen[t, :, :, :]` | Abrir 1 archivo, leer todo → 1 I/O | Leer ~16 chunks (4×4 espaciales) → 16 I/O |
| **1 banda temporal**: `banda[b, :, :]` en 1 fecha | Abrir 1 archivo, leer 1 banda → 1 I/O | Leer ~16 chunks espaciales → 16 I/O |
| **Subregion espacial**: `[:, :, y1:y2, x1:x2]` | Abrir 1552 archivos, crop cada uno → 1552 I/O | Leer solo los chunks que tocan la subregion → pocas I/O |

**Conclusión**: GeoTIFF gana en acceso a 1 imagen completa. Zarr gana en todos los patrones temporales o subregionales. Para Situaciones 2 y 3 (ConvLSTM, Kriging Espacio-Temporal) que operan sobre series temporales, Zarr es la única opción viable.

---

## 4. Compresión: por qué no es el punto

### Benchmark medido

Datos: Sentinel-2 L2A, tile T18NUJ, imagen 20210106T152641, ~3900×3900 píxeles.

| Formato/Codec | Archivo de prueba | Peso | Ratio vs raw | Nota |
|---|---|---|---|---|
| Sin compresión | `spectral.tif` (12 bandas, dense) | 347.6 MB | 1.0x | Baseline uint16 |
| GeoTIFF + LZW | `spectral.tif` | 408.6 MB | 0.85x | **Infla** por overhead de tiles + LZW sobre float32 denso |
| Zarr + LZ4 c5 | `data/0.0.0.0` | 196.8 MB | 1.77x | Rápido de escribir/leer |
| Zarr + zstd c5 bitshuffle | `data/0.0.0.0` | 131 MB | 2.65x | Mejor ratio sobre datos densos |
| | | | | |
| Sin compresión | `__B4.tif` (1 banda, sparse borde) | 28.97 MB | 1.0x | 70-95% NaN/ceros |
| GeoTIFF + LZW | `__B4.tif` | 1.99 MB | **14.6x** | LZW excelente sobre sparse |
| Zarr + zstd c5 bitshuffle | chunk | 2.31 MB | 12.6x | Bitshuffle explota exponente float32 |
| Zarr + LZ4 c5 | chunk | 3.97 MB | 7.3x | LZ4 débil sobre sparse |

**El GeoTIFF LZW de GEE comprime данныe sparse mejor que cualquier codec Zarr**. Pero esto es irrelevante porque:

1. El peso total del panel ya cumple el umbral de ≥50 GB con solo los GeoTIFFs (76.99 GB).
2. El Zarr no busca comprimir mejor que el GeoTIFF. Busca **reestructurar el acceso**.
3. Sobre datos densos (bandas interiores sin NaN), zstd+bitshuffle supera a LZW (2.65x vs 0.85x).

### Por qué zstd/c5/bitshuffle y no LZ4

| Codec | Ratio en S2 | Velocidad escritura | Velocidad lectura | Memo |
|---|---|---|---|---|
| LZ4 c5 | 7.3x en sparse, 1.77x en denso | **3-5 GB/s** | 5+ GB/s | Default en muchos tutoriales |
| zstd c5 bitshuffle | 12.6x en sparse, 2.65x en denso | 400-600 MB/s | 1-2 GB/s | **Nuestra elección** |

**Bitshuffle** no es un shuffle genérico: reorganiza los bytes de modo que todos los exponentes de float32 quedan contiguos, luego las mantissas. Sobre datos satelitales donde píxeles vecinos tienen valores similares (ej: un cuerpo de agua tiene reflectancia ~0.02-0.05 en toda su extensión), los exponentes son idénticos → runs largos → zstd los comprime extremadamente bien.

**Nivel 5** (c5) es el sweet spot: nivel 9 comprime ~5% más pero es 3x más lento en escritura. Nivel 1 es rápido pero deja ~20% de compresión en la mesa.

---

## 5. Por qué estos chunks y no otros

### Especificación del array S2

```
Shape:    (1552, 13, 3897, 3897)
Dtype:    float32 (4 bytes)
Fill:     NaN
Source:   ~19,400 GeoTIFFs → 1 Zarr store
```

Peso sin compresión: `1552 × 13 × 3897 × 3897 × 4 bytes = ~120 GB`
Peso con zstd/bitshuffle (estimado): ~87 GB (ratio ~1.4x sobre planar float32 con NaN)

### Criterios de diseño

| Criterio | Importancia | Explicación |
|---|---|---|
| **Acceso temporal** | Crítica | Situación 3 (Kriging) lee `pixel[t1:t2, :, j, i]`. Requiere pocos chunks por slice temporal. |
| **Acceso espacial (subregion)** | Alta | Situación 2 (ConvLSTM) lee `[:, :, y1:y2, x1:x2]` para subregiones. |
| **Acceso multiespectral** | Alta | Cálculos de NDVI, índices, color falso leen todas las bandas en 1 timestamp. |
| **Número total de archivos** | Alta | HF Bucket y GCS funcionan mal con >100K archivos. Objetivo: <10K chunks de datos. |
| **Tamaño por chunk** | Media | Chunks <10 MB penalizan por overhead de HTTP. Chunks >200 MB penalizan distribución. Ideal: 15-50 MB. |
| **RAM por batch de escritura** | Alta | Droplet tiene 4 GB RAM. El batch debe caber en memoria con margen para Python. |

### Alternativas evaluadas

#### Alternativa A: `(1, 1, 512, 512)` — 1 imagen, 1 banda, 512×512

```
Chunks totales: 1552 × 13 × 8 × 8 = 1,291,264
Peso por chunk: ~1 MB
Acceso temporal 1 pixel: 1552 chunks
Archivos totales: ~1.3M
```

**Problemas**: Más de 1 millón de archivos. Imposible gestionar en cualquier bucket. Overhead de HTTP request por chunk destruye el rendimiento. Acceso temporal requiere miles de requests.

#### Alternativa B: `(1, 13, 1024, 1024)` —_chunks del intento anterior

```
Chunks totales: 1552 × 1 × 4 × 4 = 99,328
Peso por chunk: ~50 MB (sin comprimir)
Acceso temporal 1 pixel: 1552 chunks (1 por timestamp)
Archivos totales: ~100K
```

**Problemas**: 
1. 99K archivos supera el límite soft de 10K de HF Dataset.
2. Acceso temporal ineficiente: para leer 5 timestamps consecutivos se leen 5 chunks diferentes en vez de 1.
3. No aprovecha la coherencia temporal: 5 imágenes consecutivas de S2 sobre la misma zona tienen ~60-80% de píxeles sin cambios (suelo, vegetación permanente), la compresión inter-temporal ahorra ~15-20%.

#### Alternativa C: `(5, 13, 974, 974)` — elegida

```
Dimensiones del array:  (1552, 13, 3897, 3897)
Dimensiones del chunk:  (5, 13, 974, 974)
Chunks en eje time:      ceil(1552/5)  = 312
Chunks en eje y:         ceil(3897/974) = 4
Chunks en eje x:         ceil(3897/974) = 4
Total data chunks:       312 × 1 × 4 × 4 = 7,808
Peso por chunk:          ~15-30 MB comprimido (varía con nubosidad)
Peso sin compresión:    5 × 13 × 974 × 974 × 4 = ~235 MB
```

**Ventajas**:
- **7,808 chunks de datos** + ~25 metadata = ~7,833 archivos totales. Bien bajo el límite de 10K.
- **Acceso temporal eficiente**: `pixel[:, j, i]` toca solo `(312 × 1 × 1) = 312` chunks. Cada chunk trae 5 timestamps contiguos — la LSTM los consume en secuencia.
- **Acceso multiespectral en 1 I/O**: todas las 13 bandas dentro del chunk. NDVI = `(B8-B4)/(B8+B4)` se calcula dentro del mismo chunk sin leer nada extra.
- **Subregiones espaciales**: una región de 512×512 píxeles (como la que usa el encoder ViT) toca 4 chunks (1 cuadrante de 974×974). Si el modelo lee 5 timestamps, son solo 4 chunks.
- **Chunk size de 15-30 MB** comprimido: óptimo para HTTP Range requests y descarga selectiva.
- **Batch de escritura = 5 timestamps = ~2.4 GB RAM**: cabe cómodamente en 4 GB con overhead de Python.

#### Alternativa D: `(10, 13, 512, 512)` — más paralelismo temporal

```
Total data chunks: ceil(1552/10) × 1 × 8 × 8 = 9,920
Peso por chunk: ~30-60 MB comprimido
RAM por batch: ~4.7 GB (apretado en 4 GB)
```

**Problemas**: 
1. Casi 10K chunks (al límite).
2. 4.7 GB por batch excede la RAM disponible (4 GB droplet).
3. Chunks de 30-60 MB son más grandes de lo ideal para descarga selectiva.

#### Alternativa E: `(1, 13, 3897, 3897)` — máximo agrupamiento espacial

```
Total data chunks: 1552 × 1 × 1 × 1 = 1,552
Peso por chunk: ~50-80 MB comprimido
Acceso temporal: 1552 chunks (1 por timestamp)
```

**Problemas**: 
1. No aprovecha coherencia temporal: 5 timestamps consecutivos leen 5 chunks completos.
2. Acceso a subregiones espaciales obliga a leer todo el chunk de 3897×3897.
3. Cada chunk de ~1.5 GB sin comprimir genera picos de 1.5 GB en descompresión.

### Cálculo de 974×974

La dimensión espacial del array es 3897×3897. Necesitamos que:
- `3897 % y_chunk == 0` (idealmente, para no tener bordes irregulares)
- O al menos que `ceil(3897 / y_chunk)` sea un número pequeño

`3897 / 4 = 974.25` — no es entero. Pero `ceil(3897/974) = 4` chunks con el último de `3897 - 3×974 = 3897 - 2922 = 975` píxeles. Zarr maneja esto nativamente: el último chunk en cada eje puede ser más pequeño.

Otras opciones de y_chunk:
- `512` → `ceil(3897/512) = 8` → `8×8 = 64` chunks espaciales × 1552 temporales = **99,328 datos chunks** (el problema original)
- `780` → `ceil(3897/780) = 5` → `5×5 = 25` chunks espaciales × 312 temporales = **9,750** (cerca del límite)
- `974` → `ceil(3897/974) = 4` → `4×4 = 16` chunks espaciales × 312 temporales = **4,992** (óptimo)
- `1299` → `ceil(3897/1299) = 3` → `3×3 = 9` chunks espaciales × 312 temporales = **2,808** (pocos, pero chunk size ~330 MB, peor distribución)

**974** es el valor que minimiza chunks (4×4=16 espaciales) manteniendo el chunk size en el rango óptimo de 15-50 MB comprimido (~235 MB sin comprimir → ~15-30 MB con zstd/bitshuffle).

### Resumen de la decisión

| Parámetro | Valor | Por qué |
|---|---|---|
| `time_chunk` | 5 | Kriging lee series de ~5-30 pasos. 5 steps/batch = 312 chunks temporales (pocos), pero cada chunk contiene una secuencia de 5 timestamps útil para LSTM. |
| `band_chunk` | 13 (todas) | Índices espectrales (NDVI, AOD, color) operan sobre múltiples bandas simultáneamente. Mantener las 13 bandas en 1 chunk evita lecturas extra. |
| `y_chunk = x_chunk` | 974 | Genera 4×4 = 16 chunks espaciales. Puzorra exactitud en bordes: Zarr soporta chunks irregulares. Tamaño sin comprimir ~235 MB → ~15-30 MB comprimido. |
| Compressor | blosc/zstd/c5/bitshuffle | Mejor ratio sobre float32 con NaN. Bitshuffle explota la estructura de exponentes IEEE 754. Nivel 5 equilibra ratio y velocidad. |

---

## 6. Comparación directa GeoTIFF vs Zarr para este proyecto

### Especificación del panel S2

| Propiedad | GeoTIFF (raw) | Zarr (panel) |
|---|---|---|
| **Archivos** | 19,400 (1 por banda-imagen) | ~7,833 |
| **Peso total** | 76.99 GB | ~87 GB (proyectado) |
| **Compresión** | LZW (server-side GEE) | blosc/zstd/c5/bitshuffle |
| **Dimensiones** | Implícito (2D + metadata) | Explícito (4D: time×band×y×x) |
| **Acceso temporal** | O(n_timestamps) files | O(n_time_chunks) chunks |
| **Acceso espacial** | 1 file → todo o crop GDAL | Selectivo por chunk |
| **Source-of-truth** | Sí (formato nativo GEE) | No (derivado) |
| **Auditable contra API** | Sí (pixel-a-pixel) | Requiere verificación de pipeline |
| **ConvLSTM-friendly** | No (1552 opens por época) | Sí (312 reads por época) |
| **Kriging-friendly** | No (serie temporal = 1552 seeks) | Sí (312 chunks secuenciales) |

### Viabilidad según las Situaciones del proyecto

**Situación 1 — Pipeline de ingesta**: la conversión GeoTIFF → Zarr es el paso final del pipeline. El Zarr es outputs, el GeoTIFF es source-of-truth. Ambos se almacenan. Costo: ~$3.28/mes en GCS Standard para 164 GB.

**Situación 2 — ConvLSTM para predicción de contaminación**: el modelo lee secuencias temporales de imágenes satelitales para predecir NO₂/SO₂/O₃. Con Zarr, una época de entrenamiento que muestrea subregiones de `5×13×256×256` lee solo 4 chunks espaciales (974×974 × 4). Con GeoTIFF, abriría 5 archivos de ~4 MB cada uno por banda, total 65 archivos开放的 por minibatch. No viable en entrenamiento distribuido.

**Situación 3 — Kriging Espacio-Temporal**: lee `pixel[t1:t2, :, j, i]` para interpolar series en puntos sin monitor. Con Zarr, esto toca `(312 time_chunks × 1 band_chunk × 1 y_chunk × 1 x_chunk) = 312` chunks. Con GeoTIFF, requiere abrir 1552 archivos y leer 1 píxel de cada uno. El overhead de I/O hace el Kriging prohibitivo (~1552 seeks vs ~312).

### Costo computacional de la conversión

| Recurso | Cantidad | Nota |
|---|---|---|
| Tiempo | ~11 horas | Droplet 4 vCPU, 4 GB RAM, batch_size=5 |
| RAM pico por batch | ~2.4 GB | `5 timestamps × 13 bandas × 3897² × 4 bytes` |
| Reads GCS | 19,400 objects | ~4 MB c/u |
| Writes GCS | ~7,833 objects | ~15-30 MB c/u |
| Costo GCS egress | ~$0 | Dentro de GCP (same region) |

---

## 7. Anatomía de un chunk Zarr

El archivo `data/0.0.0.0` en `panel.zarr/` contiene:

```
Bytes 0-15:   Blosc header
              [0-3]  version, flags, typesize
              [4-7]  uncompressed size (4 bytes → uint32 → max 4 GB)
              [8-11] block size (974 × 974 × 13 × 5 × 4 = 247,438,480 bytes)
              [12-15] compressed size
Bytes 16-N:   Zstd-compressed bitshuffle'd data
              Bitshuffle ordena: exponents[0..N], mantissa[0..N]...
              Zstd comprime las runs de exponents idénticos
```

**Decodificación paso a paso**:
1. `zarr` lee `.zmetadata` (1 request HTTP) → conoce shape, chunks, dtype, compressor
2. Calcula qué chunks tocar para la solicitud `[t1:t2, b1:b2, y1:y2, x1:x2]`
3. GET `data/{t_chunk}.{b_chunk}.{y_chunk}.{x_chunk}` (1 request HTTP por chunk)
4. Blosc decompress: lee header → extrae zstd payload → zstd_decompress → bitshuffle_unshuffle → float32 array

---

## 8. Referencias

1. [Zarr v2 specification](https://zarr-specs.readthedocs.io/en/latest/) — formato usado (zarr_format=2)
2. [Zarr v3 specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/v3.0.html) — próxima versión
3. [Cloud Optimized GeoTIFF spec](https://www.cogeo.org/) — formato source-of-truth
4. [GDAL GeoTIFF driver](https://gdal.org/drivers/raster/gtiff.html) — opciones de compresión y tiling
5. [Blosc meta-compressor](https://www.blosc.org/) — architechtura de blosc (shuffle, bitshuffle, codecs)
6. [Bitshuffle filter](https://github.com/kiyo-masui/bitshuffle) — paper original y explicación de exponente-first ordering
7. [Zstd compression](https://github.com/facebook/zstd) — ratios y velocidades de referencia
8. [xarray + Zarr for geoscience](https://docs.xarray.dev/en/stable/user-guide/io.html#zarr) — caso de uso Pangeo
9. [STAC + COG vs Zarr (Pangeo discourse)](https://discourse.pangeo.io/) — cuándo usar cada formato
10. [Pangeo Cloud Data](https://pangeo.io/) — datasets de referencia con chunking N-dimensional
11. [PDF asignatura](../../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf) — Situación 1, p. 4: requisito de Zarr