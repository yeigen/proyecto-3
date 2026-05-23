# 00. Qué busca el proyecto GeoVision-CLIP Cali

Este documento es la primera parada para entender el proyecto sin entrar todavía en todo el detalle matemático. La idea es tener claro el mapa general: qué problema se quiere resolver, qué datos se usan y por qué el proyecto mezcla satélites, estaciones de calidad del aire, meteorología, deep learning y geoestadística.

## 1. La idea en una frase

El proyecto busca estimar la contaminación atmosférica en lugares de Cali donde no hay estaciones de monitoreo, usando datos satelitales, variables meteorológicas, mediciones reales de estaciones y modelos estadísticos/de aprendizaje profundo.

Dicho más simple: queremos pasar de tener mediciones en pocos puntos a construir una idea continua de cómo se comporta la contaminación en toda la ciudad.

## 2. Qué problema quiere resolver

Cali y su zona metropolitana no tienen sensores de contaminación en cada barrio. Las estaciones del DAGMA/CVC miden bien, pero están ubicadas en puntos específicos. Eso deja muchas zonas sin medición directa: laderas, corredores viales, zonas industriales, barrios alejados o áreas cercanas a Yumbo–Acopi.

Entonces aparece la pregunta central:

> Si solo tengo algunas estaciones reales, ¿puedo estimar qué pasa en puntos donde no hay estación?

Eso es lo que el PDF llama estimación en **puntos no muestreados**.

Un punto no muestreado es simplemente una ubicación `(latitud, longitud)` donde no existe una estación midiendo directamente, pero donde sí queremos conocer una concentración aproximada de contaminantes.

## 3. Qué contaminantes mira el proyecto

El foco está en tres gases principales:

| Contaminante | Nombre | Por qué importa |
|---|---|---|
| NO₂ | Dióxido de nitrógeno | Muy asociado a tráfico, combustión, actividad industrial y calidad del aire urbana. |
| SO₂ | Dióxido de azufre | Asociado a combustión con azufre, actividad industrial y formación de aerosoles de sulfato. |
| O₃ | Ozono | No se emite directamente en superficie: se forma por reacciones químicas con luz solar. Puede ser alto lejos de la fuente original. |

Además aparece MODIS AOD:

| Variable | Nombre | Rol |
|---|---|---|
| AOD | Aerosol Optical Depth | No mide PM2.5/PM10 directamente, pero sirve como señal óptica relacionada con aerosoles en la atmósfera. |

## 4. Ojo con una diferencia clave: satélite vs estación

Aquí está uno de los puntos más importantes del proyecto.

Las estaciones DAGMA/CVC miden concentración cerca de la superficie, normalmente reportada en unidades como:

$$
\mu g/m^3
$$

Eso significa microgramos de contaminante por metro cúbico de aire.

En cambio, Sentinel-5P mide columnas atmosféricas, usualmente en:

$$
mol/m^2
$$

Eso significa cantidad de moléculas integrada en una columna vertical de atmósfera sobre un área.

No son exactamente la misma cosa.

Por eso el proyecto no debería tratar Sentinel-5P como si fuera una estación. Sentinel-5P ayuda a ver patrones atmosféricos amplios, pero la validación fuerte debe hacerse contra estaciones reales.

## 5. Qué datos usa el proyecto y para qué

El proyecto combina fuentes que observan partes distintas del problema.

| Fuente | Qué observa | Para qué sirve en el proyecto |
|---|---|---|
| Sentinel-2 MSI | Superficie: vegetación, ciudad, suelo, agua, sombras, nubes | Crear imágenes/tiles de alta resolución para que el modelo aprenda patrones territoriales. |
| Sentinel-5P TROPOMI | Columnas atmosféricas de NO₂, SO₂ y O₃ | Dar contexto de contaminación y construir pseudo-etiquetas para muestreo. |
| ERA5 | Meteorología: temperatura, viento, humedad, presión, precipitación, capa límite | Explicar dispersión, acumulación o transporte de contaminantes. |
| MODIS MAIAC | Aerosoles y vapor de agua | Aportar contexto de partículas/aerosoles en la atmósfera. |
| DAGMA/CVC | Mediciones reales en estaciones | Servir como verdad observada para validar el modelo. |

La lógica es esta: ninguna fuente por sí sola resuelve el problema completo, pero juntas pueden contar una historia más completa.

## 6. Por qué Sentinel-2 es útil si no mide gases

Sentinel-2 no mide NO₂, SO₂ ni O₃ directamente. Entonces, ¿por qué se usa?

Porque ve la superficie con mucho detalle. Puede mostrar cosas como:

- zonas con vegetación;
- zonas urbanas densas;
- suelos descubiertos;
- cuerpos de agua;
- sombras y textura urbana;
- cambios territoriales.

Esas señales pueden estar relacionadas indirectamente con contaminación. Por ejemplo, una zona muy urbana o industrial puede tener un patrón visual distinto a una zona de vegetación densa.

En términos sencillos: Sentinel-2 le da al modelo “ojos” para entender el territorio.

## 7. Por qué Sentinel-5P es útil aunque sea más grueso

Sentinel-5P sí observa gases atmosféricos, pero con resolución espacial mucho más gruesa que Sentinel-2. Eso quiere decir que un píxel de Sentinel-5P cubre una zona grande, no una cuadra o un barrio pequeño.

Por eso el proyecto intenta hacer una especie de puente:

```text
Sentinel-5P: mide gases, pero grueso
Sentinel-2: ve detalles finos, pero no mide gases
Modelo: aprende a combinar ambas señales
```

A esa idea se le suele llamar **downscaling**: usar información gruesa más información fina para intentar representar el fenómeno a una escala más detallada.

## 8. Qué hacen las tres situaciones del proyecto

### Situación 1: construir el panel de datos

Aquí el objetivo es reunir, ordenar y validar los datos.

Se construye un panel espacio-temporal: muchos datos, de varias fuentes, organizados por tiempo y espacio. En el proyecto ya existe un panel publicado y documentado con Sentinel-2, Sentinel-5P, ERA5, MODIS y DAGMA/CVC.

En esta etapa se responde:

> ¿Tenemos datos suficientes, bien ubicados, con fechas, variables y formatos claros?

### Situación 2: aprender representaciones con GeoVision-CLIP

Aquí se toman tiles de Sentinel-2 y descripciones en texto para entrenar un modelo tipo CLIP.

CLIP aprende a acercar imágenes y textos relacionados dentro de un mismo espacio matemático llamado embedding.

Una forma simple de verlo:

```text
Imagen de zona urbana contaminada  → vector numérico
Texto “contaminación alta NO₂”     → vector numérico parecido
```

El objetivo no es solo clasificar imágenes. Es aprender una representación útil del territorio y su relación con contaminación.

También aparecen los Sparse Autoencoders, que intentan comprimir la información dejando activas pocas neuronas. Eso ayuda a interpretar qué partes del embedding parecen importantes.

### Situación 3: estimar contaminación y validar

Esta es la parte más estadística.

Se busca predecir contaminantes en puntos donde no hay estación y validar contra estaciones reales usando técnicas como:

- ConvLSTM para manejar secuencias temporales;
- Kriging para interpolación espacial/espacio-temporal;
- LOO-CV para validar dejando una estación por fuera;
- Moran I y LISA para revisar estructura espacial.

La pregunta aquí es:

> Si escondo una estación, ¿el modelo puede estimar razonablemente lo que esa estación habría medido?

## 9. Fórmula conceptual del proyecto

Por ahora, sin entrar en todo el detalle, la idea general puede verse así:

$$
\hat{y}(s,t) = f(\text{imagen satelital}, \text{atmósfera}, \text{meteorología}, s, t)
$$

Donde:

| Símbolo | Significado |
|---|---|
| $\hat{y}(s,t)$ | concentración estimada en una ubicación $s$ y tiempo $t$ |
| $s$ | ubicación espacial, por ejemplo latitud y longitud |
| $t$ | momento temporal |
| $f$ | modelo que aprende o estima la relación entre datos y contaminación |

La meta es que $\hat{y}(s,t)$ se parezca lo más posible a la medición real $y(s,t)$ cuando exista una estación para comparar.

El error básico sería:

$$
e(s,t) = y(s,t) - \hat{y}(s,t)
$$

Si el error es pequeño, el modelo va bien. Si además el error no tiene patrón espacial fuerte, mejor todavía, porque significa que el modelo capturó buena parte de la estructura geográfica.

## 10. Cómo saber si el proyecto va bien

El proyecto no se debe defender solo diciendo “el modelo corre”. Debe defenderse con evidencia.

Algunas evidencias esperadas son:

- tamaño real del dataset;
- manifest con hashes MD5;
- visualizaciones EDA;
- curvas de entrenamiento;
- métricas de recuperación CLIP;
- errores RMSE/MAE/R² contra estaciones;
- mapas de incertidumbre;
- validación leave-one-out;
- discusión honesta de limitaciones.

La parte más importante es no confundir datos satelitales con verdad absoluta. El satélite ayuda, pero la verdad observada principal para calidad del aire superficial viene de las estaciones.

## 11. Qué significa “comprender el proyecto”

Para defender este proyecto bien, no basta memorizar nombres de modelos. Hay que entender la cadena completa:

```text
Problema ambiental
    ↓
Datos disponibles
    ↓
Variables y unidades
    ↓
Modelo de representación
    ↓
Predicción espacial/temporal
    ↓
Validación contra estaciones
    ↓
Limitaciones y conclusiones
```

Cada documento de conceptos va a cubrir una parte de esa cadena.

## 12. Referencias y documentación útil

### Documentación interna

- [Datos del proyecto](../contexto/datos.md)
- [Problema del proyecto](../contexto/problema.md)
- [Modelo y validación](../contexto/modelo.md)
- [Datasets del proyecto](../DATASETS.md)
- [Flujo del proyecto](../FLUJO_PROYECTO.md)

### Fuentes y catálogos externos

- [Google Earth Engine — Sentinel-2 Surface Reflectance Harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Google Earth Engine — Sentinel-5P NO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Google Earth Engine — Sentinel-5P SO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Google Earth Engine — Sentinel-5P O₃](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [Google Earth Engine — MODIS MAIAC MCD19A2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [Google Earth Engine — ERA5 Hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY)
- [Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/)
- [NASA Earthdata](https://www.earthdata.nasa.gov/)
- [IDEAM SISAIRE](http://sisaire.ideam.gov.co/ideam-sisaire-web/)
- [DAGMA Cali](https://www.cali.gov.co/dagma/)

### Nota de auditoría

La documentación de Earth Engine consultada vía Context7 confirma que las bandas principales de Sentinel-5P NO₂, SO₂ y O₃ se reportan como columnas en `mol/m²`, y que `cloud_fraction` se reporta como fracción entre 0 y 1. Esto es importante porque esas unidades no son equivalentes directamente a `µg/m³` de estaciones superficiales.
