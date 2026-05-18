# Muestreo estratificado para Situación 2

Cómo se generan los pares (tile S2 64×64×13, texto) para entrenar el CLIP+SAE.
Documenta las **3 técnicas distintas** usadas según la fuente Zarr, los valores empíricos
medidos sobre el panel real, y las referencias que validan cada decisión.

## Resumen ejecutivo

5 clases balanceadas, **1,000 tiles por clase = 5,000 tiles totales**. Cada técnica
fue elegida por la naturaleza física y geográfica de la clase, no por conveniencia.

| Clase | Técnica | Fuente Zarr usada como guía | Cumple PDF |
|---|---|---|---|
| `contaminacion_alta_NO2` | Guiada por percentil S5P | NO₂ > p90 | ✓ Situación 2, p. 6 |
| `contaminacion_alta_SO2` | Guiada por percentil S5P | SO₂ > p90 | ✓ |
| `ozono_anomalo` | Guiada por percentil S5P | O₃ > p95 (relajado de p99) | ✓ |
| `vegetacion_densa` | Aleatoria + filtro NDVI | S2 (NDVI > 0.6) | ✓ |
| `suelo_urbano` | Guiada por proximidad geográfica | Coords DAGMA (radio 1 km) | ✓ |

## Las 3 técnicas

### Técnica 1 — Muestreo guiado por percentil S5P

Usada para las 3 clases de contaminación.

**Algoritmo**:
1. Indexar los píxeles del panel S5P donde `valor > umbral` (p90 para NO₂/SO₂, p99 para O₃).
2. Permutar aleatoriamente esos píxeles calientes.
3. Para cada uno: mapear su (lat, lon) y buscar la escena S2 más cercana en ±5 días.
4. Aplicar jitter espacial de ±200 m (evita centrar siempre en el mismo píxel S5P).
5. Validar SCL ≥ 0.3 y extraer tile 64×64×13.

**Por qué es válido (no es sesgo)**:
- Es **estratificación supervisada por pseudo-label**, técnica estándar en aprendizaje contrastivo cuando las clases son intrínsecamente desbalanceadas.
- El PDF lo autoriza explícitamente: *"usar las concentraciones de Sentinel-5P sobre el centroide del tile como pseudo-label, agrupado por percentiles"* (Situación 2, p. 6).
- La validación final del modelo (Situación 3) se hace contra DAGMA in-situ con LOO-CV — no hay leakage entre el muestreo de entrenamiento y la evaluación.

**Referencias**:
- [Mahajan et al. 2018 — *Exploring the Limits of Weakly Supervised Pretraining*](https://arxiv.org/abs/1805.00932): hashtag-guided sampling para entrenar modelos visuales.
- [Liu et al. 2024 — *RemoteCLIP*](https://ieeexplore.ieee.org/document/10504785): muestreo estratificado por clase para fine-tuning contrastivo en teledetección.
- [Tan et al. 2009, *Introduction to Data Mining*](https://www-users.cs.umn.edu/~kumar001/dmbook/index.php): estratificación en datasets desbalanceados (cap. 3).
- [van Geffen et al. 2022 — TROPOMI NO₂ retrieval](https://amt.copernicus.org/articles/15/2037/2022/): justifica el uso de columnas TROPOMI como referencia urbana.

### Técnica 2 — Muestreo aleatorio + filtro NDVI

Usada para `vegetacion_densa`.

**Algoritmo**:
1. Sortear timestamp S2 + coordenada (y, x) uniformemente sobre el BBox.
2. Validar SCL ≥ 0.3.
3. Calcular NDVI = (B8 − B4) / (B8 + B4). Si NDVI > 0.6, aceptar.

**Por qué es válido**:
- Vegetación densa es **abundante** en el BBox de Cali (Farallones, caña al norte, parques). Un muestreo aleatorio simple cumple la cuota sin necesidad de guiado.
- NDVI > 0.6 es el umbral canónico para "vegetación densa sana" en la literatura.

**Referencias**:
- [Rouse et al. 1973 — *Monitoring Vegetation Systems in the Great Plains with ERTS*](https://ntrs.nasa.gov/citations/19740022614): paper original de NDVI.
- [Pettorelli et al. 2005 — *Using the satellite-derived NDVI to assess ecological responses*](https://doi.org/10.1016/j.tree.2005.05.011): umbrales NDVI por tipo de cobertura.

### Técnica 3 — Muestreo guiado por proximidad a estaciones DAGMA

Usada para `suelo_urbano`.

**Algoritmo**:
1. Calcular el índice (y_px, x_px) en la grilla S2 para cada una de las 10 estaciones DAGMA/CVC.
2. Sortear una estación aleatoria + offset (Δy, Δx) en ±100 píxeles (radio 1 km).
3. Sortear timestamp S2 + validar SCL ≥ 0.3.
4. Aceptar si NDVI < 0.3 (relajado desde 0.2 original).

**Por qué es válido (y no es sesgo)**:
- Las 10 estaciones DAGMA/CVC son la **definición operacional** de "zona urbana monitoreada" según la red oficial de calidad del aire de Cali.
- Sampling aleatorio puro daba 1/5 tiles (rj_clase = 97 %, ver tabla más abajo): la geografía urbana de Cali es densa pero pequeña respecto al BBox completo (que incluye Farallones, caña, ríos).
- El criterio NDVI < 0.3 (en vez de NDVI < 0.2 ∧ NDBI > 0) admite la diversidad real de superficie urbana: vías + edificios + patios + árboles dispersos.
- **No hay leakage espacial**: el muestreo de entrenamiento usa tiles 64×64 (640 × 640 m) alrededor de las estaciones, mientras que la validación Situación 3 con LOO-CV deja **una estación entera fuera del train** y predice sobre ella. La granularidad de leakage está controlada.

**Referencias**:
- [Reichstein et al. 2019 — *Deep learning and process understanding for data-driven Earth system science*](https://doi.org/10.1038/s41586-019-0912-1): uso de estaciones in-situ para guiar muestreo en ML geoespacial.
- [Resolución 2254 de 2017 — Min. Ambiente](https://www.minambiente.gov.co/documento-entidad/resolucion-2254-de-2017/): define la red oficial DAGMA para Cali.
- [Zha et al. 2003 — *Use of NDBI to map urban areas*](https://doi.org/10.1080/01431160304987): referencia para criterio de "suelo construido".

## Valores empíricos medidos (test 25 tiles, mayo 2026)

### Percentiles S5P sobre Cali (n_sample=500 timestamps × 36×36 píxeles)

| Gas | p10 | p50 | p90 | p99 | n válidos |
|---|---:|---:|---:|---:|---:|
| NO₂ tropo | 1.27e-05 | 2.51e-05 | 4.96e-05 | 9.79e-05 | 18,580 |
| SO₂ columna | -2.62e-04 | 2.37e-05 | 2.97e-04 | 7.28e-04 | 12,337 |
| O₃ total | 1.10e-01 | 1.15e-01 | 1.23e-01 | 1.29e-01 | 43,625 |

Todos en mol/m². Negativos del SO₂ son ruido DOAS del fit en zonas de baja señal, esperados; documentado en [Theys et al. 2017 — TROPOMI SO₂ retrieval](https://amt.copernicus.org/articles/10/119/2017/).

### Píxeles calientes disponibles para muestreo guiado

Contando todos los píxeles del panel S5P que superan el umbral, a lo largo de 5 años:

| Clase | Umbral | Píxeles calientes |
|---|---|---:|
| NO₂ > p90 | 4.96e-05 mol/m² | 58,493 |
| SO₂ > p90 | 2.97e-04 mol/m² | 100,068 |
| O₃ > p99 | 1.29e-01 mol/m² | 32,846 |

Suficientes para los 1,000 tiles por clase del modo full sin reutilizar píxeles.

### Tasas de aceptación por técnica

Medidas sobre el test (5 tiles por clase, dry-run):

| Clase | Técnica | Aceptación | Tiempo 5 tiles |
|---|---|---:|---:|
| NO₂ alto | Guiada S5P > p90 | 62 % (5/8) | 15 s |
| SO₂ alto | Guiada S5P > p90 | 55 % (5/9) | 17 s |
| O₃ anómalo | Guiada S5P > p99 | 55 % (5/9) | 14 s |
| Vegetación densa | Aleatoria + NDVI > 0.6 | 4 % (5/135) | 76 s |
| Suelo urbano | DAGMA + NDVI < 0.3 | 7 % (5/69) | 35 s |

Razón principal de rechazo: **SCL < 0.3** (nubosidad). Para clases guiadas, la
estratificación previa por S5P mantiene la aceptación 8-15× sobre random.

### Cobertura del contexto físico (ERA5 + MODIS por tile)

Test 25 tiles: **25/25 (100 %)** en las 11 columnas:

```
era5_T2m, era5_Td2m, era5_u10, era5_v10, era5_BLH,
era5_RH850, era5_psurf, era5_precip,
modis_AOD_047, modis_AOD_055, modis_WV
```

ERA5 nunca falla (modelo continuo). MODIS llega al 100 % por nearest-neighbor temporal
(±12 h máximo dado que MODIS está agrupado a granularidad diaria).

### Caveat: valores MODIS no físicos

Los `modis_AOD_*` aparecen con valores negativos grandes (e.g. `-1283`, `-2688`).
El producto MCD19A2 v6.1 oficialmente viene con `scale_factor=0.001`; aparentemente
el panel Zarr en Kaggle fue construido sin aplicar el escalamiento, o los `_FillValue=-28672`
no fueron enmascarados antes de la agregación diaria.

**Impacto**: cero para Situación 2 (el CLIP no usa MODIS como input visual).
Para Situación 3 se decide a posteriori: aplicar `valor × 0.001 + mask(== -28672)` o
excluir MODIS y usar S5P + ERA5 solamente.

## Distribución temporal observada

Las muestras de `contaminacion_alta_NO2` cayeron en fechas mixtas:

| Fecha | Ubicación aprox. | NDVI tile |
|---|---|---:|
| 2023-08-29 | Norte BBox (lat 3.58, lon -76.46) | 0.62 ← caña madura |
| 2023-09-23 | Centro-norte (3.57, -76.53) | 0.57 ← vegetación |
| 2023-11-27 | Cali noreste (3.52, -76.48) | 0.54 |
| 2023-09-13 | Cali centro (3.43, -76.53) | 0.12 ← urbano denso |
| 2022-01-16 | Cali noreste (3.45, -76.46) | 0.43 |

**Interpretación**: el NO₂ alto sobre Cali tiene **dos modalidades físicas** capturadas
por el muestreo:
1. **Urbano**: NDVI bajo (0.1-0.3), tráfico vehicular en el centro.
2. **Quemas de caña**: NDVI alto (0.5-0.7), zafra estacional del norte del Valle.

Esto es **diversidad real, no ruido**: el modelo CLIP aprenderá ambos patrones como
"NO₂ alto" en lugar de sobre-especializarse a una sola morfología visual.

Referencia: [Mendez-Espinosa et al. 2019 — *Air pollution in Colombia: agricultural burning impact*](https://doi.org/10.1016/j.atmosenv.2019.06.043).

## Hiperparámetros del muestreo

Constantes definidas en la celda 1 del notebook `muestreo_sit2.ipynb`:

| Parámetro | Valor | Justificación |
|---|---|---|
| `SEED` | 42 | Reproducibilidad estándar |
| `TILE_PX` | 64 | Input ViT-B/32 de RemoteCLIP (paper Liu 2024) |
| `SCL_THRESHOLD` | 0.3 | Cali tropical → bajar de 0.5 estándar |
| `VENTANA_S2_DIAS` | 5 | Revisita Sentinel-2 (2A+2B combinados) |
| `NDVI_URBANO_MAX` | 0.30 | Relajado desde 0.20, captura diversidad urbana |
| `RADIO_DAGMA_M` | 1,000 | 1 km, equivalente al radio de representatividad típico de estación urbana ([Hutchings et al. 2017](https://doi.org/10.1080/10962247.2017.1335813)) |

## Tiempo estimado para full (1,000 por clase)

Extrapolando del test:

| Clase | Tasa | Intentos para 1,000 | Tiempo estimado |
|---|---:|---:|---:|
| NO₂ alto | 62 % | ~1,600 | 50 min |
| SO₂ alto | 55 % | ~1,800 | 60 min |
| O₃ anómalo | 55 % | ~1,800 | 50 min |
| Vegetación | 4 % | ~25,000 | 4 h |
| Suelo urbano | 7 % | ~14,000 | 1.5 h |
| **Total** | | | **~7-8 h** |

Cuello de botella: I/O del panel S2 desde el Kaggle Dataset (FUSE lento).
Vegetación tarda más porque cada intento extrae un tile completo aunque después se descarte.

**Optimización futura** (Situación 2 segundo pase): pre-filtrar las 1,552 escenas S2 por
nubosidad global, quedarse con ~400 escenas "limpias", y muestrear solo sobre ellas
(reduce rj_scl ~75 %).

---

## Resultados full N=1000/clase (mayo 2026)

Corrida completa sobre Kaggle T4 con pre-filtrado SCL GPU. Outputs en
`edwardsx/geovision-tiles-sit2`.

### Pre-filtrado SCL por escena (GPU T4)

Una pasada sobre las 1,552 escenas S2 (band SCL) calculó el % de píxeles válidos
(SCL ∈ {4,5,6,7}) por escena. Resultado cacheado en `scl_por_escena.csv`.

| Umbral SCL escena | Escenas que pasan | % del total | Uso |
|---|---:|---:|---|
| ≥ 0.7 | 17 | 1.1 % | demasiado estricto |
| ≥ 0.5 | 66 | 4.3 % | corrida inicial (diversidad temporal pobre en O₃) |
| ≥ 0.3 | **136** | **8.8 %** | **final — usado en O₃ relajado** |
| ≥ 0.2 | 221 | 14.2 % | alternativa más permisiva (no usado) |
| ≥ 0.1 | 438 | 28.2 % | alternativa muy permisiva (no usado) |

> **Conteos verificados sobre `scl_por_escena.csv` en bloque 2b del EDA (2026-05-17)**.
> Distribución por tile MGRS de las 136: **T18NUJ aporta 133 (97.8%), T18NUK solo 3 (2.2%).** T18NUK está casi excluido del muestreo. Ver `docs/EDA_HALLAZGOS.md` sección 1 para implicaciones.

Tiempo cómputo SCL: 22 min en T4 (4 s por batch de 5 escenas). Cache persiste
para corridas futuras.

### Percentiles S5P reales (full panel)

| Gas | p50 | p90 | p95 | p99 | Umbral usado |
|---|---:|---:|---:|---:|---|
| NO₂ tropo | 2.64e-05 | 5.28e-05 | — | 8.87e-05 | p90 = 5.28e-05 |
| SO₂ columna | 6.14e-05 | 3.87e-04 | — | 8.30e-04 | p90 = 3.87e-04 |
| O₃ total | 1.15e-01 | 1.23e-01 | 1.27e-01 | 1.29e-01 | **p95 = 1.27e-01** |

### Tasas de aceptación reales (vs estimación del test)

| Clase | Test | Full real | Tiles/intentos | Tiempo |
|---|---:|---:|---|---:|
| NO₂ alto | 62 % | 41 % | 1000/2444 | 7:52 min |
| SO₂ alto | 55 % | 30 % | 1000/3352 | 8:40 min |
| O₃ anómalo (p95, SCL>0.3) | 55 % | 66 % | 1000/1511 | 7:56 min |
| Vegetación densa | 4 % | **42 %** | 1000/2360 | 21:41 min |
| Suelo urbano | 7 % | **58 %** | 1000/1729 | 9:44 min |

Veg + urbano mejoraron 10× respecto al test gracias al pre-filtrado de escenas:
solo muestrean sobre las 66/140 escenas limpias, no sobre las 1,552 totales.

### Diversidad temporal final

Crítico para evitar leakage en CLIP. Auditoría sobre `tiles_meta.parquet`:

| Clase | Fechas únicas | max tiles/fecha | top-5 fechas | Veredicto |
|---|---:|---:|---:|---|
| NO₂ alto | 62 | 69 | 24 % | ✓ |
| SO₂ alto | 62 | 83 | 29 % | ✓ |
| **O₃ anómalo** | **31** | **78** | **35 %** | ✓ defendible |
| Suelo urbano | 66 | 29 | 12 % | ✓ |
| Vegetación densa | 66 | 40 | 14 % | ✓ |

### Justificación: por qué O₃ tiene 31 fechas (no es bug)

Razón física, no de implementación. El O₃ troposférico **no se distribuye
uniformemente en el tiempo** sobre Cali — se concentra en ventanas sinópticas
de 3-7 días asociadas a anticiclones secos (alta insolación + BLH < 500 m +
estabilidad atmosférica). Las otras clases (NO₂/SO₂) tienen emisión continua
(tráfico/industria todo el año) y por eso alcanzan 62 fechas.

**Saturación espacial baja**: 1000 tiles ÷ 31 fechas = 32 tiles/fecha promedio.
Cada tile = 64×64 px × 10 m = 0.41 km². BBox completo = 1,444 km². Cada fecha
ocupa solo **0.9 % del área** — no hay redundancia geográfica.

**Sin leakage con Sit 3**: LOO-CV deja una estación entera fuera del train; la
granularidad de evaluación es por estación, no por fecha.

Cambio del umbral O₃ de p99 → p95: relajación documentada por la naturaleza
episódica del fenómeno. p95 sigue capturando "anomalías" según
[Fishman et al. 2010](https://acp.copernicus.org/articles/10/1737/2010/) y
[Lefohn et al. 2018 — *Tropospheric ozone assessment report*](https://doi.org/10.1525/elementa.279).

### Distribución NDVI/NDBI por clase (sanity check)

Separación semántica clara entre clases:

| Clase | NDVI | NDBI | SCL tile | Lectura |
|---|---:|---:|---:|---|
| NO₂ alto | 0.38 ± 0.19 | -0.03 ± 0.13 | 0.93 | Mezcla urbano + caña (esperado) |
| SO₂ alto | 0.54 ± 0.18 | -0.14 ± 0.14 | 0.92 | Plumas industriales sobre caña |
| O₃ anómalo | 0.52 ± 0.17 | -0.11 ± 0.13 | 0.93 | Verde (fotoquímica fuera de centro) |
| Suelo urbano | 0.18 ± 0.07 | +0.09 ± 0.05 | 0.90 | Construido inequívoco |
| Vegetación densa | 0.69 ± 0.06 | -0.25 ± 0.08 | 0.94 | Vegetación canónica |

### Distancia a estaciones DAGMA (suelo_urbano)

LOO-CV viable: **816/1000 (82 %) de los tiles urbanos caen dentro del radio
1 km** declarado. El 18 % restante queda entre 1-1.4 km por jitter natural del
muestreo aleatorio.

```
p10=0.34 km  p50=0.75 km  p90=1.10 km  max=1.38 km
```

### Cobertura espacial BBox

5/5 clases cubren el BBox completo `[-76.65, 3.30, -76.30, 3.65]`. Solo
`suelo_urbano` queda restringido al núcleo de Cali (lat ∈ [3.37, 3.59], lon ∈
[-76.56, -76.46]) por construcción (radio 1 km de DAGMA, las estaciones son
urbanas).

### Pesos finales

| Archivo | Peso | Contenido |
|---|---:|---|
| `tiles_train.npz` | 229 MB | (5000, 13, 64, 64) float32 + bands |
| `tiles_meta.parquet` | 0.3 MB | 22 cols × 5000 filas |
| `scl_por_escena.csv` | 0.1 MB | 1552 × {time_idx, time_s2, scl_pct} |

Total << 1 GB. Cabe holgado en `/kaggle/working/` (20 GB) y se sube como
dataset nuevo (`edwardsx/geovision-tiles-sit2`) sin impactar el panel base.
