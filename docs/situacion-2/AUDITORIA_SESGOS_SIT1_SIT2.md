# Auditoría de sesgos Sit 1 → Sit 2

Esta auditoría revisa si el panel satelital de Situación 1 pudo introducir fallos o sesgos en el muestreo y entrenamiento de Situación 2.

## Veredicto corto

No encontramos un fallo que invalide las métricas principales de CLIP v3. Sí encontramos riesgos metodológicos que deben declararse:

1. El split de validación CLIP es aleatorio global, no temporal ni espacial.
2. La clase `ozono_anomalo` usa O3 de columna total S5P, con alta nubosidad en los hot pixels.
3. Sentinel-2 fue exportado a grilla 10 m con remuestreo nearest-neighbor para bandas nativas de 20 m y 60 m.
4. MODIS tuvo versiones rotas en GCS, pero el `tiles_meta.parquet` final de Kaggle contiene valores físicos.

## 1. MODIS

### Evidencia

En GCS existen tres versiones:

| Panel | Estado |
|---|---|
| `modis_061_mcd19a2_granules/panel.zarr` | Roto: AOD con valores negativos grandes. |
| `modis_061_mcd19a2_granules/panel_v2.zarr` | Parcial: rangos iniciales no físicos para AOD/WV. |
| `modis_061_mcd19a2_granules/panel_v3.zarr` | Correcto: máscara `_FillValue`, filtro `h10v08` y escala `0.001`. |

El dataset final `edwardsx/geovision-tiles-sit2` tiene rangos físicos:

| Variable | Cobertura | p50 | max |
|---|---:|---:|---:|
| `modis_AOD_047` | 767 / 5000 | 0.3065 | 0.734 |
| `modis_AOD_055` | 767 / 5000 | 0.2220 | 0.536 |
| `modis_WV` | 4897 / 5000 | 1.7355 | 5.328 |

### Veredicto

MODIS no contaminó el entrenamiento CLIP v3 porque el modelo final usa solo bandas ópticas Sentinel-2. Además, el `tiles_meta.parquet` final ya contiene MODIS en rangos físicos.

### Pendiente

Aclarar en documentación/notebook que el contexto final corresponde a la versión corregida, aunque el notebook de muestreo mencione `modis-v2-panel`.

## 2. Split de validación CLIP

### Evidencia

El notebook `notebooks/sit2/03_clip_v3_oficial.ipynb` usa:

```python
indices_val = rng.choice(len(meta), size=n_val, replace=False)
```

Esto produce un split aleatorio global. Al reproducirlo con `SEED=42`:

| Métrica | Resultado |
|---|---:|
| Train | 4700 |
| Val | 300 |
| Fechas únicas val | 68 |
| Fechas val compartidas con train | 68 / 68 |
| Val con misma clase y misma fecha en train | 299 / 300 |
| Val a menos de 2 km de train misma clase/fecha | 138 / 300 |
| Val a menos de 5 km de train misma clase/fecha | 244 / 300 |
| Duplicados exactos train-val | 0 |

La validación también quedó desbalanceada por clase:

| Clase | Val |
|---|---:|
| `vegetacion_densa` | 77 |
| `ozono_anomalo` | 69 |
| `contaminacion_alta_NO2` | 60 |
| `contaminacion_alta_SO2` | 50 |
| `suelo_urbano` | 44 |

### Veredicto

Las métricas CLIP v3 miden separabilidad bajo una distribución mezclada, no generalización temporal o espacial estricta. No hay duplicados exactos, pero sí leakage temporal/espacial suave.

### Mitigación aplicada

Se ejecutó una auditoría v4 en `notebooks/sit2/05_clip_v4_group_split.ipynb` con split temporal por fechas completas:

| Métrica del split | Resultado |
|---|---:|
| Train | 4,531 |
| Val | 469 |
| Fechas val | 8 |
| Fechas compartidas train/val | 0 |
| Años val | 2021-2024 |
| Tile MGRS val | T18NUJ |

Resultados v4:

| Métrica | Resultado |
|---|---:|
| R@1 | 0.386 |
| R@5 | 1.000 |
| Zero-shot accuracy | 0.386 |
| Zero-shot solo visual | 0.401 |
| k-NN accuracy | 0.394 |

El modelo final sigue siendo v2/v3 porque cumple R@1 >= 0.45 en la validación original. v4 no lo reemplaza, pero muestra que la señal no desaparece bajo validación temporal estricta: R@5 se mantiene en 1.000 y zero-shot queda cerca de 2x chance.

## 3. S5P como pseudo-label

### Evidencia documental

Según la documentación de Google Earth Engine:

- NO2 L3 aplica filtros de calidad al producto troposférico.
- SO2 L3 ajusta `qa_value` con criterios que incluyen `cloud_fraction_crb < 0.3`, `qa_value > 0.5` y columna SO2 > -0.001 mol/m².
- O3 total column usa criterios propios de validez, pero no equivale a O3 troposférico de superficie.

### Evidencia en GCS

Hot pixels usados por percentiles:

| Gas | Umbral | cloud_fraction p50 | cloud_fraction p90 | % hot <= 0.3 |
|---|---:|---:|---:|---:|
| NO2 | p90 = 5.28e-05 | 0.083 | 0.169 | 98.6 % |
| SO2 | p90 = 3.87e-04 | 0.106 | 0.257 | 100.0 % |
| O3 | p95 = 0.127 | 0.435 | 0.998 | 39.6 % |

### Veredicto

NO2 y SO2 son defendibles como pseudo-labels. O3 es el punto débil: `ozono_anomalo` usa columna total de O3 y muchos hot pixels tienen nubosidad alta. La clase puede estar capturando régimen atmosférico/estacional más que contaminación superficial visible.

### Mitigación recomendada

Documentar que `ozono_anomalo` no debe interpretarse como O3 superficial directo. Si hay tiempo, evaluar `COPERNICUS/S5P/OFFL/L3_O3_TCL` o filtrar O3 por `cloud_fraction <= 0.3` y comparar distribución temporal.

## 4. Sentinel-2: escala, SCL y remuestreo

### Evidencia documental

`COPERNICUS/S2_SR_HARMONIZED` tiene reflectancia de superficie escalada por 10000 y resoluciones mixtas:

| Bandas | Resolución nativa |
|---|---:|
| B2, B3, B4, B8 | 10 m |
| B5, B6, B7, B8A, B11, B12 | 20 m |
| B1, B9 | 60 m |
| SCL | 20 m |

Earth Engine usa nearest-neighbor por defecto al reproyectar si no se llama `resample()`.

### Evidencia en tiles

Los tiles finales están en DN sin dividir por 10000. Esto no invalida el CLIP porque el notebook normaliza por banda y aplica clipping ±3σ.

Tasa de igualdad entre píxeles adyacentes en 500 tiles:

| Grupo | Igualdad adyacente aproximada |
|---|---:|
| Bandas 10 m | 1-2 % |
| Bandas 20 m | 50 % |
| B1/B9 60 m | 83-84 % |
| SCL | 95 % |

Esto confirma upsampling nearest-neighbor hacia la grilla de 10 m.

### Veredicto

La grilla 10 m es útil para tener un tensor uniforme, pero las bandas 20 m y 60 m entran al modelo con patrones bloqueados. B1 y B9 son las más delicadas. NDVI usa B8/B4, ambas 10 m, por lo que el criterio principal de vegetación no queda afectado por ese remuestreo.

### SCL

`tiles_meta.parquet` muestra:

| Métrica `scl_pct` | Valor |
|---|---:|
| min | 0.301 |
| p50 | 1.000 |
| media | 0.914 |

La mayoría de tiles está limpia, pero el umbral acepta algunos con solo 30 % de píxeles válidos. El entrenamiento CLIP usa las 12 bandas ópticas sin enmascarar píxeles inválidos por SCL.

### Mitigación recomendada

Para una versión más estricta:

- excluir B1 y B9 o tratarlas como contexto de baja resolución;
- aplicar máscara SCL antes de calcular estadísticas de normalización;
- probar `SCL_THRESHOLD >= 0.7` como ablación;
- reportar métricas por bins de `scl_pct`.

## Conclusión

La Situación 2 es defendible si se presenta con dos niveles de evidencia:

1. v2/v3 como modelo final: cumple los KPIs principales bajo el split original y corrige el data leakage por S5P.
2. v4 como auditoría temporal: no reemplaza al modelo final, pero muestra robustez parcial cuando no hay fechas compartidas entre train y validación.

Los dos riesgos que siguen afectando la interpretación son:

1. La generalización espacial estricta no fue probada; `suelo_urbano` queda cerca de train por construcción del muestreo DAGMA.
2. La clase O3 usa columna total con alta nubosidad y puede capturar régimen atmosférico/estacional más que contaminación superficial directa.
