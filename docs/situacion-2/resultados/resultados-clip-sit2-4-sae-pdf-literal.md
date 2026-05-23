# Resultados CLIP+SAE Sit 2.4 PDF literal

Notebook: [`notebooks/sit2/11_clip_sae_pdf_literal_retrieval.ipynb`](../../../notebooks/sit2/11_clip_sae_pdf_literal_retrieval.ipynb).

Objetivo: evaluar una implementación más fiel al PDF para Situación 2.

## Qué corrige frente a v3

- split 70/15/15 estratificado;
- normalización train-only;
- Recall@K real imagen→texto contra todos los textos del split;
- cinco captions por tile, siguiendo la lógica multi-caption de RemoteCLIP;
- textos en inglés;
- evaluación multi-caption: una imagen acierta si recupera cualquiera de sus 5 captions;
- no usa concentraciones Sentinel-5P crudas como input directo;
- no coloca valores S5P exactos en el texto;
- agrega SAE visual y textual;
- usa warmup de `alpha` para SAE;
- usa batch efectivo 128 con acumulación de gradiente;
- usa `L_total = L_InfoNCE + alpha * (L_sae_img + L_sae_txt)`.

## KPIs PDF mínimos

| KPI | Umbral |
|---|---:|
| Recall@1 imagen→texto | >= 0.45 |
| Recall@5 imagen→texto | >= 0.70 |
| Sparsity ratio SAE visual | >= 0.70 |
| Loss reconstrucción SAE visual | <= 0.05 |

## Resultados

Los resultados numéricos se completan solo después de ejecutar el notebook en Kaggle.

Outputs esperados:

```text
/kaggle/working/sit2_4_clip_sae_pdf_literal/metrics.json
/kaggle/working/sit2_4_clip_sae_pdf_literal/train_log.csv
/kaggle/working/sit2_4_clip_sae_pdf_literal/checkpoints/clip_sae_pdf_literal_best.pt
/kaggle/working/sit2_4_clip_sae_pdf_literal/checkpoint.md5
/kaggle/working/sit2_4_clip_sae_pdf_literal/embeddings/test_embeddings_sae_pdf_literal.npz
```

## Lectura esperada

Este notebook prioriza rigor metodológico frente al PDF. Si Recall@1 o Recall@5 no alcanzan los umbrales, el resultado se reporta como limitación real y no se reemplaza con métricas por prototipo de clase.
