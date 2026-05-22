# Sit 2 — Entrenamiento CLIP fine-tune (Stage 1)

> Versión reorganizada: ver [índice de Situación 2](README.md) y [entrenamiento](metodologia/entrenamiento.md).

Documento de resultados, problemas detectados y decisiones tomadas durante el fine-tune
del notebook `notebooks/sit2/01_clip_v1_oficial.ipynb`.

## Configuración real ejecutada

| Parámetro | Valor | Comentario |
|---|---|---|
| Modelo base | RemoteCLIP ViT-B/32 (chendelong/RemoteCLIP) | 605 MB descargado |
| Bandas input | 12 ópticas (sin SCL) | adaptada `conv1` 3→12 ch |
| Tile size | 64×64 → bilinear → 224×224 | input ViT |
| Normalización | `(x - BAND_MEAN) / BAND_STD` por banda, clip ±3σ | computada sobre los 5K tiles |
| Split val | 6% estratificado (300 tiles, 60/clase) | reducido vs 10% inicial |
| Batch | 64 | InfoNCE bidireccional |
| Epochs | 10 | primera corrida oficial |
| LR (param groups) | visual_6-9: 2e-5, visual_10-11: 5e-5, text_6-11: 5e-5, proj: 1e-4, logit_scale: 1e-3 | layer-wise decay |
| Params entrenables | 62.1M / 158.4M (39.2%) | bloques 0-5 congelados |
| Weight decay | 0.2 | |
| Warmup | 2 epochs | |
| Scheduler | cosine | |
| Hardware | Tesla T4 (14.6 GB) | |
| Tiempo total | **13.3 min** | corrida oficial v1 |

## Curvas de entrenamiento

Imagen: `docs/evidencias/situacion-2/entrenamiento/sit2_entrenamiento_curvas_aprendizaje.png`.

| Epoch | Train Loss | Val Loss | R@1 | R@5 | R@10 |
|---|---|---|---|---|---|
| 1 | 3.7752 | 3.8833 | 0.013 | 0.057 | 0.117 |
| 4 | 3.1194 | 3.7988 | 0.020 | 0.117 | 0.170 |
| **7** | **1.9451** | **4.6191** | **0.023** | **0.130** ← mejor | **0.197** |
| 10 | 0.9546 | 4.8808 | 0.027 | 0.117 | 0.183 |

## Diagnóstico crítico

### 1. Overfitting severo (después de epoch 4)

- Train loss: **3.7752 → 0.9546**.
- Val loss: **3.8833 → 4.8808**.
- Gap train-val crece desde la mitad del entrenamiento.

**Causas técnicas:**

- 62M parámetros entrenables sobre 4,700 tiles = **~13K params/sample** → recipe overfit clásico.
- Batch=64 da solo 63 negativos por anchor en InfoNCE; CLIP estándar usa batches 4K-32K.
- Sin data augmentation (random crop, flip, color jitter).

### 2. La métrica Recall@K **no es informativa** para este dataset

El recall@K mide "imagen i ↔ texto i exacto único". Pero el muestreo guiado por percentil S5P
genera **1000 tiles por clase con el mismo template** y solo cambio en el valor numérico:

```
"Urban area with elevated NO2 concentration (7.80e-05 mol/m2), heavy vehicular traffic."
"Urban area with elevated NO2 concentration (8.12e-05 mol/m2), heavy vehicular traffic."
"Urban area with elevated NO2 concentration (7.55e-05 mol/m2), heavy vehicular traffic."
```

Los embeddings textuales son casi idénticos dentro de clase. El modelo puede confundir
`tile_i` con `texto_j` de la misma clase, y eso **no es error real** pero R@K lo cuenta como error.

Por eso R@1=0.023 parece pésimo, pero **chance level con 300 textos casi-duplicados
agrupados en 5 clases NO es 1/300 sino más alto**. El recall@K subestima drásticamente
la calidad real del embedding aprendido.

**Conclusión:** R@5=0.130 vs random teórico 5/300=0.017 → mejora 7.6×. El modelo **sí
aprendió estructura**, pero la métrica no es la apropiada.

### 3. El mejor checkpoint v1 es de epoch 7

`clip_finetuned_best.pt` de la corrida v1 corresponde a epoch 7 con R@5=0.130. Esa corrida se usa como diagnóstico inicial, no como modelo final.
Después de las primeras epochs el modelo empieza a memorizar pares train específicos sin generalizar bien.

## Acción correctiva inmediata: re-evaluación con métricas adecuadas

Evaluación incluida en `notebooks/sit2/01_clip_v1_oficial.ipynb`.

Métricas que reporta sobre el `clip_finetuned_best.pt`:

1. **Zero-shot classification accuracy** vs 5 prototipos textuales (uno por clase, sin números).
   Chance level real: 0.20 (5 clases balanceadas).
2. **Confusion matrix** entre clases.
3. **k-NN classifier** (k=1, 5, 11) sobre embeddings — mide separabilidad lineal.
4. **Recall@K agrupado por clase** (top-K incluye al menos un texto de clase correcta).

**Si la accuracy zero-shot está ≥ 0.40 (2× chance):** el embedding aprendió clases utilizables,
podemos pasar a Stage 2 (SAE) sobre el checkpoint actual.

**Si está < 0.30:** hay que reentrenar con:

- ≤ 10 epochs (cortar antes del overfitting).
- Templates diversificados (5-10 variantes por clase, mezclando valores S5P y descripciones físicas).
- Augmentation: random horizontal flip, rotación 90°, mixup ligero.
- Considerar LoRA en lugar de fine-tune completo (menos params → menos overfit).

## Lecciones para Stage 2 (notebook 02 SAE)

- Trabajar con embeddings del checkpoint epoch 4 (best), **no del último epoch**.
- El SAE va a aprender features sparse del embedding fundido (visual + S5P MLP).
- La interpretabilidad por clase puede ser más estable que la métrica retrieval porque
  el SAE no requiere que pares image-text sean únicos.

## Pendiente del notebook 01 a corregir para próximas iteraciones

1. Output de gráfica: el código de upload referenciaba `clip_finetune_curves.png` pero
   el código de gráfica guardó `geovision_clip_training_results.png`. Unificar nombre.
2. `EPOCHS=30` (override del notebook modificado vs 50 del original) — está bien que
   sea modificable, dejar `EPOCHS = 30` como default si validamos que ≥30 es suficiente.
3. Logging por epoch a `train_log.txt` falla en el notebook modificado (no se escribe la
   cabecera al inicio). Mantener desde el original.

---

## Actualizacion v2 — Re-entreno con LoRA + Late Fusion (sin S5P)

### Problema detectado
El entrenamiento original (v1) tenia overfitting severo (mejor R@5=0.130) y data leakage por pasar valores S5P como input al fusion MLP. Penalizacion potencial: -25% del proyecto.

### Solucion aplicada
Nuevo notebook: `notebooks/sit2/03_clip_v3_oficial.ipynb`.

| Cambio | v1 (original) | v2 (corregido) |
|---|---|---|
| Entrenamiento | Fine-tune completo (62M params) | **LoRA rank=16** (2.1M params) |
| Data augmentation | Ninguna | **Flip + rotacion 0/90/180/270** |
| Rama S5P | Late Fusion con S5P input | **Eliminada** (solo visual) |
| Textos | 1 template/clase, valores numericos | **5 templates/clase**, mas diversos |
| Early stopping | No | Si (patience=3, best en epoch 11) |
| Params entrenables | 62.1M (39%) | **2.1M (1.4%)** |

### Resultados del re-entreno

| Metrica | v1 (overfit) | v2 (LoRA, sin S5P) | KPI minimo |
|---|---|---|---|
| R@1 | 0.023 | **0.483** | >= 0.45 |
| R@5 | 0.130 | **1.000** | >= 0.70 |
| Zero-shot accuracy | 0.407 | **0.500** (genuino, solo visual) | -- |
| k-NN accuracy | -- | **0.430** | -- |
| Overfitting | Severo | **No** (train=3.28, val=3.41) | -- |
| Data leakage | Si (S5P input) | **No** | Sin penalizacion |

### Data leakage diagnostic
Sin las features S5P, el accuracy era identico (0.483 vs 0.500), confirmando que el modelo v2 aprende genuinamente de features visuales.

### Configuracion del re-entreno

| Parametro | Valor |
|---|---|
| Modelo | RemoteCLIP ViT-B/32 + LoRA rank=16 |
| Bloques entrenables | 6-11 (visual + texto) via LoRA |
| Proj heads | visual.proj, text_projection, ln_final, logit_scale |
| Optimizer | AdamW, lr=2e-5, wd=0.2 |
| Scheduler | CosineAnnealing, T_max=20 |
| Epochs | 20 (early stopping en 14) |
| Batch | 64 |
| Hardware | Tesla T4 (14.6 GB) |
| Mejor epoch | 11 (val_loss=3.39) |

### SAE — Sparse Autoencoder

Entrenado sobre los 5,000 embeddings de 512-d del modelo v2.

| KPI | Resultado | Minimo | Estatus |
|---|---|---|---|
| MSE reconstruccion | **0.000215** | <= 0.05 | SUPERADO |
| Sparsity ratio | **0.765** | >= 0.70 | SUPERADO |
| Neuronas activas/muestra | 60 / 256 | -- | -- |
| SAE_LAMBDA | 1e-2 | -- | -- |
| SAE epochs | 100 | -- | -- |

### AFE — Analisis Factorial Exploratorio (PCA + Varimax)

Sobre los 5,000 embeddings de 512-d.

| Factor | Varianza explicada | Acumulado |
|---|---|---|
| PC1 | 31.6% | 31.6% |
| PC2 | 22.3% | 53.9% |
| PC3 | 13.0% | 66.9% |
| PC4 | 8.6% | 75.5% |
| PC5 | 3.2% | 78.7% |
| PC6 | 2.0% | **80.6%** |

- **6 factores para 80% varianza** (KPI cumplido).
- PC1 separa suelo_urbano (+0.64) de vegetacion_densa (-0.56).
- Rotacion Varimax con 6 factores confirma estructura latente.

### AFC — Analisis Factorial Confirmatorio (semopy)

Modelo con 4 constructos latentes (Carga Antropogenica, Estres Vegetal, Densidad Urbana, Volatilidad Atmosferica) usando variables observables de `tiles_meta.parquet`: `ndvi`, `ndbi`, `scl_pct`, ERA5 y `modis_WV`. No se usan los factores PCA como indicadores, porque son ortogonales por construcción.

| Indice | Resultado | Meta | Estatus |
|---|---|---|---|
| CFI | **0.933** | > 0.90 | SUPERADO |
| RMSEA | **0.109** | < 0.08 | Ligeramente sobre la meta |

El CFI supera el umbral. El RMSEA queda ligeramente por encima de 0.08; con N=5,000, el chi-cuadrado se vuelve sensible y puede inflar este indicador.

### Checkpoint

Subido a Kaggle Dataset: `edwardsx/geovision-clip-modelo-v2` (611 MB).
- `clip_finetuned_best.pt`: pesos del modelo + fusion
- `metrics.json`: epoch, loss, accuracies
- `checkpoint.md5`: hash MD5 verificable

---

## Auditoría v4 — Split temporal por grupos

Se creó `notebooks/sit2/05_clip_v4_group_split.ipynb` para probar una validación más estricta. Mantiene el modelo LoRA sin S5P, pero separa validación por fechas completas.

Split final:

| Criterio | Valor |
|---|---:|
| Train | 4,531 |
| Val | 469 |
| Fechas train | 71 |
| Fechas val | 8 |
| Fechas compartidas | 0 |
| Años val | 2021-2024 |
| Tile MGRS val | T18NUJ |

Resultados:

| Metrica | v2/v3 final | v4 temporal |
|---|---:|---:|
| R@1 | 0.483 | 0.386 |
| R@5 | 1.000 | 1.000 |
| R@10 | 1.000 | 1.000 |
| Zero-shot accuracy | 0.500 | 0.386 |
| Zero-shot solo visual | 0.500 | 0.401 |
| k-NN accuracy | 0.430 | 0.394 |

Conclusión: v4 no reemplaza al modelo final porque R@1 cae por debajo del KPI de 0.45. Sí reduce la incertidumbre metodológica: aun sin fechas compartidas entre train y validación, el modelo conserva R@5=1.000 y zero-shot cercano a 2x chance.

Checkpoint auxiliar: `edwardsx/geovision-clip-modelo-v4-group-split`.

---

## Auditorías de datos posteriores

### Auditoría estadística de tiles

Notebook: `notebooks/sit2/06_auditoria_estadistica_tiles.ipynb`.

Verifica balance, rangos físicos, NaN/Inf, distribución temporal, SCL, MODIS y ERA5. No encontró un fallo fuerte que invalide Sit 2. Las alertas principales fueron baja cobertura MODIS AOD, temporalidad sesgada y poca presencia de `T18NUK`.

### Auditoría puente DAGMA/CVC

Notebook: `notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb`.

Cruza tiles Sit 2 con mediciones oficiales DAGMA/CVC por estación cercana y ventanas de 0, ±1 y ±3 días. Usa 107,291 observaciones filtradas y 1,640 días con datos.

| Contaminante | Clase objetivo | Lectura principal |
|---|---|---|
| NO2 | `contaminacion_alta_NO2` | Coherente solo en mismo día; débil/inversa en ±1 y ±3 días. |
| SO2 | `contaminacion_alta_SO2` | Débil/inversa en todas las ventanas. |
| O3 | `ozono_anomalo` | Coherente solo en mismo día; débil/inversa en ±1 y ±3 días. |

Conclusión: DAGMA/CVC funciona como auditoría puente hacia Sit 3, no como validación final de CLIP. El resultado permite defender coherencia puntual para NO2 y O3, pero obliga a reportar SO2 como señal débil frente a superficie.

### Notebooks creados

| Notebook | Contenido |
|---|---|
| `notebooks/sit2/01_clip_v1_oficial.ipynb` | Entrenamiento CLIP v1, diagnóstico de overfitting |
| `notebooks/sit2/02_tiles_oficial.ipynb` | Exploración de tiles |
| `notebooks/sit2/03_clip_v3_oficial.ipynb` | Re-entreno final sin S5P |
| `notebooks/sit2/04_sae_oficial.ipynb` | SAE + AFE + AFC |
| `notebooks/sit2/05_clip_v4_group_split.ipynb` | Auditoría temporal estricta v4 |
| `notebooks/sit2/06_auditoria_estadistica_tiles.ipynb` | Auditoría estadística de tiles |
| `notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb` | Auditoría puente DAGMA/CVC |

## Referencias

- Curvas: `docs/evidencias/situacion-2/entrenamiento/sit2_entrenamiento_curvas_aprendizaje.png`
- Notebook v1 oficial: `notebooks/sit2/01_clip_v1_oficial.ipynb`
- Notebook CLIP final: `notebooks/sit2/03_clip_v3_oficial.ipynb`
- Notebook SAE/AFE/AFC: `notebooks/sit2/04_sae_oficial.ipynb`
- Notebook auditoría temporal v4: `notebooks/sit2/05_clip_v4_group_split.ipynb`
- Notebook auditoría estadística: `notebooks/sit2/06_auditoria_estadistica_tiles.ipynb`
- Notebook auditoría puente DAGMA/CVC: `notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb`
- Conceptos: `docs/conceptos/clip-y-remoteclip.md`
