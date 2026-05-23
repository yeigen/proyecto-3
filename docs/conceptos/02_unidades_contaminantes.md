# 02. Unidades de contaminantes y variables del proyecto

Este documento explica cómo se miden las variables principales del proyecto. La idea es separar bien tres mundos que a veces se mezclan por error:

1. **Estaciones terrestres**: concentración cerca del suelo, normalmente `µg/m³`.
2. **Satélites atmosféricos**: columnas verticales, normalmente `mol/m²`.
3. **Meteorología y superficie**: temperatura, viento, presión, lluvia, reflectancia, AOD, etc.

La regla de oro:

> No todas las unidades representan lo mismo. Un valor satelital en `mol/m²` no se compara directo con una estación en `µg/m³`.

## 1. Tabla rápida de unidades

| Variable | Fuente | Unidad principal | Qué significa |
|---|---|---|---|
| NO₂ estación | DAGMA/CVC | `µg/m³` | Microgramos de NO₂ por metro cúbico de aire cerca del suelo. |
| SO₂ estación | DAGMA/CVC | `µg/m³` | Microgramos de SO₂ por metro cúbico de aire cerca del suelo. |
| O₃ estación | DAGMA/CVC | `µg/m³` | Microgramos de O₃ por metro cúbico de aire cerca del suelo. |
| NO₂ satelital | Sentinel-5P | `mol/m²` | Moles de NO₂ integrados en una columna atmosférica. |
| SO₂ satelital | Sentinel-5P | `mol/m²` | Moles de SO₂ integrados en una columna atmosférica. |
| O₃ satelital | Sentinel-5P | `mol/m²` | Moles de O₃ en columna total atmosférica. |
| AOD | MODIS MAIAC | adimensional | Qué tanto los aerosoles bloquean/dispersan luz. |
| Temperatura | ERA5 | `K` | Kelvin. Para Celsius se resta 273.15. |
| Viento | ERA5 | `m/s` | Metros por segundo. |
| Presión | ERA5 | `Pa` | Pascales. |
| Precipitación | ERA5 | `m` | Metros de agua acumulada. |
| BLH | ERA5 | `m` | Altura de la capa límite atmosférica. |
| Reflectancia | Sentinel-2 | escala de reflectancia | Fracción de luz reflejada por la superficie. |

## 2. Qué significa `µg/m³`

La unidad `µg/m³` se lee como:

$$
\mu g/m^3 = \frac{microgramos\ de\ contaminante}{metro^3\ de\ aire}
$$

Es una concentración de masa por volumen. Es la forma más común de reportar contaminación cerca del suelo.

Ejemplo simple:

```text
O3 = 80 µg/m³
```

Significa que en cada metro cúbico de aire hay aproximadamente 80 microgramos de ozono.

En el proyecto, esta es la unidad más importante para DAGMA/CVC porque representa lo que realmente se mide cerca de donde vive y respira la gente.

## 3. Qué significa `mol/m²`

La unidad `mol/m²` se lee como:

$$
mol/m^2 = \frac{moles\ de\ gas}{metro^2\ de\ superficie}
$$

No es una concentración superficial. Es una **columna**.

Imagina un tubo invisible de 1 metro cuadrado de base que sube desde el suelo hasta la atmósfera. Sentinel-5P estima cuánto gas hay dentro de esa columna.

Por eso:

```text
Sentinel-5P NO2 = 0.00015 mol/m²
```

no significa que el aire al nivel de la calle tenga `0.00015 mol/m³`. Significa que, sumando verticalmente la atmósfera sobre ese punto, hay esa cantidad por metro cuadrado.

### Conversión cómoda: mol a micromol

Para NO₂ y SO₂, los valores suelen ser pequeños. Por eso a veces se expresan en micromoles por metro cuadrado (`umol/m²` o `µmol/m²`):

$$
1\ mol = 1{,}000{,}000\ \mu mol
$$

Entonces:

$$
0.00015\ mol/m^2 = 150\ \mu mol/m^2
$$

## 4. Por qué `mol/m²` y `µg/m³` no son lo mismo

La diferencia es esta:

| Unidad | Mira | Pregunta que responde |
|---|---|---|
| `µg/m³` | aire cerca del suelo | ¿Cuánta masa de contaminante hay en el aire que se respira? |
| `mol/m²` | columna vertical | ¿Cuánta cantidad total de gas hay encima de un área? |

Para convertir una columna satelital a concentración superficial se necesitarían supuestos sobre cómo está distribuido el gas verticalmente.

Una aproximación conceptual es:

$$
C_{superficie} \approx \frac{Columna \cdot M \cdot 10^6}{BLH}
$$

Donde:

| Símbolo | Significado |
|---|---|
| `Columna` | valor satelital en `mol/m²` |
| `M` | masa molar del gas en `g/mol` |
| `10^6` | conversión de gramos a microgramos |
| `BLH` | altura de capa límite en metros |
| `C_superficie` | concentración aproximada en `µg/m³` |

Esta fórmula sirve para entender la física, pero no debe venderse como conversión exacta. La atmósfera real no está perfectamente mezclada.

## 5. Masas molares de los contaminantes

La masa molar dice cuántos gramos pesa un mol de una sustancia.

| Contaminante | Fórmula | Masa molar aproximada |
|---|---|---:|
| Dióxido de nitrógeno | NO₂ | 46.01 g/mol |
| Dióxido de azufre | SO₂ | 64.07 g/mol |
| Ozono | O₃ | 48.00 g/mol |

Estas masas aparecen cuando queremos pasar de cantidad de sustancia (`mol`) a masa (`g` o `µg`).

## 6. NO₂: cómo se mide en el proyecto

### En estaciones

DAGMA/CVC reporta NO₂ como concentración superficial:

$$
NO_2\ [\mu g/m^3]
$$

En el parquet del proyecto, el contaminante aparece en:

```text
msfl_code = NO2
```

y el valor está en:

```text
med_concentracion_estandar
```

### En Sentinel-5P

Sentinel-5P entrega principalmente:

```text
tropospheric_NO2_column_number_density
```

con unidad:

$$
mol/m^2
$$

La palabra **tropospheric** importa porque la troposfera es la capa baja de la atmósfera, donde ocurre la calidad del aire urbana.

Lectura práctica:

- estaciones: “cuánto NO₂ hay donde respiramos”;
- satélite: “cuánto NO₂ hay integrado en la columna troposférica”.

## 7. SO₂: cómo se mide en el proyecto

### En estaciones

DAGMA/CVC reporta SO₂ como:

$$
SO_2\ [\mu g/m^3]
$$

En el parquet:

```text
msfl_code = SO2
```

### En Sentinel-5P

Sentinel-5P usa:

```text
SO2_column_number_density
```

con unidad:

$$
mol/m^2
$$

El SO₂ satelital puede ser más ruidoso en contexto urbano porque las columnas suelen ser bajas. Por eso conviene revisar `cloud_fraction` y promedios temporales.

## 8. O₃: cómo se mide en el proyecto

### En estaciones

DAGMA/CVC mide ozono superficial:

$$
O_3\ [\mu g/m^3]
$$

En el parquet:

```text
msfl_code = O3
```

Este ozono es el que importa para salud pública: el ozono que está en el aire cerca del suelo.

### En Sentinel-5P

Sentinel-5P entrega:

```text
O3_column_number_density
```

con unidad:

$$
mol/m^2
$$

Pero aquí hay un detalle importante: Sentinel-5P reporta **columna total de ozono**, no solo ozono superficial.

Eso incluye mucho ozono estratosférico, que es el ozono “bueno” de la capa de ozono. Por eso O₃ es más difícil de usar que NO₂ para estimar calidad del aire urbana.

## 9. Dobson Unit: unidad clásica del ozono

El ozono total a veces se reporta en **Dobson Units** o `DU`.

La equivalencia es:

$$
1\ DU \approx 2.687 \times 10^{20}\ moleculas/m^2
$$

En moles:

$$
1\ DU \approx 4.46 \times 10^{-4}\ mol/m^2
$$

Entonces, para convertir ozono de `mol/m²` a Dobson Units:

$$
DU \approx \frac{O_3\ [mol/m^2]}{4.46 \times 10^{-4}}
$$

Ejemplo:

$$
0.115\ mol/m^2 \approx \frac{0.115}{4.46 \times 10^{-4}} \approx 258\ DU
$$

Eso es un valor razonable para ozono total atmosférico.

## 10. ppb vs µg/m³

A veces los contaminantes gaseosos se reportan en `ppb`, partes por billón. Esa unidad habla de proporción molecular, no masa.

Para convertir de `ppb` a `µg/m³`, se usa una aproximación a 25 °C y 1 atm:

$$
\mu g/m^3 \approx ppb \cdot \frac{M}{24.45}
$$

Donde `M` es la masa molar en `g/mol`.

### Factores aproximados

| Gas | Masa molar | Conversión aproximada |
|---|---:|---:|
| NO₂ | 46.01 g/mol | 1 ppb ≈ 1.88 µg/m³ |
| SO₂ | 64.07 g/mol | 1 ppb ≈ 2.62 µg/m³ |
| O₃ | 48.00 g/mol | 1 ppb ≈ 1.96 µg/m³ |

La fórmula más general, considerando presión y temperatura, es:

$$
\mu g/m^3 = ppb \cdot M \cdot \frac{P}{R \cdot T} \cdot 10^{-3}
$$

Donde:

| Símbolo | Unidad | Significado |
|---|---|---|
| `ppb` | partes por billón | mezcla volumétrica |
| `M` | g/mol | masa molar del gas |
| `P` | Pa | presión atmosférica |
| `R` | J/(mol·K) | constante de gases ideales, 8.314 |
| `T` | K | temperatura absoluta |

En Cali, como está cerca de 1000 m de altitud, la presión suele ser menor que a nivel del mar. Eso puede cambiar un poco la conversión real.

## 11. AOD: no es concentración, es opacidad

AOD significa **Aerosol Optical Depth**.

No tiene unidad física como `µg/m³`; es adimensional. Mide qué tanto los aerosoles en la columna atmosférica reducen la luz.

Una forma sencilla de verlo es con la ley de Beer-Lambert:

$$
I = I_0 \cdot e^{-\tau m}
$$

Donde:

| Símbolo | Significado |
|---|---|
| `I_0` | luz que entraría sin aerosoles |
| `I` | luz que llega al sensor |
| `\tau` | AOD |
| `m` | masa de aire, relacionada con el ángulo solar |

Si AOD sube, la atmósfera está más cargada de partículas o aerosoles. Pero no se puede decir automáticamente “AOD = PM2.5”. Para eso se necesita calibración local con estaciones.

### Escala MODIS MAIAC

En el producto MODIS MAIAC, las bandas de AOD usan escala `0.001`:

$$
AOD_{real} = AOD_{raw} \times 0.001
$$

Ejemplo:

```text
AOD_raw = 250
AOD_real = 250 × 0.001 = 0.25
```

## 12. Temperatura: Kelvin y Celsius

ERA5 entrega temperatura en Kelvin (`K`). Para convertir a Celsius:

$$
T_{°C} = T_K - 273.15
$$

Ejemplo:

$$
300.15\ K = 27\ °C
$$

En el proyecto aparece en:

- `temperature_2m`
- `dewpoint_temperature_2m`

## 13. Viento: componentes u y v

ERA5 no entrega solo “velocidad del viento”. Entrega dos componentes:

| Variable | Unidad | Significado |
|---|---|---|
| `u_component_of_wind_10m` | `m/s` | componente este-oeste |
| `v_component_of_wind_10m` | `m/s` | componente norte-sur |

La velocidad se calcula así:

$$
wind\_speed = \sqrt{u^2 + v^2}
$$

Ejemplo:

$$
u=3,\ v=4 \Rightarrow wind\_speed=5\ m/s
$$

## 14. Presión, lluvia y BLH

| Variable | Unidad | Qué significa | Conversión útil |
|---|---|---|---|
| `surface_pressure` | `Pa` | presión superficial | 100,000 Pa ≈ 1000 hPa |
| `total_precipitation` | `m` | agua acumulada | 0.005 m = 5 mm |
| `boundary_layer_height` | `m` | altura de mezcla atmosférica | no requiere conversión |

La BLH es clave porque ayuda a entender dilución vertical:

- BLH baja: menos volumen de aire, más acumulación.
- BLH alta: más volumen de aire, más dilución.

## 15. Sentinel-2: reflectancia y escala

Sentinel-2 trabaja con reflectancia. Conceptualmente, reflectancia es:

$$
Reflectancia = \frac{luz\ reflejada}{luz\ incidente}
$$

Por eso suele estar entre 0 y 1 cuando ya está escalada.

En muchos productos de Earth Engine, las bandas ópticas se almacenan con un factor de escala. Para Sentinel-2, la documentación del catálogo indica escala `0.0001` en bandas ópticas. Eso significa:

$$
Reflectancia_{real} = valor_{raw} \times 0.0001
$$

Ejemplo:

```text
B4_raw = 2500
B4_real = 2500 × 0.0001 = 0.25
```

## 16. Ejemplo completo con datos del proyecto

Este ejemplo sirve para explicar el flujo en una exposición. Usa registros reales del parquet DAGMA/CVC y los conecta con las unidades de las demás fuentes.

### Paso 1: partir de una medición real en estación

Archivo usado:

```text
dagma/dagma_cvc_horario_raw.parquet
```

Tres ejemplos reales del parquet:

| Contaminante | Estación | Operador | Fecha inicio | Valor | Unidad | Lat | Lon |
|---|---|---|---|---:|---|---:|---:|
| NO₂ | ESTACIÓN YUMBO | CVC | 2020-11-01 00:00 | 10.76 | `ug/m3` | 3.579075 | -76.489558 |
| O₃ | COMPARTIR | DAGMA | 2020-01-01 00:00 | 10.06 | `ug/m3` | 3.428260 | -76.466584 |
| SO₂ | LA ERMITA | DAGMA | 2020-01-01 00:00 | 2.62 | `ug/m3` | 3.455514 | -76.530978 |

La lectura correcta para el primer caso sería:

> En la estación Yumbo, entre las 00:00 y 01:00 del 1 de noviembre de 2020, se midieron **10.76 µg/m³ de NO₂** cerca de superficie.

Eso viene de estas columnas:

```text
msfl_code = NO2
med_concentracion_estandar = 10.76
sigla_unidad = ug/m3
med_fecha_inicio = 2020-11-01 00:00:00
latitud = 3.579075
longitud = -76.489558
```

### Paso 2: ubicar esa medición en espacio y tiempo

Con `latitud`, `longitud` y `med_fecha_inicio`, el proyecto puede buscar información cercana en las otras fuentes:

| Fuente | Qué buscaríamos cerca de esa estación y fecha | Unidad |
|---|---|---|
| Sentinel-2 | tile visual de la zona de Yumbo | reflectancia escalada |
| Sentinel-5P NO₂ | columna troposférica de NO₂ sobre el píxel cercano | `mol/m²` |
| ERA5 | temperatura, viento, presión, BLH, lluvia | `K`, `m/s`, `Pa`, `m` |
| MODIS MAIAC | AOD y vapor de agua del día | adimensional / escala `0.001` |

La estación dice “qué pasó en el suelo”. Las otras fuentes ayudan a explicar el contexto.

### Paso 3: traducir la diferencia de unidades

Supongamos que, para una fecha comparable, Sentinel-5P entrega una columna de NO₂ como:

$$
Columna_{NO_2} = 1.5 \times 10^{-4}\ mol/m^2
$$

Eso equivale a:

$$
1.5 \times 10^{-4}\ mol/m^2 = 150\ \mu mol/m^2
$$

Si además ERA5 indica una capa límite:

$$
BLH = 1000\ m
$$

una conversión conceptual sería:

$$
C_{superficie} \approx \frac{Columna \cdot M_{NO_2} \cdot 10^6}{BLH}
$$

Sustituyendo:

$$
C_{superficie} \approx \frac{1.5 \times 10^{-4} \cdot 46.01 \cdot 10^6}{1000}
$$

$$
C_{superficie} \approx 6.90\ \mu g/m^3
$$

Comparado con la estación Yumbo:

```text
DAGMA/CVC observado = 10.76 µg/m³
Aproximación desde columna + BLH = 6.90 µg/m³
```

La diferencia sería:

$$
error = y - \hat{y} = 10.76 - 6.90 = 3.86\ \mu g/m^3
$$

Donde:

| Símbolo | Significado |
|---|---|
| `y` | valor observado por la estación |
| `\hat{y}` | valor estimado por el modelo o aproximación |
| `error` | diferencia entre observado y estimado |

Importante: este cálculo es didáctico. En el proyecto real no basta con dividir por BLH, porque la atmósfera no está perfectamente mezclada y Sentinel-5P no ve exactamente lo mismo que una estación de superficie.

### Paso 4: meter meteorología

Supongamos que ERA5 trae:

| Variable ERA5 | Valor ejemplo | Interpretación |
|---|---:|---|
| `temperature_2m` | 295.15 K | 22 °C |
| `u_component_of_wind_10m` | 3 m/s | viento hacia el este |
| `v_component_of_wind_10m` | 4 m/s | viento hacia el norte |
| `boundary_layer_height` | 1000 m | capa de mezcla moderada |
| `total_precipitation` | 0 m | sin lluvia |

La velocidad del viento sería:

$$
wind\_speed = \sqrt{3^2 + 4^2} = 5\ m/s
$$

Lectura ambiental:

- si hay viento de 5 m/s, la pluma puede transportarse y dispersarse;
- si no hay lluvia, no hay lavado húmedo importante;
- si BLH es 1000 m, hay una mezcla moderada: ni muy atrapada ni muy diluida.

### Paso 5: meter AOD si existe MODIS válido

Supongamos que MODIS MAIAC trae:

```text
Optical_Depth_047_raw = 250
```

Como la escala es `0.001`:

$$
AOD_{real} = 250 \times 0.001 = 0.25
$$

Lectura:

> AOD = 0.25 sugiere una carga moderada de aerosoles en la columna atmosférica.

Pero no significa automáticamente “PM2.5 = 0.25”. Para PM haría falta calibración local.

### Paso 6: explicar el flujo completo en una frase

Con el ejemplo de Yumbo:

```text
Estación CVC mide NO₂ superficial en µg/m³
        ↓
Usamos lat/lon/fecha para buscar satélite y meteorología cercana
        ↓
Sentinel-5P aporta columna NO₂ en mol/m²
        ↓
ERA5 aporta BLH, viento, temperatura, presión y lluvia
        ↓
MODIS aporta AOD como contexto de aerosoles
        ↓
Sentinel-2 aporta imagen fina del territorio
        ↓
El modelo intenta estimar NO₂ en puntos sin estación
        ↓
Se valida comparando estimado vs observado en DAGMA/CVC
```

### Paso 7: cómo se explicaría oralmente

Una forma simple de decirlo:

> “La estación me da la verdad local: por ejemplo, Yumbo midió 10.76 µg/m³ de NO₂. El satélite no mide eso mismo: Sentinel-5P ve una columna en mol/m². Entonces usamos meteorología, especialmente la altura de capa límite, para entender cuánto de esa columna podría estar cerca del suelo. Además usamos Sentinel-2 para entender si el punto está en zona urbana, industrial o vegetal, y MODIS para ver aerosoles. El modelo aprende a combinar todo eso y luego se valida contra estaciones reales.”

## 17. Errores comunes que debemos evitar

| Error | Por qué está mal |
|---|---|
| Comparar `mol/m²` con `µg/m³` directamente | Una es columna satelital; la otra es concentración superficial. |
| Decir que AOD es PM2.5 | AOD es proxy óptico; PM2.5 requiere calibración. |
| Tratar O₃ satelital como O₃ superficial | Sentinel-5P reporta columna total, dominada por ozono estratosférico. |
| Olvidar escalas de MODIS/Sentinel-2 | Puede inflar valores por 1000 o 10000. |
| Ignorar temperatura y presión en conversiones ppb ↔ µg/m³ | La conversión depende de condiciones atmosféricas. |
| Olvidar BLH | La misma columna puede dar concentraciones superficiales distintas según la altura de mezcla. |

## 18. Cómo leer las unidades en el proyecto sin perderse

Una guía rápida:

```text
Si viene de DAGMA/CVC  → probablemente µg/m³
Si viene de Sentinel-5P → probablemente mol/m²
Si viene de MODIS AOD   → adimensional con escala 0.001
Si viene de ERA5 T      → Kelvin
Si viene de ERA5 viento → m/s
Si viene de ERA5 presión→ Pa
Si viene de ERA5 lluvia → m
Si viene de Sentinel-2  → reflectancia escalada
```

## 19. Referencias y documentación

### Internas

- [Datasets y variables del proyecto](01_datasets_y_variables.md)
- [NO₂](contaminante-no2.md)
- [SO₂](contaminante-so2.md)
- [O₃](contaminante-o3.md)
- [Material particulado y AOD](material-particulado-aod.md)
- [Columnas troposféricas y DOAS](columnas-troposfericas-doas.md)
- [Meteorología que mueve contaminantes](humedad-temperatura-viento.md)
- [Capa límite BLH](capa-limite-blh.md)

### Externas

- [Earth Engine — Sentinel-5P NO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Earth Engine — Sentinel-5P SO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Earth Engine — Sentinel-5P O₃](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [Earth Engine — Sentinel-2 SR Harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Earth Engine — MODIS MAIAC MCD19A2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [Earth Engine — ERA5 Hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY)
- [WHO — Global Air Quality Guidelines 2021](https://www.who.int/publications/i/item/9789240034228)
- [Resolución 2254 de 2017 — MinAmbiente Colombia](https://www.minambiente.gov.co/documento-entidad/resolucion-2254-de-2017/)
- [NASA Earthdata](https://www.earthdata.nasa.gov/)
- [ECMWF ERA5 documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)

### Nota de auditoría

La revisión de documentación del catálogo Earth Engine mediante Context7 confirmó que Sentinel-5P reporta las bandas principales de NO₂, SO₂ y O₃ en `mol/m²`, y `cloud_fraction` como fracción. También confirmó que Sentinel-2 usa bandas ópticas con escala de reflectancia. La escala `0.001` de MODIS MAIAC ya estaba documentada en los archivos internos del proyecto y se mantiene como advertencia importante.
