# Material Particulado (PM) y AOD como proxy

## Qué es el material particulado

El **PM** (Particulate Matter) es una mezcla heterogénea de **partículas sólidas y líquidas suspendidas en el aire**. No es un gas: son trocitos minúsculos. Se clasifican por tamaño:

| Categoría | Diámetro | Origen típico | Penetración pulmonar |
|---|---|---|---|
| **PM₁₀** | < 10 µm | Polvo de calle, construcción, mecánica | Bronquios |
| **PM₂.₅** | < 2.5 µm | Combustión, sulfatos, nitratos, hollín | Alvéolos |
| PM₁ | < 1 µm | Aerosoles secundarios, humo | Sangre |
| Ultrafinas | < 0.1 µm | Diesel, biomasa, incendios | Cerebro vía olfatorio |

Cuanto más pequeñas, más profundo entran y más dañinas son. PM₂.₅ es el contaminante más letal del planeta según la OMS: causa ~4 millones de muertes prematuras/año.

## Fuentes en Cali

| Fuente | PM₁₀ | PM₂.₅ |
|---|:---:|:---:|
| Tráfico (resuspensión de polvo) | ✓✓✓ | ✓✓ |
| Combustión vehicular (diesel) | ✓ | ✓✓✓ |
| Industria pesada Yumbo | ✓✓ | ✓✓ |
| Quemas de caña (zafra del Valle) | ✓✓ | ✓✓✓ |
| Aerosol secundario (de SO₂/NO₂) | — | ✓✓ |
| Polvo del Sahara (sí, llega a Cali) | ✓ | — |

## Cómo se mide

### Desde el suelo

DAGMA y SISAIRE usan **gravimetría** (filtros pesados antes y después de bombear aire) y **TEOM** (microbalanzas oscilatorias). Reportan µg/m³ horarios o diarios.

> **El proyecto no usa PM in-situ como variable principal**. La razón: DAGMA mide NO₂/SO₂/O₃ gaseoso de forma confiable, pero las series de PM en Colombia tienen huecos (filtros gravimétricos no reportan en tiempo real). El proyecto usa **AOD satelital como proxy** y reserva la validación PM para trabajo futuro.

### Desde el satélite (MODIS MAIAC)

Aquí está lo importante: **el satélite no mide PM directamente**. Mide algo llamado **AOD** (Aerosol Optical Depth, profundidad óptica de aerosoles).

## ¿Qué es AOD?

AOD mide **qué tan opaca está la atmósfera** por aerosoles, en una longitud de onda específica. La idea:

```
Luz solar entra desde arriba ────► atravesando aerosoles ────► llega al sensor
        I₀                              τ (AOD)                    I

I = I₀ · exp(−τ · m)        ← Ley de Beer-Lambert
```

donde `m` es la "masa de aire" (función del ángulo solar). Si τ = 0 la atmósfera está limpia y todo pasa; si τ = 1 más del 60 % se absorbe/dispersa; si τ = 2 más del 85 %.

**AOD es adimensional**. El algoritmo MAIAC (Multi-Angle Implementation of Atmospheric Correction) recupera τ a 0.47 µm (azul) y 0.55 µm (verde), invirtiendo múltiples observaciones de MODIS Terra+Aqua bajo diferentes ángulos del mismo punto.

| Banda | Longitud de onda | Sensibilidad |
|---|---|---|
| `Optical_Depth_047` | 470 nm (azul) | Aerosoles finos (PM₂.₅) — la primaria |
| `Optical_Depth_055` | 550 nm (verde) | Aerosoles finos+gruesos — para validación cruzada |
| `Column_WV` | — | Vapor de agua para corregir aerosoles higroscópicos |
| `AOD_QA` | bitfield | Banderas de calidad |

Valores típicos:

| AOD | Interpretación visual |
|---|---|
| 0.05 | Cielo cristalino (Antártida) |
| 0.1 – 0.2 | Cali típico, día limpio |
| 0.3 – 0.5 | Cali con bruma, día de quema |
| 0.8 – 1.5 | Pluma de incendio cercana |
| 2.0+ | Tormenta de arena, erupción volcánica |

## De AOD a PM₂.₅: la relación clave

No es una conversión exacta — es una **regresión empírica**:

$$
\text{PM}_{2.5} = \frac{\text{AOD} \cdot \rho}{H_{\text{aer}} \cdot \omega \cdot Q}
$$

donde:
- `ρ` = densidad másica del aerosol
- `H_aer` = altura efectiva de la columna de aerosoles
- `ω` = albedo de dispersión simple
- `Q` = factor de eficiencia de extinción

En la práctica nadie usa esa fórmula con todos los parámetros. Lo que se hace es **calibrar localmente**:

$$
\text{PM}_{2.5} \approx \alpha + \beta \cdot \text{AOD} + \gamma \cdot \text{RH} + \delta \cdot \text{BLH}^{-1}
$$

con coeficientes ajustados contra una red de estaciones. La regla práctica para Cali:

```
PM₂.₅ [µg/m³] ≈ 50 · AOD₄₇₀     (día seco, RH < 70%)
PM₂.₅ [µg/m³] ≈ 80 · AOD₄₇₀     (día húmedo, RH > 80%)
```

La humedad infla AOD porque las gotitas crecen al absorber agua, pero el PM seco no cambia. Por eso ERA5 nos da `relative_humidity_850hPa` para corregir.

### Ejemplo numérico con datos del proyecto

Día de zafra de caña, sobre el norte del Valle del Cauca:

```
AOD₄₇₀ = 0.45     (medido por MODIS)
RH     = 75 %      (de ERA5)
BLH    = 1400 m    (de ERA5, ligeramente reducida por humedad)

Estimación naïve: PM₂.₅ ≈ 50 × 0.45 = 22.5 µg/m³
Con corrección RH: PM₂.₅ ≈ 65 × 0.45 = 29.3 µg/m³
```

La norma OMS 2021 es 15 µg/m³ promedio 24 h. Eso ya está duplicando la norma.

## Por qué MODIS y no Sentinel-5P para PM

- TROPOMI mide columnas de gases (NO₂, SO₂, O₃), no aerosoles totales.
- TROPOMI tiene una banda `absorbing_aerosol_index` pero **no es AOD cuantitativo**, solo una bandera cualitativa para humo y polvo.
- MODIS MAIAC tiene un algoritmo de aerosoles maduro (~20 años), validado en miles de estaciones AERONET.

Por eso el proyecto incluye **MODIS MCD19A2** como sexta fuente.

## Sobre el ruido de los datos MODIS del proyecto

Muchos gránulos MODIS sobre Cali están vacíos (ver [`DATASETS.md`](../DATASETS.md#6-modis-mcd19a2--maiac-aerosol-optical-depth-aod)). Esto es **normal** porque:

1. MODIS son **swaths**, no global daily — cada gránulo es un segmento de órbita.
2. Solo algunas órbitas pasan por Cali con datos válidos (resto = `_FillValue`).
3. La presencia de nubes (común en Cali) bloquea AOD → píxeles QA-filtered.

El script `modis_a_zarr.py` agrupa todos los gránulos del mismo día y promedia los válidos.

## Lecturas

- [Lyapustin et al. (2018) — MODIS Collection 6 MAIAC algorithm](https://amt.copernicus.org/articles/11/5741/2018/) — ATBD de MAIAC v6.1.
- [van Donkelaar et al. (2021) — Global PM₂.₅ from satellite AOD](https://pubs.acs.org/doi/10.1021/acs.est.1c05309) — el paper canónico para convertir AOD → PM₂.₅.
- [WHO Global Air Quality Guidelines 2021](https://www.who.int/publications/i/item/9789240034228) — guías PM.
- [AERONET — NASA Aerosol Robotic Network](https://aeronet.gsfc.nasa.gov/) — red de ground-truth global para AOD.
- [MODIS MAIAC product page](https://lpdaac.usgs.gov/products/mcd19a2v061/) — LP DAAC.

## Próximos conceptos

- [`humedad-temperatura-viento.md`](humedad-temperatura-viento.md) — la humedad que infla AOD.
- [`capa-limite-blh.md`](capa-limite-blh.md) — la BLH que diluye PM.
- [`bandas-espectrales-ndvi.md`](bandas-espectrales-ndvi.md) — cómo funcionan las bandas que usa MAIAC.
