# Resultados CLIP

## Qué contiene

Resultados principales del modelo CLIP final sin rama S5P.

## Modelo final

| Métrica | Resultado | Lectura |
|---|---:|---|
| Recall@1 | 0.483 | Cumple KPI mínimo |
| Recall@5 | 1.000 | Cumple KPI |
| Zero-shot accuracy | 0.500 | 2.5× chance |
| k-NN accuracy | 0.430 | Separabilidad útil |

## Lectura

El modelo aprende señal visual sin usar S5P como input directo. La validación principal es aleatoria global, por lo que mide separabilidad bajo distribución mezclada.

## Evidencias relacionadas

- [Curvas de aprendizaje](../evidencias/entrenamiento/sit2_entrenamiento_curvas_aprendizaje.png)
- [Matriz de confusión](../evidencias/entrenamiento/sit2_entrenamiento_clip_confusion_matrix.png)
- [Resultados de entrenamiento](../evidencias/entrenamiento/sit2_entrenamiento_training_results.png)

## Referencias

- [Entrenamiento](../metodologia/entrenamiento.md)
- [Arquitectura CLIP + SAE](../metodologia/arquitectura-clip-sae.md)
- [CLIP + SAE Sit 2 original](../SIT2_CLIP_SAE.md)
