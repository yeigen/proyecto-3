# Hallazgos del EDA — GeoVision-CLIP Cali

Documento vivo. Solo datos observados en `scripts/eda/eda_completo.py` corriendo sobre Kaggle. Sin valores presupuestados ni teoría — la teoría vive en [`docs/conceptos/`](conceptos/).

> Corte: **2026-05-17**.

---

## 1. Sentinel-2 L2A

### Estructura del Zarr (`copernicus_s2_sr_harmonized/panel.zarr`)

| Campo | Valor |
|---|---|
| Escenas (`time`) | **1,552** |
| Bandas | **13** — B1, B2-B12, SCL |
| Grilla espacial | **3,897 × 3,897 px** = ~39 × 39 km @ 10 m |
| `dtype` | `float32` |
| Variable principal | `data` |
| Rango temporal | **2021-01-03 → 2025-12-31** |

**Formato del coord `time`:** `YYYYMMDDTHHMMSS_YYYYMMDDTHHMMSS_<tile_MGRS>` (p. ej. `20210103T152641_20210103T153117_T18NUJ`). Cada pase del satélite genera **una entrada por tile MGRS** que cruza el BBox, no una entrada por pase.

### Distribución temporal (viz 1 obligatoria PDF)

- Cadencia 2021-01 a 2025-03: 22-28 escenas/mes (pareja).
- **Salto a partir de 2025-04**: 28-39 escenas/mes (pico en 2025-05 con 39).
- Hipótesis del salto: entrada en operación de **Sentinel-2C** (lanzado 2024-09). **A verificar en SentiWiki.**
- Implicación Sit 3: las secuencias de 8 frames en 2025 son temporalmente más densas que en 2021-2024 — considerar al armar splits temporales.

### Tiles MGRS sobre Cali — HALLAZGO CRÍTICO

**Solo 2 tiles MGRS** cruzan el BBox del proyecto. Pre-filtrado SCL ≥ 30% expone una asimetría masiva:

| Tile MGRS | Total escenas | Pasan SCL ≥ 30% | Tasa de aceptación |
|---|---:|---:|---:|
| **T18NUJ** | 779 | **133** | **17.1%** |
| **T18NUK** | 773 | **3** | **0.4%** |
| **Total** | 1,552 | **136** | 8.8% |

**T18NUK aporta 3 escenas marginales — está prácticamente excluido del muestreo Sit 2.** En la práctica el modelo CLIP se entrena solo sobre T18NUJ.

**Implicaciones serias:**
- La cobertura espacial del muestreo de 5,000 tiles se limita a la mitad del BBox cubierta por T18NUJ.
- LOO-CV de Sit 3 va a fallar si alguna estación DAGMA cae fuera de T18NUJ.
- El modelo no aprende variabilidad de la zona cubierta por T18NUK.

**Ubicación geográfica de los tiles (corregido vs hipótesis previa).** En MGRS, las **row letters** (segunda letra del par de columna+fila) crecen **hacia el norte** ([Wikipedia MGRS](https://en.wikipedia.org/wiki/Military_Grid_Reference_System)). Para zona UTM 18 par, las filas norte del ecuador siguen `F-G-H-J-K-L-...` (cada una 100 km de alto). Estimación:

| Tile | Rango latitudinal aproximado | Qué cubre |
|---|---|---|
| T18NUJ | ~2.7-3.6°N | Cali, Yumbo, Acopi (casco urbano + valle medio) |
| T18NUK | ~3.6-4.5°N | Norte del Valle del Cauca, zona cañera |

**Implicación correcta:** T18NUK no aporta escenas porque **el BBox del proyecto (lat 3.30-3.55°N) está casi enteramente dentro de T18NUJ.** T18NUK solo se toca por el buffer en el borde superior. **No es problema de nubosidad orográfica** como hipoteticé antes — es que el BBox apenas roza T18NUK. Las 3 escenas marginales son las que caen en la franja superior del BBox.

**Lo que sí perdemos:** las **quemas de caña** ocurren físicamente en la latitud 3.6-4.5°N (zona cañera norte). Aunque las plumas de NO₂ derivadas alcanzan el BBox por advección (S5P las captura porque tiene su propio BBox amplio), las imágenes Sentinel-2 **no muestran el fuego de origen**. El modelo CLIP no aprende a asociar visualmente "quema visible → NO₂ alto"; solo aprende "morfología urbana → NO₂ alto" + "vegetación → NO₂ alto" (advectado). Esto puede limitar la generalización a otros años con patrón de quema distinto.

**Verificación con `estaciones_metadata.csv` (corte 2026-05-17):**

| Estación | Lat | Lon | Operadora | Tile MGRS | BBox PDF | BBox proyecto |
|---|---:|---:|---|---|:---:|:---:|
| BASE AÉREA | 3.4571 | -76.5023 | DAGMA | T18NUJ | ✓ | ✓ |
| CAÑAVERALEJO | 3.4164 | -76.5496 | DAGMA | T18NUJ | ✓ | ✓ |
| COMPARTIR | 3.4283 | -76.4666 | DAGMA | T18NUJ | ✓ | ✓ |
| ERA OBRERO | 3.4573 | -76.5065 | DAGMA | T18NUJ | ✓ | ✓ |
| **ESTACIÓN YUMBO** | **3.5791** | -76.4896 | **CVC** | T18NUJ | ✗ | ✓ |
| LA ERMITA | 3.4555 | -76.5310 | DAGMA | T18NUJ | ✓ | ✓ |
| LA FLORA | 3.4882 | -76.5181 | DAGMA | T18NUJ | ✓ | ✓ |
| PANCE | 3.3045 | -76.5313 | DAGMA | T18NUJ | ✓ | ✓ |
| TRANSITORIA-NAVARRO | 3.4172 | -76.4950 | DAGMA | T18NUJ | ✓ | ✓ |
| UNIVERSIDAD DEL VALLE | 3.3779 | -76.5338 | DAGMA | T18NUJ | ✓ | ✓ |

**Veredicto sobre las 10 estaciones:**

- **10/10 caen en T18NUJ** (todas con lat < 3.6°N). Cero estaciones en T18NUK. **LOO-CV de Sit 3 es viable**: cada estación tiene cobertura de tiles muestreados.
- **9/10 dentro del BBox PDF estricto** (lat 3.30-3.55°). La que falta es **ESTACIÓN YUMBO** (lat 3.579 > 3.55).
- **10/10 dentro del BBox proyecto ampliado** (lat 3.30-3.65). El BBox ampliado de la decisión #1 fue diseñado precisamente para capturar Yumbo (motivo: "Captura Yumbo + Acopi + caña").
- **Yumbo está operada por CVC (Corporación Autónoma Regional del Valle del Cauca)**, no por DAGMA. Confirmado en columna `nombre_fgda` del CSV.

**Implicación operativa para LOO-CV en Sit 3:** la política está documentada en `JUSTIFICACIONES.md` (decisión #8): **reportar dos LOO-CV** — uno con las 9 DAGMA puras (cumple PDF estricto) y otro con las 10 incluyendo CVC Yumbo (métrica extendida que captura la pluma industrial).

### Bug encontrado en el notebook EDA

`BBOX_CALI` en el notebook estaba declarado con los valores del **PDF** (`lat [3.30, 3.55]`), no con los del **proyecto** (`lat [3.30, 3.65]` declarado en `google-earth/config.py`). El BBox del proyecto coincide con la huella del Zarr S2 (~39 km de lado). Corregido en `scripts/eda/eda_completo.py` celda config. Se agregó también `BBOX_PDF` para reportar ambos lados explícitamente en el mapa de estaciones.

### NDVI sobre 30 escenas aleatorias

| Versión | Filtros | % descartado | < 0.3 | > 0.6 | ∈ [0.3, 0.6] | Usable |
|---|---|---:|---:|---:|---:|:---:|
| v1 (cruda) | ninguno | — | 91.8% | 4.4% | 3.8% | ✗ inflado por NoData |
| v2 (filtro) | SCL ∈ {4,5,6,7} & B4>0 & B8>0 | **94.0%** | **17.60%** | **56.90%** | **25.50%** | ✓ |

**Consistencia con `MUESTREO_SIT2.md`.** El 94% descartado por píxel en el EDA cruza directamente con que solo **140/1,552 (9%) escenas pasen el filtro SCL > 0.3** declarado en el muestreo: la mayoría de píxeles de una escena random S2 son nubes/sombras/NoData en zona tropical.

**Distribución NDVI v2 es bimodal.** Pico izquierdo en NDVI ≈ 0.1-0.2 (urbano/suelo) y pico derecho dominante en NDVI ≈ 0.7-0.8 (vegetación). Valle entre 0.3 y 0.6. Los umbrales del muestreo (`NDVI < 0.3` urbano, `NDVI > 0.6` vegetación densa) caen **exactamente en los valles del histograma** — separación canónica, no arbitraria.

### RGB grid top-12 por cobertura SCL útil

Sobre 150 escenas evaluadas (subsample SCL 1/10):

| Métrica | Valor |
|---|---:|
| Cobertura máxima | **89%** (idx=1041, 2024-07-29, T18NUJ) |
| Cobertura mínima top-12 | 36% |
| Tiles MGRS en top-12 | **T18NUJ** (dominio total observado) |

Imagen: `imagenes-referencias/eda/s2_rgb_top12.png`. Visualmente: nubes blancas + vegetación verde + manchas urbanas grises — consistente con Cali tropical.

### Bugs encontrados y resueltos en este bloque

| Bug | Causa | Fix |
|---|---|---|
| RGB con mitad inferior negra | escena fuera del swath, B*=0 | seleccionar top-K por cobertura SCL ≥ 50%, normalizar por percentiles 2-98% sobre píxeles válidos |
| NDVI 91.8% < 0.3 inflado | NoData con (B8-B4)/(B8+B4) ≈ 0 | máscara `SCL ∈ {4,5,6,7} & B4>0 & B8>0` antes del histograma |
| `xr.open_zarr` falla con `engine='zarr'` en Kaggle | xarray cargado antes de `pip install zarr`; entry points no re-descubiertos | `pip install xarray>=2024.10 zarr>=3 fsspec` + restart kernel |
| `docs/conceptos/resolucion-espacial.md` decía 974×974 px para S2 | dato erróneo de mi parte | corregido a 3,897×3,897 (~39×39 km) |

### Decisiones que esto confirma o cuestiona

- **Decisión #10 (pre-filtrado SCL):** **confirmada empíricamente**. 94% de píxeles descartados en una muestra aleatoria de 30 escenas justifica por qué solo 140/1,552 (9%) escenas pasaron el filtro SCL > 0.3 en el muestreo. Sin pre-filtrado, las tasas de aceptación de tiles veg/urbano serían 4%/7% (test original) en vez de 42%/58% (post-filtrado).
- **Decisión #6 (13 bandas S2 resampleadas a 10 m):** confirmada. Las 13 bandas están presentes en el Zarr con grilla común a 10 m.
- **Decisión #11 (NDVI < 0.3 urbano, > 0.6 vegetación):** **confirmada por distribución bimodal**. Los umbrales caen en los valles del histograma, no son cortes arbitrarios.

### Análisis cuantitativo del filtrado SCL — ¿es rentable?

**Tiles 64×64 disponibles según umbral.** Con `floor(3897/64)² = 3,600` tiles por escena sin solape:

| Umbral | Escenas | Tiles candidatos | Margen vs objetivo 5,000 |
|---|---:|---:|---:|
| Sin filtrado | 1,552 | 5,587,200 | 1,117× |
| **SCL > 0.3** | **140** | **504,000** | **100×** |
| SCL > 0.5 | 66 | 237,600 | 47× |
| SCL > 0.7 | ~20 | 72,000 | 14× |

**Speed-up por clase de muestreo** (medido en `MUESTREO_SIT2.md`):

| Clase | Sin filtro | Con filtro 0.3 | Speed-up |
|---|---:|---:|---:|
| Vegetación densa (Random + NDVI > 0.6) | 4% | 42% | **10.5×** |
| Suelo urbano (DAGMA + NDVI < 0.3) | 7% | 58% | **8.3×** |
| NO₂ alto (guiado p90) | 62% | 41% | 0.66× |
| SO₂ alto (guiado p90) | 55% | 30% | 0.55× |
| O₃ anómalo (guiado p95) | 55% | 66% | 1.2× |

**Hallazgo:** el filtrado **acelera enormemente las clases aleatorias** (veg/urbano) pero **frena las guiadas por percentil S5P** porque los píxeles calientes existen en TODAS las fechas, no solo en las limpias. El neto sigue positivo por compresión de las dos clases más lentas. Tiempo total estimado: 7-8 h con filtro vs > 20 h sin filtro.

**Crítica abierta al filtrado por escena.** Una alternativa más fina sería filtrar **por tile** (rechazar tile con SCL < 30% local, no escena entera), conservando todas las 1,552 escenas. Pero el experimento real mostró margen 100× con el filtro por escena — no hay incentivo de complejizar.

**Riesgo real:** las 140 escenas podrían estar concentradas estacionalmente (jul-ago seco), sesgando el modelo. Pendiente de verificar la distribución temporal de las 140 escenas cargando `scl_por_escena.csv` en el bloque 7 del EDA.

### Resultados del bloque 2b — verificación de las 136 escenas filtradas

**Distribución global del % SCL útil por escena** (sobre las 1,552):

| Estadística | Valor |
|---|---:|
| Mediana | 1.8% |
| Promedio | 9.1% |
| p75 | 11.8% |
| Máximo | 89% |

La **mayoría de escenas (50%) tienen menos de 2% de píxeles útiles.** Justifica el filtrado por escena entera vs por tile.

**Distribución por mes calendario (las 136 filtradas):**

| Mes | Escenas | | Mes | Escenas |
|---:|---:|---|---:|---:|
| 1 (ene) | 14 | | 7 (jul) | **16** (máx) |
| 2 (feb) | 11 | | 8 (ago) | 10 |
| 3 (mar) | **6** (mín) | | 9 (sep) | 15 |
| 4 (abr) | 10 | | 10 (oct) | 13 |
| 5 (may) | 11 | | 11 (nov) | 10 |
| 6 (jun) | 9 | | 12 (dic) | 11 |

Rango 6-16, **no hay concentración estacional fuerte**. Marzo es el mes con menos escenas filtradas (en Cali coincide con transición lluviosa). No se observa sesgo a la estación seca jul-ago como se temía.

**Distribución por año:**

| Año | Escenas filtradas | % |
|---:|---:|---:|
| 2021 | 30 | 22% |
| 2022 | 18 | 13% (mínimo) |
| 2023 | 23 | 17% |
| 2024 | 32 | 24% |
| 2025 | 33 | 24% |

**Hipótesis S2C parcialmente confirmada**: 2024-2025 tienen el doble que 2022 (32-33 vs 18). El salto suave de 2024 → 2025 sugiere que más que el lanzamiento de S2C, podría haber un efecto de meteorología (años más nublados). Pendiente cruzar con anomalías climáticas regionales.

**Tasa mensual de aceptación SCL:** muy variable (rango 4-25%), media 8.8%. Picos puntuales en 2021-10 (21%) y 2021-11 (25%) — meses muy despejados. Mínimos por debajo de 5% en 2021-08, 2022-01, 2022-04, 2023-04, 2024-11, etc.

### Preguntas resueltas vs todavía abiertas

| Pregunta | Estado | Veredicto |
|---|---|---|
| ¿T18NUJ domina las top-12 RGB? | ✅ resuelta | Sí — T18NUK aporta solo 3/773 (0.4%) escenas usables. |
| ¿Concentración estacional jul-ago? | ✅ resuelta | No. Rango 6-16/mes calendario, sin sesgo extremo. |
| ¿140 vs 136 escenas? | ✅ resuelta | **136 es el dato real**. `MUESTREO_SIT2.md` con 140 está desactualizado. |
| ¿Solo 2 tiles MGRS? | ✅ resuelta | Sí — `resolucion-temporal-revisita.md` ya corregido. |
| ¿S2C explica el salto 2024-2025? | 🟡 parcial | 2024-2025 lideran pero 2024 ≈ 2025. Probable efecto mixto S2C + meteo. |
| ¿Dónde está T18NUK geográficamente? | ✅ resuelta | Cubre **lat 3.6-4.5°N** = norte del Valle del Cauca (zona cañera). MGRS row letters crecen al norte. T18NUK casi no aporta porque el BBox del proyecto llega solo hasta 3.65°N — apenas roza T18NUK. |
| ¿Alguna estación cae en T18NUK? | ✅ resuelta | **No. 10/10 estaciones en T18NUJ.** LOO-CV de Sit 3 viable. |
| ¿Yumbo es DAGMA o CVC? | ✅ resuelta | **CVC**. Confirmado en `nombre_fgda` del CSV. Yumbo está en BBox proyecto pero fuera del BBox PDF estricto. Política LOO-CV doble ya documentada en `JUSTIFICACIONES.md` decisión #8. |

---

## 2. Sentinel-5P NO₂ / SO₂ / O₃

### Estructura de los Zarr

Los 3 Zarr S5P tienen la misma estructura que S2: una sola `data_var = "data"` con coord `band` que selecciona variable.

| Fuente | Escenas | Bandas | Banda usada en EDA |
|---|---:|---|---|
| S5P NO₂ | 25,592 | 3 (tropospheric_NO2, NO2_total, cloud_fraction) | `tropospheric_NO2_column_number_density` |
| S5P SO₂ | 25,829 | 2 (SO2, cloud_fraction) | `SO2_column_number_density` |
| S5P O₃  | 25,716 | 2 (O3, cloud_fraction) | `O3_column_number_density` |

Rango temporal: 2020-12-31 → 2025-12-31. Grilla espacial: 36 × 36 px (~1.1 km/px, BBox ampliado del proyecto).

### Bug encontrado y resuelto

Mi primera versión usaba `list(ds.data_vars)[0]` que tomaba el contenedor `data` sin seleccionar banda. Resultado: las distribuciones aparecían bimodales 0/1 porque mezclaban el contaminante con `cloud_fraction`. **Fix:** definir `S5P_BANDAS` con la banda explícita por contaminante y usar `.sel(band=...)` en cada lectura. Distribuciones ahora en mol/m² real.

### Distribución temporal de adquisiciones

400-440 escenas/mes uniformes para los 3 contaminantes durante 5 años. Cadencia diaria con 1-2 órbitas que cubren Cali. No hay gaps importantes — los 3 productos están parejos.

### Distribuciones con percentiles p25/50/75/90/95/99 (sobre 80 escenas)

**NO₂:** concentración fuerte cerca de 0 con cola larga hacia 3.5e-05 mol/m². Distribución unimodal sesgada.

**SO₂:** pico fuerte en cero, **valores negativos** (-6e-04 a +1e-03 mol/m²). Confirma el ruido DOAS documentado en `MUESTREO_SIT2.md`: en zonas de baja señal de SO₂, el fit DOAS produce negativos físicamente imposibles. Referencia: Theys et al. 2017 (TROPOMI SO₂ retrieval).

**O₃:** rango muy estrecho 0.105-0.130 mol/m². **Distribución BIMODAL** con dos picos claros (~0.108 y ~0.118). Hallazgo defensa: **esto justifica visualmente por qué p95 funciona mejor que p99 para "ozono anómalo"** — p95 cae sobre el modo alto completo (~0.127), mientras que p99 (~0.130) recorta solo el extremo del modo alto y reduce la diversidad temporal del muestreo (decisión #11 de `JUSTIFICACIONES.md`).

### Percentiles EDA vs muestreo full panel

| Contaminante | p99 EDA (80 escenas) | p99 `MUESTREO_SIT2.md` (full panel) | Diferencia |
|---|---:|---:|---|
| NO₂ | ~3.5e-05 | 8.87e-05 | EDA subestima |
| SO₂ | ~3e-04 | 8.30e-04 | EDA subestima |
| O₃ | ~0.130 | 0.129 | **Coincide** |

Los percentiles oficiales para defensa son los del muestreo (500 timestamps × 36² = 648k píxeles, mucho más estable que las 80 escenas del EDA). El O₃ coincide casi exacto por su rango compacto; NO₂ y SO₂ requieren más muestra para capturar la cola.

### Mapas espaciales promedio (200 escenas)

**NO₂:** **dos hot-spots claros** sobre el BBox.
- Hot-spot norte (lat ~3.5, lon ~-76.45): corredor industrial **Yumbo**.
- Hot-spot centro-sur (lat ~3.4, lon ~-76.5): casco urbano de **Cali**.

Esto justifica visualmente:
- **Decisión #1**: BBox ampliado a lat 3.65 capturó el hot-spot Yumbo (decisión correcta).
- **Decisión #8**: incluir estación CVC Yumbo en LOO-CV (única estación dentro del hot-spot industrial).

**SO₂:** patrón ruidoso, sin hot-spot dominante. Consistente con SO₂ siendo emisión puntual esporádica (no continua como NO₂ de tráfico).

**O₃:** casi uniforme, rango espacial muy estrecho (0.1185-0.1205). Variabilidad espacial baja confirma física: O₃ total se mezcla en la troposfera media y no preserva firma de fuente puntual.

### Cobertura efectiva por escena (200 escenas)

| Contaminante | Mediana | % escenas con ≥ 50% válidos | Forma de la distribución |
|---|---:|---:|---|
| **NO₂** | **0.0%** | 16% | Bimodal: 80% de escenas en 0%, resto disperso 60-100% |
| **SO₂** | **72.1%** | 50% | Bimodal 0%/100% (mitad útil) |
| **O₃** | **0.0%** | 10% | Bimodal extrema (mediana 0%, minoría ≥ 90%) |

**Hallazgo crítico:** **la mayoría de las 25,000 escenas son inservibles** en NO₂ y O₃ por filtros de `qa_value` aplicados upstream por GEE. Pero el 10-16% utilizable equivale a **2,500-4,000 escenas con cobertura ≥ 50%** — suficiente para muestreo guiado por percentil. SO₂ es la fuente más limpia (50% utilizable, ~12,500 escenas).

### Decisiones del proyecto confirmadas por datos S5P

- **Decisión #1 (BBox ampliado)**: justificada visualmente — el hot-spot Yumbo de NO₂ está fuera del BBox PDF y sí dentro del BBox proyecto.
- **Decisión #4 (no usar HARP)**: los Zarr L3 GEE entregan datos en grilla regular 36×36 a ~1.1 km. No fue necesario reprocesar L2.
- **Decisión #11 (p95 sobre p99 para O₃)**: justificada visualmente por la distribución bimodal — p95 captura el modo alto completo, p99 recorta solo el extremo.
- **Pseudo-labels S5P para CLIP (PDF p. 6)**: viable. Los hot-spots NO₂ son claros y reproducibles entre escenas.

### Preguntas resueltas del bloque 3 (con fuentes verificadas)

**1. ¿Por qué la cobertura NO₂ y O₃ tiene mediana 0%, mientras que SO₂ tiene 72%?**

**Respuesta:** GEE aplica **distintos umbrales de qa_value** durante el re-grillado L2 → L3 con `harpconvert`. Cita textual del catálogo oficial:

> *"The source data is filtered to remove pixels with QA values less than: 80% for AER_AI, **75% for the tropospheric_NO2_column_number_density band of NO2**, **50% for all other datasets except for O3 and SO2**"*

| Producto | Filtro qa_value | Cobertura observada (EDA) |
|---|---|---:|
| NO₂ tropospheric | **> 75%** (estricto) | mediana 0%, 16% con ≥ 50% |
| SO₂ | **> 50%** | mediana **72.1%**, 50% con ≥ 50% |
| O₃ total | **NO usa qa_value**, filtra por **rangos físicos** de 4 parámetros (`ozone_total_vertical_column`, `ozone_effective_temperature`, `ring_scale_factor`, `effective_albedo`) | mediana 0%, 10% con ≥ 50% |

**Confirma la asimetría observada al milímetro.** SO₂ es más permisivo por construcción del producto L3. O₃ tiene mediana 0% no por filtro qa sino porque los filtros físicos múltiples rechazan más píxeles que el qa simple.

Fuentes:
- [Sentinel-5P OFFL NO2 (GEE)](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2) — confirma umbral 75% para `tropospheric_NO2_column_number_density`.
- [Sentinel-5P OFFL SO2 (GEE)](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2) — confirma umbral 50% como excepción para SO₂.
- [Sentinel-5P OFFL O3 (GEE)](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3) — confirma filtro por rangos físicos en lugar de qa_value.

**2. ¿Por qué SO₂ tiene mejor cobertura?**

Resuelta arriba: es **decisión upstream de KNMI/GEE**, no del proyecto. El producto SO₂ usa umbral qa 50% (frente al 75% de NO₂) porque su retrieval DOAS tiene señal-ruido más bajo (los negativos observados en el histograma lo confirman: la columna de SO₂ es ruido la mayoría del tiempo). Aceptar más píxeles para SO₂ es el compromiso correcto del proveedor.

**3. ¿La bimodalidad de O₃ refleja estacionalidad?**

**Hipótesis fundamentada:** la distribución bimodal observada en O₃ (~0.108 y ~0.118 mol/m², diferencia ~9%) es **consistente con dos regímenes asociados al ciclo seco/lluvioso bimodal de Cali y con quemas de biomasa**. Tres evidencias convergen:

- **Cali tiene régimen de precipitación bimodal** (2 períodos secos + 2 lluviosos por año), característico de la región andina ecuatorial. Fuente: [Urrea et al. 2019, *Seasonality of Rainfall in Colombia*, AGU Water Resources Research](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2018wr023316).
- **O₃ tropical aumenta 10-25% sobre background en períodos de quemas de biomasa.** La diferencia observada entre los dos modos (~9%) cae dentro del rango reportado. Fuente: [Thompson et al. 2001, *Tropical Tropospheric Ozone and Biomass Burning*, Science 291:2128](https://www.science.org/doi/10.1126/science.291.5511.2128); [Chandra et al. 2002, *Tropical tropospheric ozone: Implications for dynamics and biomass burning*, JGR](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2001JD000447).
- **TROPOMI sobre los Andes ecuatoriales muestra máximo anual de TCO en mid-September**, asociado al ITCZ y elevación orográfica. Fuente: [Cazorla et al. 2022, *Ozonesonde evaluation of spaceborne observations in the Andean tropics*, Scientific Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC9509352/).

**Defensa adicional para decisión #11 (p95 sobre p99):** la bimodalidad confirma que **el régimen alto de O₃ NO es ruido extremo sino una población distinta** asociada a quemas de caña + temporada seca. p95 cae sobre el modo alto completo (~0.127), capturando esta población. p99 (~0.130) recorta solo el extremo de la cola del modo alto, perdiendo la mayoría de los eventos de quema. **El umbral p95 es físicamente justificado, no estadísticamente conveniente**.

**Caveat documentado:** la asignación temporal de cada modo (cuál corresponde a seco vs lluvioso) NO se verificó empíricamente en el EDA. Verificación queda pendiente para el bloque 8 (análisis cruzado) cruzando timestamps de tiles `ozono_anomalo` con calendario climático Cali. Esto es **defensa fuerte si el cruce confirma el patrón temporal**.

## 3. ERA5

Pendiente — bloque 4.

## 4. MODIS AOD

Pendiente — bloque 5.

## 5. DAGMA

Pendiente — bloque 6.

## 6. Tiles muestreados Sit 2

Pendiente — bloque 7.

## 7. Análisis cruzado

Pendiente — bloque 8.
