# Resultados CLIP Sit 2.3 S5P auxiliar controlado

Notebook: [`notebooks/sit2/10_clip_v6_s5p_aux_controlado.ipynb`](../../../notebooks/sit2/10_clip_v6_s5p_aux_controlado.ipynb).

Objetivo: evaluar si Sentinel-5P mejora la señal semántica de contaminación sin perder el avance de retrieval real logrado en Sit 2.2.

## Cambios frente a Sit 2.2

- agrega S5P NO2/SO2/O3 normalizado con train-only;
- agrega rama MLP auxiliar para S5P;
- permite ablations A/B/C;
- usa `BETA_CLASS = 0.35`;
- mantiene métricas separadas para retrieval real, prototipos y kNN.

## Baseline Sit 2.2

| Métrica | Valor |
|---|---:|
| retrieval test R@1 | 0.0493 |
| retrieval test R@5 | 0.1747 |
| retrieval test R@10 | 0.3000 |
| class prototype test acc | 0.4533 |
| kNN test acc | 0.4600 |

## Resultados Sit 2.3

Los resultados numéricos se completan solo después de ejecutar el notebook en Kaggle.

## Criterios de éxito

| Criterio | Umbral |
|---|---:|
| retrieval test R@5 preservado | >= 0.17 |
| retrieval test R@10 preservado | >= 0.30 |
| class prototype acc mejora Sit 2.2 | > 0.4533 |
| class prototype acc objetivo | >= 0.48 |
| kNN test preservado | >= 0.46 |

## Lectura metodológica

S5P se usa como señal auxiliar controlada porque el proyecto plantea integrar columnas atmosféricas satelitales. Para reducir leakage, las variables `no2`, `so2` y `o3` se normalizan solo con train y el texto atmosférico usa niveles discretizados, no valores exactos.

Si mejora la clasificación por prototipos sin perder retrieval, Sit 2.3 será una mejor candidata metodológica que Sit 2.2. Si solo mejora el retrieval por texto atmosférico pero no mejora kNN ni prototipos, el aporte de S5P debe reportarse como débil o parcialmente dependiente del texto.
