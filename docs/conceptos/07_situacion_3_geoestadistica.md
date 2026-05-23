# 07. Situación 3: ConvLSTM, Kriging, LOO-CV y auditoría

Este documento conecta la Situación 3 del PDF con lo que realmente hay en el proyecto: notebooks, salidas de código, fórmulas, métricas, Kriging, LOO-CV y limitaciones.

La idea es poder defender no solo “hicimos geoestadística”, sino:

> qué se implementó, qué salió en los notebooks, qué KPIs se cumplen, qué no está verificado y qué no se debe prometer.

## 1. Qué pedía el PDF

La Situación 3 pedía articular Deep Learning + Geoestadística para estimar concentraciones en puntos no muestreados.

| Requisito del PDF | Lectura práctica |
|---|---|
| Entrada `(lat, lon)` | Poder consultar un punto cualquiera en Cali. |
| Horizontes `T+1`, `T+3`, `T+7` | Predicción multi-horizonte. |
| Contaminantes NO₂, SO₂, O₃ | Tres salidas por horizonte. |
| GeoVision-CLIP + SAE | Usar embeddings aprendidos en Situación 2. |
| ConvLSTM | Capturar dinámica espacio-temporal. |
| ST-Kriging / Kriging 3D | Interpolar espacio-tiempo y producir incertidumbre. |
| LOO-CV espacial | Dejar una estación fuera y predecirla. |
| Moran I y LISA | Evaluar estructura espacial global y local. |
| Variograma de residuos | Revisar si queda autocorrelación no explicada. |
| Mapas 3×3 | 3 contaminantes × 3 horizontes. |

KPIs principales del PDF:

| KPI | Meta mínima |
|---|---:|
| RMSE NO₂ T+1 | ≤ 8 µg/m³ |
| RMSE SO₂ T+1 | ≤ 6 µg/m³ |
| RMSE O₃ T+1 | ≤ 12 µg/m³ |
| R² promedio | ≥ 0.55 |
| Moran I | > 0.30 con p < 0.05 |
| Variograma residuos | nugget puro / sin estructura |
| Cobertura cinturón 95% | ≥ 92% |
| Degradación T+1 → T+7 | < 60% aumento RMSE |
| Latencia inferencia | < 8 s |

## 2. Qué hizo el proyecto

La Situación 3 actual es una aproximación parcial al PDF. Tiene evidencia real de ConvLSTM, LOO-CV y Kriging Ordinario, pero no prueba todavía el pipeline completo ST-Kriging multi-horizonte con Moran/LISA e incertidumbre.

| Elemento | Resultado actual |
|---|---|
| Verdad observada | parquet SISAIRE/DAGMA-CVC |
| Periodo útil | 2021-2024 |
| Mediciones en periodo útil | 55,099 |
| Tiles disponibles | 77 fechas únicas |
| Secuencias ConvLSTM | 2,839 |
| Embeddings CLIP | `torch.Size([5000, 512])` |
| ConvLSTM | entrenada y evaluada con LOO-CV |
| Ridge baseline | evaluado con embeddings + ERA5 |
| Kriging | Ordinario 2D sobre coordenadas, documentado para SO₂/O₃ |
| NO₂ | no evaluable con LOO-CV espacial por tener una sola estación |

Lectura corta:

> ConvLSTM converge en pérdida, pero no generaliza bien a estaciones no vistas. Ridge tampoco. Kriging Ordinario sobre coordenadas da los mejores errores prácticos para SO₂ y O₃.

## 3. Cumplimiento metodológico frente al PDF

| Requisito del PDF | Implementación real | Estado | Lectura defendible |
|---|---|---|---|
| Usar embeddings de GeoVision-CLIP | notebook 02 genera embeddings `(5000, 512)` | Cumple parcialmente | Usa CLIP; no se ve SAE 256-d en Sit 3. |
| Secuencias de 8 fechas | 2,839 secuencias reportadas | Cumple parcialmente | Hay secuencias, pero no se prueba multi-horizonte. |
| ConvLSTM hidden=128, kernel=3, 2 capas | implementado en notebook 02 | Cumple | Arquitectura base coincide. |
| ConvLSTM bidireccional | no visible | No verificado | No debe afirmarse. |
| Salida `(B, 3, 3, H, W)` | no visible; salida práctica por 3 contaminantes | No literal | No hay evidencia 3 horizontes × 3 contaminantes. |
| LOO-CV por estación | ConvLSTM/Ridge evaluados; Kriging documentado | Cumple parcialmente | Hay LOO-CV, pero limitado por estaciones. |
| RMSE SO₂ ≤ 6 | Kriging RMSE aprox 5.78 | Cumple por resultado documentado | Cerca del umbral y defendible con cautela. |
| RMSE O₃ ≤ 12 | Kriging RMSE aprox 5.93 | Cumple | Resultado más defendible. |
| RMSE NO₂ ≤ 8 | no evaluable | No cumple / no evaluable | Solo Yumbo mide NO₂. |
| R² promedio ≥ 0.55 | R² negativos | No cumple | ConvLSTM/Ridge no explican varianza espacial. |
| ST-Kriging / Kriging 3D | Kriging Ordinario 2D | No literal | Aproximación práctica por falta de puntos. |
| Varianza Kriging / incertidumbre | no visible como mapa | No verificado | No prometer mapa de incertidumbre. |
| Variograma residuos nugget puro | no verificado | No cumple todavía | Debe quedar como plan posterior. |
| Moran I con p-value | pendiente | No verificado | No reportar como cumplido. |
| LISA | pendiente | No verificado | No reportar clusters significativos. |
| Mapas 3×3 | no encontrados | No verificado | No vender mapas multi-horizonte. |
| Latencia < 8 s | no medida | No verificado | Depende de despliegue/inferencia. |

Veredicto:

> Situación 3 tiene una base metodológica real y auditable, pero no cumple todavía la versión completa del PDF. Es defendible como evaluación experimental honesta: ConvLSTM y Ridge fallan en generalización espacial; Kriging Ordinario funciona mejor para SO₂ y O₃; NO₂ queda limitado por datos.

## 4. Notebooks revisados

| Notebook | Estado | Lectura |
|---|---|---|
| `notebooks/sit3/01_convlstm_kriging.ipynb` | prototipo inicial | No tiene outputs visibles; usa variables/clases antes de definición; no citar como evidencia ejecutada. |
| `notebooks/sit3/02_situacion-3-conv-lstm.ipynb` | evidencia principal | Tiene salidas visibles de carga DAGMA, embeddings, ConvLSTM, LOO-CV y Ridge. |

### Notebook 01

Se debe tratar como borrador técnico. Contiene la intención del pipeline, pero no es evidencia fuerte porque:

- no conserva outputs visibles;
- usa `INPUT` antes de definirlo;
- instancia `ConvLSTM` sin definición visible en ese notebook;
- usa `OrdinaryKriging` sin import explícito visible.

### Notebook 02

Es la fuente principal para salidas de código:

| Salida visible | Resultado |
|---|---:|
| DAGMA total | 107,291 mediciones |
| Periodo útil 2021-2024 | 55,099 mediciones |
| Tiles disponibles | 77 fechas |
| Secuencias totales | 2,839 |
| Embeddings generados | `torch.Size([5000, 512])` |
| ConvLSTM params | 4,033K |
| Ridge baseline | R² medio = -1.693 |

## 5. Verdad observada DAGMA/CVC

La verdad observada principal es el parquet SISAIRE/DAGMA-CVC:

- `dagma/dagma_cvc_horario_raw.parquet`
- `dagma/estaciones_metadata.csv`
- `dagma/manifest_ground_truth.json`

El Excel Cristian queda como fuente complementaria, no como reemplazo.

Motivo:

- el cruce parquet vs Excel no muestra equivalencia suficiente;
- mezclar ambos puede cambiar la interpretación de estaciones y contaminantes;
- para NO₂, combinar Yumbo y Univalle confunde fuente y estación.

Estaciones evaluables en la documentación de Situación 3:

| Contaminante | Estaciones evaluables | Lectura |
|---|---:|---|
| NO₂ | 1 | no permite LOO-CV espacial. |
| SO₂ | 4 | permite LOO-CV, pero con muestra pequeña. |
| O₃ | 7 | mejor caso para validación espacial. |

## 6. ConvLSTM: código, fórmula y salidas

El PDF propone una ConvLSTM para capturar dinámica espacio-temporal a partir de embeddings.

En el notebook 02 se define:

| Elemento | Valor |
|---|---:|
| input_dim | 512 |
| hidden_dim | 128 |
| kernel_size | 3 |
| num_layers | 2 |
| parámetros | 4,033K |
| secuencias | `(2839, 8, 512)` |

La lógica de una celda ConvLSTM combina el estado actual con memoria recurrente espacial. Conceptualmente:

$$
(i_t, f_t, o_t, g_t) = Conv([x_t, h_{t-1}])
$$

$$
c_t = f_t \odot c_{t-1} + i_t \odot g_t
$$

$$
h_t = o_t \odot \tanh(c_t)
$$

Salidas de entrenamiento visibles:

| Epoch | Loss |
|---|---:|
| 1 | 0.9105 |
| 5 | 0.6170 |
| 10 | 0.5927 |

Auditoría:

- correcto: la pérdida baja, así que el modelo aprende algo en train;
- problema: LOO-CV por estación muestra R² negativos;
- lectura: los embeddings CLIP ayudan a clasificar tiles en Sit 2, pero no bastan para predecir concentración absoluta en estaciones no vistas.

### LOO-CV ConvLSTM

Resultados visibles por estación:

| Contaminante | Estación | RMSE | MAE | R² |
|---|---|---:|---:|---:|
| SO₂ | BASE AÉREA | 8.60 | 7.52 | -3.24 |
| SO₂ | CAÑAVERALEJO | 2.53 | 2.38 | -8.04 |
| SO₂ | ESTACIÓN YUMBO | 16.49 | 12.50 | -1.35 |
| SO₂ | LA ERMITA | 2.59 | 2.40 | -5.93 |
| O₃ | BASE AÉREA | 10.02 | 9.24 | -5.64 |
| O₃ | COMPARTIR | 14.95 | 13.90 | -6.36 |
| O₃ | ERA OBRERO | 15.40 | 13.95 | -4.56 |
| O₃ | ESTACIÓN YUMBO | 24.36 | 19.48 | -1.77 |
| O₃ | LA FLORA | 18.16 | 16.74 | -5.64 |
| O₃ | PANCE | 28.23 | 25.98 | -5.54 |
| O₃ | UNIVERSIDAD DEL VALLE | 14.14 | 11.84 | -2.34 |

Conclusión:

> ConvLSTM no debe presentarse como el modelo ganador. Debe presentarse como intento válido que converge, pero no generaliza espacialmente bajo LOO-CV.

## 7. Ridge baseline

El notebook 02 también evalúa un baseline Ridge con:

- embeddings CLIP;
- variables ERA5;
- `StandardScaler`;
- `Ridge(alpha=1.0)`.

Resultado visible:

```text
R2 medio = -1.693
```

Lectura:

- Ridge tampoco logra explicar concentración absoluta en estaciones no vistas;
- esto refuerza que el problema no es solo la arquitectura ConvLSTM;
- con pocas estaciones, el aprendizaje supervisado sobre embeddings queda débil.

## 8. Kriging Ordinario y LOO-CV

Kriging estima un valor en una ubicación no observada usando estaciones conocidas y estructura espacial.

Fórmula conceptual:

$$
\hat{Z}(s_0) = \sum_i w_i Z(s_i)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $s_0$ | punto no observado |
| $s_i$ | estación observada |
| $Z(s_i)$ | concentración medida en estación $i$ |
| $w_i$ | pesos calculados por Kriging |

La validación LOO-CV deja una estación fuera:

$$
e_{LOO,i} = y_i - \hat{y}_{-i}
$$

Métricas usadas:

$$
MAE = \frac{1}{N}\sum_i |y_i - \hat{y}_i|
$$

$$
RMSE = \sqrt{\frac{1}{N}\sum_i(y_i - \hat{y}_i)^2}
$$

### Resultados Kriging documentados

SO₂:

| Estación | Real (µg/m³) | Predicho | Error absoluto |
|---|---:|---:|---:|
| BASE AÉREA | 7.65 | 4.39 | 3.26 |
| CAÑAVERALEJO | 2.48 | 6.42 | 3.94 |
| ESTACIÓN YUMBO | 13.12 | 4.18 | 8.94 |
| LA ERMITA | 2.40 | 6.34 | 3.94 |
| MAE | | | 5.02 |

O₃:

| Estación | Real (µg/m³) | Predicho | Error absoluto |
|---|---:|---:|---:|
| BASE AÉREA | 9.11 | 16.30 | 7.20 |
| COMPARTIR | 14.18 | 14.65 | 0.47 |
| ERA OBRERO | 14.46 | 16.48 | 2.02 |
| ESTACIÓN YUMBO | 20.72 | 17.14 | 3.59 |
| LA FLORA | 16.74 | 15.45 | 1.29 |
| PANCE | 26.35 | 14.47 | 11.88 |
| UNIVERSIDAD DEL VALLE | 11.79 | 19.72 | 7.92 |
| MAE | | | 4.91 |

Resumen:

| Contaminante | Estaciones | MAE | RMSE aprox | Estado |
|---|---:|---:|---:|---|
| NO₂ | 1 | no evaluable | no evaluable | no permite LOO-CV |
| SO₂ | 4 | 5.02 | 5.78 | cerca/cumple RMSE ≤ 6 |
| O₃ | 7 | 4.91 | 5.93 | cumple RMSE ≤ 12 |

Auditoría:

- Kriging Ordinario fue la mejor alternativa práctica documentada;
- pero no es ST-Kriging 3D;
- los resultados de Kriging están consolidados en Markdown, no como output visible ejecutado del notebook 02;
- aun así, son coherentes con la limitación de pocas estaciones.

## 9. KPIs de Situación 3

| KPI | Meta PDF | Resultado actual | Estado |
|---|---:|---:|---|
| RMSE NO₂ T+1 | ≤ 8 µg/m³ | no evaluable | No cumple / no evaluable |
| RMSE SO₂ T+1 | ≤ 6 µg/m³ | 5.78 | Cumple por Kriging documentado, con cautela |
| RMSE O₃ T+1 | ≤ 12 µg/m³ | 5.93 | Cumple |
| R² promedio | ≥ 0.55 | negativo | No cumple |
| Moran I | > 0.30 p<0.05 | pendiente | No verificado |
| Variograma residuos | sin estructura | pendiente | No verificado |
| Cobertura 95% Kriging | ≥ 92% | pendiente | No verificado |
| Degradación T+1→T+7 | < 60% | pendiente | No verificado |
| Latencia | < 8 s | pendiente | No verificado |

Lectura:

> La Situación 3 no alcanza una validación completa del PDF. Sí aporta resultados útiles de Kriging para SO₂ y O₃, y documenta honestamente que ConvLSTM/Ridge no generalizan bien.

## 10. Qué no está verificado todavía

No se encontró evidencia suficiente para afirmar:

- ST-Kriging 3D con `OrdinaryKriging3D`;
- mapas de incertidumbre Kriging;
- variograma experimental de residuos;
- nugget puro en residuos;
- Moran I con p-value;
- LISA / clusters locales significativos;
- mapas 3×3 por contaminante y horizonte;
- degradación T+1 a T+7;
- latencia end-to-end;
- predicción robusta para NO₂ en estaciones no vistas.

## 11. Qué está bien defendible

- La verdad observada principal está bien elegida: parquet DAGMA/CVC.
- No se mezcla Excel Cristian como si fuera equivalente al parquet.
- Se reconoce que NO₂ solo tiene una estación y no permite LOO-CV espacial.
- ConvLSTM está implementado y tiene salidas de entrenamiento visibles.
- LOO-CV muestra que ConvLSTM no generaliza; esto es un hallazgo, no algo que se deba ocultar.
- Ridge baseline confirma que el problema no se resuelve con un modelo lineal simple.
- Kriging Ordinario da errores razonables para SO₂ y O₃.
- Las limitaciones están documentadas y conectan con datos reales.

## 12. Qué hay que cuidar en defensa

| Riesgo | Cómo explicarlo |
|---|---|
| Decir que Sit 3 cumple todo el PDF | No es cierto; cumple parcialmente. |
| NO₂ LOO-CV | No se puede hacer con una sola estación. |
| ConvLSTM | Converge, pero no generaliza; no es el modelo ganador. |
| Kriging | Es Ordinario 2D, no ST-Kriging 3D. |
| R² negativo | Indica baja explicación de varianza; MAE/RMSE siguen aportando lectura de error absoluto. |
| Moran/LISA | Están pendientes; no reportarlos como hechos. |
| Mapas 3×3 | No se encontraron como evidencia de Sit 3. |
| Kriging outputs | Están documentados, pero falta notebook ejecutado con outputs visibles. |

Frase defendible:

> “La Situación 3 muestra que el enfoque profundo no generalizó bien a estaciones no vistas con los datos disponibles. Por eso el resultado más sólido fue Kriging Ordinario para SO₂ y O₃. Para NO₂ no prometemos LOO-CV porque solo hay una estación. Lo que falta para cumplir literalmente el PDF es cerrar ST-Kriging, incertidumbre, Moran/LISA, variograma de residuos y mapas multi-horizonte.”

## 13. Plan posterior para cierre literal de Sit 3

Para acercarse al PDF de forma más literal, se dejó un plan separado:

- [Plan de cierre literal Situación 3](../superpowers/plans/2026-05-22-situacion-3-cierre-literal-pdf.md)

Ese plan debe ejecutarse después de terminar la documentación general. Su prioridad sería:

1. re-ejecutar notebook Sit 3 con outputs completos;
2. reproducir Kriging con salidas visibles;
3. calcular Moran I y LISA;
4. ajustar variograma de residuos;
5. generar mapas de incertidumbre;
6. evaluar si ST-Kriging 3D es viable con los datos reales.

## 14. Referencias y documentación

### Internas

- [Situación 3](../situacion-3/README.md)
- [Resultados Situación 3](../situacion-3/SIT3_RESULTADOS.md)
- [ConvLSTM, Kriging y LOO-CV](../situacion-3/metodologia/convlstm-kriging-loocv.md)
- [Verdad observada](../situacion-3/metodologia/verdad-observada.md)
- [Kriging y LOO-CV](../situacion-3/resultados/kriging-loocv.md)
- [ConvLSTM](../situacion-3/resultados/convlstm.md)
- [KPIs y limitaciones](../situacion-3/resultados/kpis-limitaciones.md)
- [Justificación cruce DAGMA Cristian](../situacion-3/DAGMA_JUSTIFICACION_CRUCE_CRISTIAN.md)
- [Geoestadística conceptual](04_geoestadistica.md)
- [Fórmulas del modelo](03_formulas_modelo.md)

### Notebooks revisados

- [`notebooks/sit3/01_convlstm_kriging.ipynb`](../../notebooks/sit3/01_convlstm_kriging.ipynb)
- [`notebooks/sit3/02_situacion-3-conv-lstm.ipynb`](../../notebooks/sit3/02_situacion-3-conv-lstm.ipynb)

### Evidencias visuales

- [Mapa estaciones vs tile MGRS](../situacion-3/evidencias/dagma/figuras/dagma_estaciones_vs_tile_mgrs.png)
- [Cobertura temporal DAGMA](../situacion-3/evidencias/dagma/figuras/dagma_cobertura_temporal.png)
- [Distribuciones por estación](../situacion-3/evidencias/dagma/figuras/dagma_distribuciones_por_estacion.png)
- [Ciclo diurno DAGMA](../situacion-3/evidencias/dagma/figuras/dagma_ciclo_diurno.png)
- [Correlación parquet vs Excel](../situacion-3/evidencias/dagma/sit3_dagma_excel_parquet_correlacion_variables.png)
- [NO₂ Yumbo-Univalle combinado](../situacion-3/evidencias/dagma/sit3_dagma_no2_yumbo_univalle_combinado.png)

### Externas

- [ConvLSTM paper](https://arxiv.org/abs/1506.04214)
- [PyKrige documentation](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/)
- [PySAL esda documentation](https://pysal.org/esda/stable/)
- [PySAL libpysal documentation](https://pysal.org/libpysal/stable/)
