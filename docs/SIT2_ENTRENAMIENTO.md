# Sit 2 — Entrenamiento CLIP fine-tune (Stage 1)

Documento de resultados, problemas detectados y decisiones tomadas durante el fine-tune
del notebook `scripts/sit2/situacion-2-clip-modificado.ipynb` (versión modificada de
`01_clip_finetune.py`).

## Configuración real ejecutada

| Parámetro | Valor | Comentario |
|---|---|---|
| Modelo base | RemoteCLIP ViT-B/32 (chendelong/RemoteCLIP) | 605 MB descargado |
| Bandas input | 12 ópticas (sin SCL) | adaptada `conv1` 3→12 ch |
| Tile size | 64×64 → bilinear → 224×224 | input ViT |
| Normalización | `(x - BAND_MEAN) / BAND_STD` por banda, clip ±3σ | computada sobre los 5K tiles |
| Split val | 6% estratificado (300 tiles, 60/clase) | reducido vs 10% inicial |
| Batch | 64 | InfoNCE bidireccional |
| Epochs | 30 | de 50 originales |
| LR (param groups) | visual_6-9: 2e-5, visual_10-11: 5e-5, text_6-11: 5e-5, proj: 1e-4, logit_scale: 1e-3 | layer-wise decay |
| Params entrenables | 62.1M / 158.4M (39.2%) | bloques 0-5 congelados |
| Weight decay | 0.2 | |
| Warmup | 2 epochs | |
| Scheduler | cosine | |
| Hardware | Tesla T4 (14.6 GB) | |
| Tiempo total | **43.1 min** | mucho menos que estimación 4-5h |

## Curvas de entrenamiento

Imagen: `entrenamiento/curvas_aprendizaje.png`.

| Epoch | Train Loss | Val Loss | R@1 | R@5 | R@10 |
|---|---|---|---|---|---|
| 1 | 3.48 | 3.82 | 0.020 | 0.083 | 0.147 |
| **4** | **2.95** | **3.93** | **0.040** | **0.117** ← mejor | **0.210** |
| 10 | 0.71 | 5.39 | 0.023 | 0.100 | 0.157 |
| 20 | 0.38 | 6.38 | 0.013 | 0.070 | 0.150 |
| 30 | 0.35 | 6.58 | 0.023 | 0.080 | 0.147 |

## Diagnóstico crítico

### 1. Overfitting severo (después de epoch 4)

- Train loss: **3.48 → 0.35** (cae 10×).
- Val loss: **3.82 → 6.58** (sube 73%).
- Gap train-val crece monotónicamente desde epoch 5.

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

Por eso R@1=0.04 (4%) parece pésimo, pero **chance level con 300 textos casi-duplicados
agrupados en 5 clases NO es 1/300 sino más alto**. El recall@K subestima drásticamente
la calidad real del embedding aprendido.

**Conclusión:** R@5=0.117 vs random teórico 5/300=0.017 → mejora 7×. El modelo **sí
aprendió estructura**, pero la métrica no es la apropiada.

### 3. El mejor checkpoint es de epoch 4

`clip_finetuned_best.pt` corresponde a epoch 4 con R@5=0.117. Es el que vamos a usar.
Después de epoch 4 el modelo memoriza pares train específicos sin generalizar.

## Acción correctiva inmediata: re-evaluación con métricas adecuadas

Nuevo notebook: `scripts/sit2/01b_eval_classification.py`.

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

## Referencias

- Curvas: `entrenamiento/curvas_aprendizaje.png`
- Notebook efectivo: `scripts/sit2/situacion-2-clip-modificado.ipynb`
- Notebook fuente: `scripts/sit2/01_clip_finetune.py`
- Eval correcta: `scripts/sit2/01b_eval_classification.py`
- Conceptos: `docs/conceptos/clip-y-remoteclip.md`
