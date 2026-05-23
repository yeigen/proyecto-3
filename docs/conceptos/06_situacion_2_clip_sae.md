# 06. Situación 2: tiles, CLIP, SAE y auditoría

Este documento conecta la Situación 2 del PDF con lo que realmente hay en el proyecto: muestreo de tiles, entrenamiento CLIP, análisis SAE/AFE/AFC, auditorías y limitaciones.

La idea es poder defender no solo “entrenamos un modelo”, sino:

> con qué datos se entrenó, qué se corrigió, qué métricas son válidas y qué no se debe prometer.

## 1. Qué pedía el PDF

La Situación 2 pedía construir un modelo multimodal tipo CLIP para aprender representaciones imagen-texto a partir del panel de Situación 1.

| Requisito | Lectura práctica |
|---|---|
| Tiles Sentinel-2 | Recortes espaciales para alimentar el encoder visual. |
| Textos asociados | Descripciones por clase o condición ambiental. |
| Pseudo-labels S5P | Usar NO₂, SO₂ y O₃ por percentiles como guía de muestreo. |
| Fine-tuning CLIP | Ajustar un modelo contrastivo imagen-texto. |
| Interpretabilidad | Analizar embeddings con SAE, AFE y AFC. |
| Auditoría | Revisar sesgos, leakage y consistencia con datos externos. |

## 2. Qué hizo el proyecto

El proyecto generó 5,000 tiles balanceados y entrenó un modelo RemoteCLIP con LoRA, sin usar S5P como input directo en la versión final.

| Elemento | Resultado |
|---|---:|
| Tiles totales | 5,000 |
| Clases | 5 |
| Tiles por clase | 1,000 |
| Tensor de imágenes | `(5000, 13, 64, 64)` |
| Metadata | `(5000, 22)` |
| Fechas únicas | 79 |
| Modelo final | RemoteCLIP ViT-B/32 + LoRA |
| Checkpoint principal | `edwardsx/geovision-clip-modelo-v2` |
| Auditoría temporal | v4 con split por fechas completas |

La decisión clave fue separar dos usos de S5P:

| Uso de S5P | Estado |
|---|---|
| Guía de muestreo / pseudo-label | válido para construir clases débiles. |
| Input numérico directo al modelo | descartado por riesgo de data leakage. |

## 3. Cumplimiento metodológico frente al PDF

Veredicto corto:

> La Situación 2 cumple el objetivo metodológico central del PDF, pero no replica de forma literal toda la arquitectura propuesta.

Esto no invalida la Situación 2. Sí obliga a explicar con precisión qué se cumplió, qué se cambió y por qué.

| Requisito del PDF | Implementación real | Estado | Lectura defendible |
|---|---|---|---|
| Mínimo 1,000 pares imagen-texto | 5,000 pares balanceados | Cumple | Se supera el mínimo por 5x. |
| Al menos 5 clases | 5 clases, 1,000 tiles por clase | Cumple | Balance útil para contraste. |
| Tile Sentinel-2 64×64 | Tensor `(5000, 13, 64, 64)` | Cumple | El entrenamiento usa 12 bandas ópticas; SCL queda como control/calidad. |
| Pseudo-labels S5P por percentiles | NO₂ p90, SO₂ p90, O₃ p95 | Cumple | O₃ se relajó a p95 por cobertura y estabilidad. |
| RemoteCLIP / CLIP satelital | RemoteCLIP ViT-B/32 + LoRA | Cumple | Adaptación eficiente al dominio satelital. |
| No pasar S5P como input directo | v1 lo hizo; v3 lo elimina | Cumple en modelo final | La versión reportable evita data leakage. |
| Recall@1 ≥ 0.45 | v3 reporta 0.483 por prototipo/clase; Sit 2.1 retrieval real test = 0.0027 | No cumple como retrieval real | La métrica v3 no era Recall@K imagen-texto exacto. |
| Recall@5 ≥ 0.70 | v3 reporta 1.000 por prototipo/clase; Sit 2.1 retrieval real test = 0.0147 | No cumple como retrieval real | El R@5 anterior era clasificación por clase/prototipo, no KPI PDF literal. |
| SAE sparsity ≥ 0.70 | 0.765 | Cumple | Representación sparse lograda. |
| SAE MSE ≤ 0.05 | 0.000215 | Cumple | Reconstrucción muy por debajo del umbral. |
| AFE varianza ≥ 80% | 80.6% con 6 factores | Cumple | Criterio de varianza acumulada cumplido. |
| CFI > 0.90 | 0.933 | Cumple | Ajuste confirmatorio aceptable por CFI. |
| RMSEA < 0.08 | 0.109 | No cumple | Se reporta como limitación del AFC. |
| Split 70/15/15 | v3 usa validación 94/6; v4 usa split temporal | Cumple parcialmente | v4 es más estricto temporalmente, pero no es el split literal. |
| Dos SAE simétricos visual/textual end-to-end | SAE post-hoc sobre embeddings | Cumple parcialmente | Sirve para interpretabilidad, no replica la pérdida total del PDF. |
| Pérdida conjunta `L_InfoNCE + α(L_sae_img + L_sae_txt)` | CLIP y SAE entrenados por etapas | No literal | Queda como mejora futura planificada. |
| Encoder textual XLM-R/MiniLM | Encoder textual de RemoteCLIP | Desviación aceptable | Mantiene compatibilidad nativa imagen-texto del modelo CLIP. |
| Series de 8 fechas para forecasting | Se deja para Situación 3 | Fuera del cierre de Sit 2 | Debe tratarse al documentar ConvLSTM/ST-Kriging. |

### Qué significa “cumple” en esta situación

Metodológicamente, la Situación 2 es correcta si se presenta así:

1. El modelo final aprende representaciones visual-textuales sin usar S5P como atajo.
2. Los pseudo-labels S5P se usan para construir clases débiles, no como ground truth superficial.
3. Los KPIs principales de CLIP, SAE, AFE y CFI se cumplen con evidencia computacional.
4. Las desviaciones frente al PDF se declaran: SAE post-hoc, split no literal, RMSEA alto y ausencia de pérdida conjunta end-to-end.

Lo que no se debe decir:

> “Implementamos exactamente la arquitectura CLIP + dos SAE end-to-end del PDF.”

Lo correcto es decir:

> “Implementamos una versión metodológicamente estable y auditable de GeoVision-CLIP: CLIP con LoRA sin leakage, seguido de SAE/AFE/AFC para interpretación. La versión end-to-end literal queda planificada como corrida experimental posterior.”

### Plan posterior para cumplimiento literal

Para acercarse al PDF de forma más literal, se dejó un plan separado:

- [Plan CLIP + SAE end-to-end experimental](../superpowers/plans/2026-05-22-situacion-2-cumplimiento-literal-clip-sae.md)

Ese plan propone una corrida futura en Kaggle GPU con SAE visual y SAE textual dentro del entrenamiento, usando:

$$
L_{total} = L_{InfoNCE} + \alpha(L_{sae\_img} + L_{sae\_txt})
$$

Por ahora no reemplaza el modelo v3. Solo debería incorporarse como resultado principal si mantiene los KPIs de retrieval y cumple los KPIs SAE.

## 4. Notebooks revisados

| Notebook | Rol |
|---|---|
| `notebooks/sit2/01_clip_v1_oficial.ipynb` | Entrenamiento inicial, diagnóstico de overfitting y métricas base. |
| `notebooks/sit2/02_tiles_oficial.ipynb` | Exploración de tiles, clases, NDVI/NDBI, MODIS, S5P y temporalidad. |
| `notebooks/sit2/03_clip_v3_oficial.ipynb` | Entrenamiento final con LoRA, sin rama S5P. |
| `notebooks/sit2/04_sae_oficial.ipynb` | SAE, PCA/AFE, Varimax y AFC con `semopy`. |
| `notebooks/sit2/05_clip_v4_group_split.ipynb` | Auditoría con split temporal estricto. |
| `notebooks/sit2/06_auditoria_estadistica_tiles.ipynb` | Auditoría estadística de tiles y rangos físicos. |
| `notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb` | Cruce tiles vs mediciones DAGMA/CVC. |
| `notebooks/sit2/08_clip_v4_reparacion_metricas.ipynb` | Auditoría Sit 2.1 con split 70/15/15, normalización train-only, `fusion` entrenable y retrieval real. |

También se revisaron los documentos reorganizados en `docs/situacion-2/`.

## 5. Dataset de tiles

Cada tile viene del panel Sentinel-2 de Situación 1.

| Archivo | Contenido |
|---|---|
| `tiles_train.npz` | tensor `(5000, 13, 64, 64)` |
| `tiles_meta.parquet` | metadata `(5000, 22)` |
| `scl_por_escena.csv` | cobertura limpia por escena S2 |

Bandas incluidas:

```text
B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12, SCL
```

La clase está balanceada:

| Clase | Tiles |
|---|---:|
| `contaminacion_alta_NO2` | 1,000 |
| `contaminacion_alta_SO2` | 1,000 |
| `ozono_anomalo` | 1,000 |
| `vegetacion_densa` | 1,000 |
| `suelo_urbano` | 1,000 |

Auditoría:

- correcto: las clases quedan balanceadas para entrenamiento contrastivo;
- correcto: la metadata conserva contexto S5P, ERA5, MODIS, NDVI/NDBI y texto;
- importante: SCL está dentro del tensor, pero el modelo final usa 12 bandas ópticas para entrenamiento.

## 6. Muestreo estratificado

El muestreo no fue aleatorio puro. Usó tres estrategias según la clase.

| Clase | Estrategia | Fuente guía |
|---|---|---|
| `contaminacion_alta_NO2` | percentil alto | S5P NO₂ > p90 |
| `contaminacion_alta_SO2` | percentil alto | S5P SO₂ > p90 |
| `ozono_anomalo` | percentil alto | S5P O₃ > p95 |
| `vegetacion_densa` | aleatorio + filtro espectral | NDVI > 0.6 |
| `suelo_urbano` | proximidad a estaciones | DAGMA/CVC + NDVI < 0.3 |

La fórmula usada para vegetación fue:

$$
NDVI = \frac{B8 - B4}{B8 + B4}
$$

Auditoría:

- correcto: S5P se usa como pseudo-label débil, no como verdad superficial directa;
- correcto: vegetación se define con NDVI alto;
- defendible: suelo urbano se guía por estaciones oficiales porque el área urbana es pequeña frente al BBox total;
- cuidado: `ozono_anomalo` usa columna total de O₃, no ozono superficial.

## 7. Fórmula CLIP / InfoNCE

CLIP aprende a acercar embeddings de imagen y texto correctos, y separar pares incorrectos.

Para una imagen $i$ y su texto $t$:

$$
L_{img \rightarrow txt} = -\log \frac{\exp(sim(z_i, z_t)/\tau)}{\sum_j \exp(sim(z_i, z_{t_j})/\tau)}
$$

La pérdida bidireccional se resume como:

$$
L_{CLIP} = \frac{1}{2}(L_{img \rightarrow txt} + L_{txt \rightarrow img})
$$

Donde:

| Símbolo | Significado |
|---|---|
| $z_i$ | embedding visual del tile |
| $z_t$ | embedding textual |
| $sim$ | similitud coseno |
| $\tau$ | temperatura aprendible |

En el proyecto, los textos describen clases ambientales y condiciones físicas. Esto permite entrenar representaciones sin tener una etiqueta manual perfecta por píxel.

## 8. Evolución del modelo: v1, v3 y v4

### v1: diagnóstico inicial

La primera versión entrenó demasiados parámetros y presentó overfitting.

| Métrica v1 | Resultado |
|---|---:|
| Train loss final | 0.9546 |
| Val loss final | 4.8808 |
| Mejor R@5 | 0.130 |
| Zero-shot accuracy | 0.407 |

Además, la versión histórica con S5P como input directo podía aprender el pseudo-label como atajo. Eso se marcó como data leakage y no se usa como modelo final.

### v3: modelo final

La versión final corrigió el problema principal.

| Cambio | Decisión |
|---|---|
| Fine-tuning completo | reemplazado por LoRA rank=16 |
| Rama S5P | eliminada |
| Data augmentation | flip + rotaciones 0/90/180/270 |
| Textos | 5 templates por clase |
| Early stopping | mejor epoch 11 |
| Parámetros entrenables | 2.1M / 152.8M |

Auditoría:

- correcto: quitar S5P como input evita leakage directo;
- correcto: LoRA reduce overfitting frente a fine-tuning completo;
- correcto: augmentations ayudan con invariancias espaciales simples.

### v4: auditoría temporal

v4 no reemplaza al modelo final. Se usa para medir robustez con fechas completas fuera del train.

| Criterio | Resultado |
|---|---:|
| Train | 4,531 |
| Val | 469 |
| Fechas val | 8 |
| Fechas compartidas train/val | 0 |
| R@1 | 0.386 |
| R@5 | 1.000 |
| Zero-shot | 0.386 |
| Zero-shot solo visual | 0.401 |

Lectura: el rendimiento baja bajo split temporal estricto, pero no cae a azar. Por eso v4 es evidencia de robustez parcial, no el checkpoint principal.

## 9. Resultados CLIP

Resultados principales del modelo final v3:

| Métrica | Resultado | Lectura |
|---|---:|---|
| Class prototype accuracy v3 | 0.483-0.500 | separabilidad por clase sobre azar |
| Class prototype accuracy Sit 2.1 test | 0.496 | se mantiene señal visual por clase |
| Class prototype top-3 Sit 2.1 test | 0.925 | la clase correcta suele quedar entre las 3 más cercanas |
| Retrieval real R@1 Sit 2.1 test | 0.0027 | no cumple KPI PDF |
| Retrieval real R@5 Sit 2.1 test | 0.0147 | no cumple KPI PDF |
| Retrieval real R@10 Sit 2.1 test | 0.0240 | bajo para recuperación exacta imagen-texto |
| k-NN accuracy Sit 2.1 test | 0.404 | embeddings separables, pero menos que v3 original |

Comparación importante:

| Modelo | Lectura |
|---|---|
| v1 | útil como diagnóstico, pero con overfitting y riesgo de leakage. |
| v3 | modelo final: sin S5P directo, LoRA, mejores métricas. |
| v4 group split | auditoría temporal: más estricta, menor R@1, robustez parcial. |
| Sit 2.1 reparación | auditoría de métricas: muestra que el retrieval real imagen-texto es bajo, aunque la clasificación por prototipo se mantiene cerca de 0.50. |

Cuidado con Recall@K: la auditoría Sit 2.1 mostró que el Recall@K real imagen-texto es bajo. Lo que sí se sostiene es la separabilidad por clase: el modelo aproxima bien prototipos semánticos de clase, pero no recupera el texto exacto asociado a cada tile.

## 10. SAE: Sparse Autoencoder

Después del CLIP, el proyecto entrenó un Sparse Autoencoder sobre embeddings de 512 dimensiones.

Arquitectura:

```text
512 → 256 → 512
```

La pérdida combina reconstrucción y penalización de sparsity:

$$
L_{SAE} = ||x - \hat{x}||_2^2 + \lambda ||z||_1
$$

| Símbolo | Significado |
|---|---|
| $x$ | embedding CLIP original |
| $\hat{x}$ | embedding reconstruido |
| $z$ | representación latente sparse |
| $\lambda$ | peso de la penalización L1 |

Resultados:

| KPI | Resultado | Meta |
|---|---:|---:|
| MSE reconstrucción | 0.000215 | ≤ 0.05 |
| Sparsity ratio | 0.765 | ≥ 0.70 |
| Neuronas activas por muestra | 60 / 256 | — |

Auditoría:

- correcto: el SAE reconstruye bien y fuerza una representación sparse;
- defendible: permite buscar neuronas asociadas a clases o patrones;
- cuidado: una neurona activa no prueba causalidad física, solo asociación en embedding.

## 11. AFE y AFC

### AFE

El Análisis Factorial Exploratorio se hizo con PCA sobre embeddings de 512 dimensiones.

| Componente | Varianza explicada | Acumulado |
|---|---:|---:|
| PC1 | 31.6% | 31.6% |
| PC2 | 22.3% | 53.9% |
| PC3 | 13.0% | 66.9% |
| PC4 | 8.6% | 75.5% |
| PC5 | 3.2% | 78.7% |
| PC6 | 2.0% | 80.6% |

Resultado clave:

> 6 factores explican cerca del 80.6% de la varianza.

Lectura: hay estructura latente concentrada. PC1 separa principalmente `suelo_urbano` de `vegetacion_densa`.

### AFC

El Análisis Factorial Confirmatorio usó 4 constructos latentes con variables observables de `tiles_meta.parquet`.

| Índice | Resultado | Meta | Lectura |
|---|---:|---:|---|
| CFI | 0.933 | > 0.90 | cumple |
| RMSEA | 0.109 | < 0.08 | queda alto |

Auditoría:

- CFI respalda ajuste aceptable;
- RMSEA no cumple la meta estricta;
- con N=5,000, el chi-cuadrado puede volver RMSEA más sensible;
- no conviene vender AFC como “perfecto”, sino como soporte parcial.

## 12. Auditorías: tiles y puente DAGMA/CVC

### Auditoría estadística de tiles

El notebook `06_auditoria_estadistica_tiles.ipynb` revisó:

- balance de clases;
- NaN/Inf;
- rangos físicos;
- distribución temporal;
- SCL;
- MODIS y ERA5;
- estadísticas globales y por clase.

Hallazgos relevantes:

| Tema | Lectura |
|---|---|
| MODIS AOD | baja cobertura, esperable por nubosidad. |
| MODIS final | rangos físicos en `tiles_meta.parquet`. |
| SCL | mayoría de tiles limpios, pero el umbral mínimo acepta 30%. |
| MGRS | predominio fuerte de `T18NUJ`; `T18NUK` casi no entra. |

### Auditoría puente DAGMA/CVC

Esta auditoría cruza tiles con mediciones oficiales cercanas. No valida CLIP como predictor; solo revisa coherencia externa.

| Elemento | Resultado |
|---|---:|
| Tiles revisados | 5,000 |
| Observaciones DAGMA/CVC filtradas | 107,291 |
| Días con datos DAGMA/CVC | 1,640 |
| Ventanas | mismo día, ±1 día, ±3 días |

Resultados por contaminante:

| Contaminante | Mejor lectura | Detalle |
|---|---|---|
| NO₂ | coherente solo mismo día | mediana objetivo 14.88 vs resto 13.32 |
| O₃ | coherente solo mismo día | mediana objetivo 17.63 vs resto 16.75 |
| SO₂ | débil o inversa | objetivo queda menor que resto |

Auditoría:

- NO₂ y O₃ tienen soporte externo puntual;
- SO₂ es la clase más débil frente a superficie;
- al ampliar ventana temporal, la señal se diluye o invierte;
- la auditoría sirve como puente hacia Situación 3, no como validación predictiva final.

## 13. Qué está bien defendible

- Hay 5,000 tiles balanceados, con metadata y contexto físico.
- El muestreo estratificado sigue el rol de pseudo-labels S5P pedido por el PDF.
- La versión final elimina S5P como input directo, reduciendo data leakage.
- CLIP v3/Sit 2.1 muestran señal visual por clase, pero el Recall@K imagen-texto real no cumple el KPI literal del PDF.
- v4 aporta una validación temporal más estricta, aunque con menor R@1.
- SAE cumple reconstrucción y sparsity.
- AFE encuentra estructura compacta en pocos factores.
- AFC tiene CFI aceptable, aunque RMSEA alto.
- Las auditorías declaran limitaciones en vez de ocultarlas.

## 14. Qué hay que cuidar en defensa

| Riesgo | Cómo explicarlo |
|---|---|
| v1 tuvo leakage | Fue diagnóstico; el modelo final elimina S5P directo. |
| Split v3 aleatorio | Mide separabilidad mezclada, no generalización temporal estricta. |
| Recall@K v3 | No reportarlo como retrieval imagen-texto real; Sit 2.1 mostró R@5 test = 0.0147. |
| v4 baja R@1 | Es auditoría más dura; no reemplaza el checkpoint principal. |
| O₃ S5P | Es columna total, no ozono superficial. |
| SO₂ débil frente DAGMA | Se mantiene como pseudo-label satelital, no como predicción in-situ. |
| MODIS antiguo roto | No afecta CLIP final; tiles finales tienen rangos físicos. |
| SCL mínimo 30% | Algunos tiles pueden tener nubosidad; la mayoría tiene SCL alto. |
| AFC RMSEA alto | CFI cumple; RMSEA se reporta como limitación. |

## 15. Referencias y documentación

### Internas

- [Situación 2](../situacion-2/README.md)
- [Muestreo Sit 2](../situacion-2/MUESTREO_SIT2.md)
- [CLIP + SAE Sit 2](../situacion-2/SIT2_CLIP_SAE.md)
- [Entrenamiento Sit 2](../situacion-2/SIT2_ENTRENAMIENTO.md)
- [Auditoría de sesgos Sit 1 → Sit 2](../situacion-2/AUDITORIA_SESGOS_SIT1_SIT2.md)
- [Resultados CLIP](../situacion-2/resultados/resultados-clip.md)
- [Resultados CLIP Sit 2.1 reparación](../situacion-2/resultados/resultados-clip-sit2-1-reparacion.md)
- [Resultados SAE, AFE y AFC](../situacion-2/resultados/resultados-sae-afe-afc.md)
- [Auditoría DAGMA/CVC](../situacion-2/resultados/auditoria-dagma-cvc.md)
- [Fórmulas del modelo](03_formulas_modelo.md)
- [Situación 1: panel de datos](05_situacion_1_panel_datos.md)

### Notebooks revisados

- [`notebooks/sit2/01_clip_v1_oficial.ipynb`](../../notebooks/sit2/01_clip_v1_oficial.ipynb)
- [`notebooks/sit2/02_tiles_oficial.ipynb`](../../notebooks/sit2/02_tiles_oficial.ipynb)
- [`notebooks/sit2/03_clip_v3_oficial.ipynb`](../../notebooks/sit2/03_clip_v3_oficial.ipynb)
- [`notebooks/sit2/04_sae_oficial.ipynb`](../../notebooks/sit2/04_sae_oficial.ipynb)
- [`notebooks/sit2/05_clip_v4_group_split.ipynb`](../../notebooks/sit2/05_clip_v4_group_split.ipynb)
- [`notebooks/sit2/06_auditoria_estadistica_tiles.ipynb`](../../notebooks/sit2/06_auditoria_estadistica_tiles.ipynb)
- [`notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb`](../../notebooks/sit2/07_auditoria_puente_dagma_tiles.ipynb)
- [`notebooks/sit2/08_clip_v4_reparacion_metricas.ipynb`](../../notebooks/sit2/08_clip_v4_reparacion_metricas.ipynb)

### Salidas de auditoría

- [`resumen_auditoria_tiles.json`](../../notebooks/sit2/auditoria_tiles_local_output/auditoria_tiles/resumen_auditoria_tiles.json)
- [`resumen_auditoria_puente_dagma.json`](../../notebooks/sit2/auditoria_puente_dagma_local_output/auditoria_puente_dagma/resumen_auditoria_puente_dagma.json)

### Externas

- [CLIP — Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- [RemoteCLIP — A Vision Language Foundation Model for Remote Sensing](https://ieeexplore.ieee.org/document/10504785)
- [LoRA — Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [Rouse et al. 1973 — NDVI](https://ntrs.nasa.gov/citations/19740022614)
- [Earth Engine — Sentinel-5P NO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Earth Engine — Sentinel-5P SO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Earth Engine — Sentinel-5P O₃](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
