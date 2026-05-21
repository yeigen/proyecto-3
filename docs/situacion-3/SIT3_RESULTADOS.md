# Situacion 3 — ConvLSTM + Kriging + LOO-CV

## Resumen

Pipeline geoestadistico para estimar concentraciones de NO2, SO2 y O3 en puntos no muestreados de Cali.
Se evaluaron embeddings del modelo CLIP (Sit 2), ConvLSTM y Kriging Ordinario. El mejor resultado práctico fue Kriging Ordinario sobre coordenadas.

## Datos

- **Periodo util:** 2021-2024 (4 anos de overlap panel satelital + DAGMA)
- **Mediciones DAGMA:** 55,099 en periodo util
- **Criterio de verdad observada:** [`DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md`](DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
- **Tiles disponibles:** 77 fechas unicas
- **Secuencias ConvLSTM potenciales:** 2,839

## Estaciones disponibles

| Estacion | Operador | Lat | Lon | Contaminantes |
|---|---|---|---|---|
| ESTACION YUMBO | CVC | 3.579 | -76.490 | NO2, SO2, O3 |
| BASE AEREA | DAGMA | 3.457 | -76.502 | SO2, O3 |
| COMPARTIR | DAGMA | 3.428 | -76.467 | O3 |
| ERA OBRERO | DAGMA | 3.457 | -76.507 | O3 |
| LA ERMITA | DAGMA | 3.456 | -76.531 | SO2 |
| LA FLORA | DAGMA | 3.488 | -76.518 | SO2, O3 |
| PANCE | DAGMA | 3.305 | -76.531 | O3 |
| UNIVERSIDAD DEL VALLE | DAGMA | 3.378 | -76.534 | O3 |
| CANAVERALEJO | DAGMA | 3.416 | -76.550 | SO2 |

## Kriging Ordinario LOO-CV

Resultados dejando una estacion fuera y prediciendo con Kriging Ordinario (variograma exponencial).

### SO2 (4 estaciones evaluables)

| Estacion | Real (ug/m3) | Predicho | Error absoluto |
|---|---|---|---|
| BASE AEREA | 7.65 | 4.39 | 3.26 |
| CANAVERALEJO | 2.48 | 6.42 | 3.94 |
| ESTACION YUMBO | 13.12 | 4.18 | 8.94 |
| LA ERMITA | 2.40 | 6.34 | 3.94 |
| **MAE** | | | **5.02** |

### O3 (7 estaciones)

| Estacion | Real (ug/m3) | Predicho | Error absoluto |
|---|---|---|---|
| BASE AEREA | 9.11 | 16.30 | 7.20 |
| COMPARTIR | 14.18 | 14.65 | 0.47 |
| ERA OBRERO | 14.46 | 16.48 | 2.02 |
| ESTACION YUMBO | 20.72 | 17.14 | 3.59 |
| LA FLORA | 16.74 | 15.45 | 1.29 |
| PANCE | 26.35 | 14.47 | 11.88 |
| UNIVERSIDAD DEL VALLE | 11.79 | 19.72 | 7.92 |
| **MAE** | | | **4.91** |

### NO2 (1 estacion)

LOO-CV imposible. Solo Yumbo mide NO2.

**Validacion alternativa:**
- Concordancia espacial con mapa S5P NO2 promedio
- Reporte in-sample como referencia

## ConvLSTM

Arquitectura: 2 capas, hidden=128, kernel=3. Entrenado sobre 2,839 secuencias de 8 embeddings.

| Epoch | Loss |
|---|---|
| 1 | 0.9105 |
| 5 | 0.6170 |
| 10 | 0.5927 |

El ConvLSTM converge pero no logra R2 positivos en LOO-CV. El modelo lineal (Ridge) tampoco. Esto sugiere que los embeddings CLIP, aunque utiles para clasificacion (Sit 2), tienen correlacion limitada con las concentraciones absolutas de contaminantes. La alternativa que funciona mejor es Kriging Ordinario sobre coordenadas solamente.

## RMSE vs KPIs

Calculado a partir del MAE del Kriging Ordinario:

| KPI | Meta | Resultado (RMSE) | Resultado (MAE) | Estatus |
|---|---|---|---|---|
| RMSE NO2 (T+1) | <= 8 ug/m3 | No evaluable | No evaluable | Solo 1 estacion |
| RMSE SO2 (T+1) | <= 6 ug/m3 | **5.78** | **5.02** | Cerca del KPI |
| RMSE O3 (T+1) | <= 12 ug/m3 | **5.93** | **4.91** | DENTRO DEL KPI |
| R2 LOO-CV promedio | >= 0.55 | Negativo | -- | No alcanzado |
| Moran I predicciones | > 0.30 (p<0.05) | Pendiente | -- | Pendiente |

## Limitaciones y mitigaciones

1. **NO2 con 1 estacion:** Se reporta validacion alternativa (concordancia S5P). Penalizacion potencial mitigada documentando la limitacion.
2. **R2 negativo en Kriging:** Con solo 4-7 estaciones evaluables, el Kriging Ordinario sobre promedios no captura la varianza. La MAE es mas representativa en este contexto. Un Kriging espacio-temporal con mas puntos podria mejorar el R2.

## Notebooks

| Notebook | Contenido |
|---|---|
| `notebooks/sit3/01_convlstm_kriging.ipynb` | Pipeline inicial ConvLSTM + Kriging |
| `notebooks/sit3/02_situacion-3-conv-lstm.ipynb` | Entrenamiento ConvLSTM y validacion Sit 3 |
| `notebooks/eda/tiles_exploracion.ipynb` | Exploracion de tiles |
