# Resultados CLIP Sit 2.2 textos ricos + loss mixta

Notebook: [`notebooks/sit2/09_clip_v5_textos_ricos_loss_mixta.ipynb`](../../../notebooks/sit2/09_clip_v5_textos_ricos_loss_mixta.ipynb).

Objetivo: mejorar retrieval real imagen-texto frente a Sit 2.1.

## Cambios frente a Sit 2.1

- textos ricos por tile usando metadata real;
- split 70/15/15 estratificado;
- normalización calculada solo con train;
- InfoNCE pairwise como pérdida principal;
- pérdida auxiliar de clase contra prototipos textuales;
- loss total: `loss_pairwise + 0.25 * loss_class`;
- métricas separadas para retrieval real, prototipos y kNN.

## Baseline Sit 2.1

| Métrica | Valor |
|---|---:|
| retrieval test R@1 | 0.0027 |
| retrieval test R@5 | 0.0147 |
| retrieval test R@10 | 0.0240 |
| class prototype test acc | 0.496 |
| kNN test acc | 0.404 |

## Resultados Sit 2.2

Los resultados numéricos de Sit 2.2 se completan solo después de ejecutar el notebook en Kaggle.

Outputs esperados:

```text
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/metrics.json
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/train_log.csv
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/checkpoints/clip_v5_textos_ricos_best.pt
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/checkpoint.md5
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/text_richness_stats.json
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/figures/training_curves.png
/kaggle/working/sit2_2_clip_textos_ricos_loss_mixta/figures/confusion_test.png
```

## Criterios de éxito

| Criterio | Umbral |
|---|---:|
| retrieval test R@5 | mayor que 0.0147 |
| retrieval test R@10 | mayor que 0.0240 |
| class prototype test acc | al menos 0.45 |
| kNN test acc | al menos 0.40 |

## Lectura esperada

Si sube el retrieval real sin caer por debajo de los umbrales de clase y kNN, Sit 2.2 sería mejor candidata metodológica que Sit 2.1. Si no sube, el hallazgo sigue siendo útil: los textos ricos discretizados no serían suficientes y habría que pasar a una formulación más fuerte, como CLIP+SAE end-to-end o descripciones continuas más identificables por tile.
