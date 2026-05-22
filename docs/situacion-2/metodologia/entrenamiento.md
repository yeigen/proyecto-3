# Entrenamiento

## Qué contiene

Resumen del entrenamiento CLIP y sus iteraciones principales.

## Iteraciones

### v1

La primera versión hizo fine-tune de muchos parámetros y usó una rama S5P. Sirvió como diagnóstico, pero tuvo overfitting y data leakage.

### v2/v3 final

La versión final elimina S5P como input directo y usa LoRA.

| Métrica | Resultado final |
|---|---:|
| Recall@1 | 0.483 |
| Recall@5 | 1.000 |
| Zero-shot accuracy | 0.500 |
| k-NN accuracy | 0.430 |

## Auditoría v4

Se entrenó una versión con split temporal por fechas completas. No reemplaza el modelo final, pero muestra robustez parcial sin fechas compartidas.

| Métrica | v4 temporal |
|---|---:|
| Recall@1 | 0.386 |
| Recall@5 | 1.000 |
| Zero-shot accuracy | 0.386 |
| k-NN accuracy | 0.394 |

## Evidencias relacionadas

- [Curvas de aprendizaje](../evidencias/entrenamiento/sit2_entrenamiento_curvas_aprendizaje.png)
- [Matriz de confusión](../evidencias/entrenamiento/sit2_entrenamiento_clip_confusion_matrix.png)
- [Resultados de entrenamiento](../evidencias/entrenamiento/sit2_entrenamiento_training_results.png)

## Referencias

- [Entrenamiento Sit 2 original](../SIT2_ENTRENAMIENTO.md)
- [CLIP + SAE Sit 2 original](../SIT2_CLIP_SAE.md)
- [Notebook CLIP v1](../../../notebooks/sit2/01_clip_v1_oficial.ipynb)
- [Notebook CLIP final](../../../notebooks/sit2/03_clip_v3_oficial.ipynb)
- [Notebook split temporal v4](../../../notebooks/sit2/05_clip_v4_group_split.ipynb)
