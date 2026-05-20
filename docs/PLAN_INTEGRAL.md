# Plan integral GeoVision-CLIP Cali — panorama completo

Documento maestro de planeación, escrito tras la revisión exhaustiva del proyecto al **2026-05-19**.
Sustituye el roadmap parcial de [`HANDOFF.md`](HANDOFF.md) (desactualizado en varios puntos) y
cruza el estado real verificado contra el PDF [`proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf`](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf).

> Corte: **2026-05-19**. Lectura previa obligatoria: [`AGENTS.md`](../AGENTS.md), [`docs/VEREDICTO_DATOS.md`](VEREDICTO_DATOS.md), [`docs/EDA_HALLAZGOS.md`](EDA_HALLAZGOS.md).

---

## 1. Estado real verificado

### Sit 1 — Panel cloud (20 % rúbrica) — **95 % cerrado**

| Item | Estado | Evidencia |
|---|:---:|---|
| Panel ≥ 50 GB | ✅ | **89.7 GB** en `manifest/manifest_output/manifest.json` (8,847 archivos, 7 fuentes) |
| 6 fuentes Zarr | ✅ | S2 (1552,13,3897²) + S5P NO₂/SO₂/O₃ + ERA5 (43824 h) + MODIS v3 (1826 d) |
| Manifest MD5 | ✅ **ya existe** | `manifest_output/manifest.json` con `aggregate_hash_md5` por fuente — el HANDOFF está desactualizado |
| Lossless verificado | ✅ | `diff_max = 0` para B1/B4/B8/SCL |
| MODIS v3 corregido | ✅ | bug doble (scale + tile h10v08) resuelto |
| Conversión Zarr | ✅ | chunks `(5,13,974,974)`, zstd+bitshuffle |
| EDA ≥ 8 viz | ✅ | 8 bloques en `EDA_HALLAZGOS.md` (1171 líneas) + ~30 PNGs en `imagenes-referencias/eda/` |
| **Diagrama arquitectura cloud** | ❌ **FALTA** | sólo existe el de arquitectura de modelo (`arquitecturas/c63b5ec6-...jpeg`) |
| **Reporte costos cloud** | ❌ **FALTA** | sin redactar |

### Sit 2 — CLIP + SAE (20 % rúbrica) — **40 % real**

| Item | Estado | Evidencia |
|---|:---:|---|
| 5,000 tiles balanceados | ✅ | `edwardsx/geovision-tiles-sit2` (229 MB npz + 0.3 MB parquet) |
| Pseudo-labels por percentil | ✅ | NO₂/SO₂ p90, O₃ p95 |
| Pre-filtrado SCL GPU | ✅ | `scl_por_escena.csv` cache |
| CLIP Stage 1 entrenado | ⚠ **SUBÓPTIMO** | `clip_finetuned.pt` con **R@5=0.117** (KPI mín ≥ 0.70, **falla**) |
| Overfitting severo | 🔴 | train 3.48→0.35, val 3.82→6.58. Best en epoch 4. |
| Zero-shot accuracy | ⚠ | 0.407 (2× chance, marginal). Confusion: SO₂/ozono se confunden 33-45 % |
| Late Fusion B (S5P MLP) | ❌ | el código actual sólo entrena S2→ViT, falta la rama MLP S5P |
| SAE 256 neuronas + sparsity | ❌ | pendiente |
| AFE Varimax + scree | ❌ | pendiente (PCA ya hecho en EDA: 6 factores → 80 %) |
| AFC con CFI/RMSEA/SRMR | ❌ | pendiente (`semopy`) |
| Interpretabilidad SAE | ❌ | pendiente |
| MD5 reproducible | ⚠ | generado en `manifest_stage1.json` pero falta sync 3 integrantes |

### Sit 3 — DL + Geoestadística (30 % rúbrica) — **0 %**

| Item | Estado |
|---|:---:|
| Secuencias ConvLSTM (8 frames) | ❌ |
| ConvLSTM bidir (h=128, k=3, 2 capas) | ❌ |
| Variograma teórico (exponencial/esférico) | ❌ |
| OK3D Kriging con `pykrige` | ❌ |
| **LOO-CV obligatorio** | ❌ — limitación severa NO₂ (1 estación) |
| Moran I + LISA (`esda`) | ❌ |
| K-Means perfiles tipológicos | ❌ |
| Mapas gradiente + incertidumbre | ❌ |

### Frontend / informe / defensa (30 % rúbrica) — **0 %**

Nada hecho. React + Vite + Leaflet obligatorio (Streamlit prohibido = -30 %).

---

## 2. Hallazgos críticos (no obvios)

| # | Hallazgo | Implicación |
|---|---|---|
| 1 | **CLIP overfit severo** (val sube 73 %, train cae 10×) | KPI Recall@5 = 0.117 lejos del mínimo 0.70. Re-entreno obligatorio. |
| 2 | **Sólo 2 tiles MGRS** sobre BBox; T18NUK aporta 3/773 escenas (0.4 %) | El modelo aprende sólo sobre T18NUJ. Quemas de caña al norte (3.6-4.5°N) no visibles, sólo su pluma advectada. |
| 3 | **NO₂ en 1 sola estación** (Yumbo CVC) | LOO-CV literal **imposible** para NO₂ → -60 % Sit 3 si no se mitiga con validación alternativa documentada |
| 4 | **Cobertura DAGMA heterogénea** (Yumbo 80.9 % vs mediana 17 %) | LOO-CV ponderado + restringido a ≥ 20 % cobertura es defensa estándar |
| 5 | **86 % de tiles O₃ en 2022+2024** | Split estratificado por año obligatorio en Sit 2 |
| 6 | **MODIS v3 con AOD 85 % NaN** sobre tiles (15.3 % cobertura) | AOD NO feature primaria de Kriging — usar Column_WV (97.9 %) como feature física, AOD cualitativo |
| 7 | **S5P captura 97 % pico O₃ pero sólo 53 % NO₂ y 46 % SO₂** | Justifica ERA5 horario + DAGMA horario para reconstruir ciclo diurno completo |
| 8 | **Correlaciones cross-source < 0.3** en valor absoluto | Justificación empírica fuerte para Deep Learning no-lineal |
| 9 | **PCA: 6 factores → 80 % varianza** | Cumple criterio AFE del PDF anticipadamente |
| 10 | **2020 tiene 48.6 % de mediciones DAGMA** pero sin panel S2 | No extender panel (10-15 h sin beneficio). 2020 = contexto + validación opcional. |
| 11 | **manifest.json YA generado** (89.7 GB, MD5 por fuente) | HANDOFF y FLUJO_PROYECTO desactualizados al marcarlo pendiente |
| 12 | **Late Fusion B** es la arquitectura recomendada en `arquitecturas/c63b5ec6-...jpeg`, pero el código entrenado sólo tiene S2→ViT sin la rama MLP S5P | Falta implementar la fusión |
| 13 | **HF dataset sólo tiene DAGMA parquet** (64.5 MB), no los 5 paneles Zarr pequeños | Verificar si los Zarr de HF se sincronizaron — doc desactualizado |

---

## 3. Veredicto de viabilidad

**SÍ es viable y defendible** si se ejecutan estas 4 mitigaciones obligatorias:

| Mitigación | Esfuerzo | Penalización evitada |
|---|---:|---|
| **A. Validación NO₂ alternativa** (in-sample Yumbo + concordancia S5P + KS test) | 2 h doc + 1 h código | parte de -60 % Sit 3 |
| **B. LOO-CV triple** (uniforme + ponderado + restringido ≥ 20 %) | 1 h código | parte de -60 % Sit 3 |
| **C. Re-entrenar CLIP** con early stopping (epoch 6-10) + augmentation + Late Fusion B | 6-8 h GPU T4 | -50 % KPIs Sit 2 |
| **D. Split estratificado por año** en Sit 2 + reportar métricas por año | 30 min | leakage en defensa |

**Sin mitigaciones**: expectativa ~50-60 % rúbrica. **Con ellas**: ~85-90 %.

---

## 4. Plan de ejecución (priorizado por dependencias y penalización)

### Bloque A — Cierre Sit 1 (~6 h, paralelizable, no bloquea Sit 2)

| Tarea | Tiempo | Por qué |
|---|---:|---|
| Diagrama arquitectura cloud (PNG/SVG con draw.io o diagrams.net) | 1.5 h | rúbrica |
| Reporte costos cloud (GCS egress, HF storage, Kaggle compute, GEE quotas) | 1 h | rúbrica |
| Notebook EDA Sit 1 consolidado (4-8 viz del PDF p. 5) | 3 h | rúbrica |
| Sync HF Bucket (verificar que los 5 Zarr pequeños están subidos) | 30 min | doc |

### Bloque B — Sit 2 re-entrenamiento (8-10 h GPU T4, **bloquea Sit 3**)

| Tarea | Tiempo | Opción A (segura) | Opción B (mejor pero arriesgada) |
|---|---:|---|---|
| **Re-entrenar CLIP** | 4 h | EPOCHS=8 + early stopping + flip/rotate aug + clase aux head | LoRA r=16 sobre todos los bloques (menos params, menos overfit) |
| **Late Fusion B** (S5P MLP 128) | 2 h | MLP: 3 feats S5P (NO₂/SO₂/O₃ normalizados) → ℝ¹²⁸ → concat con ViT ℝ⁵¹² → ℝ⁶⁴⁰ → ℝ²⁵⁶ | igual |
| **SAE 256 neuronas** (L1 λ=1e-3, MSE) | 1.5 h | dos SAEs simétricos (uno por encoder), trainable end-to-end | igual |
| **AFE PCA + Varimax** (sklearn FactorAnalysis con rotation='varimax') | 30 min | scree plot + ≥ 6 factores | igual |
| **AFC con `semopy`** (4 constructos: Antropógenica, Vegetal, Urbana, Volatilidad) | 1 h | CFI/RMSEA/SRMR | igual |
| **Interpretabilidad SAE** (top-10 neuronas activas por clase) | 30 min | tabla + heatmap | igual |
| Checkpoint MD5 → 3 integrantes | 15 min | seed=42 + torch determinístico | igual |

### Bloque C — Sit 3 (10-12 h, bloquea frontend)

| Tarea | Tiempo | Hardware |
|---|---:|---|
| Generar secuencias ConvLSTM (8 frames sobre embeddings 256, por estación) | 1 h | CPU |
| ConvLSTM bidir (h=128, k=3, 2 capas, AdamW 1e-4, batch=16) | 3 h | T4 |
| Variograma experimental + ajuste teórico (exponencial) `pykrige` | 30 min | CPU |
| OK3D Kriging Espacio-Temporal `OrdinaryKriging3D` | 30 min | CPU |
| **LOO-CV triple** (uniforme/ponderado/restringido) × 3 contaminantes × 3 horizontes T+1/T+3/T+7 | 3 h | CPU |
| **Mitigación A NO₂**: in-sample Yumbo + Pearson r vs S5P + KS test | 1 h | CPU |
| Variograma residuos (debe ser nugget puro) | 30 min | CPU |
| Moran I + permutation test n=999 + LISA mapas | 1 h | CPU |
| Cobertura cinturón 95 % σ Kriging | 30 min | CPU |
| K-Means perfiles tipológicos sobre superficies predichas | 30 min | CPU |
| 9 mapas gradiente (3×3) + incertidumbre | 1 h | CPU |

### Bloque D — Frontend (12-16 h, ~1.5 días)

Stack **obligatorio** (penalización -30 % si Streamlit/Gradio):

```
Backend:  FastAPI + Uvicorn
          POST /predict (lat,lon,horizonte,contaminante)
          POST /validate (LOO-CV results)
          GET  /metadata (BBox, estaciones, KPIs)
          GET  /geotiff/{layer} (descarga)
Frontend: React 18 + Vite + TypeScript
          react-leaflet con mapa centrado en Cali
          9 mapas gradient (3×3) con slider T+1/T+3/T+7
          Capa de incertidumbre con opacidad ∝ 1/σ
          Tooltips con valor ± σ
          Toggle 10 estaciones DAGMA/CVC + popups
          Botón descarga GeoTIFF / CSV
Bonus:    Modo oscuro (+2 pts, 30 min)
Docker:   multi-stage (Python slim + node-alpine + nginx)
Despliegue: HuggingFace Spaces (free tier) o Render
Latencia: < 8 s end-to-end (pre-computar mapas en GeoTIFF y servir directo)
```

### Bloque E — Informe + cierre (~12-16 h)

15-25 páginas con la estructura PDF p. 10:

1. Resumen ejecutivo
2. Construcción del panel (arquitectura, manifest, EDA)
3. Modelo GeoVision-CLIP (arquitectura, training, AFE/AFC)
4. Pipeline DL + Geoestadística (ConvLSTM + ST-Kriging)
5. Resultados y validación (KPIs, LOO-CV, Moran/LISA, mapas)
6. **Análisis de ablación** (con/sin SAE, DL solo vs DL+Kriging, MODIS sí/no)
7. Despliegue (URL, latencia, diagrama)
8. Discusión + limitaciones + trabajo futuro (incluir 2020 DAGMA como contexto)

- Apéndice A: MD5 + manifest + semillas
- Apéndice B: código clave

**Bonus recomendados** (+6 pts, ~5 h):

- Modo oscuro frontend (+2, 30 min)
- Análisis equidad espacial por estrato socioeconómico Cali (+4, 4 h con shapefile estratos DANE)

---

## 5. Calendario realista (3-4 personas, ~3-4 h/día)

**Tiempo neto restante estimado: 50-70 h grupo** (≈ 7-10 días calendario con margen).

| Día | Bloque A | Bloque B | Bloque C | Bloque D | Bloque E |
|---:|---|---|---|---|---|
| 1 (hoy) | Diagrama + costos | Re-entreno CLIP (T4) | — | — | — |
| 2 | EDA notebook consolidado | Late Fusion + SAE + AFE/AFC | — | — | — |
| 3 | — | MD5 sync 3 integrantes | Secuencias + ConvLSTM | Setup repo React | — |
| 4 | — | — | Kriging + variograma | UI mapa base | — |
| 5 | — | — | LOO-CV triple + Mit. A | 9 mapas + slider | — |
| 6 | — | — | Moran/LISA + KMeans | Docker + despliegue HF | Esqueleto informe |
| 7 | — | — | — | Bonus modo oscuro + equidad | Secciones 1-4 |
| 8 | — | — | — | Test latencia | Secciones 5-8 |
| 9 | — | — | — | URL final | Apéndices |
| 10 | — | — | — | — | Defensa + .zip |

---

## 6. Riesgos abiertos

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| CLIP no llega a R@5 ≥ 0.70 ni con re-entreno | Alta | Reportar **zero-shot accuracy** + **k-NN sobre embeddings** (ya implementado en `_v2.py` líneas 642-713). El PDF acepta KPIs reportados con evidencia |
| Sesión Kaggle T4 cae en 4-6 h entreno | Media | Checkpoint cada N epochs en `/kaggle/working/checkpoints/` |
| Frontend Leaflet con 9 capas raster lento | Media | Pre-renderizar PNGs por horizonte + servir vía CDN HF Spaces |
| Defensa cuestiona "1 estación NO₂" | Alta | Citar Mitigación A + tabla cobertura por estación + explicar límite operacional DAGMA |
| MD5 difiere entre 3 PCs | Media | Fijar `torch==2.x.y` + `cuda 12.x` + `seed=42` + `torch.use_deterministic_algorithms(True)` + ejecutar el mismo notebook en los 3 equipos |
| HF Spaces free tier no soporta Docker grande | Baja | Backup: Render free / fly.io |

---

## 7. Lo que NO hay que hacer

1. **No usar Streamlit/Gradio** ni siquiera para prototipo (-30 % despliegue)
2. **No pasar S5P como input directo al CLIP** (es pseudo-label en texto, no input visual) — el código actual ya lo hace bien
3. **No re-versionar `juanjoseorozcolopez/geovision-fuentes`** (riesgo de borrar el panel base 83 GB)
4. **No extender panel a 2020** (10-15 h sin beneficio real en KPIs)
5. **No usar Dask explícitamente** si no fluye — el PDF dice "ETL distribuido", se defiende GEE+GCS+HF como arquitectura distribuida (decisión #11 en JUSTIFICACIONES)
6. **No reportar sólo LOO-CV uniforme** — siempre reportar 3 versiones (uniforme/ponderado/restringido)
7. **No omitir MD5 del checkpoint final** entre 3 integrantes (-20 % modelo)
8. **No olvidar `enable_gpu=true`** en `kernel-metadata.json` del notebook entrenamiento
9. **No subir checkpoint `.pt` al repo Git** (>100 MB → usar HF Hub o Kaggle dataset)
10. **No mostrar bug MODIS sin contar el fix v3** en defensa

---

## 8. Siguiente acción inmediata

**Hoy mismo, 2-3 personas en paralelo:**

1. **Persona 1 (GPU Kaggle):** abrir notebook nuevo `scripts/sit2/02_clip_late_fusion.py` con EPOCHS=10, early stopping epoch 5, flip+rotate aug, Late Fusion B (MLP S5P 128), seed fijo. **Destraba Sit 3.**
2. **Persona 2 (CPU local):** redactar `docs/COSTOS_CLOUD.md` + generar `imagenes-referencias/arquitectura_cloud.png` (diagrams.net con iconos GCP/HF/Kaggle reales).
3. **Persona 3 (informe):** esqueleto del informe en LaTeX/Markdown con las 8 secciones del PDF p. 10, dejando placeholders para resultados de Sit 2 retrain y Sit 3.

Cuando el re-entreno termine y los KPIs estén estables → arrancar Bloque C (Sit 3) y Bloque D (frontend) en paralelo.

---

## 9. Cotización referencial (Colombia 2026)

Asumiendo este proyecto como **freelance/consultoría profesional** (no académica), perfil senior data engineer + ML engineer + geo-especialista + full-stack.

### Desglose por horas y tarifa

| Fase | Horas | Tarifa COP/h | Subtotal COP |
|---|---:|---:|---:|
| Discovery + arquitectura cloud + decisiones técnicas | 16 | 200,000 | 3,200,000 |
| Sit 1 — Pipeline GEE+GCS+HF+Kaggle (6 fuentes, 89 GB) | 60 | 180,000 | 10,800,000 |
| Sit 1 — EDA exhaustivo + 18 docs/conceptos | 40 | 150,000 | 6,000,000 |
| Sit 2 — Muestreo estratificado (3 técnicas, pre-filtrado GPU) | 30 | 180,000 | 5,400,000 |
| Sit 2 — CLIP fine-tune + Late Fusion + SAE + AFE/AFC | 45 | 220,000 | 9,900,000 |
| Sit 3 — ConvLSTM + ST-Kriging + LOO-CV + Moran | 55 | 220,000 | 12,100,000 |
| Frontend FastAPI + React + Leaflet + Docker + despliegue | 50 | 150,000 | 7,500,000 |
| Informe técnico + defensa preparada | 25 | 150,000 | 3,750,000 |
| Documentación técnica continua (HANDOFF/JUSTIFICACIONES/VEREDICTO/etc.) | 25 | 130,000 | 3,250,000 |
| Gestión + iteración + bugfixes (MODIS v3, CLIP overfit) | 30 | 180,000 | 5,400,000 |
| **TOTAL** | **376 h** | | **~67.3 M COP** |

### Rangos por perfil de cliente

| Perfil del cliente | Cotización justa | USD (~4,000 COP/USD) |
|---|---:|---:|
| Universidad / proyecto académico (descuento educativo) | 15 — 25 M COP | $3,750 — $6,250 |
| Startup / PYME tech colombiana | 45 — 60 M COP | $11,250 — $15,000 |
| Entidad pública (DAGMA, CVC, IDEAM, MinAmbiente) | 65 — 90 M COP | $16,250 — $22,500 |
| Empresa privada mediana / grande (contratista cloud) | 70 — 110 M COP | $17,500 — $27,500 |
| Consultora premium / fondo multilateral (BID, BM, GIZ) | 130 — 200 M COP | $32,500 — $50,000 |
| Cliente internacional remoto (USA/EU) | 180 — 280 M COP | $45,000 — $70,000 |

### Recomendación

**Cliente colombiano profesional (privado/público):** **65 — 80 M COP** (≈ USD $16K — $20K), 8 semanas, incluye:

- 3 modelos de ML (CLIP+SAE, ConvLSTM, Kriging) entrenados y validados
- 1 panel de datos multimodal 90 GB en cloud
- 1 aplicación web profesional desplegada
- 1 informe técnico 25 pp + defensa
- 18 documentos técnicos defendibles ante auditoría
- Código abierto en GitHub + Kaggle + HF público
- Manifest MD5 verificable + checkpoints reproducibles

**Tarifa plana sugerida:** **75 M COP** cubre overruns de Sit 3 (LOO-CV es lo más riesgoso) y deja margen de iteración.

Para una **consultora especializada** (Geo + DL + MLOps) orientada a entidades ambientales colombianas: **80 — 100 M COP** justificado por (1) calidad técnica del stack (Zarr + GEE + HF + cloud distribuido), (2) rigurosidad de validación geoestadística (LOO-CV + Moran/LISA), (3) 18 documentos defendibles, y (4) frontend profesional desplegado.

---

## Referencias internas

- [`AGENTS.md`](../AGENTS.md) — perfil del owner y reglas de trabajo
- [`HANDOFF.md`](HANDOFF.md) — handoff anterior (parcialmente desactualizado, este documento lo sustituye)
- [`VEREDICTO_DATOS.md`](VEREDICTO_DATOS.md) — balance honesto de calidad de datos y mitigaciones
- [`EDA_HALLAZGOS.md`](EDA_HALLAZGOS.md) — hallazgos empíricos sobre el panel (1171 líneas, 8 bloques)
- [`JUSTIFICACIONES.md`](JUSTIFICACIONES.md) — defensas técnicas de cada decisión
- [`MUESTREO_SIT2.md`](MUESTREO_SIT2.md) — pipeline de muestreo y resultados full N=5000
- [`SIT2_ENTRENAMIENTO.md`](SIT2_ENTRENAMIENTO.md) — diagnóstico del entrenamiento CLIP actual (overfit)
- [`FLUJO_PROYECTO.md`](FLUJO_PROYECTO.md) — cronología y decisiones por fecha
- [`DATASETS.md`](DATASETS.md) — catálogo de fuentes con justificación de bandas
- [`conceptos/README.md`](conceptos/README.md) — índice de los 18 conceptos teóricos
- [`proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf`](../proyecto/ProyectoFinal_GeoVisionCLIP_Cali.pdf) — spec académico (UAO Analítica de Datos I)
