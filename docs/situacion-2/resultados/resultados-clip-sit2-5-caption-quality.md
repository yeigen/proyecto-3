# Resultados CLIP+SAE Sit 2.5 caption quality

Notebook: [`notebooks/sit2/12_clip_sae_caption_quality_retrieval.ipynb`](../../../notebooks/sit2/12_clip_sae_caption_quality_retrieval.ipynb).

Objetivo: mejorar Recall@K imagen→texto atacando el problema detectado en Sit 2.4: captions demasiado repetidas.

## Cambios frente a Sit 2.4

- captions en inglés más específicas y únicas;
- auditoría textual antes de entrenar;
- bloqueo si `unique_caption_ratio < 0.60`;
- batch efectivo 128;
- sampler balanceado por clase;
- SAE con warmup suave hasta `alpha = 0.05`;
- `LAMBDA_L1 = 1e-2` para subir sparsity;
- mantiene evaluación multi-caption y KPIs PDF.

## Baseline Sit 2.4

| Métrica | Valor |
|---|---:|
| Recall@1 test | 0.0107 |
| Recall@5 test | 0.0760 |
| Recall@10 test | 0.1400 |
| Sparsity SAE visual | 0.4827 |
| Recon SAE visual | 0.1176 |
| Captions únicas | 633 / 25000 |
| Unique caption ratio | 0.0253 |

## KPIs PDF mínimos

| KPI | Umbral |
|---|---:|
| Recall@1 imagen→texto | >= 0.45 |
| Recall@5 imagen→texto | >= 0.70 |
| Sparsity ratio SAE visual | >= 0.70 |
| Loss reconstrucción SAE visual | <= 0.05 |

## Resultados Sit 2.5

Los resultados numéricos se completan después de ejecutar el notebook en Kaggle.

Primero debe verificarse:

```text
unique_caption_ratio >= 0.60
```

Si el notebook se detiene en esa auditoría, hay que ajustar captions antes de entrenar.
