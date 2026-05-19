# Resolución temporal y revisita

## La idea fundamental

La **resolución temporal** (también llamada **revisita**) es **cada cuánto el satélite vuelve a pasar por el mismo punto**. Es la otra cara de la resolución espacial: define qué tipo de fenómenos puedes estudiar.

| Si el fenómeno dura | Necesitas resolución temporal de |
|---|---|
| Segundos (rayo) | No es viable con satélite de órbita baja |
| Minutos (avance de tormenta) | Geoestacionario (GOES, Meteosat) |
| Horas (ciclo diurno de O₃) | Geoestacionario o reanálisis horario (ERA5) |
| Días (pluma de humo) | Polar diaria (Sentinel-5P, MODIS) |
| Semanas (deforestación) | Polar cada ~5 días (Sentinel-2) |
| Meses-años (urbanización) | Polar cada 16 días (Landsat) |

## Las 6 fuentes del proyecto

| Fuente | Cadencia nativa | En 5 años | Cubre ciclo diurno |
|---|---|---:|---|
| Sentinel-2 | 5 días (2A+2B) | 1,552 escenas sobre Cali | ❌ |
| Sentinel-5P NO₂/SO₂/O₃ | 1-2 órbitas/día | ~25,000 escenas c/u | ⚠️ una hora del día |
| MODIS MAIAC | 1-2 swaths/día (Terra+Aqua) | 151,558 gránulos crudos | ⚠️ dos horas del día |
| ERA5 | 1 hora | 43,824 frames | ✅ |
| DAGMA in-situ | 1 hora | ~87,600 valores/estación | ✅ |

## Por qué ERA5 es horario

ERA5 no es un satélite — es un **reanálisis**. Es un modelo numérico (IFS de ECMWF) que se reinicializa cada 6 horas con todas las observaciones disponibles (satelitales, terrestres, radiosondas, barcos, aviones) y "rellena" lo que pasa entre observaciones con física atmosférica.

Por eso ERA5 puede entregar cada hora **incluso si en esa hora no pasó ningún satélite por Cali**: el modelo propaga la información temporalmente. Esto es exactamente lo que necesitamos para capturar la dinámica diurna de BLH, T₂ₘ y RH (ver [`reanalisis-era5.md`](reanalisis-era5.md)).

## Por qué Sentinel-5P es "1-2 órbitas/día"

Sentinel-5P es un satélite **polar heliosíncrono**: pasa siempre a la misma hora local sobre cada punto. Para Cali, la hora local de paso es **~13:30 (1:30 PM)**. Si esa órbita cubre Cali el día N, el satélite vuelve aproximadamente cada día (cobertura global cada 24 h).

Algunos días caben **dos órbitas** sobre el BBox del proyecto porque el ancho de barrido (2600 km) genera traslapes en latitudes cercanas al ecuador.

### Consecuencia para el proyecto

**Sentinel-5P solo muestrea la atmósfera al mediodía local**. No vemos el pico nocturno de NO₂ que ocurre a las 7-9 PM con BLH baja. Eso es una **limitación intrínseca** que el modelo CLIP+SAE no puede inventar: para modelar el ciclo diurno necesitamos combinar S5P (mediodía) + ERA5 (todo el día) + DAGMA (todo el día).

### Sobre los 25,000 archivos por contaminante

```
5 años × 365 días × ~1.4 órbitas/día ≈ 2,555 órbitas
```

Pero el conteo real es **25,592 para NO₂**. La diferencia se debe a que **L3 entrega un archivo por órbita**, y muchas órbitas se dividen en múltiples granules según el procesado de KNMI/ESA. Cada granule = un archivo en el panel raw.

## Por qué Sentinel-2 es "cada 5 días"

Sentinel-2A y 2B son satélites idénticos con órbitas separadas 180°. Cada uno revisita el mismo punto cada **10 días**. Combinándolos: **5 días**.

```
2A pasa día N → 2B pasa día N+5 → 2A pasa día N+10 → 2B pasa día N+15 ...
```

### Pero solo unos días tienen datos útiles

El BBox de Cali es cruzado por **2 tiles MGRS** (T18NUJ y T18NUK, verificado contra `panel.zarr` en bloque 2 del EDA — ver `docs/EDA_HALLAZGOS.md`). En 5 años acumulamos **1,552 escenas** sobre el BBox completo (779 + 773, distribución 50/50). El proyecto **no filtra por nubosidad** en este conteo — todas las escenas, con o sin nubes, están incluidas (S2 sobre Cali tiene mucha nube por ser zona tropical húmeda). Tras pre-filtrado por SCL > 0.3, solo ~140/1552 (9%) escenas son usables.

> Esto importa para Situación 2: el modelo CLIP debe aprender a tolerar nubes (usando la banda SCL para identificarlas), no a filtrarlas. Filtrar reduciría drásticamente el dataset.

## MODIS MAIAC — 151,558 archivos para 5 años?

Sí. La razón:

- MODIS son **dos satélites** (Terra: 10:30 local; Aqua: 13:30 local).
- Cada satélite hace **múltiples pasadas/día** que tocan Cali parcialmente (swaths).
- Cada gránulo MAIAC es un swath, **no un mosaico diario**.
- Muchos gránulos están **vacíos sobre Cali** (es la realidad del producto, ver [`material-particulado-aod.md`](material-particulado-aod.md)).

```
5 años × 365 días × ~80 gránulos/día con cobertura parcial ≈ 146,000
```

El script `modis_a_zarr.py` agrupa los gránulos por fecha y promedia. El zarr final tiene **~1,800 días con AOD agregado**, no 151,558 entradas.

## El ciclo diurno: qué se ve, qué no

Para entender por qué la resolución temporal importa, miremos el NO₂ típico de Cali en un día laboral:

```
   NO₂ (µg/m³)
    40 ┤              ╱╲                ╱╲
       │             ╱  ╲              ╱  ╲
    30 ┤            ╱    ╲            ╱    ╲
       │           ╱      ╲          ╱      ╲
    20 ┤          ╱        ╲────╲   ╱        ╲
       │         ╱           hora  ╲╱          ╲
    10 ┤        ╱            mediodía           ╲___
       │  ┄┄┄┄╱   ↑               ↑               ↑
     0 ┴────────────────────────────────────────────
          0h  3h  6h  9h  12h  15h  18h  21h  24h
                  ↑                    ↑
              Pico AM              Pico PM
              (rush hora            (rush hora
               + BLH baja)          + BLH alta...)
              
        ⬆ S5P pasa aquí
          (mediodía, valle del día)
```

**Sentinel-5P captura el valle entre los dos picos, no los picos**. Por eso el modelo necesita las variables ERA5 horarias y las observaciones DAGMA horarias para reconstruir lo que ocurre cuando S5P no está mirando.

## Latencia: cuánto tarda en estar disponible

Otro aspecto de "resolución temporal" es **cuándo** ves los datos, no solo cuándo se midieron.

| Producto | Latencia típica |
|---|---|
| Sentinel-5P **NRTI** (Near Real-Time) | 3 horas |
| Sentinel-5P **OFFL** (Offline) | 5 días |
| Sentinel-2 L2A | 1-2 días |
| MODIS MAIAC | 1-2 días |
| ERA5 (Reanalysis) | 2-3 meses |
| ERA5T (preliminary) | 1 semana |

> **El proyecto usa todo OFFL**. La latencia no nos afecta porque trabajamos sobre 2021-2026 (datos históricos). Si el sistema desplegado de Situación 3 quisiera operar "en vivo", habría que migrar a NRTI para S5P y a ERA5T para meteo.

## Implicación para Situación 2 (CLIP+SAE)

El PDF pide construir "series temporales de 8 fechas consecutivas" para alimentar el ConvLSTM. La fuente más densa para esto **debe ser Sentinel-5P** (~5 muestras/día efectivas tras filtrar calidad), porque S2 cada 5 días no daría 8 fechas en una ventana razonable.

```
Estrategia natural:
  - serie de 8 frames de S5P (cubre ~8-10 días)
  - serie de 8 frames de ERA5 horarios alrededor de cada S5P (cubre la dinámica meteo)
  - 1-2 frames de S2 dentro de la ventana (lo que haya disponible)
```

Esa es la razón por la que el modelo se llama **ConvLSTM**: la LSTM modela la dimensión temporal a tasa irregular, no fija.

## Lecturas

- Jensen, J. R. (2015). *Introductory Digital Image Processing: A Remote Sensing Perspective*. — capítulo sobre resoluciones.
- [Sentinel-5P — SentiWiki Copernicus](https://sentiwiki.copernicus.eu/web/sentinel-5p) — órbita, revisita y especificaciones de la misión.
- [Sentinel-2 — SentiWiki Copernicus](https://sentiwiki.copernicus.eu/web/sentinel-2) — diseño de la constelación 2A+2B y revisita de 5 días.
- [MODIS Spacecraft Information](https://modis.gsfc.nasa.gov/about/specifications.php) — Terra/Aqua.
- [ECMWF — How ERA5 is produced](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation#ERA5:datadocumentation-IFSmodel) — el ciclo de asimilación 4D-Var.

## Próximos conceptos

- [`resolucion-espacial.md`](resolucion-espacial.md) — la otra cara de la resolución.
- [`reanalisis-era5.md`](reanalisis-era5.md) — cómo ERA5 entrega datos horarios.
- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — qué significa NRTI vs OFFL.
