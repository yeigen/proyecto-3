# Conceptos — GeoVision-CLIP Cali

Orden sugerido de lectura para alguien que parte desde cero. Cada archivo tiene teoría básica, ejemplos numéricos con datos del proyecto, y enlaces a papers/docs oficiales al final.

## 1. Atmósfera y contaminantes

Empieza acá si no sabes qué es la troposfera ni por qué medimos NO₂.

- [`atmosfera-capas.md`](atmosfera-capas.md) — las 5 capas, dónde vive cada contaminante, qué hay en el aire que respiramos.
- [`contaminante-no2.md`](contaminante-no2.md) — dióxido de nitrógeno, tráfico vehicular, normativa Res. 2254/2017.
- [`contaminante-so2.md`](contaminante-so2.md) — dióxido de azufre, refinerías Yumbo, formación de sulfatos.
- [`contaminante-o3.md`](contaminante-o3.md) — ozono troposférico ("malo") vs estratosférico ("bueno"), fotoquímica.
- [`material-particulado-aod.md`](material-particulado-aod.md) — PM₂.₅/PM₁₀, AOD como proxy, MODIS MAIAC.

## 2. Meteorología que mueve los contaminantes

Las 8 bandas ERA5 del proyecto y por qué cada una importa.

- [`capa-limite-blh.md`](capa-limite-blh.md) — Boundary Layer Height: el "techo móvil" que decide si un día es limpio o contaminado.
- [`humedad-temperatura-viento.md`](humedad-temperatura-viento.md) — T₂ₘ, RH (Magnus), viento u/v, presión, precipitación.

## 3. Teledetección — "por qué unas imágenes se ven pixeladas y otras no"

- [`resolucion-espacial.md`](resolucion-espacial.md) — comparación lado a lado de las 6 fuentes (10 m a 28 km).
- [`resolucion-temporal-revisita.md`](resolucion-temporal-revisita.md) — cada cuánto revisita el satélite el mismo punto.
- [`bandas-espectrales-ndvi.md`](bandas-espectrales-ndvi.md) — qué es una banda, índices (NDVI, NDBI, NDWI) con ejemplo de Cali.

## 4. Productos satelitales — cómo leer el catálogo

- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — L0/L1/L2/L3/L4, por qué saltamos HARP, OFFL vs NRTI.
- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — qué es una columna en mol/m², cómo DOAS la mide desde 800 km de altura.
- [`reanalisis-era5.md`](reanalisis-era5.md) — qué es un reanálisis (modelo + observaciones), por qué ERA5 horario sobre ERA5-Land.

## 5. Geografía y proyecciones

- [`bbox-proyecciones-grillas.md`](bbox-proyecciones-grillas.md) — lat/lon, EPSG:4326 vs UTM vs Web Mercator, por qué ERA5 entrega 2×2 píxeles.

## 6. Conceptos de ingeniería de datos (Situación 1)

- [`geotiff-vs-zarr.md`](geotiff-vs-zarr.md) — cómo se almacenan los datos, diseño de chunks, benchmarks de compresión.

## 7. Conceptos de muestreo y modelado (Situación 2)

- [`tiles-y-percentiles.md`](tiles-y-percentiles.md) — qué es un tile (64×64×13), por qué ese tamaño, qué es un percentil (p90/p95/p99), por qué bajamos a p95 para O₃.

---

## Sugerencia para defender la Situación 1

Si vas a hacer la defensa oral del proyecto, asegúrate de poder explicar **al menos en una frase** cada uno de los siguientes 7 puntos (vienen de los conceptos):

1. **Qué es la columna troposférica de NO₂** ([`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md), [`contaminante-no2.md`](contaminante-no2.md)).
2. **Por qué necesitas BLH para interpretar la columna** ([`capa-limite-blh.md`](capa-limite-blh.md)).
3. **Por qué Sentinel-2 a 10 m y Sentinel-5P a 1 km no es contradicción** ([`resolucion-espacial.md`](resolucion-espacial.md)).
4. **Por qué cambiamos ERA5-Land por ERA5 atmosférico** ([`reanalisis-era5.md`](reanalisis-era5.md)).
5. **Qué pasa con el BBox y la grilla nativa de ERA5** ([`bbox-proyecciones-grillas.md`](bbox-proyecciones-grillas.md)).
6. **Por qué saltamos HARP** ([`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md)).
7. **AOD vs PM₂.₅ — por qué AOD es un proxy y no una medición directa** ([`material-particulado-aod.md`](material-particulado-aod.md)).
