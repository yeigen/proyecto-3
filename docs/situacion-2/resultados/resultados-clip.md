# Resultados CLIP

## Qué contiene

Resultados principales del modelo CLIP final sin rama S5P.

## Modelo final vigente

La versión final vigente para el componente CLIP + SAE es el notebook `17-clip-sae-pseudolabel.ipynb`, documentado en [Resultados CLIP Sit 2.17 pseudo-label retrieval](resultados-clip-sit2-17-pseudolabel.md).

| Métrica | Resultado | Lectura |
|---|---:|---|
| Recall@1 imagen→texto pseudo-label centroid | 0.505 | Cumple KPI mínimo |
| Recall@5 imagen→texto pseudo-label centroid | 1.000 | Cumple KPI |
| Sparsity ratio SAE visual | 0.728 | Cumple KPI |
| Reconstrucción SAE visual | 0.00924 | Cumple KPI |

## Versión previa de referencia

| Métrica | Resultado | Lectura |
|---|---:|---|
| Recall@1 | 0.483 | Cumplía KPI mínimo |
| Recall@5 | 1.000 | Cumplía KPI |
| Zero-shot accuracy | 0.500 | 2.5× chance |
| k-NN accuracy | 0.430 | Separabilidad útil |

## Lectura

El modelo aprende señal visual sin usar S5P como input directo. La versión 17 mejora la defensa metodológica porque evalúa retrieval imagen→texto en el nivel semántico del pseudo-label, que es la unidad real de etiquetado semi-supervisado del dataset.

## Evidencias relacionadas

- [Curvas de aprendizaje](../evidencias/entrenamiento/sit2_entrenamiento_curvas_aprendizaje.png)
- [Matriz de confusión](../evidencias/entrenamiento/sit2_entrenamiento_clip_confusion_matrix.png)
- [Resultados de entrenamiento](../evidencias/entrenamiento/sit2_entrenamiento_training_results.png)

## Referencias

- [Entrenamiento](../metodologia/entrenamiento.md)
- [Arquitectura CLIP + SAE](../metodologia/arquitectura-clip-sae.md)
- [CLIP + SAE Sit 2 original](../SIT2_CLIP_SAE.md)
