# Resultados CLIP Sit 2.1 reparación de métricas

Notebook: [`notebooks/sit2/08_clip_v4_reparacion_metricas.ipynb`](../../../notebooks/sit2/08_clip_v4_reparacion_metricas.ipynb).

Este notebook corrige la evaluación de CLIP v3 sin reemplazar automáticamente el checkpoint oficial.

## Qué corrigió

- split 70/15/15 estratificado;
- normalización calculada solo con train;
- optimizer incluye `fusion`;
- InfoNCE usa `logit_scale.exp()`;
- retrieval real imagen-texto separado de métricas por prototipo;
- `num_workers=0` para evitar warnings de DataLoader en Kaggle;
- métricas y checkpoint guardados con MD5.

## Configuración ejecutada

| Elemento | Valor |
|---|---:|
| GPU | Tesla T4 |
| Tiles | `(5000, 13, 64, 64)` |
| Metadata | `(5000, 22)` |
| Split train/val/test | 3500 / 750 / 750 |
| Clases por split | 700 / 150 / 150 por clase |
| Bandas ópticas | 12, sin SCL |
| LoRA | 36 capas |
| Parámetros entrenables CLIP | 11.57M |
| Parámetros `fusion` | 0.26M |
| Total entrenable | 11.83M |
| Mejor epoch | 3 |
| Mejor val loss | 3.7086 |
| Checkpoint MD5 | `2236b23237519702a5ebadd9e956c881` |

## Entrenamiento

| Epoch | Train loss | Val loss | logit scale |
|---:|---:|---:|---:|
| 1 | 4.0878 | 3.7687 | 99.67 |
| 2 | 3.7516 | 3.7197 | 99.51 |
| 3 | 3.7000 | 3.7086 | 99.38 |
| 4 | 3.6524 | 3.7221 | 99.27 |
| 5 | 3.6316 | 3.7184 | 99.18 |
| 6 | 3.5875 | 3.7127 | 99.10 |

Se activó early stopping en epoch 6. El mejor checkpoint fue epoch 3.

## Métricas reales imagen-texto

Estas métricas sí comparan cada imagen contra los textos del split correspondiente.

| Split | R@1 | R@5 | R@10 |
|---|---:|---:|---:|
| Val | 0.0067 | 0.0200 | 0.0360 |
| Test | 0.0027 | 0.0147 | 0.0240 |

Lectura: el retrieval par-imagen-texto exacto es bajo. Esto confirma que el `R@5=1.000` reportado antes no medía retrieval real del PDF, sino ranking por prototipos/clases.

## Métricas por prototipo de clase

Estas métricas comparan cada imagen contra prototipos textuales por clase. Son útiles para clasificación semántica, pero no reemplazan el Recall@K imagen-texto del PDF.

| Split | Accuracy prototipo | Top-3 clase |
|---|---:|---:|
| Val | 0.4840 | 0.9280 |
| Test | 0.4960 | 0.9253 |

Reporte test:

| Clase | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `contaminacion_alta_NO2` | 0.416 | 0.280 | 0.335 | 150 |
| `contaminacion_alta_SO2` | 0.360 | 0.240 | 0.288 | 150 |
| `ozono_anomalo` | 0.406 | 0.347 | 0.374 | 150 |
| `vegetacion_densa` | 0.513 | 0.680 | 0.585 | 150 |
| `suelo_urbano` | 0.631 | 0.933 | 0.753 | 150 |
| **accuracy** | | | **0.496** | 750 |

## kNN sobre embeddings visuales

| Split | kNN accuracy k=5 |
|---|---:|
| Val | 0.4067 |
| Test | 0.4040 |

## Comparación contra CLIP v3 oficial

| Métrica | v3 oficial | Sit 2.1 reparación | Lectura |
|---|---:|---:|---|
| Split | 4700/300 | 3500/750/750 | Sit 2.1 es más fiel al PDF. |
| Normalización | todo el dataset | train only | Sit 2.1 reduce leakage estadístico. |
| `fusion` optimizer | no incluido | incluido | Sit 2.1 corrige entrenamiento. |
| `logit_scale` | uso directo | `exp()` + clamp | Sit 2.1 sigue CLIP estándar. |
| Métrica principal anterior | R@5 prototipo/clase = 1.000 | retrieval real test R@5 = 0.0147 | El R@5 anterior no era comparable al KPI PDF. |
| Class prototype accuracy | 0.483-0.500 aprox | test 0.496 | La clasificación por clase se mantiene similar. |
| kNN | 0.430 aprox | test 0.404 | Baja ligeramente con split más estricto. |

## Veredicto

Sit 2.1 no reemplaza todavía al modelo oficial como “mejor resultado”, pero sí mejora la honestidad metodológica.

Conclusiones:

1. La señal visual por clase existe: accuracy por prototipo ≈ 0.50 y kNN ≈ 0.40, ambas sobre azar de 0.20.
2. El retrieval imagen-texto exacto es bajo: R@5 test ≈ 0.015.
3. La métrica `R@5=1.000` del v3 oficial no debe reportarse como Recall@5 imagen-texto del PDF.
4. Para cumplir mejor el PDF, hace falta entrenar/evaluar con textos más únicos o una formulación CLIP+SAE end-to-end.

## Recomendación

Usar Sit 2.1 como auditoría metodológica de métricas y mantener v3 oficial como checkpoint histórico hasta ejecutar una versión nueva con objetivo explícito:

```text
mejorar retrieval real imagen-texto sin perder separabilidad por clase
```

La siguiente mejora razonable es crear una versión Sit 2.2 con textos más ricos por tile y pérdida CLIP+SAE end-to-end o, como mínimo, entrenamiento contrastivo con pares texto-imagen menos duplicados.
