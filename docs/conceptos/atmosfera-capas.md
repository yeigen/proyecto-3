# La atmósfera y sus capas

## La analogía rápida

Imagina la atmósfera como una **cebolla de aire** alrededor de la Tierra: capas concéntricas, cada una con su densidad y temperatura. El 99 % del aire (y de la contaminación) vive en los **primeros 30 km**, y casi todo lo que respiramos en los **primeros 2-3 km**.

## Las 5 capas (de abajo hacia arriba)

| Capa | Altura | Qué hay ahí | Relevancia para el proyecto |
|---|---|---|---|
| **Troposfera** | 0 – 12 km | Aire que respiramos, nubes, clima | **Aquí vive el NO₂ y SO₂ que medimos.** Aquí también está el O₃ "malo". |
| **Estratosfera** | 12 – 50 km | Capa de ozono "buena" (filtra UV) | Sentinel-5P mide la **columna total** de O₃, incluyendo este. |
| **Mesosfera** | 50 – 85 km | Donde se queman los meteoritos | Irrelevante. |
| **Termosfera** | 85 – 600 km | Auroras, ISS | Irrelevante. |
| **Exosfera** | > 600 km | Transición al espacio | Irrelevante. |

```
   600+ km  ┄┄┄┄┄┄┄┄┄ EXOSFERA ┄┄┄┄┄┄┄┄┄
            
    85 km   ━━━━━━━━━ TERMOSFERA ━━━━━━━━━
            
    50 km   ─────────  MESOSFERA  ─────────
            
                     O₃ "bueno" (capa de ozono)
    12 km   ━━━━━━━━━ ESTRATOSFERA ━━━━━━━━━
            
                     ← BLH típico día (2 km)
     2 km   ┄┄┄┄┄┄┄┄ (capa límite) ┄┄┄┄┄┄┄┄
            
                     NO₂, SO₂, O₃ "malo", PM, vapor, lluvia
     0 km   ═════════ SUELO (Cali, 1000 msnm) ═════════
```

## Por qué nos importan solo los primeros 2-3 km

La **capa límite planetaria** (PBL o BLH = *Boundary Layer Height*) es la parte de la troposfera que está en contacto directo con el suelo y se "mezcla" verticalmente por turbulencia.

- **De día**: el sol calienta el suelo → aire caliente sube → BLH crece hasta ~1500–2500 m. Los contaminantes se diluyen en una caja grande.
- **De noche**: el suelo se enfría → no hay mezcla vertical → BLH cae a 100–500 m. Los contaminantes se concentran en una caja pequeña → **picos de contaminación nocturna**.

Por eso ERA5 nos da `boundary_layer_height` como banda obligatoria del proyecto: **sin BLH no puedes interpretar columnas de NO₂**. Una columna alta de día con BLH=2000 m es poca concentración en superficie; la misma columna de noche con BLH=300 m es muchísima concentración respirada.

Más detalle en [`capa-limite-blh.md`](capa-limite-blh.md).

## Composición de la atmósfera (aire seco)

| Gas | % en volumen | Comentario |
|---|---:|---|
| Nitrógeno (N₂) | 78.08 % | Inerte, no contamina |
| Oxígeno (O₂) | 20.95 % | Respiramos esto |
| Argón (Ar) | 0.93 % | Inerte |
| CO₂ | ~0.042 % | 420 ppm en 2026, gas de efecto invernadero |
| **NO₂, SO₂, O₃** | **trazas (ppb-ppm)** | **Los que mide este proyecto** |

"Trazas" significa **partes por mil millones** (ppb): el NO₂ urbano típico de Cali está entre 5 y 50 ppb, eso es 1 molécula de NO₂ por cada 20 millones de moléculas de aire. Aún así daña los pulmones.

## Cali en particular

Santiago de Cali está a **~1000 m sobre el nivel del mar**, en un valle interandino entre la Cordillera Occidental y la Central. Esto tiene consecuencias:

- El valle **atrapa aire** en condiciones de inversión térmica nocturna → contaminación se acumula.
- La altitud reduce la presión atmosférica (~900 hPa vs 1013 hPa al nivel del mar) → los modelos de columna a concentración necesitan corregir por presión (`surface_pressure` del ERA5).
- Los vientos alisios del oeste (Pacífico) y la sombra orográfica afectan la dispersión: por eso ERA5 nos entrega `u_component_of_wind_10m` y `v_component_of_wind_10m`.

## Lecturas

- [NOAA — Layers of the Atmosphere](https://scied.ucar.edu/learning-zone/atmosphere/layers-earths-atmosphere) — introducción visual a las capas.
- [NASA Earth Observatory — The Atmosphere](https://earthobservatory.nasa.gov/features/Atmosphere) — composición y procesos.
- [WMO Air Quality and Climate Bulletin](https://wmo.int/publication-series/wmo-air-quality-and-climate-bulletin) — informe global anual de calidad del aire.
- Stull, R. (1988). *An Introduction to Boundary Layer Meteorology* — el libro de referencia sobre la capa límite (técnico pero clarísimo).
- Seinfeld, J. & Pandis, S. (2016). *Atmospheric Chemistry and Physics: From Air Pollution to Climate Change* — la biblia de la química atmosférica.

## Próximos conceptos

- [`capa-limite-blh.md`](capa-limite-blh.md) — el "techo" móvil donde se acumula la contaminación.
- [`contaminante-no2.md`](contaminante-no2.md) — el contaminante #1 de Cali.
- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — cómo se traduce una columna satelital a la concentración que respiras.
