# Handoff GeoVision-CLIP Cali — estado y plan

Documento de transición para retomar el proyecto desde otro entorno (otro agente, otra máquina). Captura el estado al **2026-05-16** después del cierre del muestreo de Situación 2.

> **Antes de empezar cualquier tarea, leer en orden**:
> 1. Este archivo (`HANDOFF.md`).
> 2. [`AGENTS.md`](../AGENTS.md) — perfil del owner y reglas de trabajo.
> 3. [`docs/FLUJO_PROYECTO.md`](FLUJO_PROYECTO.md) — cronología y decisiones.
> 4. [`docs/JUSTIFICACIONES.md`](JUSTIFICACIONES.md) — defensas técnicas (sección final sobre N=5000 es nueva).
> 5. [`docs/MUESTREO_SIT2.md`](MUESTREO_SIT2.md) — sección final "Resultados full" tiene los números reales del muestreo cerrado.

---

## Estado actual (corte 2026-05-16)

| Situación | Estado | Bloqueante para Sit siguiente? |
|---|---|---|
| **Sit 1 — Panel satelital** | ✓ Cerrada en infraestructura. Falta solo entregables documentales (manifest, EDA, diagrama, costos). | No |
| **Sit 2 — CLIP+SAE** | ✓ Muestreo completo (5,000 tiles balanceados, ya subidos a Kaggle). Pendiente: entrenamiento. | Sí, bloquea Sit 3 |
| **Sit 3 — ConvLSTM+Kriging** | ⏸ Pendiente | — |
| **Frontend + despliegue** | ⏸ Pendiente (Día 7-9) | — |
| **Informe + defensa** | ⏸ Pendiente (Día 9-10) | — |

---

## Artefactos ya producidos (no rehacer)

### Datos remotos (públicos)

| Recurso | Path | Contenido |
|---|---|---|
| Kaggle Dataset | `juanjoseorozcolopez/geovision-fuentes` | Panel base 83.6 GiB (S2/S5P/ERA5/MODIS Zarr + DAGMA parquet) |
| Kaggle Dataset | `edwardsx/geovision-tiles-sit2` | **5,000 tiles + meta + cache SCL** (subido 2026-05-16) |
| Kaggle Notebook | `edwardsx/geo-vision-proyecto-3-muestreo` | Notebook activo del muestreo (público) |
| HF Bucket | `yeigen/fuentes-proyecto-3` | 5 paneles pequeños espejo (S2 vive solo en GCS por peso) |
| GCS | `gs://fuentes-proyecto-3` (proyecto `proyecto-analitica-3-495618`) | Source-of-truth GeoTIFFs |
| Droplet | `root@192.241.132.222` | SSH preconfigurada con EE creds + GCS ADC |

### Archivos en `edwardsx/geovision-tiles-sit2`

| Archivo | Peso | Shape / contenido |
|---|---:|---|
| `tiles_train.npz` | 229 MB | `data: (5000, 13, 64, 64) float32` + `bands: (13,) str` |
| `tiles_meta.parquet` | 0.3 MB | 22 cols × 5000 filas (clase, time_s2, lat, lon, ndvi, ndbi, scl_pct, no2, so2, o3, texto, era5_{8}, modis_{3}) |
| `scl_por_escena.csv` | 0.1 MB | 1552 escenas S2 × scl_pct (cache del pre-filtrado GPU) |

### Notebooks locales (versionados)

| Archivo | Rol |
|---|---|
| `EDA.ipynb` | EDA exploratorio de Sit 1 (parcial, falta consolidar) |
| `manifest/manifest.ipynb` | Generación de `manifest.json` con MD5 (parcial) |
| `scripts/muestreo_sit2.ipynb` | Versión inicial del muestreo (obsoleta, mantener por historia) |
| `scripts/notebook-kaggle/geovision-proyecto-3.ipynb` | **Espejo local del notebook Kaggle activo** (38 celdas, sincronizado tras el muestreo) |
| `scripts/notebook-kaggle/kernel-metadata.json` | Metadata Kaggle del kernel |

---

## Decisiones cerradas (no re-discutir)

Listas para defensa, documentadas con referencias en `JUSTIFICACIONES.md`:

| # | Decisión | Justificación corta | Doc |
|---|---|---|---|
| 1 | BBox 0.35°×0.35° (más amplio que PDF) | Captura Yumbo + Acopi + caña | `JUSTIFICACIONES.md` |
| 2 | Zarr `(5,13,974,974)` chunks | Sweet spot HTTP Range + ConvLSTM | `conceptos/geotiff-vs-zarr.md` |
| 3 | xee vs toCloudStorage | 5-15 min vs 30 días | `JUSTIFICACIONES.md` |
| 4 | ERA5 horario (no ERA5-Land) | ERA5-Land no tiene BLH/RH | `JUSTIFICACIONES.md` |
| 5 | HARP saltado | L3 GEE ya es post-`bin_spatial` | `JUSTIFICACIONES.md` |
| 6 | 13 bandas S2 (B1+B2-B12+SCL) | Resampleado a 10 m | `JUSTIFICACIONES.md` |
| 7 | 4 años overlap DAGMA (2021-2024) | Parquet SISAIRE cubre 2020-2024 | `JUSTIFICACIONES.md` |
| 8 | 10 estaciones (9 DAGMA + 1 CVC Yumbo) | Captura pluma industrial | `JUSTIFICACIONES.md` |
| 9 | `N_POR_CLASE = 1000` (5K tiles total) | Holgura 31× AFC, 2× Recall@5 | `JUSTIFICACIONES.md` |
| 10 | Pre-filtrado SCL GPU + cache CSV | Veg/urbano de 4/7 % → 42/58 % aceptación | `MUESTREO_SIT2.md` |
| 11 | O₃ umbral p95 + SCL>0.3 (vs p99+SCL>0.5) | p99+0.5 daba 11 fechas únicas (81 % top-5); p95+0.3 da 31 fechas | `MUESTREO_SIT2.md` |
| 12 | Dataset separado `edwardsx/geovision-tiles-sit2` | No tocar el panel base (83 GiB) al versionar | `MUESTREO_SIT2.md` |
| 13 | MODIS AOD raw sin scale_factor — caveat documentado | Impacto cero en Sit 2 (CLIP no usa MODIS). Decisión Sit 3 pendiente. | `JUSTIFICACIONES.md` |

---

## Lo que falta (priorizado por dependencia)

### Bloque A — Cierre Sit 1 (no bloquea Sit 2)

Entregables documentales, ~6 h. Hacerlo en paralelo al entrenamiento.

| Tarea | Esfuerzo | Output | Penalización si falta |
|---|---:|---|---|
| **Manifest JSON con MD5** de los 8,848 archivos del panel | 30 min | `manifest/manifest.json` | -3 % proyecto (PDF p.5) |
| **Notebook EDA Sit 1** con ≥ 8 visualizaciones consolidadas | 4 h | `EDA.ipynb` final | -X % rúbrica |
| **Diagrama arquitectura cloud** (PNG/SVG) | 1 h | `imagenes-referencias/arquitectura.png` | rúbrica |
| **Reporte costos cloud** (GCS, HF, Kaggle) | 30 min | sección en informe | rúbrica |

### Bloque B — Sit 2 entrenamiento (BLOQUEA Sit 3)

Notebook nuevo de entrenamiento. ~4-6 h GPU T4.

**Setup**:
- Kernel Kaggle nuevo, GPU T4, internet ON.
- `dataset_sources`: `juanjoseorozcolopez/geovision-fuentes` + **`edwardsx/geovision-tiles-sit2`**.
- Inputs: `tiles_train.npz` + `tiles_meta.parquet`.

**Tareas**:

| Tarea | Esfuerzo | Hardware | Output |
|---|---:|---|---|
| Cargar 5K tiles + tokenizar textos | 30 min | CPU | DataLoader |
| Fine-tune ViT-B/32 RemoteCLIP (50 epochs, batch 64-128) | 4-6 h | T4 | `clip_finetuned.pt` |
| Entrenar 2 SAEs sobre embeddings (256 neuronas) | 1 h | T4 | `sae.pt` |
| Curvas (loss, sparsity, recall@K por epoch) | incluido | T4 | PNGs |
| AFE (PCA + rotación Varimax) | 15 min | CPU | tabla factores |
| AFC (CFI/RMSEA/SRMR via `semopy`) | 15 min | CPU | tabla bondad ajuste |
| Análisis interpretabilidad SAE (top-k neuronas por clase) | 30 min | CPU | tabla por clase |
| Checkpoint `.pt` + MD5 verificable | 5 min | — | hash MD5 |

**Restricciones del PDF que NO romper**:
- No pasar concentraciones S5P como input directo al modelo (penalización -25 % por data leakage). S5P solo como pseudo-label en el texto.
- Checkpoint `.pt` MD5 reproducible entre los 3 integrantes (penalización -20 % si difieren).

### Bloque C — Sit 3 (depende de Sit 2)

Día 5-7. ~6-8 h.

| Tarea | Esfuerzo | Hardware |
|---|---:|---|
| Secuencias ConvLSTM (8 frames por estación, sobre embeddings) | 1 h | CPU |
| ConvLSTM bidir (hidden=128, 2 capas, AdamW lr=1e-4) | 2-4 h | T4 |
| Variograma teórico (esférico/exponencial) sobre residuos | 30 min | CPU |
| OK3D Kriging Espacio-Temporal con `pykrige` | 30 min | CPU |
| **LOO-CV obligatorio** (10 est × 3 contaminantes × T+1/T+3/T+7) | 2 h | CPU |
| Moran I + LISA con `pysal.esda` | 30 min | CPU |
| Mapas gradiente + incertidumbre Kriging | 30 min | CPU |
| K-Means sobre superficies predichas (perfiles tipológicos) | 30 min | CPU |

**LOO-CV es obligatorio** (penalización -60 % Sit 3 si falta).

### Bloque D — Frontend (depende de Sit 3)

Día 7-9. ~1.5 días.

| Tarea | Stack | Tiempo |
|---|---|---:|
| Backend FastAPI: `/predict`, `/validate` | Python | 4 h |
| Frontend React + Vite + Leaflet (mapa, 9 mapas gradient, slider temporal, tooltips, opacidad incertidumbre) | React | 1 día |
| Dockerfile multi-stage | Docker | 1 h |
| Despliegue HF Spaces o Render (free) | HF | 2 h |
| Verificación latencia < 8 s end-to-end | — | 30 min |

**Frontend NO puede ser Streamlit/Gradio** (penalización -30 % despliegue ≈ -3 % total). React + Vite + Leaflet obligatorio.

### Bloque E — Informe + cierre

Día 9-10.

| Tarea | Tiempo |
|---|---:|
| Informe técnico PDF (15-25 páginas) | 1 día |
| Verificación MD5 checkpoint entre integrantes | 30 min |
| Repo Git limpio + README final | 2 h |
| Empaquetar .zip de entrega | 30 min |
| Defensa oral (7 puntos clave en `conceptos/README.md`) | 2 h |

---

## Comandos clave para retomar

### Sincronizar el notebook Kaggle a local

```powershell
# Pull versión actual del notebook activo
kaggle kernels pull edwardsx/geo-vision-proyecto-3-muestreo -p scripts/notebook-kaggle/ --metadata
```

### Bajar tiles para auditar localmente

```powershell
kaggle datasets download edwardsx/geovision-tiles-sit2 -p data/tiles_v1/ --unzip
```

### Push del notebook actualizado a Kaggle

```powershell
# Asumiendo que scripts/notebook-kaggle/ tiene kernel-metadata.json + .ipynb actualizado
kaggle kernels push -p scripts/notebook-kaggle/
```

### Crear notebook NUEVO para entrenamiento

```powershell
mkdir scripts/notebook-entrenamiento
cd scripts/notebook-entrenamiento
kaggle kernels init -p .
# Editar kernel-metadata.json:
#   "id": "edwardsx/geo-vision-clip-sae-entrenamiento"
#   "enable_gpu": true
#   "dataset_sources": ["juanjoseorozcolopez/geovision-fuentes", "edwardsx/geovision-tiles-sit2"]
kaggle kernels push -p .
```

---

## Riesgos abiertos

| Riesgo | Mitigación |
|---|---|
| Streamlit como atajo tentador | Compromiso: React + Vite + Leaflet desde día 1 del frontend |
| Manifest JSON con MD5 sin generar | 30 min script al cierre de Sit 1 |
| MODIS AOD no físico → Sit 3 puede usar AOD raw | Opción (b): excluir MODIS, usar solo S5P + ERA5 en Kriging |
| Checkpoint `.pt` MD5 difiere entre integrantes | Seed fijo + versiones idénticas de torch/python + commit del docker image |
| Diversidad temporal O₃ (31 fechas) cuestionada en defensa | Sección "Defensa contra críticas" en `JUSTIFICACIONES.md` línea ~270 |
| Sesión Kaggle se cae en entrenamiento de 4-6 h | Guardar checkpoint cada N epochs en `/kaggle/working/checkpoints/` |

---

## Bonus disponibles (opcional, +6 puntos recomendado)

| Bonus | Puntos | Esfuerzo | Recomendado |
|---|---:|---|---|
| Modo oscuro frontend | +2 | 30 min | ✓ trivial |
| Análisis equidad espacial por estrato socioeconómico | +4 | 4 h | ✓ si hay tiempo |
| Audio Whisper como 3ª modalidad | +3 | 1 día | ✗ no compensa |
| Comparación con OMI/AURA o GOME-2 | +3 | 4 h | ✗ requiere bajar dataset adicional |

---

## Para el agente que continúa

**Pregúntale al owner antes de**:
- Crear archivos nuevos fuera de los paths ya documentados.
- Cambiar decisiones del cuadro "Decisiones cerradas".
- Hacer `kaggle datasets version` sobre `juanjoseorozcolopez/geovision-fuentes` (riesgo: borrar el panel de 83 GiB).
- Usar Streamlit/Gradio para el frontend.

**No re-hagas**:
- El panel base (87 GB en Zarr ya están en Kaggle/GCS).
- El muestreo Sit 2 (5,000 tiles ya están en `edwardsx/geovision-tiles-sit2`).
- El pre-filtrado SCL (cache en `scl_por_escena.csv` dentro del dataset de tiles).

**Antes de cualquier cambio de código**:
- Leer `AGENTS.md` para entender el perfil del owner (español LATAM, GPU si disponible, no sobre-ingeniería, preguntar antes de actuar).
- Revisar la sección "Defensa contra críticas" en `JUSTIFICACIONES.md` para no contradecir argumentos ya armados.

**Siguiente acción inmediata recomendada**: Bloque B (entrenamiento Sit 2). Es lo que bloquea Sit 3, Sit 3 bloquea frontend, y frontend bloquea informe.
