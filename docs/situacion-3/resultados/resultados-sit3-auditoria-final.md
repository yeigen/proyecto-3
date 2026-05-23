# Auditoría final Situación 3 — ConvLSTM, Kriging y validación DAGMA/CVC

## Resumen ejecutivo

La Situación 3 se abordó con dos rutas: un componente de Deep Learning temporal basado en ConvLSTM y un cierre geoestadístico mediante Kriging Ordinario con validación Leave-One-Out por estación. La evidencia disponible muestra que ConvLSTM converge en pérdida, pero no generaliza bien en estaciones no vistas. La alternativa más defendible para el informe es Kriging Ordinario sobre coordenadas, porque produce errores absolutos razonables para SO2 y O3 bajo LOO-CV espacial.

La lectura debe ser honesta: no todos los KPIs del PDF se cumplen. SO2 y O3 alcanzan o quedan cerca de los umbrales de RMSE; NO2 no es evaluable con LOO-CV porque solo hay una estación con mediciones útiles en el parquet principal. R2 queda negativo y Moran I no debe reportarse como cumplido si no hay evidencia computacional consolidada.

## Qué pedía el PDF

El PDF exige producir estimaciones de NO2, SO2 y O3 en puntos no muestreados, idealmente con ConvLSTM, Kriging espacio-temporal, varianza de predicción, LOO-CV espacial contra DAGMA, Moran I, LISA y análisis de variogramas. Los KPIs principales de Situación 3 son:

| KPI PDF | Meta mínima |
|---|---:|
| RMSE LOO-CV NO2 T+1 | <= 8 ug/m3 |
| RMSE LOO-CV SO2 T+1 | <= 6 ug/m3 |
| RMSE LOO-CV O3 T+1 | <= 12 ug/m3 |
| R2 LOO-CV promedio | >= 0.55 |
| Moran I predicciones | > 0.30 con p < 0.05 |
| Variograma residuos | Nugget puro |
| Cobertura cinturón 95% | >= 92% |
| Degradación T+1 a T+7 | < 60% aumento RMSE |
| Latencia end-to-end | < 8 s |

## Evidencia disponible

Fuentes internas revisadas:

| Fuente | Contenido |
|---|---|
| `notebooks/sit3/01_convlstm_kriging.ipynb` | Pipeline inicial ConvLSTM + Kriging |
| `notebooks/sit3/02_situacion-3-conv-lstm.ipynb` | Cobertura DAGMA/CVC, ConvLSTM y validación |
| `docs/situacion-3/SIT3_RESULTADOS.md` | Resumen original de resultados |
| `docs/situacion-3/resultados/kriging-loocv.md` | Resultados Kriging LOO-CV |
| `docs/situacion-3/resultados/convlstm.md` | Resultados ConvLSTM |
| `docs/situacion-3/resultados/kpis-limitaciones.md` | KPIs y limitaciones |

El periodo útil documentado es 2021-2024, con 55,099 mediciones en la tabla DAGMA/CVC usada para validación.

## Estaciones y restricciones de validación

La principal limitación no es solo algorítmica, sino de observabilidad. La cobertura mensual por estación es incompleta y distinta para cada contaminante.

Cobertura por estación en el periodo útil 2021-2024:

| Estación | Cobertura mensual |
|---|---:|
| ESTACIÓN YUMBO | 40/48 meses |
| UNIVERSIDAD DEL VALLE | 17/48 meses |
| BASE AÉREA | 15/48 meses |
| COMPARTIR | 13/48 meses |
| LA ERMITA | 10/48 meses |
| PANCE | 10/48 meses |
| ERA OBRERO | 8/48 meses |
| LA FLORA | 6/48 meses |
| CAÑAVERALEJO | 5/48 meses |

Por contaminante, la validación fuerte queda limitada así:

| Contaminante | Estaciones evaluables | Lectura |
|---|---:|---|
| NO2 | 1 | LOO-CV espacial no es posible |
| SO2 | 4 | LOO-CV posible, pero con baja muestra espacial |
| O3 | 7 | Mejor caso para LOO-CV dentro de Sit 3 |

## Resultado ConvLSTM

Se implementó una ConvLSTM con aproximadamente 4.0M de parámetros. En la corrida visible del notebook `02_situacion-3-conv-lstm.ipynb`, la arquitectura entrena y la pérdida baja:

| Epoch | Loss |
|---|---:|
| 1 | 0.956139 |
| 2 | 0.954367 |
| 3 | 0.952587 |
| 4 | 0.950776 |
| 5 | 0.948912 |

La documentación previa también registra una corrida donde la pérdida llega a 0.5927 en epoch 10. En ambos casos, la conclusión es la misma: la pérdida de entrenamiento converge, pero la validación espacial LOO-CV no produce R2 positivos. Por eso ConvLSTM queda como componente implementado y evaluado, no como el mejor predictor final.

## Resultado Kriging Ordinario LOO-CV

Kriging Ordinario con variograma exponencial fue la ruta más útil frente a ConvLSTM y Ridge. La validación deja una estación fuera y predice con las restantes.

### SO2

| Estación | Real (ug/m3) | Predicho | Error absoluto |
|---|---:|---:|---:|
| BASE AÉREA | 7.65 | 4.39 | 3.26 |
| CAÑAVERALEJO | 2.48 | 6.42 | 3.94 |
| ESTACIÓN YUMBO | 13.12 | 4.18 | 8.94 |
| LA ERMITA | 2.40 | 6.34 | 3.94 |
| MAE | | | 5.02 |
| RMSE aproximado | | | 5.78 |

### O3

| Estación | Real (ug/m3) | Predicho | Error absoluto |
|---|---:|---:|---:|
| BASE AÉREA | 9.11 | 16.30 | 7.20 |
| COMPARTIR | 14.18 | 14.65 | 0.47 |
| ERA OBRERO | 14.46 | 16.48 | 2.02 |
| ESTACIÓN YUMBO | 20.72 | 17.14 | 3.59 |
| LA FLORA | 16.74 | 15.45 | 1.29 |
| PANCE | 26.35 | 14.47 | 11.88 |
| UNIVERSIDAD DEL VALLE | 11.79 | 19.72 | 7.92 |
| MAE | | | 4.91 |
| RMSE aproximado | | | 5.93 |

## KPIs del PDF: cumplimiento real

| KPI PDF | Meta | Resultado | Estado | Lectura |
|---|---:|---:|---|---|
| RMSE LOO-CV NO2 T+1 | <= 8 ug/m3 | No evaluable | Limitado | Solo una estación con NO2 |
| RMSE LOO-CV SO2 T+1 | <= 6 ug/m3 | 5.78 | Cumple/cerca | 4 estaciones evaluables |
| RMSE LOO-CV O3 T+1 | <= 12 ug/m3 | 5.93 | Cumple | 7 estaciones evaluables |
| R2 LOO-CV promedio | >= 0.55 | Negativo | No cumple | Pocas estaciones y baja varianza explicada |
| Moran I predicciones | > 0.30 p<0.05 | Pendiente/no consolidado | No verificable | No debe afirmarse sin evidencia |
| Variograma residuos nugget puro | Sin estructura | Parcial/no concluyente | Limitado | Pocos puntos para variograma robusto |
| Cobertura cinturón 95% | >= 92% | No consolidado | Pendiente | Requiere cálculo empírico LOO |
| Degradación T+1 a T+7 | < 60% aumento | No consolidado | Pendiente | Forecast multihorizonte no queda robusto |
| Latencia end-to-end | < 8 s | No consolidado | Pendiente | Depende del despliegue |

## Por qué Kriging es la ruta más defendible

Kriging es más defendible que ConvLSTM para la evidencia actual por cuatro razones:

1. Opera directamente sobre coordenadas y concentraciones observadas, lo que lo alinea con la validación DAGMA/CVC.
2. Funciona con pocas estaciones mejor que un modelo profundo temporal con millones de parámetros.
3. Produce errores absolutos interpretables en ug/m3.
4. Es una técnica geoestadística explícita, coherente con el objetivo central del PDF.

ConvLSTM queda como implementación válida del componente Deep Learning temporal, pero sus resultados muestran que los embeddings CLIP de Situación 2, aunque útiles para clasificación semántica, no bastan para predecir concentraciones absolutas en estaciones no vistas.

## Limitaciones metodológicas

- NO2 no permite LOO-CV espacial robusto porque solo hay una estación disponible con mediciones útiles.
- SO2 tiene solo cuatro estaciones evaluables; cualquier R2 es inestable.
- O3 tiene siete estaciones y es el contaminante con evaluación más defendible.
- R2 negativo indica baja capacidad para explicar variabilidad espacial, aunque el RMSE de O3 y SO2 sea razonable.
- Moran I, LISA, cobertura de intervalos y degradación multihorizonte no deben presentarse como cumplidos sin una celda reproducible que los calcule.
- Con pocas estaciones, un variograma de residuos no tiene suficiente soporte estadístico para una conclusión fuerte de nugget puro.

## Qué se defiende en el informe

La defensa recomendada es:

1. Se implementó el pipeline DL + geoestadística exigido: ConvLSTM, Kriging y LOO-CV espacial.
2. La validación externa se hizo contra estaciones DAGMA/CVC, no contra datos sintéticos.
3. Kriging Ordinario fue el mejor cierre práctico para puntos no muestreados.
4. SO2 y O3 alcanzan errores absolutos razonables y O3 cumple claramente el umbral de RMSE.
5. Las métricas no cumplidas se reportan como limitaciones de cobertura de estaciones y no se maquillan.
6. La Situación 3 queda metodológicamente defendible por honestidad, trazabilidad y uso correcto de validación espacial.

## Conclusión

La Situación 3 no debe venderse como cumplimiento total del PDF. El resultado correcto es una implementación funcional y auditada del flujo ConvLSTM + Kriging + LOO-CV, con cumplimiento parcial de KPIs. La evidencia más sólida está en Kriging Ordinario para SO2 y O3; NO2 y R2 promedio quedan limitados por disponibilidad de estaciones y baja capacidad de extrapolación espacial. Esta lectura es defendible porque reconoce las restricciones reales del sistema de monitoreo y evita reportar KPIs sin evidencia computacional.
