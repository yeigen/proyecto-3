# Guía del proyecto y Situación 1

Este documento explica qué quiere lograr GeoVision-CLIP Cali y ordena la lectura de la Situación 1. La Situación 2 y la Situación 3 se documentan aparte para no mezclar objetivos.

## 1. Qué busca el proyecto

GeoVision-CLIP Cali busca construir una base geoespacial para estudiar la contaminación atmosférica en Santiago de Cali y el corredor industrial Yumbo-Acopi.

La idea central es sencilla: unir imágenes satelitales, variables atmosféricas y mediciones de estaciones en un mismo panel temporal y espacial. Con ese panel se pueden entrenar modelos que relacionen patrones visuales del territorio con señales de calidad del aire.

El proyecto no parte de una sola fuente. Usa varias capas:

- Sentinel-2 para ver superficie urbana, vegetación, suelo, humedad y nubosidad.
- Sentinel-5P para columnas satelitales de NO2, SO2 y O3.
- ERA5 para contexto meteorológico horario.
- MODIS MAIAC para aerosoles y vapor de agua.
- DAGMA/CVC como verdad observada puntual en estaciones de monitoreo.

La meta final del proyecto completo es pasar de datos dispersos a un sistema integrado que permita entrenar CLIP, extraer factores latentes y apoyar interpolación espacial de contaminantes.

## 2. Por qué Cali + Yumbo

El área de estudio no se limita al casco urbano de Cali. Se amplió para incluir Yumbo y Acopi porque ahí está una parte clave del problema atmosférico: industria, transporte pesado y estaciones con datos relevantes.

El PDF original pedía un recorte más pequeño. El proyecto usa este BBox operativo:

```text
[-76.65, 3.30, -76.30, 3.65]
```

Ese recorte cubre Cali, Yumbo, Acopi y zonas agrícolas cercanas. También incluye la estación de Yumbo, que es crítica porque es la única estación con NO2 en la verdad observada principal.

![Comparación entre BBox del PDF y BBox usado por el proyecto](/docs/evidencias/situacion-1/panel/sit1_panel_bbox_pdf_vs_proyecto.png)

Vista general del área:

![Vista satelital de Cali y el área de estudio](/docs/evidencias/situacion-1/panel/sit1_panel_cali_google_earth.png)

## 3. Qué es la Situación 1

La Situación 1 es la construcción y validación del panel de datos. No entrena el modelo final. Su trabajo es dejar una base confiable para que las situaciones siguientes no dependan de descargas manuales, archivos sueltos o datos sin trazabilidad.

En términos prácticos, Situación 1 entrega:

- Un panel longitudinal 2021-2025 sobre Cali + Yumbo, con ventana técnica `2021-01-01` a `2026-01-01`.
- 6 fuentes satelitales/atmosféricas principales.
- DAGMA/CVC como verdad observada in situ.
- Datos en GeoTIFF raw y Zarr analítico.
- Publicación en GCS, HuggingFace y Kaggle.
- Manifest con tamaño, archivos, hashes y metadatos.
- EDA para verificar cobertura, rangos físicos y problemas de calidad.

El resultado operativo es el Kaggle Dataset `juanjoseorozcolopez/geovision-fuentes`, que pesa 89.73 GB. Kaggle muestra 8,848 archivos; el manifest técnico registra 8,847 archivos de datos porque Kaggle cuenta además `dataset-metadata.json`.

![Dataset del panel en Kaggle](/docs/evidencias/situacion-1/panel/sit1_panel_kaggle_dataset.png)

## 4. Flujo de datos

El flujo de Situación 1 fue:

```text
Google Earth Engine
        ↓
GeoTIFF raw en Google Cloud Storage
        ↓
Conversión a paneles Zarr
        ↓
Publicación en Kaggle Dataset y HuggingFace Hub
        ↓
Consumo por notebooks de Sit 2 y Sit 3
```

GCS queda como almacenamiento upstream. Kaggle es la fuente práctica para el equipo porque funciona bien con notebooks y GPU T4. HuggingFace se usa como respaldo público para paneles pequeños.

![Bucket en Google Cloud Storage](/docs/evidencias/situacion-1/panel/sit1_panel_bucket_gcs.png)

![Bucket público en HuggingFace](/docs/evidencias/situacion-1/panel/sit1_panel_bucket_hugging_face.png)

## 5. Resumen del panel

| Fuente | Rol en el proyecto | Shape Zarr | Periodo | Peso aproximado |
|---|---|---:|---|---:|
| Sentinel-2 MSI L2A | Imagen óptica de superficie | `(1552, 13, 3897, 3897)` | 2021-2025 | 76.99 GB raw |
| Sentinel-5P NO2 | Señal satelital de dióxido de nitrógeno | `(25592, 3, 36, 36)` | 2021-2025 | 0.04 GB raw |
| Sentinel-5P SO2 | Señal satelital de dióxido de azufre | `(25829, 2, 36, 36)` | 2021-2025 | 0.04 GB raw |
| Sentinel-5P O3 | Columna total de ozono | `(25716, 2, 36, 36)` | 2021-2025 | 0.06 GB raw |
| ERA5 horario | Meteorología y dispersión | `(43824, 8, 2, 2)` | 2021-2025 | 0.09 GB raw |
| MODIS MAIAC | Aerosoles y vapor de agua | `(1826, 4, 43, 43)` | 2021-2025 | 0.02 GB raw |
| DAGMA/CVC | Verdad observada puntual | 107,291 filas | 2020-2024 | 875 KB parquet |

El panel incluye 30 bandas seleccionadas de 360 disponibles. La selección no busca guardar todo; busca guardar lo útil para calidad del aire, modelado geoespacial y entrenamiento posterior.

## 6. Tiles MGRS: T18NUJ y T18NUK

Sentinel-2 organiza sus escenas con una grilla MGRS. En nuestro BBox aparecen dos tiles: `T18NUJ` y `T18NUK`. No son satélites distintos; son celdas geográficas de la grilla Sentinel-2.

| Tile MGRS | Qué cubre aproximadamente | Escenas totales | Escenas con SCL ≥ 30% | Lectura |
|---|---|---:|---:|---|
| `T18NUJ` | Cali, Yumbo, Acopi y valle medio | 779 | 133 | Aporta casi todo el material útil |
| `T18NUK` | Norte del Valle, zona cañera; apenas toca el borde norte del BBox | 773 | 3 | Aporte marginal para el muestreo |

La diferencia no se explica principalmente por nubosidad. El punto es geométrico: el BBox del proyecto llega hasta 3.65°N y `T18NUK` empieza cerca del borde norte. Por eso el panel útil de Sentinel-2 queda dominado por `T18NUJ`.

![Estaciones DAGMA/CVC frente a tiles MGRS](/docs/evidencias/situacion-3/dagma/figuras/dagma_estaciones_vs_tile_mgrs.png)

Esta figura también ayuda a leer la validación posterior: las 10 estaciones DAGMA/CVC caen en `T18NUJ`. No tenemos una foto separada de cada tile porque el proyecto no la necesitó; la evidencia útil es la relación entre BBox, estaciones y grilla MGRS.

## 7. Sentinel-2: la base visual

Sentinel-2 es la fuente más pesada y la más importante visualmente. Aporta la imagen multiespectral que luego se convierte en tiles para CLIP.

Se usan 13 bandas. Esta tabla traduce la columna técnica a una lectura más humana:

| Columna | Símbolo | Nombre en español | Unidad / escala | Resolución nativa | Uso en el proyecto |
|---|---|---|---|---:|---|
| `B1` | Aerosol | Aerosol costero | reflectancia escalada | 60 m | Señal atmosférica azul-violeta |
| `B2` | Azul | Banda azul | reflectancia escalada | 10 m | Color, bruma y agua |
| `B3` | Verde | Banda verde | reflectancia escalada | 10 m | Vegetación y color natural |
| `B4` | Rojo | Banda roja | reflectancia escalada | 10 m | Clorofila; cálculo NDVI |
| `B5` | RE1 | Borde rojo 1 | reflectancia escalada | 20 m | Estrés vegetal |
| `B6` | RE2 | Borde rojo 2 | reflectancia escalada | 20 m | Estructura vegetal |
| `B7` | RE3 | Borde rojo 3 | reflectancia escalada | 20 m | Continuo del borde rojo |
| `B8` | NIR | Infrarrojo cercano | reflectancia escalada | 10 m | Vegetación; cálculo NDVI |
| `B8A` | NIRn | Infrarrojo cercano estrecho | reflectancia escalada | 20 m | Vegetación con menor efecto de vapor de agua |
| `B9` | WV | Vapor de agua | reflectancia escalada | 60 m | Humedad atmosférica alta |
| `B11` | SWIR1 | Infrarrojo de onda corta 1 | reflectancia escalada | 20 m | Humedad de suelo y materiales urbanos |
| `B12` | SWIR2 | Infrarrojo de onda corta 2 | reflectancia escalada | 20 m | Suelo, minerales, zonas secas |
| `SCL` | Clase | Clasificación de escena | código categórico | 20 m | Filtro de nubes, sombras, agua y píxeles válidos |

Las bandas tienen resoluciones nativas distintas: 10 m, 20 m y 60 m. Para el panel se exportan en una grilla común de 10 m. Esto facilita el consumo posterior por modelos, aunque introduce una limitación: las bandas de 20 m y 60 m quedan representadas sobre una grilla más fina que su resolución real.

Ejemplo visual de Sentinel-2:

![Escena RGB Sentinel-2](/docs/evidencias/situacion-1/eda/sentinel-2/s2_rgb_escena_138.png)

Hallazgos principales:

- Hay 1,552 escenas en el periodo 2021-2025.
- Solo 136 escenas pasan el umbral SCL > 30%.
- La nubosidad es un problema fuerte en Cali.
- La distribución NDVI es bimodal: urbano cerca de 0.15 y vegetación cerca de 0.75.
- Solo 2 tiles MGRS cruzan el BBox; T18NUJ domina casi todo el panel útil.

![Distribución temporal Sentinel-2](/docs/evidencias/situacion-1/eda/sit1_eda_s2_distribucion_temporal_captura.png)

![Distribución NDVI Sentinel-2](/docs/evidencias/situacion-1/eda/sentinel-2/s2_ndvi_distribucion.png)

## 8. Sentinel-5P: contaminantes satelitales

Sentinel-5P/TROPOMI aporta mediciones satelitales de gases atmosféricos. En este proyecto se usan NO2, SO2 y O3.

Estas variables no son mediciones directas a nivel de calle. Son columnas atmosféricas. Aun así, sirven como señal espacial y temporal para construir pseudo-etiquetas y entender patrones regionales.

| Fuente | Columna | Símbolo | Nombre en español | Unidad | Uso |
|---|---|---|---|---|---|
| S5P NO2 | `tropospheric_NO2_column_number_density` | NO2 trop. | Columna troposférica de dióxido de nitrógeno | mol/m2 | Señal principal de NO2 cerca de la troposfera |
| S5P NO2 | `NO2_column_number_density` | NO2 total | Columna total de dióxido de nitrógeno | mol/m2 | Contexto tropósfera + estratósfera |
| S5P NO2 | `cloud_fraction` | nubosidad | Fracción de nube | 0-1 | Control de calidad |
| S5P SO2 | `SO2_column_number_density` | SO2 | Columna de dióxido de azufre | mol/m2 | Señal de emisiones industriales/combustión |
| S5P SO2 | `cloud_fraction` | nubosidad | Fracción de nube | 0-1 | Control de calidad |
| S5P O3 | `O3_column_number_density` | O3 total | Columna total de ozono | mol/m2 | Contexto de ozono; no equivale a O3 superficial |
| S5P O3 | `cloud_fraction` | nubosidad | Fracción de nube | 0-1 | Control de calidad |

### NO2

NO2 está asociado a tráfico vehicular, combustión e industria. En el panel se usa principalmente `tropospheric_NO2_column_number_density`, más columna total y fracción de nubes.

En el EDA aparecen dos zonas relevantes: Yumbo y Cali centro.

### SO2

SO2 está asociado a fuentes industriales y combustión con azufre. Su señal es más ruidosa y esporádica que NO2.

### O3

O3 se maneja con más cuidado. Sentinel-5P entrega columna total de ozono, no ozono superficial directo. Esto sirve para contexto atmosférico, pero no debe interpretarse como medición local equivalente a una estación.

Mapas promedio de S5P:

![Mapas promedio Sentinel-5P](/docs/evidencias/situacion-1/eda/s5p/s5p_mapas_promedio.png)

Percentiles usados como referencia en el panel:

| Gas | p50 | p90 | p99 | Unidad |
|---|---:|---:|---:|---|
| NO2 | 2.64e-05 | 5.28e-05 | 8.87e-05 | mol/m2 |
| SO2 | 6.14e-05 | 3.87e-04 | 8.30e-04 | mol/m2 |
| O3 | 1.15e-01 | 1.23e-01 | 1.29e-01 | mol/m2 |

## 9. ERA5: contexto meteorológico

ERA5 aporta meteorología horaria. Es importante porque la concentración observada de contaminantes no depende solo de emisiones; también depende de mezcla atmosférica, viento, humedad, presión y lluvia.

Se usan 8 variables:

| Columna | Símbolo | Nombre en español | Unidad | Qué significa |
|---|---|---|---|---|
| `temperature_2m` | T2m | Temperatura del aire a 2 metros | K | Temperatura cerca de superficie |
| `dewpoint_temperature_2m` | Td2m | Temperatura de punto de rocío a 2 metros | K | Humedad del aire expresada como temperatura de condensación |
| `u_component_of_wind_10m` | u10 | Componente zonal del viento a 10 metros | m/s | Viento oeste-este; valores negativos indican viento hacia el oeste |
| `v_component_of_wind_10m` | v10 | Componente meridional del viento a 10 metros | m/s | Viento sur-norte; valores negativos indican viento hacia el sur |
| `boundary_layer_height` | BLH | Altura de la capa límite atmosférica | m | Altura de mezcla donde se diluyen contaminantes |
| `relative_humidity_850hPa` | RH850 | Humedad relativa a 850 hPa | % | Humedad en nivel atmosférico bajo-medio |
| `surface_pressure` | Ps | Presión superficial | Pa | Presión del aire en superficie |
| `total_precipitation` | TP | Precipitación total | m | Lluvia acumulada; ayuda a explicar lavado atmosférico |

La variable más importante para dispersión es `boundary_layer_height` o BLH. En Cali varía mucho durante el día: cerca de 66 m en la mañana y cerca de 607 m al mediodía. Esa diferencia cambia la dilución de contaminantes.

![Ciclo diurno de ERA5](/docs/evidencias/situacion-1/eda/era5/era5_ciclo_diurno.png)

También se observó viento medio desde el norte, coherente con transporte desde Yumbo hacia Cali. Esto respalda la decisión de ampliar el BBox.

## 10. MODIS MAIAC: aerosoles y vapor de agua

MODIS MAIAC aporta AOD, una señal relacionada con aerosoles. Es útil como proxy atmosférico para material particulado, aunque no reemplaza una medición PM2.5 o PM10 en superficie.

| Columna | Símbolo | Nombre en español | Unidad / escala | Uso |
|---|---|---|---|---|
| `Optical_Depth_047` | AOD 0.47 | Profundidad óptica de aerosoles a 0.47 µm | escala 0.001 | Proxy de aerosoles en banda azul |
| `Optical_Depth_055` | AOD 0.55 | Profundidad óptica de aerosoles a 0.55 µm | escala 0.001 | Proxy de aerosoles en banda verde |
| `Column_WV` | WV | Columna de vapor de agua | escala 0.001 | Humedad atmosférica integrada |
| `AOD_QA` | QA | Calidad de AOD | bitfield | Máscara de calidad del producto MAIAC |

La fuente tuvo un problema técnico importante. Se detectó y corrigió en tres iteraciones:

| Versión | Problema | Resultado |
|---|---|---|
| v1 | `_FillValue=-28672` no se enmascaró antes de promediar | AOD negativo inválido |
| v2 | Escala aplicada, pero se mezclaban gránulos no representativos de Cali | AOD diluido |
| v3 | Filtro tile h10v08 + máscara + escala correcta | AOD físico |

La versión final confiable es `panel_v3.zarr`.

![Mapa promedio MODIS corregido](/docs/evidencias/situacion-1/eda/modis/v2/modis_mapa_promedio.png)

La baja cobertura AOD no es un error del proyecto. Es esperable en una zona tropical con nubosidad frecuente. La columna de vapor de agua sí mantiene cobertura alta y queda como variable útil.

## 11. DAGMA/CVC: verdad observada

DAGMA/CVC no es una fuente satelital. Es la referencia puntual medida en estaciones de calidad del aire.

En la guía lo leemos así:

| Campo / variable | Símbolo | Nombre en español | Unidad | Uso |
|---|---|---|---|---|
| `NO2` | NO2 | Dióxido de nitrógeno medido en estación | µg/m3 | Verdad observada para NO2; solo Yumbo en parquet principal |
| `SO2` | SO2 | Dióxido de azufre medido en estación | µg/m3 | Verdad observada para SO2 |
| `O3` | O3 | Ozono medido en estación | µg/m3 | Verdad observada para O3 superficial |
| `fecha` / `datetime` | t | Fecha y hora de medición | hora local / timestamp | Cruce temporal con panel satelital |
| `lat`, `lon` | φ, λ | Coordenadas de estación | grados | Ubicación para validación espacial |
| `nombre_est` | estación | Nombre de estación | texto | Identificación legible en mapas y tablas |

El archivo principal es:

```text
dagma/dagma_cvc_horario_raw.parquet
```

Contiene 107,291 registros horarios entre 2020-01-01 y 2024-12-31. El cruce útil con el panel satelital es 2021-2024.

Hay 10 estaciones dentro del BBox:

| Estación | Operador | Rol |
|---|---|---|
| BASE AÉREA | DAGMA | SO2 y O3 |
| CAÑAVERALEJO | DAGMA | SO2 |
| COMPARTIR | DAGMA | O3 |
| ERA OBRERO | DAGMA | O3 |
| ESTACIÓN YUMBO | CVC | NO2, SO2 y O3 |
| LA ERMITA | DAGMA | SO2 |
| LA FLORA | DAGMA | SO2 y O3 |
| PANCE | DAGMA | O3 |
| TRANSITORIA-NAVARRO | DAGMA | SO2 y O3 |
| UNIVERSIDAD DEL VALLE | DAGMA | O3 |

El hallazgo más delicado es NO2: solo Yumbo tiene datos en la verdad observada principal. Eso no invalida Situación 1, pero sí limita la validación posterior de modelos para NO2.

![Cobertura temporal DAGMA/CVC](/docs/evidencias/situacion-3/dagma/figuras/dagma_cobertura_temporal.png)

## 12. Validaciones realizadas

La Situación 1 no solo descargó datos. También verificó que el panel tuviera sentido.

Validaciones principales:

- Conversión GeoTIFF → Zarr verificada como bit-perfect para fuentes clave.
- Manifest generado con tamaño, conteo de archivos y hashes MD5.
- Rangos físicos revisados para S5P, ERA5 y MODIS.
- MODIS corregido hasta obtener AOD físico.
- Evidencias visuales centralizadas en `docs/evidencias/`.
- Pesos y conteos reconciliados entre Kaggle y manifest.

Resumen del manifest:

| Campo | Valor |
|---|---:|
| Tamaño total | 89.732 GB |
| Archivos de datos | 8,847 |
| Fuentes | 7 |
| Umbral de 50 GB | Cumplido |

Nota importante: el manifest conserva en su campo global el BBox original del PDF. Para defensa y análisis se usa el BBox operativo del proyecto, confirmado por `google-earth/config.py` y por los bounds reales de las fuentes.

## 13. Qué queda claro al cerrar Situación 1

Situación 1 deja una base sólida para el resto del proyecto:

- El panel existe y está publicado.
- Los datos tienen trazabilidad.
- La cobertura satelital y temporal está documentada.
- Las limitaciones fuertes ya están identificadas.
- Kaggle puede consumir el panel para entrenamiento y análisis.

También deja riesgos que no se deben esconder:

- Sentinel-2 tiene mucha nubosidad útil baja.
- NO2 en estaciones solo existe para Yumbo.
- O3 de Sentinel-5P es columna total, no ozono superficial directo.
- MODIS AOD tiene cobertura baja por nubosidad tropical.
- El BBox del manifest global no coincide con el BBox operativo, aunque las fuentes sí cubren el área ampliada.

Mi lectura: Situación 1 cumple su objetivo. No resuelve todavía el modelado, pero entrega el activo más importante del proyecto: un panel multi-fuente verificable y reutilizable.

## 14. Archivos relacionados

- `docs/situacion-1/SIT1_PANEL.md`: resumen técnico de Situación 1.
- `docs/DATASETS.md`: catálogo de fuentes, bandas incluidas y bandas excluidas.
- `docs/JUSTIFICACIONES.md`: decisiones técnicas del proyecto.
- `docs/EDA_HALLAZGOS.md`: hallazgos exploratorios.
- `manifest/manifest_output/manifest.json`: manifest técnico del dataset.
- `google-earth/config.py`: BBox, fuentes y bandas útiles.
