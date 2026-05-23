# 08. Cumplimiento global frente al PDF

Este documento resume el estado real del proyecto frente al PDF. Está pensado para defensa: qué cumple, qué cumple parcialmente, qué no está verificado y cómo explicarlo sin prometer más de lo probado.

## 1. Veredicto ejecutivo

El proyecto cumple con fuerza la ingeniería de datos de Situación 1. En Situación 2 hay una señal visual multimodal real y sin leakage directo de S5P, pero la auditoría Sit 2.1 mostró que el Recall@K imagen-texto literal del PDF no se cumple. La Situación 3 es el componente más limitado: se implementó y evaluó ConvLSTM, Ridge y Kriging Ordinario, pero el pipeline ST-Kriging multi-horizonte con Moran/LISA e incertidumbre queda como cierre técnico pendiente.

Dicho de forma directa:

| Situación | Veredicto |
|---|---|
| Situación 1 | Cumple |
| Situación 2 | Cumple parcialmente, con señal por clase pero sin Recall@K real suficiente |
| Situación 3 | Cumple parcialmente, con faltantes importantes |

La defensa debe ser honesta: el proyecto no replica al 100% todo el PDF, pero sí tiene evidencia fuerte en datos, aprendizaje multimodal y una evaluación geoestadística inicial.

## 2. Semáforo global

| Bloque | Estado | Evidencia principal | Riesgo |
|---|---|---|---|
| Situación 1 | Cumple | 89.73 GB, Zarr, manifest, EDA | token HF en notebook manifest |
| Situación 2 | Cumple parcialmente | CLIP/Sit 2.1: class prototype test=0.496, SAE/AFE/CFI | retrieval real R@5 test=0.0147, no end-to-end literal, RMSEA alto |
| Situación 3 | Cumple parcialmente | ConvLSTM, LOO-CV, Kriging SO₂/O₃ | falta ST-Kriging/Moran/LISA/NO₂ LOO-CV |

Estados usados:

| Estado | Significado |
|---|---|
| Cumple | Hay evidencia suficiente y coherente con el PDF. |
| Cumple parcialmente | Hay implementación real, pero no replica todo lo pedido. |
| No verificado | No hay salida o evidencia suficiente para afirmarlo. |
| No evaluable por datos | Los datos disponibles no permiten medirlo de forma honesta. |
| No cumple | La métrica o requisito queda por debajo del umbral. |

## 3. Situación 1: panel de datos

### Veredicto

Situación 1 es la parte más fuerte del proyecto.

| Requisito PDF | Evidencia real | Estado |
|---|---|---|
| Dataset ≥ 50 GB | 89.73 GB en Kaggle | Cumple |
| Formato Zarr/Parquet | 6 paneles Zarr + DAGMA/CVC | Cumple |
| Fuentes satelitales | Sentinel-2, Sentinel-5P, ERA5, MODIS | Cumple |
| Ground truth DAGMA/SISAIRE | parquet DAGMA/CVC 107,291 filas | Cumple |
| Manifest con hashes | `manifest/manifest_output/manifest.json` | Cumple |
| EDA con visualizaciones | EDA general y EDA completo | Cumple |
| Cloud/object storage | Kaggle, HF, GCS documentados | Cumple |

### Lo defendible

- El dataset supera el umbral de 50 GB.
- Zarr es apropiado para arrays multidimensionales grandes.
- Las fuentes obligatorias están presentes.
- Las unidades están documentadas: S5P en `mol/m²`, DAGMA en `ug/m3`, MODIS AOD adimensional escalado.
- El BBox ampliado es defendible porque incluye Yumbo/Acopi y zona industrial relevante.

### Riesgos

| Riesgo | Cómo explicarlo |
|---|---|
| BBox no idéntico al PDF | Se amplió para cubrir Yumbo/Acopi y caña al norte, relevantes para NO₂/SO₂. |
| MODIS tuvo versiones rotas | Se auditó y se documentó la versión corregida con escala/máscara. |
| NO₂ solo en Yumbo | Es limitación del ground truth, afecta Situación 3. |
| Token HF en manifest notebook | Debe limpiarse antes de entrega pública. |

## 4. Situación 2: CLIP + SAE

### Veredicto

Situación 2 cumple el objetivo metodológico central, pero no replica literalmente la arquitectura completa del PDF.

| Requisito PDF | Evidencia real | Estado |
|---|---|---|
| Mínimo 1,000 pares | 5,000 pares | Cumple |
| 5 clases | 5 clases balanceadas | Cumple |
| Tiles 64×64 | `(5000, 13, 64, 64)` | Cumple |
| Pseudo-labels S5P | NO₂ p90, SO₂ p90, O₃ p95 | Cumple |
| RemoteCLIP | RemoteCLIP ViT-B/32 + LoRA | Cumple |
| Evitar S5P como input directo | v3 elimina rama S5P | Cumple |
| Recall@1 ≥ 0.45 | Sit 2.1 retrieval real test = 0.0027 | No cumple |
| Recall@5 ≥ 0.70 | Sit 2.1 retrieval real test = 0.0147 | No cumple |
| SAE sparsity ≥ 0.70 | 0.765 | Cumple |
| SAE MSE ≤ 0.05 | 0.000215 | Cumple |
| AFE ≥ 80% varianza | 80.6% con 6 factores | Cumple |
| CFI > 0.90 | 0.933 | Cumple |
| RMSEA < 0.08 | 0.109 | No cumple |
| SAE visual/textual end-to-end | SAE post-hoc | Cumple parcialmente |
| Split 70/15/15 | v3 94/6 + v4 temporal | Cumple parcialmente |

### Lo defendible

- El modelo final evita la penalización más grave: no pasa S5P como input directo.
- CLIP v3/Sit 2.1 conserva señal visual por clase, pero no cumple los KPIs literales de retrieval imagen-texto.
- SAE cumple reconstrucción y sparsity.
- AFE cumple el umbral de varianza.
- CFI cumple el umbral de AFC.
- La auditoría v4 temporal muestra robustez parcial sin fechas compartidas.

### Riesgos

| Riesgo | Cómo explicarlo |
|---|---|
| No hay CLIP+dos-SAE end-to-end literal | Se implementó una versión estable: CLIP con LoRA + SAE post-hoc para interpretabilidad. |
| RMSEA alto | CFI cumple, pero RMSEA se reporta como limitación. |
| Split no literal 70/15/15 | Sit 2.1 corrige el split, pero al medir retrieval real los KPIs bajan fuerte. |
| Recall@K anterior | El R@5=1.000 era métrica por prototipo/clase, no retrieval imagen-texto real. |
| SO₂ débil frente DAGMA | Es pseudo-label satelital, no predicción in-situ. |
| O₃ S5P | Es columna total, no ozono superficial. |

## 5. Situación 3: geoestadística

### Veredicto

Situación 3 es el componente más incompleto frente al PDF. Hay implementación real y resultados útiles, pero no alcanza el pipeline completo exigido.

| Requisito PDF | Evidencia real | Estado |
|---|---|---|
| Usar embeddings CLIP | embeddings `(5000, 512)` | Cumple parcialmente |
| Secuencias de 8 fechas | 2,839 secuencias | Cumple parcialmente |
| ConvLSTM | implementada, loss baja | Cumple |
| LOO-CV por estación | ConvLSTM/Ridge evaluados; Kriging documentado | Cumple parcialmente |
| RMSE SO₂ ≤ 6 | 5.78 por Kriging documentado | Cumple |
| RMSE O₃ ≤ 12 | 5.93 por Kriging documentado | Cumple |
| RMSE NO₂ ≤ 8 | solo una estación | No evaluable por datos |
| R² promedio ≥ 0.55 | R² negativos | No cumple |
| ST-Kriging 3D | no implementado/verificado | No verificado |
| Moran I | pendiente | No verificado |
| LISA | pendiente | No verificado |
| Variograma residuos | pendiente | No verificado |
| Mapas 3×3 | no encontrados | No verificado |
| Latencia < 8 s | no medida | No verificado |

### Lo defendible

- Se intentó ConvLSTM con embeddings y secuencias reales.
- ConvLSTM converge en loss, pero no generaliza en LOO-CV.
- Ridge baseline también falla, lo que indica que el problema no es solo la arquitectura.
- Kriging Ordinario da errores razonables para SO₂ y O₃.
- NO₂ no se fuerza: se declara no evaluable por tener una sola estación.

### Riesgos

| Riesgo | Cómo explicarlo |
|---|---|
| Decir que Sit 3 cumple todo | No es cierto; es parcial. |
| ST-Kriging no implementado | Se usó Kriging Ordinario 2D como alternativa práctica inicial. |
| Moran/LISA pendientes | No reportarlos como resultados. |
| R² negativo | Indica baja explicación de varianza; MAE/RMSE siguen siendo útiles con pocas estaciones. |
| NO₂ | No hay LOO-CV espacial posible con una sola estación. |

## 6. Riesgos principales de defensa

| Riesgo global | Impacto | Mitigación |
|---|---|---|
| Sobrevender Situación 3 | Alto | Decir explícitamente que es parcial. |
| Ocultar desviaciones de Sit 2 | Alto | Explicar SAE post-hoc y plan end-to-end futuro. |
| Prometer NO₂ LOO-CV | Alto | Declarar no evaluable por datos. |
| Reportar Moran/LISA sin evidencia | Alto | Mantener como pendiente. |
| Token HF en notebook manifest | Medio | Limpiar antes de entrega pública. |
| Confundir S5P con DAGMA | Medio | Recordar S5P `mol/m²` vs DAGMA `µg/m³`. |
| Decir AOD = PM2.5 | Medio | Presentar AOD solo como proxy óptico. |

## 7. Qué sí se puede afirmar

- El proyecto construyó un panel multi-fuente mayor a 50 GB.
- El panel usa formatos adecuados para datos geoespaciales grandes.
- Se revisaron unidades, escalas y problemas de bandas.
- Sit 2 entrenó un modelo CLIP sin S5P como input directo.
- Sit 2 cumple KPIs SAE/AFE/CFI y muestra señal visual por clase; no cumple Recall@K imagen-texto real.
- Sit 2 tiene auditorías de sesgo, temporalidad y puente DAGMA.
- Sit 3 intentó ConvLSTM y evaluó generalización con LOO-CV.
- Sit 3 encontró que Kriging Ordinario funciona mejor que ConvLSTM/Ridge para SO₂/O₃.
- Las limitaciones de NO₂, O₃ columna total, SO₂ débil y pocas estaciones están documentadas.

## 8. Qué no se debe afirmar

- Que Sit 3 implementa completamente ST-Kriging multi-horizonte.
- Que hay mapas 3×3 validados para NO₂, SO₂ y O₃.
- Que Moran I y LISA ya cumplen el PDF.
- Que NO₂ tiene LOO-CV espacial robusto.
- Que Sit 2 cumple Recall@K imagen-texto literal del PDF.
- Que el SAE de Sit 2 fue entrenado end-to-end dentro de CLIP.
- Que RMSEA cumple en AFC.
- Que S5P mide lo mismo que DAGMA/CVC.
- Que MODIS AOD es PM2.5 directo.

## 9. Plan de cierre técnico

Prioridad alta antes de entrega final:

1. Limpiar token HF del notebook `manifest/manifest.ipynb`.
2. Re-ejecutar o consolidar notebook de Situación 3 con Kriging outputs visibles.
3. Calcular Moran I y LISA si hay superficie/predicciones suficientes.
4. Ajustar variograma de residuos y documentar si hay estructura remanente.
5. Generar mapas de incertidumbre si Kriging devuelve varianza utilizable.
6. Solo después, evaluar ST-Kriging 3D si los datos realmente lo soportan.
7. Si queda tiempo en Kaggle GPU, ejecutar el plan experimental CLIP+SAE end-to-end.

Planes ya escritos:

- [Plan CLIP + SAE end-to-end experimental](../superpowers/plans/2026-05-22-situacion-2-cumplimiento-literal-clip-sae.md)
- [Plan de cierre literal Situación 3](../superpowers/plans/2026-05-22-situacion-3-cierre-literal-pdf.md)

## 10. Referencias internas

- [Situación 1: panel de datos](05_situacion_1_panel_datos.md)
- [Situación 2: CLIP + SAE](06_situacion_2_clip_sae.md)
- [Situación 3: geoestadística](07_situacion_3_geoestadistica.md)
- [Objetivo del proyecto](00_objetivo_del_proyecto.md)
- [Datasets y variables](01_datasets_y_variables.md)
- [Unidades de contaminantes](02_unidades_contaminantes.md)
- [Fórmulas del modelo](03_formulas_modelo.md)
- [Geoestadística conceptual](04_geoestadistica.md)
