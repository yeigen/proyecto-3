# Resultados SAE, AFE y AFC

## Qué contiene

Resultados de interpretabilidad sobre embeddings del modelo CLIP final.

## SAE

| KPI | Resultado | Meta |
|---|---:|---:|
| MSE reconstrucción | 0.000215 | ≤ 0.05 |
| Sparsity ratio | 0.765 | ≥ 0.70 |
| Neuronas activas por muestra | 60 / 256 | — |

## AFE

PCA sobre embeddings de 512 dimensiones:

| Componente | Varianza explicada | Acumulado |
|---|---:|---:|
| PC1 | 31.6% | 31.6% |
| PC2 | 22.3% | 53.9% |
| PC3 | 13.0% | 66.9% |
| PC4 | 8.6% | 75.5% |
| PC5 | 3.2% | 78.7% |
| PC6 | 2.0% | 80.6% |

## AFC

| Índice | Resultado | Meta |
|---|---:|---:|
| CFI | 0.933 | > 0.90 |
| RMSEA | 0.109 | < 0.08 |

CFI cumple. RMSEA queda alto, probablemente sensible al tamaño muestral de 5,000.

## Referencias

- [Arquitectura CLIP + SAE](../metodologia/arquitectura-clip-sae.md)
- [CLIP + SAE Sit 2 original](../SIT2_CLIP_SAE.md)
- [Notebook SAE/AFE/AFC](../../../notebooks/sit2/04_sae_oficial.ipynb)
