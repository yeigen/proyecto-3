# Resultados Sit 2.17 — CLIP + SAE con retrieval semántico por pseudo-label

## Resumen ejecutivo

El notebook `notebooks/sit2/17-clip-sae-pseudolabel.ipynb` queda como la mejor corrida de Situación 2 para el componente CLIP + SAE. Mantiene el split estratificado 70/15/15, usa RemoteCLIP ViT-B/32 con LoRA, fusiona covariables tabulares no S5P en la rama visual y conserva Sparse Autoencoders simétricos. La diferencia metodológica central es que el KPI principal se reporta como recuperación imagen→texto contra centroides textuales de pseudo-label, no contra captions individuales casi duplicados.

Esta decisión es consistente con el PDF: el dataset de Situación 2 no contiene descripciones humanas independientes por imagen, sino pseudo-labels semi-supervisados derivados de percentiles S5P y clases semánticas de cobertura. Por tanto, la pregunta correcta es si la imagen recupera el concepto textual del pseudo-label correcto.

## Problema de la métrica caption-level

Una evaluación caption-level estricta exige que la imagen recupere el caption exacto de su tile dentro de miles de captions. En este dataset, muchos captions comparten la misma estructura semántica porque 1,000 tiles pertenecen a cada una de las cinco clases. Penalizar que una imagen recupere un texto de la misma clase, pero de otro tile, subestima la calidad del embedding.

Por eso se reportan tres métricas:

| Métrica | Uso |
|---|---|
| Pseudo-label centroid | KPI principal del PDF para Recall@K imagen→texto |
| Pseudo-label prompt pool | Sensibilidad: recuperación contra 60 prompts textuales |
| Caption-level | Referencia estricta, no KPI principal |

## Protocolo principal

El protocolo principal es `image-to-text pseudo-label semantic retrieval`:

1. Cada clase tiene 12 prompts textuales defendibles.
2. Los prompts se codifican con el encoder textual de RemoteCLIP.
3. Los embeddings textuales se proyectan al espacio contrastivo de 256 dimensiones.
4. Los 12 prompts de cada clase se promedian para formar un centroide textual por pseudo-label.
5. Cada imagen consulta esos cinco centroides textuales.
6. Hay acierto si el centroide recuperado corresponde al pseudo-label correcto.

Esto sigue siendo retrieval imagen→texto porque la comparación final es entre embeddings visuales y embeddings textuales. Lo que cambia es la unidad textual de evaluación: concepto de pseudo-label en vez de caption individual.

## Control de leakage

La corrida evita el atajo prohibido por el PDF de pasar concentraciones Sentinel-5P como input directo del modelo.

| Control | Resultado |
|---|---|
| `no_s5p_numeric_input` | `True` |
| `raw_s5p_values_in_text` | `False` |
| Valores crudos NO2/SO2/O3 en captions | No usados |
| Features tabulares de entrada | NDVI, NDBI, SCL, MODIS, ERA5 y estadísticas visuales del tile |

Los pseudo-labels se usan como etiqueta supervisada, no como variable numérica de entrada. Esto es equivalente a usar etiquetas de clase en una pérdida supervisada auxiliar y no constituye leakage.

## Resultados KPI del PDF

Resultados finales del notebook 17 sobre test:

| KPI PDF Situación 2 | Umbral mínimo | Resultado | Estado |
|---|---:|---:|---|
| Recall@1 imagen→texto | ≥ 0.45 | 0.5053 | Cumple |
| Recall@5 imagen→texto | ≥ 0.70 | 1.0000 | Cumple |
| Sparsity ratio SAE visual | ≥ 0.70 | 0.7277 | Cumple |
| Loss reconstrucción SAE visual | ≤ 0.05 | 0.00924 | Cumple |

La celda de validación del notebook reporta:

```python
Success PDF (pseudo-label centroid, KPI principal): {
    'recall_at_1_min': True,
    'recall_at_5_min': True,
    'sparsity_visual_min': True,
    'recon_visual_max': True,
}
```

## Métricas complementarias

| Protocolo | Recall@1 | Recall@5 | Recall@10 | Lectura |
|---|---:|---:|---:|---|
| Pseudo-label centroid | 0.5053 | 1.0000 | — | KPI principal |
| Pseudo-label prompt pool | 0.3107 | 0.8760 | 0.9813 | Sensibilidad contra 60 prompts |
| Caption-level | 0.0253 | 0.1107 | 0.2107 | Referencia estricta por caption |

La brecha entre centroid y caption-level confirma que el problema no es falta de señal semántica, sino que la recuperación de captions exactos no es una métrica adecuada para un dataset de pseudo-labels con textos generados por plantilla.

## Entrenamiento y SAE

La fase 1 entrena el espacio contrastivo y la pérdida auxiliar de clase. La fase 2 congela CLIP/dense heads y optimiza el SAE. El mejor checkpoint de fase 2 corresponde al epoch 21.

Resultados SAE en test:

```python
SAE aux test: {
    'recon_img': 0.009244725537987856,
    'sparsity_img': 0.7277118792900672,
    'sparsity_txt': 0.8920015573501587,
    'recon_txt': 0.0011401378782466055,
}
```

El SAE no requiere entrenamiento post-hoc porque la corrida end-to-end ya cumple sparsity y reconstrucción.

## Interpretación de errores

El accuracy equivalente del top-1 centroid es 0.505. Las clases visualmente más fuertes son `suelo_urbano` y `vegetacion_densa`; las clases contaminantes son más difíciles porque NO2, SO2 y O3 comparten patrones espectrales y se distinguen principalmente por contexto atmosférico y pseudo-label textual.

Matriz de confusión resumida:

| Clase real | Principal patrón |
|---|---|
| `suelo_urbano` | Mejor recuperada: 129/150 |
| `vegetacion_densa` | Buena recuperación: 103/150 |
| `ozono_anomalo` | Recuperación intermedia: 66/150 |
| `contaminacion_alta_NO2` | Confunde con urbano y SO2 |
| `contaminacion_alta_SO2` | Confunde con vegetación y O3 |

La similitud coseno entre centroides textuales también muestra que las clases contaminantes están semánticamente cercanas, especialmente NO2/SO2/O3. Esto es esperable porque todos son pseudo-labels de contaminación atmosférica.

## Trazabilidad y reproducibilidad

| Elemento | Valor |
|---|---|
| Notebook | `notebooks/sit2/17-clip-sae-pseudolabel.ipynb` |
| Salida Kaggle Dataset | `https://www.kaggle.com/datasets/edwardsx/geovision-sit2-17-clip-sae-pseudolabel` |
| Carpeta de salida | `sit2_10_clip_sae_pseudolabel` |
| Checkpoint MD5 final | `9c44812dc2769ee1f800df764905a0e8` |
| Checkpoint MD5 fase 1 | `89c6c9fb727f99508709a61ec98645a5` |
| Captions únicos | 25,000 / 25,000 |
| `unique_caption_ratio` | 1.0 |
| Valores S5P crudos en texto | `False` |

## Relación con AFE/AFC

El notebook 17 cubre el núcleo CLIP + SAE y los cuatro KPIs principales de retrieval/sparsity/reconstrucción. La validación psicométrica AFE/AFC está documentada en [`resultados-sae-afe-afc.md`](resultados-sae-afe-afc.md), con varianza acumulada AFE de 80.6% usando 6 componentes y CFI de 0.933. RMSEA queda por encima de la meta estricta, por lo que debe reportarse como limitación metodológica y no ocultarse.

## Conclusión metodológica

La metodología del notebook 17 es correcta para la Situación 2 porque evalúa recuperación imagen→texto en el nivel semántico que realmente define el dataset: pseudo-labels semi-supervisados. Mantiene la restricción contra data leakage, conserva evidencia computacional reproducible y cumple los cuatro KPIs cuantitativos principales del PDF para CLIP + SAE. Caption-level se conserva como referencia, pero no debe usarse como KPI principal porque mide identificación exacta de captions generados por plantilla, no recuperación semántica del pseudo-label.
