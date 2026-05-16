# Dióxido de Nitrógeno (NO₂)

## Qué es

El **NO₂** es un gas rojizo-marrón, irritante, formado por la oxidación del óxido nítrico (NO). Junto al NO forma los llamados **NOₓ** (óxidos de nitrógeno). Es el **trazador #1 del tráfico vehicular** porque se produce siempre que algo quema combustible a alta temperatura.

```
Combustión a alta T (motor diesel, gasolina, planta térmica):
   N₂ + O₂  ──────────────►  2 NO
                  ΔT alta

Luego en la atmósfera:
   2 NO + O₂  ────────►  2 NO₂   (cuestión de minutos a horas)
```

## Fuentes en Cali

| Fuente | % aproximado | Comentario |
|---|---:|---|
| Tráfico vehicular | ~60-70 % | Motos, buses MIO, camiones del corredor Yumbo–Acopi |
| Industria del Valle del Cauca | ~15-20 % | Refinerías, calderas, generación térmica |
| Quemas de caña de azúcar | ~5-10 % | Estacional (zafra del norte del Valle) |
| Aportes regionales | ~5 % | Vientos del Pacífico, fondo natural |

> Es por esto que el PDF del proyecto subraya el corredor industrial Yumbo–Acopi y la zona de cultivos de caña dentro del BBox `[-76.65, 3.30, -76.30, 3.65]`.

## Por qué importa para la salud

El NO₂ es un **gas irritante de las vías respiratorias bajas**. La OMS y el Ministerio de Ambiente de Colombia (Resolución 2254 de 2017) lo regulan así:

| Promedio | Norma OMS 2021 | Norma Colombia (Res. 2254) |
|---|---|---|
| 1 hora | 200 µg/m³ | 200 µg/m³ |
| 24 horas | 25 µg/m³ | 100 µg/m³ |
| Anual | 10 µg/m³ | 60 µg/m³ |

La norma colombiana es más permisiva que la OMS, pero el modelo del proyecto debe predecir valores que un técnico ambiental pueda comparar contra **cualquiera** de las dos referencias.

## Cómo se mide

### Desde el suelo (DAGMA / SISAIRE)

Las 9 estaciones DAGMA usan **quimioluminiscencia**: bombean aire por una cámara con ozono, la reacción NO + O₃ → NO₂* emite luz que se cuenta con un fotomultiplicador. Reportan concentración en **µg/m³** o **ppb** cada hora. Es la *ground truth* para el LOO-CV del proyecto.

### Desde el satélite (Sentinel-5P TROPOMI)

TROPOMI mide la **columna troposférica de NO₂** usando **DOAS** (Differential Optical Absorption Spectroscopy). Mira los huecos en el espectro UV/visible del sol reflejado: cada gas tiene su firma de absorción única. Resultado:

```
tropospheric_NO2_column_number_density   [mol/m²]
```

Eso significa "cuántos moles de NO₂ hay verticalmente sobre 1 m² de Cali, desde el suelo hasta la tropopausa". Valores típicos urbanos: **40 – 300 µmol/m²** (es decir 4×10⁻⁵ a 3×10⁻⁴ mol/m²).

Detalle del algoritmo en [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md).

## De columna satelital a concentración respirada

La columna `C [mol/m²]` no es lo mismo que la concentración `c [µg/m³]` que mide el DAGMA. Para pasar de una a la otra hay que asumir cómo está distribuido el NO₂ verticalmente:

$$
c_{\text{superficie}} \approx \frac{C \cdot M_{\text{NO}_2} \cdot 10^6}{\text{BLH}}
$$

donde:
- `C` = columna troposférica [mol/m²]
- `M_NO₂` = 46.0055 g/mol (masa molar)
- `BLH` = altura de capa límite [m] (de ERA5)
- `10⁶` = conversión g → µg
- El resultado está en **µg/m³**

### Ejemplo numérico con datos del proyecto

Una imagen típica de Sentinel-5P sobre Cali al mediodía:

```
C    = 150 µmol/m²  = 1.5 × 10⁻⁴ mol/m²
BLH  = 1800 m  (ERA5, diurno)
M    = 46.0055 g/mol

c = (1.5 × 10⁻⁴ × 46.0055 × 10⁶) / 1800
  = 6900.8 / 1800
  ≈ 3.83 µg/m³
```

Esa misma columna a las 3 AM con BLH = 250 m daría:

```
c = 6900.8 / 250 ≈ 27.6 µg/m³
```

**Mismo NO₂ total en la columna, 7 veces más concentración respirada de noche.** Por eso el proyecto necesita ERA5 y BLH como variable explicativa, no solo Sentinel-5P. Esta es la razón fundamental por la que el modelo CLIP+SAE (Situación 2) recibe meteorología como input además de las imágenes ópticas.

## El truco del proyecto: NO₂ tropo vs total

El asset GEE entrega **dos columnas**:

- `tropospheric_NO2_column_number_density` — solo troposfera (0–12 km). **Lo que importa para calidad del aire**.
- `NO2_column_number_density` — total (tropo + estratosfera). Útil porque permite calcular la fracción `tropo/total` y validar que el algoritmo separó bien las dos componentes.

El proyecto usa ambas (ver [`DATASETS.md`](../DATASETS.md#2-sentinel-5p-tropomi--dióxido-de-nitrógeno-no)).

## Lecturas

- [van Geffen et al. (2022) — Sentinel-5P TROPOMI NO₂ retrieval](https://amt.copernicus.org/articles/15/2037/2022/) — ATBD oficial del producto NO₂.
- [Veefkind et al. (2012) — TROPOMI on the ESA Sentinel-5 Precursor](https://www.sciencedirect.com/science/article/pii/S0034425712000661) — paper fundacional del instrumento.
- [WHO — Global Air Quality Guidelines 2021](https://www.who.int/publications/i/item/9789240034228) — niveles recomendados.
- [Resolución 2254 de 2017 — Min. Ambiente Colombia](https://www.minambiente.gov.co/documento-entidad/resolucion-2254-de-2017/) — norma nacional.
- [Goldberg et al. (2021) — TROPOMI NO₂ in the United States: weekly cycles, temperature, correlation with surface NO₂](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2020EF001665) — Earth's Future.
- [S5P Products — SentiWiki](https://sentiwiki.copernicus.eu/web/s5p-products) — ATBDs y manuales técnicos de KNMI para cada producto.

## Próximos conceptos

- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — cómo DOAS reconstruye la columna.
- [`capa-limite-blh.md`](capa-limite-blh.md) — la BLH del ejemplo numérico.
- [`contaminante-so2.md`](contaminante-so2.md) — el primo del NO₂.
