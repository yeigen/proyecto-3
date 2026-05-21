# Flujo del proyecto GeoVision-CLIP Cali

Cronología y estado del trabajo. Se actualiza con cada hito.

**Plazo total**: 10 días. **Equipo**: 3 personas. **Hardware**: T4 Kaggle (30 h GPU/cuenta/semana = 90 h grupo/semana).

---

## Estado actual (fecha de corte: 2026-05-16)

**Situación 1**: ✓ casi cerrada. Panel ≥ 50 GB con margen, 6 fuentes verificadas, conversión lossless bit-perfect.
**Situación 2**: ✓ muestreo completo. 5,000 tiles balanceados con pre-filtrado SCL GPU, O₃ relajado a p95 + SCL>0.3 (31 fechas únicas, justificado por Fishman 2010). Pendiente: subir como `edwardsx/geovision-tiles-sit2` + entrenamiento CLIP+SAE.
**Situación 3**: ⏸ pendiente.

---

## Hitos completados

### Hito 1 — Inventario y verificación del panel (Situación 1)

- ✓ 6 paneles Zarr publicados en Kaggle Dataset [`juanjoseorozcolopez/geovision-fuentes`](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes) (89.73 GB, 8,848 archivos en Kaggle; 8,847 archivos de datos en manifest).
- ✓ Shapes verificadas vía API: `S2 (1552,13,3897,3897)`, `S5P (~25K,n,36,36)`, `ERA5 (43824,8,2,2)`, `MODIS (1826,4,43,43)`.
- ✓ DAGMA: 107,291 filas, 10 estaciones (9 DAGMA + 1 CVC Yumbo).
- ✓ Cobertura temporal panel: 2021-01-03 a 2025-12-31 (5 años exactos).
- ✓ Cobertura DAGMA: 2020-01-01 a 2024-12-31. **Overlap útil con panel: 4 años (2021-2024)**.
- ✓ Conversión lossless bit-perfect verificada (B1/B4/B8/SCL `diff_max = 0`).
- ✓ Documentación consolidada en `docs/DATASETS.md`, `docs/JUSTIFICACIONES.md`, `docs/REFERENCIAS.md`, `docs/conceptos/`.

### Hito 2 — Conceptos básicos documentados

14 conceptos en `docs/conceptos/` cubriendo: atmósfera, contaminantes (NO₂/SO₂/O₃/PM), meteorología (BLH, viento, RH), teledetección (resolución espacial/temporal/espectral), productos satelitales (L1/L2/L3, DOAS, ERA5), geografía (BBox/proyecciones). Con fórmulas, ejemplos del proyecto y papers.

### Hito 3 — Pipeline de muestreo estratificado para Sit 2

Notebook `scripts/muestreo_sit2.ipynb` validado con test de 25 tiles (5/5 por clase).

**Tres técnicas usadas según la clase** (documentado en `docs/MUESTREO_SIT2.md`):

1. **Guiada por percentil S5P** (NO₂ > p90, SO₂ > p90, O₃ > p99) → 3 clases de contaminación.
2. **Aleatoria + filtro NDVI > 0.6** → `vegetacion_densa`.
3. **Proximidad a estaciones DAGMA (radio 1 km) + NDVI < 0.3** → `suelo_urbano`.

**Pseudo-labels**: percentiles S5P como criterio de clase (PDF Sit 2 p.6 lo autoriza explícitamente).

**Contexto físico pre-computado** en `tiles_meta.parquet`: 8 columnas ERA5 (T2m, Td2m, u10, v10, BLH, RH850, psurf, precip) + 3 columnas MODIS (AOD_047, AOD_055, WV) por cada tile. Cobertura 25/25 en el test.

**Caveat documentado**: valores MODIS AOD no físicos (falta `scale_factor=0.001` del producto MCD19A2 v6.1). Impacto cero en Sit 2; pendiente decisión para Sit 3.

### Hito 4 — Justificaciones técnicas defensibles

Documentadas en `docs/JUSTIFICACIONES.md` con tabla de decisiones y trade-offs:

- BBox extendido para capturar Yumbo + corredor industrial.
- ERA5 atmosférico (no ERA5-Land, que no contiene BLH/RH).
- HARP saltado (L3 GEE ya es post-`bin_spatial`).
- 13 bandas S2 (B1 + B2-B12 + SCL).
- ThreadPool sobre Dask (cuello de botella es API GEE).
- 4 años overlap DAGMA (no 5).
- 10 estaciones (no 9).
- Muestreo guiado defensa: PDF lo autoriza + Mahajan 2018 + Liu 2024 RemoteCLIP.
- SCL ≥ 0.3 (nubosidad tropical).
- Suelo urbano por DAGMA (Reichstein 2019).

---

## Roadmap pendiente (estimación 35-40 h trabajo activo)

### Día 1-2 (hoy): cierre Situación 1 + muestreo Situación 2

| Tarea | Tiempo | Quién | Estado |
|---|---:|---|---|
| Manifest JSON con MD5 de todos los archivos del panel | 30 min | 1 persona | ⏳ pendiente |
| Notebook EDA Sit 1 con ≥ 8 visualizaciones | 4 h | 1 persona | ⏳ parcial (PNGs sueltos) |
| Diagrama arquitectura cloud (PNG/SVG) | 1 h | 1 persona | ⏳ pendiente |
| Reporte costos cloud | 30 min | 1 persona | ⏳ pendiente |
| **Muestreo full Sit 2** (`N_POR_CLASE = 1000`) | **~7 h** | corriendo | ⏳ EN CURSO |
| Subir `tiles_train.npz` + `tiles_meta.parquet` como nueva versión del Kaggle Dataset | 15 min | 1 persona | ⏳ tras muestreo |

### Día 3-5: entrenamiento del modelo (Situación 2)

| Tarea | Tiempo | Hardware |
|---|---:|---|
| Entrenamiento CLIP fine-tune + 2 SAEs (50 epochs, batch 64-128) | **4-6 h** | T4 |
| Curvas de entrenamiento (loss, sparsity, recall por epoch) | incluido | T4 |
| AFE (PCA + rotación Varimax) sobre embeddings | 15 min | CPU |
| AFC (CFI/RMSEA/SRMR vía `semopy`) | 15 min | CPU |
| Análisis interpretabilidad SAE (top neuronas por clase) | 30 min | CPU |
| Checkpoint `.pt` + MD5 verificable | 5 min | — |

### Día 5-7: deep learning + geoestadística (Situación 3)

| Tarea | Tiempo | Hardware |
|---|---:|---|
| Generar secuencias ConvLSTM (8 frames por estación, sobre embeddings) | 1 h | CPU |
| Entrenamiento ConvLSTM bidir (hidden=128, 2 capas, AdamW lr=1e-4) | 2-4 h | T4 |
| Ajuste variograma teórico (esférico/exponencial) sobre residuos | 30 min | CPU |
| OK3D Kriging Espacio-Temporal con `pykrige` | 30 min | CPU |
| Validación LOO-CV (10 estaciones × 3 contaminantes × 3 horizontes T+1/T+3/T+7) | 2 h | CPU |
| Análisis Moran I + LISA con `pysal.esda` | 30 min | CPU |
| Reporte tabla RMSE/MAE/R² | incluido | — |
| Mapas de gradiente + incertidumbre Kriging | 30 min | CPU |
| K-Means clustering sobre superficies predichas (perfiles tipológicos) | 30 min | CPU |

### Día 7-9: frontend + despliegue

| Tarea | Tiempo | Stack |
|---|---:|---|
| Backend FastAPI: endpoints `/predict`, `/validate` | 4 h | Python |
| Frontend React + Vite + Leaflet (mapa interactivo, 9 mapas gradient, slider temporal, tooltips, opacidad incertidumbre) | **1 día** | React |
| Dockerfile multi-stage | 1 h | Docker |
| Despliegue HuggingFace Spaces o Render (free tier) | 2 h | HF |
| Verificación latencia < 8 s end-to-end | 30 min | — |

### Día 9-10: informe + cierre

| Tarea | Tiempo |
|---|---:|
| Informe técnico PDF (15-25 páginas según PDF) con resumen, panel, modelo, validación, ablación, despliegue, discusión | 1 día |
| Verificación checkpoint MD5 consistente entre los 3 integrantes | 30 min |
| Repositorio Git: README final + estructura limpia | 2 h |
| Empaquetar entrega .zip con todo | 30 min |
| Defensa oral preparada (~ 7 puntos clave en `conceptos/README.md`) | 2 h |

---

## Restricciones operativas a recordar

1. **Frontend NO puede ser Streamlit/Gradio** (penalización -30 % despliegue ≈ -3 % total). Usar React + Vite + Leaflet (1 día de dev).
2. **Manifest JSON con MD5** es entregable obligatorio (PDF p.5).
3. **Checkpoints `.pt` con MD5 reproducible** entre los 3 integrantes (penalización -20 % modelo si difieren).
4. **LOO-CV obligatorio** (penalización -60 % Sit 3 si no se hace).
5. **No pasar concentraciones S5P como input directo al modelo** (penalización -25 % por data leakage). Se usan solo como pseudo-label.

---

## Bonificaciones disponibles (+12 puntos máx)

| Bonus | Puntos | Esfuerzo | Recomendado |
|---|---:|---|---|
| Modo oscuro frontend | +2 | 30 min | ✓ trivial |
| Audio Whisper como 3ª modalidad | +3 | 1 día | ✗ no compensa |
| Análisis equidad espacial por estrato socioeconómico | +4 | 4 h | ✓ si hay tiempo |
| Comparación con OMI/AURA o GOME-2 | +3 | 4 h | ✗ requiere bajar dataset adicional |

**Total recomendado de bonus**: modo oscuro (+2) + equidad espacial (+4) = +6 puntos por ~5 h extra de trabajo.

---

## Decisiones explícitas tomadas (ordenadas cronológicamente)

| Fecha | Decisión | Razón | Doc |
|---|---|---|---|
| 2026-05-07 | BBox 0.35°×0.35° (no el del PDF) | Captura Yumbo + Acopi + cultivos caña | `JUSTIFICACIONES.md` |
| 2026-05-07 | ERA5 atmosférico vs ERA5-Land | ERA5-Land no tiene BLH/RH | `JUSTIFICACIONES.md` |
| 2026-05-07 | HARP saltado | L3 GEE ya está re-grillado | `JUSTIFICACIONES.md` |
| 2026-05-08 | xee sobre `Export.image.toCloudStorage` | Bypass de cuota tasks GEE | `JUSTIFICACIONES.md` |
| 2026-05-10 | Chunks Zarr `(5,13,974,974)` | Sweet spot HTTP Range + ConvLSTM-friendly | `conceptos/geotiff-vs-zarr.md` |
| 2026-05-14 | Panel publicado en Kaggle Dataset | Acceso libre + sin egress GCS | `DATASETS.md` |
| 2026-05-16 | 4 años overlap DAGMA (2021-2024) | Parquet SISAIRE cubre 2020-2024 | `JUSTIFICACIONES.md` |
| 2026-05-16 | 10 estaciones en uso (9 DAGMA + Yumbo CVC) | Captura pluma industrial | `JUSTIFICACIONES.md` |
| 2026-05-16 | Muestreo guiado por S5P para 3 clases contaminación | Random daba 0/5; estratificación supervisada | `MUESTREO_SIT2.md` |
| 2026-05-16 | Muestreo DAGMA-guided para `suelo_urbano` | Definición operacional de "zona urbana" | `MUESTREO_SIT2.md` |
| 2026-05-16 | SCL ≥ 0.3 (relajado de 0.5) | Nubosidad tropical 60-80 % | `JUSTIFICACIONES.md` |
| 2026-05-16 | Contexto ERA5+MODIS pre-computado en meta | Acelera Sit 3 | `JUSTIFICACIONES.md` |
| 2026-05-16 | `N_POR_CLASE = 1000` (5,000 tiles totales) | Holgura para Recall@5≥0.85 y N>5×features en AFC | `FLUJO_PROYECTO.md` |
| 2026-05-16 | Pre-filtrado SCL GPU (1 vez, cache en CSV) | Veg/urbano pasaron de 4%/7% a 42%/58% aceptación | `MUESTREO_SIT2.md` |
| 2026-05-16 | O₃ umbral p95 + SCL>0.3 (vs p99 + SCL>0.5) | p99+0.5 dio solo 11 fechas únicas (81% en top-5); p95+0.3 da 31 fechas | `MUESTREO_SIT2.md` |
| 2026-05-16 | Dataset separado `edwardsx/geovision-tiles-sit2` | Evita reemplazar el panel base (83 GiB) al subir versión | `MUESTREO_SIT2.md` |

---

## Riesgos abiertos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Sesión Kaggle se cae durante muestreo de 7 h | Pérdida de `aceptados` en memoria | Guardar parcial tras cada clase guiada (TODO) |
| MODIS scale_factor pendiente para Sit 3 | Predicciones PM erróneas si se usa AOD raw | Aplicar `× 0.001` + máscara `_FillValue=-28672` antes de Kriging |
| Streamlit como atajo tentador | -3 % penalización | Compromiso: React + Vite + Leaflet desde el inicio del frontend |
| `manifest.json` con MD5 no existe aún | -3 % proyecto si falta | Script de 30 min al cierre de Sit 1 |
| Notebook EDA Sit 1 no consolidado | -X% rúbrica | Consolidar PNGs existentes + las 4 visualizaciones obligatorias del PDF |

---

## Próximo paso inmediato

1. Esperar a que el muestreo termine (ETA ~7 h desde inicio).
2. Verificar conteos finales por clase y cobertura ERA5/MODIS.
3. Descomentar la celda final del notebook para guardar `tiles_train.npz` + `tiles_meta.parquet`.
4. Subir como **nueva versión** del Kaggle Dataset `juanjoseorozcolopez/geovision-fuentes` (`kaggle datasets version -m "tiles_train v1: 5000 tiles 64x64x13 estratificados + meta enriquecido"`).
5. Avisar al equipo para empezar el entrenamiento CLIP+SAE en una sesión T4 separada.
