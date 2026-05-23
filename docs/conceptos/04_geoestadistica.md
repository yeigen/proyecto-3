# 04. Geoestadística: Kriging, variogramas, Moran y LOO-CV

Este documento explica la parte geoestadística del proyecto sin volverla pesada. La idea es entender cómo pasamos de mediciones puntuales en estaciones a una superficie estimada de contaminación.

## 1. Qué problema resuelve la geoestadística

Las estaciones DAGMA/CVC miden en puntos específicos. Pero el proyecto quiere estimar contaminación en lugares donde no hay estación.

La geoestadística ayuda a responder:

> Si conozco la contaminación en algunas estaciones, ¿qué valor tendría en un punto cercano no medido?

Ejemplo:

```text
Estación A: SO₂ = 7.65 µg/m³
Estación B: SO₂ = 2.48 µg/m³
Estación C: SO₂ = 13.12 µg/m³
        ↓
Quiero estimar SO₂ en un punto sin estación
```

La idea no es adivinar a ciegas. La geoestadística usa la estructura espacial: puntos cercanos suelen parecerse más que puntos lejanos.

## 2. Autocorrelación espacial

La autocorrelación espacial significa que una variable se parece a sí misma en el espacio.

En calidad del aire:

- zonas cercanas a una vía pueden compartir niveles altos de NO₂;
- zonas cercanas a Yumbo pueden compartir señales industriales;
- zonas con vegetación o buena ventilación pueden tener valores más bajos.

La idea clásica es:

> Cerca se parece más; lejos se parece menos.

No siempre se cumple perfecto, pero es el punto de partida.

## 3. Kriging en una frase

Kriging es una forma inteligente de interpolar.

En vez de hacer un promedio simple de estaciones, asigna pesos según la distancia y la estructura espacial observada.

Fórmula conceptual:

$$
\hat{Z}(s_0) = \sum_{i=1}^{N} w_i Z(s_i)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $\hat{Z}(s_0)$ | valor estimado en el punto nuevo $s_0$ |
| $Z(s_i)$ | valor observado en la estación $i$ |
| $w_i$ | peso asignado a la estación $i$ |
| $N$ | número de estaciones usadas |

Lectura:

> El valor estimado es una mezcla ponderada de estaciones conocidas.

## 4. Qué hace distinto a Kriging

Kriging no solo estima un valor. También estima incertidumbre.

Produce dos salidas:

| Salida | Qué significa |
|---|---|
| $\hat{Z}(s_0)$ | concentración estimada |
| $\sigma^2_K(s_0)$ | varianza/incertidumbre de predicción |

La incertidumbre es clave. No es lo mismo predecir cerca de muchas estaciones que predecir en una zona alejada sin datos.

En un mapa, la incertidumbre puede usarse como opacidad o como capa aparte:

```text
baja incertidumbre  → más confianza
alta incertidumbre  → menos confianza
```

## 5. Variograma: medir cómo cambia la similitud con la distancia

El variograma mide cuánto cambian los valores cuando los puntos se separan en el espacio.

Semivariograma experimental:

$$
\gamma(h) = \frac{1}{2N(h)}\sum_{i,j: d(i,j) \approx h} [Z(s_i) - Z(s_j)]^2
$$

Donde:

| Símbolo | Significado |
|---|---|
| $\gamma(h)$ | semivarianza a distancia $h$ |
| $h$ | distancia entre pares de puntos |
| $N(h)$ | número de pares separados aproximadamente por $h$ |
| $Z(s_i)$ | valor observado en el punto $i$ |

Lectura chill:

> Si dos estaciones cercanas tienen valores parecidos, la semivarianza a distancias cortas será baja. Si estaciones lejanas son muy distintas, la semivarianza sube.

## 6. Nugget, sill y range

Son tres palabras raras pero importantes.

| Concepto | Traducción práctica | Qué indica |
|---|---|---|
| Nugget | salto inicial | ruido, error de medición o variación a escala muy pequeña |
| Sill | meseta | variabilidad total cuando la distancia ya no importa |
| Range | alcance | distancia a partir de la cual los puntos dejan de parecerse |

Visualmente:

```text
semivarianza
   ↑
   |              _________ sill
   |            /
   |          /
   | nugget /
   |______/
   +----------------------→ distancia
          range
```

Ejemplo de lectura:

> Si el range de SO₂ fuera 8 km, significaría que estaciones separadas menos de 8 km todavía comparten estructura espacial; más allá de eso, ya se parecen poco.

## 7. Modelos de variograma

El variograma experimental suele ser ruidoso. Por eso se ajusta un modelo teórico.

Modelos comunes:

| Modelo | Cuándo tiene sentido |
|---|---|
| Esférico | cambios suaves hasta una distancia límite clara |
| Exponencial | correlación que cae rápido pero nunca desaparece del todo |
| Gaussiano | superficie muy suave |
| Nugget puro | no hay estructura espacial clara, solo ruido |

En los documentos de Situación 3 se menciona Kriging Ordinario con variograma exponencial.

## 8. Kriging Ordinario

Kriging Ordinario asume que la media local es desconocida pero constante dentro de la zona analizada.

La restricción típica es:

$$
\sum_{i=1}^{N} w_i = 1
$$

Esto evita que la predicción se sesgue por pesos que sumen más o menos que uno.

Intuición:

> El modelo decide cuánto pesa cada estación, pero los pesos deben formar una combinación balanceada.

## 9. Kriging espacio-temporal

El PDF propone Kriging espacio-temporal. Eso significa que no solo importa la distancia espacial, también la distancia temporal.

Punto clásico:

$$
s = (lat, lon)
$$

Punto espacio-temporal:

$$
(s,t) = (lat, lon, tiempo)
$$

La predicción busca estimar:

$$
\hat{Z}(s_0,t_0)
$$

Es decir: contaminación esperada en un lugar y momento específico.

En la práctica del proyecto actual, el mejor resultado documentado fue Kriging Ordinario sobre coordenadas, porque el número de estaciones limita una validación espacio-temporal más fuerte.

## 10. LOO-CV: validación dejando una estación fuera

LOO-CV significa **Leave-One-Out Cross-Validation**.

En la Situación 3 se usa así:

```text
1. Quito una estación.
2. Ajusto/interpolo con las demás.
3. Predigo la estación que quité.
4. Comparo predicción vs valor real.
5. Repito para cada estación.
```

Fórmula del error:

$$
e_{LOO,i} = y_i - \hat{y}_{-i}
$$

Donde:

| Símbolo | Significado |
|---|---|
| $y_i$ | valor real de la estación $i$ |
| $\hat{y}_{-i}$ | predicción de la estación $i$ sin usarla para ajustar |

Esto es importante porque evita evaluar al modelo en puntos que ya conoce.

## 11. Resultados LOO-CV actuales del proyecto

Según la documentación actual de Situación 3:

### SO₂

| Métrica | Resultado |
|---|---:|
| Estaciones evaluables | 4 |
| MAE | 5.02 µg/m³ |
| RMSE aproximado | 5.78 µg/m³ |

### O₃

| Métrica | Resultado |
|---|---:|
| Estaciones evaluables | 7 |
| MAE | 4.91 µg/m³ |
| RMSE aproximado | 5.93 µg/m³ |

### NO₂

NO₂ no tiene LOO-CV espacial robusto porque en el parquet principal solo aparece en una estación: Yumbo.

Esto no significa que NO₂ no exista en el proyecto. Significa que no hay suficientes estaciones con NO₂ para hacer una validación leave-one-out espacial seria.

## 12. Cómo interpretar esos resultados

Lectura honesta:

| Contaminante | Lectura |
|---|---|
| SO₂ | Error razonable y cerca del KPI del PDF, pero solo con 4 estaciones. |
| O₃ | Cumple RMSE del PDF con 7 estaciones. |
| NO₂ | No evaluable espacialmente con LOO-CV por falta de estaciones. |
| R² | Bajo o negativo, señal de poca capacidad para explicar varianza con tan pocos puntos. |

En defensa, lo correcto sería decir:

> Kriging dio resultados útiles para SO₂ y O₃ en términos de MAE/RMSE, pero la validación sigue limitada por el número de estaciones. Para NO₂ no se puede prometer LOO-CV espacial robusto porque solo hay una estación con datos en el parquet principal.

## 13. Moran I: autocorrelación espacial global

Moran I mide si valores parecidos tienden a agruparse espacialmente.

Fórmula conceptual:

$$
I = \frac{N}{W}\frac{\sum_i\sum_j w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_i (x_i - \bar{x})^2}
$$

Donde:

| Símbolo | Significado |
|---|---|
| $N$ | número de puntos o celdas |
| $w_{ij}$ | peso espacial entre $i$ y $j$ |
| $W$ | suma total de pesos espaciales |
| $x_i$ | valor en el punto $i$ |
| $\bar{x}$ | promedio |

Interpretación:

| Moran I | Lectura |
|---:|---|
| positivo | valores parecidos se agrupan |
| cercano a 0 | patrón parecido a aleatorio |
| negativo | valores altos cerca de bajos, patrón disperso |

El PDF espera algo como:

```text
Moran I > 0.30 con p < 0.05
```

Eso indicaría que el mapa predicho tiene coherencia espacial y no parece ruido puro.

## 14. Qué es el p-value en Moran

PySAL suele evaluar significancia con permutaciones.

Idea:

```text
1. Calculo Moran I real.
2. Revuelvo los valores muchas veces entre ubicaciones.
3. Calculo Moran I para cada permutación.
4. Miro si el Moran real es raro frente al azar.
```

Si:

$$
p < 0.05
$$

se interpreta como evidencia estadística de autocorrelación espacial.

## 15. LISA: autocorrelación espacial local

LISA significa **Local Indicators of Spatial Association**.

Mientras Moran I global responde:

> ¿Hay patrón espacial general?

LISA responde:

> ¿Dónde están los clusters específicos?

Tipos comunes:

| Tipo | Significado |
|---|---|
| High-High | zona alta rodeada de zonas altas |
| Low-Low | zona baja rodeada de zonas bajas |
| High-Low | zona alta rodeada de zonas bajas, posible outlier |
| Low-High | zona baja rodeada de zonas altas, posible outlier |

En contaminación, un cluster High-High puede indicar una zona crítica.

## 16. Matriz de pesos espaciales

Para Moran y LISA se necesita definir quién es vecino de quién.

Eso se hace con una matriz de pesos espaciales:

$$
W = [w_{ij}]
$$

Ejemplos:

| Tipo de pesos | Idea |
|---|---|
| Distancia | vecinos pesan más si están cerca |
| K vecinos más cercanos | cada punto se conecta con sus K vecinos más próximos |
| Queen/Rook | para polígonos: vecinos si comparten borde o vértice |

En una grilla de contaminación, se puede usar contigüidad o K vecinos. En estaciones puntuales, KNN suele ser más práctico.

## 17. Nugget puro en residuos

El PDF dice que el variograma de residuos debería ser “nugget puro”.

Primero, residuo:

$$
r_i = y_i - \hat{y}_i
$$

Si los residuos todavía tienen estructura espacial, significa que el modelo dejó un patrón geográfico sin aprender.

Si el variograma de residuos parece nugget puro:

```text
no hay estructura espacial clara en los errores
```

Eso es buena señal: el modelo capturó la parte espacial importante.

## 18. Relación entre Deep Learning y geoestadística

En el PDF, el flujo ideal es:

```text
Sentinel-2 + Sentinel-5P + ERA5 + MODIS
        ↓
GeoVision-CLIP + SAE
        ↓
Embeddings
        ↓
ConvLSTM
        ↓
Predicción inicial
        ↓
Kriging sobre residuos o predicciones
        ↓
Mapa continuo + incertidumbre
```

La idea es combinar:

| Parte | Qué aporta |
|---|---|
| Deep Learning | aprende patrones complejos visuales/temporales |
| Kriging | impone coherencia espacial e incertidumbre |
| LOO-CV | prueba si funciona en estaciones no vistas |
| Moran/LISA | revisa si los mapas tienen estructura espacial |

## 19. Por qué ConvLSTM no ganó en los resultados actuales

Según la documentación actual:

- ConvLSTM converge en pérdida.
- Pero no logra R² positivos en LOO-CV.
- Ridge tampoco mejora.
- Kriging Ordinario sobre coordenadas fue más útil.

Lectura:

> Los embeddings CLIP fueron útiles para clasificación en Situación 2, pero no necesariamente contienen suficiente información para predecir concentraciones absolutas en estaciones no vistas.

Esto es una conclusión honesta, no un fracaso. En estadística, saber qué no generaliza también es resultado.

## 20. Ejemplo de defensa oral

Una explicación sencilla:

> “La geoestadística entra porque tenemos pocas estaciones y queremos estimar en puntos sin medición. Kriging usa las estaciones conocidas y aprende cómo cambia la contaminación con la distancia mediante un variograma. Además devuelve incertidumbre, que es clave para no vender el mapa como si fuera exacto. Validamos con leave-one-out: quitamos una estación, predecimos su valor y comparamos. Para SO₂ y O₃ los errores fueron razonables; para NO₂ no se puede hacer LOO-CV espacial porque solo hay una estación con NO₂ en el parquet principal. Moran y LISA sirven para revisar si el mapa resultante tiene estructura espacial o si parece ruido.”

## 21. Errores comunes que debemos evitar

| Error | Corrección |
|---|---|
| Decir que Kriging “adivina” valores | Kriging interpola usando estructura espacial y variograma. |
| Reportar mapa sin incertidumbre | La varianza Kriging es parte importante del resultado. |
| Decir que NO₂ pasó LOO-CV | No es defendible con una sola estación. |
| Confundir Moran I con RMSE | Moran mide estructura espacial; RMSE mide error contra observaciones. |
| Confundir LISA con Moran global | LISA ubica clusters locales; Moran global resume el patrón general. |
| Decir que R² negativo invalida todo | Indica baja explicación de varianza; MAE/RMSE aún pueden ser informativos con pocas estaciones. |
| Mezclar Excel Cristian con parquet sin justificar | La verdad observada principal es el parquet DAGMA/CVC. |

## 22. Referencias y documentación

### Internas

- [Fórmulas del modelo](03_formulas_modelo.md)
- [Unidades de contaminantes](02_unidades_contaminantes.md)
- [Verdad observada](../situacion-3/metodologia/verdad-observada.md)
- [ConvLSTM, Kriging y LOO-CV](../situacion-3/metodologia/convlstm-kriging-loocv.md)
- [Kriging y LOO-CV](../situacion-3/resultados/kriging-loocv.md)
- [KPIs y limitaciones](../situacion-3/resultados/kpis-limitaciones.md)
- [Resultados Situación 3](../situacion-3/SIT3_RESULTADOS.md)

### Externas

- [PyKrige documentation](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/)
- [PySAL documentation](https://pysal.org/)
- [PySAL esda stable documentation](https://pysal.org/esda/stable/)
- [libpysal stable documentation](https://pysal.org/libpysal/stable/)
- [Anselin 1995 — Local Indicators of Spatial Association](https://onlinelibrary.wiley.com/doi/10.1111/j.1538-4632.1995.tb00338.x)

### Nota de auditoría

La consulta vía Context7 para PySAL confirma el uso de Moran global y Moran local/LISA con una matriz de pesos espaciales. En este documento se citan las rutas estables de PySAL (`esda/stable` y `libpysal/stable`) para evitar enlaces generados frágiles. Context7 no devolvió documentación útil de PyKrige en esta sesión, así que para Kriging se citan la documentación oficial pública de PyKrige y los documentos internos de Situación 3.
