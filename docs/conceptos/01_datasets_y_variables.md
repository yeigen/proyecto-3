# 01. Datasets y variables del proyecto

Este documento explica qué dataset usa el proyecto, qué variables trae cada uno y por qué esas variables tienen sentido para estimar contaminación en Cali.

La idea no es memorizar nombres raros de bandas. La idea es entender qué aporta cada fuente dentro de la historia completa.

## 1. Vista rápida

El proyecto mezcla cinco tipos de información:

| Tipo de información | Fuente | Qué aporta |
|---|---|---|
| Superficie visible/multiespectral | Sentinel-2 | Cómo se ve el territorio: ciudad, vegetación, suelo, agua, sombras. |
| Gases atmosféricos | Sentinel-5P | Columnas de NO₂, SO₂ y O₃. |
| Meteorología | ERA5 | Condiciones que dispersan o acumulan contaminación. |
| Aerosoles | MODIS MAIAC | AOD y vapor de agua como contexto de partículas/aerosoles. |
| Verdad observada | DAGMA/CVC | Mediciones reales en estaciones. |

La clave es esta:

> Sentinel-2 ayuda a entender el territorio, Sentinel-5P ayuda a entender gases desde satélite, ERA5 explica el clima que mueve esos gases, MODIS aporta aerosoles y DAGMA/CVC permite validar contra mediciones reales.

## 2. Resumen del panel usado

Según la documentación interna del proyecto, el panel publicado integra:

| Dataset | Shape Zarr aproximado | Periodo | Rol principal |
|---|---:|---|---|
| Sentinel-2 | `(1552, 13, 3897, 3897)` | 2021-2025 | Imágenes de alta resolución para tiles. |
| S5P NO₂ | `(25592, 3, 36, 36)` | 2020-2025 | Contexto/pseudo-label de dióxido de nitrógeno. |
| S5P SO₂ | `(25829, 2, 36, 36)` | 2020-2025 | Contexto/pseudo-label de dióxido de azufre. |
| S5P O₃ | `(25716, 2, 36, 36)` | 2020-2025 | Contexto/pseudo-label de ozono. |
| ERA5 | `(43824, 8, 2, 2)` | 2021-2025 | Meteorología horaria. |
| MODIS MAIAC | `(1826, 4, 43, 43)` | 2021-2025 | Aerosoles y vapor de agua diario. |
| DAGMA/CVC | 107,291 filas | 2020-2024 | Mediciones reales de estaciones. |

Importante: los satélites y ERA5 no “reemplazan” las estaciones. Las estaciones son el punto de comparación más directo para calidad del aire superficial.

## 3. Sentinel-2: la foto detallada del territorio

**Dataset en Earth Engine:** `COPERNICUS/S2_SR_HARMONIZED`
**Sensor:** MSI, MultiSpectral Instrument
**Tipo:** reflectancia de superficie
**Rol:** generar tiles visuales para CLIP y describir el contexto territorial.

Sentinel-2 no mide gases como NO₂, SO₂ u O₃. Lo que mide es cómo refleja la superficie en varias bandas del espectro. Esa información permite ver si un lugar parece vegetación, suelo urbano, agua, suelo descubierto, sombra o infraestructura.

### Variables usadas

| Banda | Resolución nativa | Qué ve | Por qué sirve |
|---|---:|---|---|
| `B1` | 60 m | Aerosoles/costa | Ayuda con contexto atmosférico y corrección. |
| `B2` | 10 m | Azul | Útil para RGB y dispersión atmosférica. |
| `B3` | 10 m | Verde | Vegetación y composición RGB. |
| `B4` | 10 m | Rojo | Vegetación, clorofila y cálculo de NDVI. |
| `B5` | 20 m | Red Edge 1 | Cambios finos en vegetación. |
| `B6` | 20 m | Red Edge 2 | Estrés vegetal. |
| `B7` | 20 m | Red Edge 3 | Continuidad del borde rojo vegetal. |
| `B8` | 10 m | Infrarrojo cercano, NIR | Vegetación sana; clave para NDVI. |
| `B8A` | 20 m | NIR estrecho | Vegetación con menos ruido de vapor de agua. |
| `B9` | 60 m | Vapor de agua | Contexto atmosférico. |
| `B11` | 20 m | SWIR 1 | Humedad de suelo, construcciones, sequedad. |
| `B12` | 20 m | SWIR 2 | Suelo, minerales, agua y zonas urbanas. |
| `SCL` | 20 m | Clasificación de escena | Identifica nubes, sombras, vegetación, agua, suelo. |

### Fórmula útil: NDVI

El NDVI es un índice simple para medir verdor o vigor vegetal:

$$
NDVI = \frac{NIR - Red}{NIR + Red}
$$

En Sentinel-2 normalmente:

$$
NDVI = \frac{B8 - B4}{B8 + B4}
$$

Interpretación chill:

| NDVI | Lectura rápida |
|---:|---|
| cercano a -1 | agua, sombras o superficies raras |
| cercano a 0 | suelo, concreto, zonas urbanas |
| alto, por ejemplo > 0.5 | vegetación densa |

En el proyecto ayuda a separar zonas como `vegetación_densa` y `suelo_urbano`.

## 4. Sentinel-5P: gases desde satélite

**Dataset:** `COPERNICUS/S5P/OFFL/L3_*`
**Sensor:** TROPOMI
**Tipo:** columnas atmosféricas
**Rol:** aportar señales de NO₂, SO₂ y O₃.

Sentinel-5P observa gases en la atmósfera. Pero ojo: mide columnas, no concentración directa a nivel respiración humana.

Una columna se reporta como:

$$
mol/m^2
$$

Eso significa “cantidad de sustancia integrada verticalmente sobre un metro cuadrado”.

### 4.1 NO₂: dióxido de nitrógeno

**Dataset:** `COPERNICUS/S5P/OFFL/L3_NO2`

| Variable | Unidad | Qué significa | Por qué se usa |
|---|---|---|---|
| `tropospheric_NO2_column_number_density` | `mol/m²` | Columna troposférica de NO₂ | Es la variable principal para contaminación urbana. |
| `NO2_column_number_density` | `mol/m²` | Columna total de NO₂ | Sirve como apoyo para entender cuánto NO₂ hay en toda la columna. |
| `cloud_fraction` | 0 a 1 | Fracción de nube | Ayuda a filtrar mediciones menos confiables. |

El NO2 suele asociarse con combustión: tráfico, camiones, buses, industria y quemas. En contexto urbano es muy importante.

### 4.2 SO₂: dióxido de azufre

**Dataset:** `COPERNICUS/S5P/OFFL/L3_SO2`

| Variable | Unidad | Qué significa | Por qué se usa |
|---|---|---|---|
| `SO2_column_number_density` | `mol/m²` | Columna vertical de SO₂ | Variable principal para azufre atmosférico. |
| `cloud_fraction` | 0 a 1 | Fracción de nube | Control de calidad. |

El SO₂ suele relacionarse con combustión de combustibles con azufre, procesos industriales y formación de aerosoles de sulfato.

### 4.3 O₃: ozono

**Dataset:** `COPERNICUS/S5P/OFFL/L3_O3`

| Variable | Unidad | Qué significa | Por qué se usa |
|---|---|---|---|
| `O3_column_number_density` | `mol/m²` | Columna total de ozono | Variable principal para ozono satelital. |
| `cloud_fraction` | 0 a 1 | Fracción de nube | Control de calidad. |

El ozono es especial: no se emite directamente como “humo de ozono”. Se forma por reacciones químicas entre otros contaminantes, con ayuda de la luz solar. Por eso puede aparecer alto en zonas distintas a la fuente original.

## 5. ERA5: la meteorología que mueve la contaminación

**Dataset en Earth Engine:** `ECMWF/ERA5/HOURLY`
**Tipo:** reanálisis meteorológico horario
**Rol:** explicar transporte, acumulación y dispersión.

ERA5 no mide contaminación. Mide variables del clima/atmósfera que ayudan a explicar por qué un contaminante se concentra o se dispersa.

### Variables usadas

| Variable | Unidad | Qué significa | Por qué sirve |
|---|---|---|---|
| `temperature_2m` | K | Temperatura a 2 metros | Afecta química atmosférica y mezcla del aire. |
| `dewpoint_temperature_2m` | K | Temperatura de punto de rocío | Ayuda a estimar humedad. |
| `u_component_of_wind_10m` | m/s | Viento este-oeste | Indica transporte horizontal. |
| `v_component_of_wind_10m` | m/s | Viento norte-sur | Indica transporte horizontal. |
| `boundary_layer_height` | m | Altura de capa límite | Clave: define cuánto aire hay disponible para diluir contaminantes. |
| `relative_humidity_850hPa` | % | Humedad relativa en altura | Relacionada con formación y crecimiento de aerosoles. |
| `surface_pressure` | Pa | Presión superficial | Útil para contexto físico y columnas atmosféricas. |
| `total_precipitation` | m | Precipitación acumulada | La lluvia puede remover contaminantes del aire. |

### Fórmula útil: velocidad del viento

ERA5 separa el viento en dos componentes: `u` y `v`. Para obtener la velocidad total:

$$
wind\_speed = \sqrt{u^2 + v^2}
$$

Donde:

- `u` indica viento este-oeste;
- `v` indica viento norte-sur.

Si el viento es fuerte, los contaminantes tienden a dispersarse más. Si el viento es débil, pueden acumularse.

### BLH explicado fácil

`boundary_layer_height` o BLH es la altura de la capa de aire cerca del suelo donde se mezclan contaminantes.

Si la BLH es baja, la contaminación queda atrapada en poco volumen de aire. Si la BLH es alta, hay más espacio para diluirla.

Una forma conceptual de verlo:

$$
concentracion \approx \frac{emisiones}{volumen\ de\ mezcla}
$$

No es una fórmula operacional exacta del modelo, pero sí ayuda a entender por qué BLH importa.

## 6. MODIS MAIAC: aerosoles y vapor de agua

**Dataset en Earth Engine:** `MODIS/061/MCD19A2_GRANULES`
**Sensor:** MODIS Terra/Aqua
**Tipo:** AOD y vapor de agua
**Rol:** contexto de aerosoles, no verdad directa de PM2.5/PM10.

MODIS MAIAC aporta AOD, que significa **Aerosol Optical Depth** o profundidad óptica de aerosoles.

AOD no dice directamente cuántos microgramos de PM2.5 hay al nivel de la calle. Más bien indica cuánta luz bloquean o dispersan los aerosoles en la columna atmosférica.

### Variables usadas

| Variable | Unidad/escala | Qué significa | Por qué sirve |
|---|---|---|---|
| `Optical_Depth_047` | escala 0.001 | AOD a 0.47 µm | Señal de aerosoles en longitud de onda azul. |
| `Optical_Depth_055` | escala 0.001 | AOD a 0.55 µm | Señal de aerosoles en longitud de onda verde. |
| `Column_WV` | escala 0.001 | Columna de vapor de agua | Humedad atmosférica, afecta aerosoles. |
| `AOD_QA` | bitfield | Calidad del pixel | Permite filtrar datos malos. |

Si el valor crudo viene escalado, se interpreta así:

$$
AOD_{real} = AOD_{raw} \times 0.001
$$

Esta escala es importante. Si se olvida, los valores quedan mil veces más grandes de lo esperado.

## 7. DAGMA/CVC: la verdad observada

**Fuente:** estaciones de calidad del aire DAGMA/CVC vía SISAIRE/datos abiertos
**Tipo:** mediciones puntuales horarias
**Rol:** validación real del proyecto.

Las estaciones miden contaminantes cerca de superficie, justo donde respira la gente. Por eso son la referencia principal para validar.

### Variables principales

| Variable | Unidad esperada | Qué significa | Uso |
|---|---|---|---|
| NO₂ | `µg/m³` | Dióxido de nitrógeno en aire superficial | Validación, aunque en el parquet principal solo aparece en Yumbo. |
| SO₂ | `µg/m³` | Dióxido de azufre en aire superficial | Validación espacial en varias estaciones. |
| O₃ | `µg/m³` | Ozono superficial | Validación espacial en varias estaciones. |
| fecha/hora | fecha | Momento de medición | Cruce temporal. |
| estación | texto/coordenadas | Lugar de medición | Cruce espacial. |

### Columnas reales del parquet DAGMA/CVC

Archivo revisado:

```text
dagma/dagma_cvc_horario_raw.parquet
```

El archivo tiene **107,291 filas** y **14 columnas**:

| Columna | Tipo | Qué contiene | Cómo se interpreta en el proyecto |
|---|---|---|---|
| `estacion_id` | texto | Código de la estación | Identificador interno para agrupar mediciones por estación. |
| `nombre_est` | texto | Nombre de la estación | Ejemplo: `BASE AÉREA`, `ESTACIÓN YUMBO`, `PANCE`. |
| `nombre_fgda` | texto | Entidad/fuente operadora | Indica si viene de DAGMA o CVC. |
| `msfl_code` | texto | Código del contaminante | Valores como `NO2`, `SO2` u `O3`. Es la columna que dice qué gas se midió. |
| `med_concentracion_estandar` | número decimal | Concentración medida | Valor principal de contaminación en estación. |
| `med_fecha_inicio` | fecha-hora | Inicio del intervalo de medición | Marca cuándo empieza la hora medida. |
| `med_fecha_final` | fecha-hora | Final del intervalo de medición | Marca cuándo termina la hora medida. |
| `nombre_unidad` | texto | Nombre largo de la unidad | Ejemplo: `Microgramos por metro cúbico`. |
| `sigla_unidad` | texto | Sigla de la unidad | En el parquet aparece como `ug/m3`, equivalente práctico a `µg/m³`. |
| `latitud` | número decimal | Latitud de la estación | Coordenada para ubicar la estación en el mapa. |
| `longitud` | número decimal | Longitud de la estación | Coordenada para cruce espacial con satélites/modelos. |
| `altitud` | número entero | Altura de la estación | Altura aproximada sobre el nivel del mar, en metros. |
| `municipio` | texto | Municipio de la estación | En este panel aparece Santiago de Cali/Yumbo según estación. |
| `departamento` | texto | Departamento | Valle del Cauca. |

La columna más importante para modelar es:

```text
med_concentracion_estandar
```

Pero esa concentración solo tiene sentido si se lee junto con:

```text
msfl_code + sigla_unidad + med_fecha_inicio + latitud + longitud
```

En otras palabras: necesitamos saber **qué contaminante**, **en qué unidad**, **cuándo** y **dónde** fue medido.

La unidad `µg/m³` significa:

$$
\mu g/m^3 = \frac{microgramos\ de\ contaminante}{metro^3\ de\ aire}
$$

Esta unidad sí representa concentración cerca del suelo. Por eso no se debe mezclar sin cuidado con `mol/m²` de Sentinel-5P.

## 8. Cómo se conectan todos los datasets

Una forma simple de entender el flujo:

```text
Sentinel-2       → cómo se ve el lugar
Sentinel-5P      → qué señales de gases hay sobre la zona
ERA5             → cómo se mueve/mezcla la atmósfera
MODIS            → qué señal de aerosoles hay
DAGMA/CVC        → qué se midió realmente en estaciones
        ↓
Modelo + estadística
        ↓
Estimación de contaminación en puntos sin estación
```

El proyecto necesita todas esas piezas porque la contaminación no depende de una sola cosa. Depende de emisiones, superficie urbana, meteorología, química atmosférica y ubicación.

## 9. Variables por rol dentro del proyecto

| Rol | Variables/datasets |
|---|---|
| Imagen para CLIP | Bandas Sentinel-2 seleccionadas (`B1`, `B2`, `B3`, `B4`, `B5`, `B6`, `B7`, `B8`, `B8A`, `B9`, `B11`, `B12`) + `SCL` |
| Pseudo-labels de contaminación | Columnas Sentinel-5P de NO₂, SO₂ y O₃ |
| Calidad/filtro satelital | `cloud_fraction`, `SCL`, `AOD_QA` |
| Contexto meteorológico | Temperatura, viento, BLH, humedad, presión, lluvia |
| Aerosoles/proxy PM | `Optical_Depth_047`, `Optical_Depth_055` |
| Validación real | NO₂, SO₂ y O₃ medidos por DAGMA/CVC |

## 10. Auditoría conceptual rápida

Puntos que están bien planteados:

- Usar Sentinel-2 para contexto espacial fino.
- Usar Sentinel-5P como señal atmosférica de gases.
- Usar ERA5 porque la contaminación depende mucho del clima.
- Usar DAGMA/CVC para validar con mediciones reales.
- Guardar en Zarr porque el panel es grande y multidimensional.

Puntos que hay que cuidar:

- No confundir `mol/m²` satelital con `µg/m³` de estación.
- No usar Sentinel-5P como input directo si eso causa fuga de información en la predicción.
- No vender AOD como PM2.5 directo; es solo proxy.
- No decir que hay buena validación espacial de NO₂ si solo hay una estación con NO₂ en el parquet principal.
- No ignorar nubosidad: afecta Sentinel-2, Sentinel-5P y MODIS.

## 11. Referencias y documentación

### Internas

- [Datasets del proyecto](../DATASETS.md)
- [Datos del proyecto](../contexto/datos.md)
- [Sentinel-2 en Situación 1](../situacion-1/fuentes/sentinel-2.md)
- [Sentinel-5P en Situación 1](../situacion-1/fuentes/sentinel-5p.md)
- [ERA5 en Situación 1](../situacion-1/fuentes/era5.md)
- [MODIS MAIAC en Situación 1](../situacion-1/fuentes/modis-maiac.md)
- [DAGMA/CVC en Situación 1](../situacion-1/fuentes/dagma-cvc.md)

### Externas

- [Earth Engine — Sentinel-2 SR Harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Earth Engine — Sentinel-5P NO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Earth Engine — Sentinel-5P SO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Earth Engine — Sentinel-5P O₃](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [Earth Engine — ERA5 Hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY)
- [Earth Engine — MODIS MAIAC MCD19A2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [LP DAAC — MCD19A2 v061](https://lpdaac.usgs.gov/products/mcd19a2v061/)
- [ECMWF — ERA5 documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [IDEAM SISAIRE](http://sisaire.ideam.gov.co/ideam-sisaire-web/)
- [DAGMA Cali](https://www.cali.gov.co/dagma/)

### Nota de auditoría

La revisión con Context7 confirmó las unidades principales del catálogo Earth Engine para Sentinel-5P: NO₂, SO₂ y O₃ aparecen como columnas en `mol/m²`, y `cloud_fraction` como fracción. También confirmó que las bandas ópticas de Sentinel-2 se manejan con escala de reflectancia y resoluciones nativas distintas. Para MODIS MAIAC, se mantiene la advertencia de escala `0.001`, ya documentada internamente en el proyecto.
