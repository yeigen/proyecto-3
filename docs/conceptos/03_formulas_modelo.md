# 03. Fórmulas del modelo y métricas del proyecto

Este documento explica las fórmulas principales del proyecto en modo entendible. La idea es que puedas mirar una fórmula y saber qué papel cumple, sin perderte en tecnicismos.

El proyecto tiene tres familias de fórmulas:

1. **Fórmulas de variables**: NDVI, viento, escalas, conversiones.
2. **Fórmulas de entrenamiento**: CLIP, InfoNCE, SAE, pérdida total.
3. **Fórmulas de evaluación**: error, MAE, RMSE, R², Recall@K, LOO-CV.

## 1. Notación básica

| Símbolo | Qué significa |
|---|---|
| $x$ | dato de entrada, por ejemplo una imagen o embedding |
| $\hat{x}$ | reconstrucción de $x$ |
| $y$ | valor real observado |
| $\hat{y}$ | valor predicho por el modelo |
| $e$ | error entre real y predicho |
| $N$ | número de ejemplos |
| $s$ | ubicación espacial |
| $t$ | tiempo |
| $i, j$ | índices de ejemplos dentro de un batch |

La regla mental:

> Lo que tiene sombrero, como $\hat{y}$, normalmente es algo estimado o predicho.

## 2. NDVI: índice de vegetación

El NDVI mide qué tan vegetal parece un píxel usando rojo e infrarrojo cercano.

$$
NDVI = \frac{NIR - Red}{NIR + Red}
$$

En Sentinel-2:

$$
NDVI = \frac{B8 - B4}{B8 + B4}
$$

Interpretación rápida:

| NDVI | Lectura |
|---:|---|
| bajo o negativo | agua, sombra, nubes o superficies raras |
| cercano a 0 | suelo desnudo, concreto, zona urbana |
| alto | vegetación densa |

En el proyecto sirve para distinguir zonas vegetadas de zonas urbanas o suelo descubierto.

## 3. Velocidad del viento

ERA5 entrega viento en dos componentes:

- $u$: componente este-oeste;
- $v$: componente norte-sur.

La velocidad total se calcula así:

$$
wind\_speed = \sqrt{u^2 + v^2}
$$

Ejemplo:

$$
u=3,\quad v=4
$$

$$
wind\_speed = \sqrt{3^2 + 4^2} = 5\ m/s
$$

En contaminación, más viento suele significar más dispersión y menos acumulación local.

## 4. Error básico: observado menos predicho

La fórmula más simple para auditar un modelo es el error:

$$
e_i = y_i - \hat{y}_i
$$

Donde:

| Símbolo | Significado |
|---|---|
| $y_i$ | valor real observado, por ejemplo DAGMA |
| $\hat{y}_i$ | valor predicho por el modelo |
| $e_i$ | error |

Si $e_i$ es positivo, el modelo predijo menos que lo observado. Si es negativo, predijo más.

Ejemplo:

$$
y = 10.76,\quad \hat{y} = 6.90
$$

$$
e = 10.76 - 6.90 = 3.86\ \mu g/m^3
$$

## 5. MAE: error absoluto medio

MAE significa **Mean Absolute Error**.

$$
MAE = \frac{1}{N}\sum_{i=1}^{N}|y_i - \hat{y}_i|
$$

Traducción:

> Promedio de qué tan lejos estuvo el modelo, sin importar si se pasó por arriba o por abajo.

Ejemplo simple:

```text
errores absolutos = [2, 4, 6]
MAE = (2 + 4 + 6) / 3 = 4
```

Es fácil de explicar porque queda en la misma unidad del contaminante, por ejemplo `µg/m³`.

## 6. MSE y RMSE

MSE significa **Mean Squared Error**:

$$
MSE = \frac{1}{N}\sum_{i=1}^{N}(y_i - \hat{y}_i)^2
$$

RMSE es la raíz del MSE:

$$
RMSE = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(y_i - \hat{y}_i)^2}
$$

Traducción:

- MSE castiga más fuerte errores grandes porque eleva al cuadrado.
- RMSE vuelve a la unidad original, por ejemplo `µg/m³`.

En el PDF, los KPIs de la Situación 3 usan RMSE para NO₂, SO₂ y O₃.

## 7. R²: proporción de variación explicada

R² compara el modelo contra una predicción muy básica: predecir siempre el promedio.

$$
R^2 = 1 - \frac{\sum_{i=1}^{N}(y_i - \hat{y}_i)^2}{\sum_{i=1}^{N}(y_i - \bar{y})^2}
$$

Donde $\bar{y}$ es el promedio observado.

Interpretación:

| R² | Lectura |
|---:|---|
| cercano a 1 | el modelo explica muy bien la variación |
| cercano a 0 | parecido a predecir el promedio |
| negativo | peor que predecir el promedio |

En este proyecto, R² puede salir bajo o negativo cuando hay pocas estaciones. Por eso MAE y RMSE son más estables para explicar resultados con DAGMA/CVC.

## 8. CLIP: acercar imagen y texto

CLIP aprende a poner imágenes y textos relacionados cerca dentro de un espacio numérico.

Ejemplo:

```text
Imagen Sentinel-2 de zona industrial
Texto: “contaminación alta NO₂”
```

El modelo convierte ambos en vectores:

$$
e_i = encoder_{img}(imagen_i)
$$

$$
f_i = encoder_{txt}(texto_i)
$$

Donde:

| Símbolo | Qué es |
|---|---|
| $e_i$ | embedding de imagen |
| $f_i$ | embedding de texto |

La meta es que la imagen correcta y su texto correcto tengan alta similitud.

## 9. Similitud coseno

CLIP suele comparar embeddings con similitud coseno:

$$
sim(e, f) = \frac{e \cdot f}{\|e\|\|f\|}
$$

Interpretación:

| Valor | Lectura |
|---:|---|
| cercano a 1 | muy parecidos |
| cercano a 0 | poca relación |
| cercano a -1 | opuestos |

En palabras simples: mide si dos vectores apuntan hacia una dirección parecida.

## 10. InfoNCE: pérdida contrastiva de CLIP

La pérdida contrastiva premia que cada imagen encuentre su texto correcto y no los textos incorrectos del batch.

Una forma simplificada:

$$
L_{InfoNCE} = -\frac{1}{N}\sum_{i=1}^{N}\log\left(\frac{\exp(sim(e_i,f_i)/\tau)}{\sum_{j=1}^{N}\exp(sim(e_i,f_j)/\tau)}\right)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $e_i$ | embedding de la imagen $i$ |
| $f_i$ | embedding del texto correcto para $i$ |
| $f_j$ | textos candidatos dentro del batch |
| $sim$ | similitud coseno |
| $\tau$ | temperatura |
| $N$ | tamaño del batch |

Lectura chill:

> El numerador es la pareja correcta. El denominador son todas las opciones. La pérdida baja cuando la pareja correcta destaca sobre las demás.

### Qué hace la temperatura $\tau$

La temperatura controla qué tan exigente es la comparación.

- $\tau$ bajo: el modelo se vuelve más estricto.
- $\tau$ alto: suaviza las diferencias.

En el PDF se menciona una temperatura inicial típica:

$$
\tau = 0.07
$$

## 11. Sparse Autoencoder: comprimir y reconstruir

Un autoencoder intenta reconstruir su entrada.

```text
x → encoder → z → decoder → x_hat
```

En fórmula:

$$
z = encoder(x)
$$

$$
\hat{x} = decoder(z)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $x$ | embedding original |
| $z$ | representación comprimida |
| $\hat{x}$ | reconstrucción |

En el proyecto, el SAE se usa para analizar embeddings de CLIP y buscar representaciones más interpretables.

## 12. Pérdida de reconstrucción del SAE

La reconstrucción se mide con error cuadrático:

$$
L_{recon} = \|x - \hat{x}\|^2
$$

Si $\hat{x}$ se parece mucho a $x$, la pérdida es baja.

En PyTorch esto normalmente se implementa con `MSELoss`, que calcula error cuadrático medio.

## 13. Penalización L1: sparsity

El SAE no solo reconstruye. También se le pide que use pocas neuronas activas.

Eso se logra con una penalización L1:

$$
L_{sparse} = \lambda \|z\|_1
$$

La norma L1 es:

$$
\|z\|_1 = \sum_k |z_k|
$$

Intuición:

> Si muchas activaciones son grandes, la penalización sube. El modelo aprende a representar usando pocas activaciones importantes.

En el PDF se propone:

$$
\lambda = 10^{-3}
$$

## 14. Pérdida completa del SAE

Juntando reconstrucción y sparsity:

$$
L_{SAE} = \|x - \hat{x}\|^2 + \lambda \|z\|_1
$$

Traducción:

> Reconstruye bien, pero no actives todo al mismo tiempo.

## 15. Pérdida total del modelo

El PDF propone combinar CLIP + SAE:

$$
L_{total} = L_{InfoNCE} + \alpha \cdot (L_{sae\_img} + L_{sae\_txt})
$$

Donde:

| Término | Qué representa |
|---|---|
| $L_{InfoNCE}$ | que imagen y texto correcto queden cerca |
| $L_{sae\_img}$ | SAE aplicado a embeddings de imagen |
| $L_{sae\_txt}$ | SAE aplicado a embeddings de texto |
| $\alpha$ | peso de la parte SAE |

En el PDF:

$$
\alpha = 0.1
$$

Lectura:

> La prioridad principal es aprender alineación imagen-texto; el SAE ayuda como regularización e interpretabilidad.

## 16. Sparsity ratio

El sparsity ratio mide qué proporción de activaciones son casi cero.

En el PDF aparece como:

$$
sparsity = mean(z < 0.01)
$$

Interpretación:

| Sparsity | Lectura |
|---:|---|
| baja | muchas neuronas activas |
| alta | pocas neuronas activas |

Si el KPI pide sparsity visual ≥ 0.70, significa que al menos 70% de activaciones deberían estar casi apagadas.

## 17. Recall@K

Recall@K mide si el texto correcto aparece dentro de los K textos más parecidos a una imagen.

Para una imagen:

- Recall@1 acierta si el texto correcto queda primero.
- Recall@5 acierta si el texto correcto queda dentro de los primeros 5.

Fórmula conceptual:

$$
Recall@K = \frac{\text{número de consultas donde el correcto aparece en top K}}{\text{número total de consultas}}
$$

Ejemplo:

```text
100 imágenes evaluadas
Recall@1 = 0.48 → 48 imágenes recuperaron el texto correcto en primer lugar
Recall@5 = 1.00 → 100 imágenes tuvieron el texto correcto dentro del top 5
```

En el proyecto final documentado:

| Métrica | Resultado |
|---|---:|
| Recall@1 | 0.483 |
| Recall@5 | 1.000 |

## 18. ConvLSTM: secuencias espacio-temporales

ConvLSTM es una LSTM pensada para datos con forma espacial. En vez de procesar solo una lista de números, procesa secuencias de grillas o mapas.

En el PDF, la idea es:

```text
8 fechas de embeddings → ConvLSTM → predicción T+1, T+3, T+7
```

La salida esperada se puede pensar como:

$$
\hat{Y} \in \mathbb{R}^{3 \times 3 \times H \times W}
$$

Donde:

| Dimensión | Significado |
|---|---|
| 3 | horizontes: T+1, T+3, T+7 |
| 3 | contaminantes: NO₂, SO₂, O₃ |
| H, W | grilla espacial |

Lectura simple:

> Para cada punto de la grilla, el modelo predice tres contaminantes en tres horizontes.

## 19. Kriging: predicción espacial con incertidumbre

Kriging estima un valor en un punto no observado usando puntos cercanos y la estructura espacial.

Forma conceptual:

$$
\hat{Z}(s_0) = \sum_{i=1}^{N} w_i Z(s_i)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $s_0$ | punto donde quiero predecir |
| $s_i$ | puntos conocidos, por ejemplo estaciones |
| $Z(s_i)$ | valor observado en cada estación |
| $w_i$ | pesos calculados por Kriging |

La ventaja frente a un promedio simple es que Kriging también calcula incertidumbre:

$$
\sigma^2_K(s_0)
$$

Esa varianza ayuda a construir mapas de confianza.

## 20. LOO-CV: dejar una estación por fuera

LOO-CV significa **Leave-One-Out Cross-Validation**.

En este proyecto:

```text
1. Quito una estación.
2. Entreno/interpolo con las demás.
3. Predigo la estación quitada.
4. Comparo predicción vs valor real.
5. Repito para cada estación.
```

Fórmula del error por estación:

$$
e_{LOO,i} = y_i - \hat{y}_{-i}
$$

Donde $\hat{y}_{-i}$ significa que se predijo la estación $i$ sin usarla para ajustar.

Esto evita una trampa común: evaluar el modelo en los mismos puntos que usó para entrenar.

## 21. Lectura de resultados actuales del proyecto

Según los documentos actuales:

| Componente | Lectura |
|---|---|
| CLIP | Recall@1 final 0.483 y Recall@5 final 1.000. Cumple mínimo de Recall@1 del PDF. |
| SAE | Se usa para analizar embeddings de 512 dimensiones con capa interna de 256. |
| ConvLSTM | Converge en pérdida, pero no logra R² positivos en LOO-CV. |
| Kriging | Mejor alternativa práctica para SO₂ y O₃ con pocas estaciones. |
| NO₂ | LOO-CV espacial no es evaluable bien porque el parquet principal solo tiene NO₂ en Yumbo. |

Esta lectura es importante para la defensa: no basta decir qué modelo se usó; hay que explicar qué funcionó, qué no y por qué.

## 22. Errores comunes al explicar estas fórmulas

| Error | Corrección |
|---|---|
| Decir que CLIP predice directamente contaminación | CLIP aprende representaciones imagen-texto; la predicción viene después. |
| Decir que SAE mejora automáticamente el modelo | SAE ayuda a regularizar/interpretar, pero debe validarse. |
| Confundir MSE con RMSE | RMSE vuelve a la unidad original; MSE queda al cuadrado. |
| Decir que R² negativo es imposible | Sí puede ser negativo si el modelo es peor que predecir el promedio. |
| Evaluar Kriging con las mismas estaciones usadas para ajustar | Por eso se usa LOO-CV. |
| Confundir Recall@5 con accuracy normal | Recall@5 permite que el correcto esté dentro de los cinco primeros. |

## 23. Referencias y documentación

### Internas

- [Objetivo del proyecto](00_objetivo_del_proyecto.md)
- [Datasets y variables](01_datasets_y_variables.md)
- [Unidades de contaminantes](02_unidades_contaminantes.md)
- [CLIP y RemoteCLIP](clip-y-remoteclip.md)
- [Arquitectura CLIP + SAE](../situacion-2/metodologia/arquitectura-clip-sae.md)
- [Entrenamiento Situación 2](../situacion-2/metodologia/entrenamiento.md)
- [ConvLSTM, Kriging y LOO-CV](../situacion-3/metodologia/convlstm-kriging-loocv.md)
- [Kriging y LOO-CV](../situacion-3/resultados/kriging-loocv.md)

### Externas

- [CLIP paper — Radford et al. 2021](https://arxiv.org/abs/2103.00020)
- [RemoteCLIP paper](https://ieeexplore.ieee.org/document/10504785)
- [LoRA paper](https://arxiv.org/abs/2106.09685)
- [ConvLSTM paper](https://arxiv.org/abs/1506.04214)
- [PyKrige documentation](https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/)
- [PyTorch documentation](https://pytorch.org/docs/stable/index.html)
- [PyTorch MSELoss](https://pytorch.org/docs/stable/generated/torch.nn.MSELoss.html)
- [PyTorch AdamW](https://pytorch.org/docs/stable/generated/torch.optim.AdamW.html)

### Nota de auditoría

La documentación de PyTorch consultada vía Context7 confirma el uso estándar de `MSELoss` para error cuadrático medio y `AdamW` como optimizador. Las fórmulas de InfoNCE, SAE y pérdida total vienen del PDF del proyecto y de la arquitectura CLIP/SAE documentada internamente. La parte de Kriging se deja aquí como introducción; se desarrolla mejor en el documento de geoestadística.
