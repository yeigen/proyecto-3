# Reanálisis atmosférico (ERA5)

## Lo más importante: ERA5 no es un satélite

ERA5 es un **reanálisis**: una combinación de **modelo físico + asimilación de observaciones globales**. No es un sensor, es un sistema computacional que reconstruye el estado de la atmósfera hora por hora desde 1940 hasta hoy.

```
Observaciones reales                  Modelo físico (IFS de ECMWF)
─────────────────────                 ──────────────────────────
- Satélites                            - Ecuaciones de Navier-Stokes
- Radiosondas                          - Termodinámica
- Estaciones terrestres                - Radiación
- Boyas oceánicas        ╲    ╱       - Microfísica de nubes
- Aviones comerciales     ╲  ╱
                       ╲   ╲╱   ╱
                        ╲  ╲╱  ╱        ASIMILACIÓN
                         ╲ ╲╱ ╱         (4D-Var)
                          ╲╲╱╱
                            ↓
                ┌───────────────────────┐
                │   ERA5: estado de la  │
                │  atmósfera cada hora  │
                │   en grilla 0.25°     │
                └───────────────────────┘
```

## Por qué necesitamos un reanálisis

Las observaciones reales **no cubren todo el planeta todo el tiempo**:

- Las estaciones terrestres están en tierra, no en el océano.
- Los satélites pasan a horas específicas.
- Las radiosondas se lanzan 2 veces/día desde puntos específicos.

Un modelo físico **rellena los huecos** propagando las observaciones disponibles con las leyes de la atmósfera. Si una radiosonda mide presión y temperatura sobre Bogotá a las 12 PM, y otra mide algo sobre Caracas a las 6 PM, el modelo conecta esas observaciones físicamente y te da una estimación coherente sobre Cali a cualquier hora intermedia.

## El ciclo de asimilación 4D-Var

ECMWF corre el modelo IFS (Integrated Forecasting System) con ciclos de 12 horas. Cada ciclo:

1. **Background**: arranca con el estado pronosticado por el ciclo anterior.
2. **Asimilación**: ingiere todas las observaciones disponibles en una ventana de 12 horas. Optimiza el estado de modo que minimice las diferencias modelo-observación (esto es 4D-Var: 3D de espacio + 1D de tiempo).
3. **Pronóstico**: corre el modelo hacia adelante 12 horas para producir el background del siguiente ciclo.

El resultado es **un estado físicamente consistente** de la atmósfera con resolución 0.25° (~28 km) y cadencia 1 hora. Esto es ERA5.

## Diferencia clave con observaciones puras

| Tipo de variable | Cómo viene en ERA5 |
|---|---|
| **Observada** (T₂ₘ, P_s, viento en estaciones) | Ajustada a observaciones cercanas |
| **Diagnóstica** (BLH, RH a 850 hPa) | Calculada por el modelo, **no medida** |
| **Pronosticada** (precipitación) | Output del modelo entre asimilaciones |

> Por eso `boundary_layer_height` de ERA5 **no es BLH observada** — es BLH que el modelo IFS calcula con el criterio de Richardson > 0.25 (ver [`capa-limite-blh.md`](capa-limite-blh.md)). Es la mejor estimación disponible pero tiene sus propias incertidumbres.

## ERA5 vs ERA5-Land (el del PDF)

El PDF pide ERA5-Land. ERA5-Land es un **downscale** de ERA5 que:

- Toma el output ERA5 a 0.25° (28 km).
- Lo desagrega a 0.1° (9 km) usando topografía detallada.
- Recalcula **solo variables de superficie terrestre** con un modelo de suelo más detallado (HTESSEL).

Variables de ERA5-Land:

- Temperatura del suelo
- Humedad del suelo
- Vegetación
- Evapotranspiración
- Balance hídrico

Variables que **no** están en ERA5-Land:

- ❌ Boundary Layer Height
- ❌ Relative Humidity (vertical)
- ❌ Variables de altura (`u_100m`, `v_100m`, etc.)
- ❌ Cobertura de nubes

El proyecto necesita **BLH y RH explícitamente** (por las fórmulas C/BLH del NO₂ y la formación de aerosoles secundarios). Por eso usamos **ERA5 atmosférico horario** (`ECMWF/ERA5/HOURLY`) aunque la resolución sea 28 km. Trade-off justificado en [`JUSTIFICACIONES.md`](../JUSTIFICACIONES.md).

## Cómo se procesa la temperatura ERA5

ERA5 entrega `temperature_2m` en **Kelvin**, no Celsius. La razón histórica: las ecuaciones termodinámicas trabajan en Kelvin y evitar conversiones intermedias reduce errores numéricos en cascada.

```python
T_celsius = T_kelvin - 273.15
T_celsius_28C = 301.15   # típico mediodía Cali
```

### El trick de los "instantáneos" vs "acumulados"

ERA5 mezcla variables instantáneas y acumuladas en la misma cadencia horaria:

| Tipo | Ejemplo | Significado de `t = 12:00` |
|---|---|---|
| Instantánea | `temperature_2m` | T₂ₘ exactamente a las 12:00 UTC |
| Acumulada | `total_precipitation` | mm caídos entre 11:00 y 12:00 UTC |
| Media | `boundary_layer_height` | Promedio entre 11:00 y 12:00 UTC |

Esto es una **fuente común de errores** en pipelines. La documentación oficial:

> "Many parameters in ERA5 are accumulated over the hour ending at the validity time/date. Other are means or instantaneous."

El proyecto trata todas como "valores a la hora de referencia" por simplicidad — apropiado para meteorología urbana donde los gradientes no son fuertes en una hora.

## Cobertura temporal de ERA5 en el proyecto

```
5 años × 365 días × 24 horas = 43,800 timestamps
Con manejo de bisiestos (2024) y bordes: 43,824 imágenes ERA5 en el panel
```

Sobre el BBox de Cali esto son **43,824 frames de 2×2 píxeles × 8 bandas** = unas **11 MB de datos** brutos. Diminuto. La conversión Zarr final pesa **~8 MB** (ver [`JUSTIFICACIONES.md`](../JUSTIFICACIONES.md#pesos-del-panel--análisis-por-etapa)).

## ERA5 vs ERA5T

| | ERA5 | ERA5T |
|---|---|---|
| Latencia | ~3 meses | ~5 días |
| Cómo se produce | Asimilación final con todas las obs reanalizadas | Asimilación rápida con obs preliminares |
| Calidad | Definitiva | Preliminar (puede cambiar) |

El proyecto usa **ERA5 (no T)** porque trabajamos sobre 2021-2026 históricos. Para un sistema operacional habría que cambiar a ERA5T.

## Limitaciones que afectan al proyecto

1. **Resolución 28 km no resuelve heterogeneidad urbana**. El modelo CLIP del proyecto debe aprender a corregirla usando S2 (10 m).
2. **BLH urbana real está subestimada**. La isla de calor de Cali (3-5 °C extra) eleva la BLH ~30 % respecto a lo que ERA5 reporta.
3. **Topografía suavizada**. ERA5 no "ve" los Farallones a su altura real, lo que afecta las brisas de montaña-valle.
4. **Asimilación de observaciones es sparse en Sudamérica**. Comparado con Europa, donde hay redes densas, ERA5 sobre Colombia depende más del modelo y menos de observaciones reales.

## Por qué ERA5 sigue siendo la mejor opción

A pesar de las limitaciones:

- Es **el reanálisis más usado en literatura mundial** (>10,000 papers).
- **Coherencia temporal**: misma metodología desde 1940, ideal para series largas.
- **Coherencia espacial**: misma metodología sobre todo el globo.
- **Acceso libre y rápido** vía Copernicus CDS o GEE.
- **Bien documentado** (decenas de PDFs técnicos de ECMWF).

Para mejores datos sobre Cali habría que correr **WRF-Chem** o **HARMONIE** acoplado a sondas locales — meses de trabajo y cómputo, fuera de alcance.

## Lecturas

- Hersbach, H. et al. (2020). *The ERA5 global reanalysis*. Q. J. R. Meteorol. Soc. — paper oficial fundacional. [DOI:10.1002/qj.3803](https://doi.org/10.1002/qj.3803).
- [ERA5 documentation (ECMWF)](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation) — referencia completa.
- [ERA5 vs ERA5-Land comparison](https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation) — diferencias detalladas.
- [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/) — fuente oficial.
- [ECMWF IFS documentation](https://www.ecmwf.int/en/publications/ifs-documentation) — el modelo numérico que corre adentro.
- Bechtold, P. et al. (2008). *Advances in simulating atmospheric variability with the ECMWF model*. — parametrizaciones físicas del modelo IFS.

## Próximos conceptos

- [`capa-limite-blh.md`](capa-limite-blh.md) — cómo ERA5 diagnostica BLH.
- [`humedad-temperatura-viento.md`](humedad-temperatura-viento.md) — las 7 variables ERA5 además de BLH.
- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — comparación con productos satelitales.
