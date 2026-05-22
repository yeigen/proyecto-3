# Contexto del proyecto

GeoVision-CLIP Cali estudia la contaminación atmosférica en Santiago de Cali y el corredor industrial Yumbo-Acopi usando datos satelitales, meteorología y estaciones de calidad del aire.

El proyecto parte de una idea simple: ningún dato por sí solo alcanza. Las estaciones miden bien, pero en pocos puntos. Los satélites cubren todo el territorio, pero muchas veces observan columnas atmosféricas o señales indirectas. La meteorología explica si una emisión se concentra, se transporta o se dispersa.

## Qué problema aborda

El área Cali + Yumbo + Acopi combina ciudad, industria, transporte pesado, zonas agrícolas y estaciones de monitoreo. Esa mezcla vuelve relevante estudiar contaminantes como NO2, SO2, O3 y aerosoles.

![Distribución global de aerosoles](imagenes/atmosfera/nasa_global_aerosol_distribution.jpg)

Fuente: [NASA image — global aerosol distribution](https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/content-feature/aerosols/images/aerosol_fine_fraction_depth_201008_hammer.jpg?w=720&h=424&fit=clip&crop=faces%2Cfocalpoint)

## Qué mide cada dataset

| Dataset | Qué mide | Cómo se usa en el proyecto | Cuidado de interpretación |
|---|---|---|---|
| Sentinel-2 MSI | Reflectancia óptica de superficie: ciudad, vegetación, suelo, agua, sombras y nubes | Base visual para tiles y CLIP | No mide contaminación directamente |
| Sentinel-5P NO2 | Columna de dióxido de nitrógeno, especialmente troposférica | Pseudo-label de contaminación NO2 | No equivale a concentración de calle |
| Sentinel-5P SO2 | Columna de dióxido de azufre | Pseudo-label SO2 y señal industrial/combustión | Señal ruidosa y esporádica |
| Sentinel-5P O3 | Columna total de ozono | Contexto atmosférico y clase `ozono_anomalo` | No es O3 superficial directo |
| MODIS MAIAC | AOD y vapor de agua | Proxy de aerosoles y contexto atmosférico | AOD no equivale a PM2.5/PM10 superficial |
| ERA5 | Temperatura, humedad, viento, precipitación, presión y altura de capa límite | Contexto de dispersión y mezcla atmosférica | Reanálisis, no estación local puntual |
| DAGMA/CVC | NO2, SO2 y O3 medidos en estaciones | Verdad observada principal para validación | Cobertura espacial limitada; NO2 solo en Yumbo |

## Cómo se conectan los datos

```text
Satélites + ERA5 + DAGMA/CVC
        ↓
Panel multi-fuente
        ↓
Tiles Sentinel-2 + textos
        ↓
CLIP + SAE
        ↓
ConvLSTM / Kriging / LOO-CV
```

## Por qué importan atmósfera y meteorología

Los contaminantes no se quedan quietos. El viento puede transportar emisiones desde Yumbo hacia Cali. La altura de capa límite cambia cuánto volumen de aire mezcla los contaminantes. La nubosidad afecta qué puede observar Sentinel-2, MODIS y Sentinel-5P.

![Efecto indirecto de aerosoles sobre nubes](imagenes/atmosfera/nasa_aerosol_indirect_effect_diagram.jpg)

Fuente: [NASA image — aerosol indirect effect diagram](https://assets.science.nasa.gov/dynamicimage/assets/science/esd/eo/content-feature/aerosols/images/indirect_effect_diagram.jpg?w=720&h=357&fit=clip&crop=faces%2Cfocalpoint)

## Ozono: cuidado especial

El ozono puede ser protector en la estratósfera y contaminante cerca del suelo. En este proyecto, Sentinel-5P aporta columna total de O3. Por eso la clase `ozono_anomalo` no se interpreta como medición directa de O3 superficial.

![Formación de ozono a nivel superficial](imagenes/contaminantes/epa_ozone_formation.jpg)

Fuente: [EPA image — ground-level ozone formation](https://www.epa.gov/sites/default/files/2018-10/ozone_formation.jpg)

## Mapa de lectura

- [El problema](problema.md)
- [Atmósfera y medición satelital](atmosfera.md)
- [Contaminantes](contaminantes.md)
- [Datos del proyecto](datos.md)
- [Modelo y validación](modelo.md)
- [Referencias](referencias.md)

## Relación con las situaciones

- [Situación 1](../situacion-1/README.md): construye y valida el panel multi-fuente.
- [Situación 2](../situacion-2/README.md): genera tiles y entrena CLIP + SAE.
- [Situación 3](../situacion-3/README.md): valida con DAGMA/CVC, ConvLSTM, Kriging y LOO-CV.
