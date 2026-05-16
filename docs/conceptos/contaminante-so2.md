# Dióxido de Azufre (SO₂)

## Qué es

El **SO₂** es un gas incoloro, picante, soluble en agua. Se forma cuando se quema cualquier combustible que tenga azufre: carbón, fuel-oil, ACPM (diesel), crudo en una refinería. A diferencia del NO₂, **no aparece de combustión limpia**: solo si hay azufre en el combustible.

```
S (en el combustible) + O₂ ────► SO₂   (combustión)
```

En la atmósfera el SO₂ se oxida lentamente a sulfato (SO₄²⁻), que es **material particulado fino (PM₂.₅)**:

```
SO₂ + OH ────► HSO₃
HSO₃ + O₂ ──► SO₃ + HO₂
SO₃ + H₂O ──► H₂SO₄  ──► partículas de sulfato (aerosol secundario)
```

Por eso reduce la visibilidad y forma **lluvia ácida** cuando se disuelve en gotas.

## Fuentes en Cali

A diferencia del NO₂ (dominado por tráfico), el SO₂ es **dominantemente industrial**:

| Fuente | % aproximado | Comentario |
|---|---:|---|
| Refinería de Yumbo (ECOPETROL) | ~40-50 % | El crudo procesado contiene azufre |
| Industria pesada Yumbo–Acopi | ~25-30 % | Calderas, hornos, generación térmica con ACPM |
| Vehículos diesel viejos | ~10-15 % | El ACPM colombiano bajó de 5000 a 50 ppm de azufre en 2010 |
| Quemas de caña | ~5 % | Trazas |
| Aportes naturales | ~5 % | Volcanes andinos, océano |

Por eso el BBox del proyecto extiende `x_max = -76.30` para capturar Yumbo (al norte de Cali). Sin Yumbo, el modelo de SO₂ tendría señales débiles.

## Por qué importa para la salud

| Promedio | Norma OMS 2021 | Norma Colombia (Res. 2254) |
|---|---|---|
| 10 minutos | 500 µg/m³ | — |
| 1 hora | — | 100 µg/m³ |
| 24 horas | 40 µg/m³ | 50 µg/m³ |
| Anual | — | 20 µg/m³ |

Efectos: **broncoconstricción aguda** en asmáticos (a 10-30 min de exposición), tos, dolor de garganta. A largo plazo: bronquitis crónica.

## Cómo se mide

### Desde el suelo

Las estaciones DAGMA usan **fluorescencia UV**: una lámpara UV excita las moléculas de SO₂ que reemiten luz medible. Salida en µg/m³ horaria.

### Desde el satélite (Sentinel-5P TROPOMI)

Igual que NO₂, usa **DOAS** sobre el rango ultravioleta (~310-320 nm). El producto que descarga el proyecto:

```
SO2_column_number_density   [mol/m²]
```

**Pero hay un detalle clave**: el SO₂ urbano tiene columnas mucho más bajas que el NO₂ (típicamente 5–50 µmol/m² vs 40–300 para NO₂). La señal está cerca del **límite de detección** de TROPOMI. Por eso:

- Muchos píxeles aparecen como **ruido** o valores negativos (es un artefacto del fit DOAS, no significa "menos SO₂ que el vacío").
- El proyecto necesita la banda `cloud_fraction` para filtrar píxeles nublados que amplifican el ruido.
- Para detectar fuentes industriales con confianza, se suele **promediar varios días o semanas**.

### El truco de los 15 km

El asset GEE entrega también una banda `SO2_column_number_density_15km` que es **SO₂ a 15 km de altura**. Es para detectar **plumas volcánicas** que viajan en la estratosfera, no contaminación urbana. **No la usamos en el proyecto** porque en Cali nuestra señal vive en los primeros 2 km (capa límite).

## De columna a concentración

Misma fórmula que NO₂:

$$
c_{\text{superficie}} \approx \frac{C \cdot M_{\text{SO}_2} \cdot 10^6}{\text{BLH}}
$$

con `M_SO₂ = 64.066 g/mol`.

### Ejemplo numérico con datos del proyecto

Pluma típica de la refinería de Yumbo al mediodía:

```
C    = 25 µmol/m²  = 2.5 × 10⁻⁵ mol/m²
BLH  = 2000 m  (ERA5, diurno con viento del Pacífico)
M    = 64.066 g/mol

c = (2.5 × 10⁻⁵ × 64.066 × 10⁶) / 2000
  = 1601.65 / 2000
  ≈ 0.80 µg/m³
```

Esto está muy debajo de la norma colombiana (50 µg/m³ diaria). El SO₂ urbano de Cali normalmente no excede las normas, pero **picos episódicos** durante mantenimientos de refinería o eventos térmicos pueden llegar a 30–80 µg/m³ horarios — esos son los que el modelo debe identificar para alertas.

## Lecturas

- [Theys et al. (2017) — Sulfur dioxide retrievals from TROPOMI](https://amt.copernicus.org/articles/10/119/2017/) — ATBD del producto SO₂.
- [Fioletov et al. (2020) — Anthropogenic and volcanic SO₂ emissions from TROPOMI](https://acp.copernicus.org/articles/20/5591/2020/) — catálogo global de fuentes detectadas con satélite.
- [Sentinel-5P SO₂ Product User Manual](https://sentinels.copernicus.eu/documents/247904/2474726/Sentinel-5P-Level-2-Product-User-Manual-Sulphur-Dioxide.pdf) — manual oficial.
- [WHO — Sulfur dioxide and health](https://www.who.int/news-room/fact-sheets/detail/ambient-(outdoor)-air-quality-and-health) — guía de salud.

## Próximos conceptos

- [`material-particulado-aod.md`](material-particulado-aod.md) — el sulfato del SO₂ se convierte en PM₂.₅.
- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — el algoritmo DOAS en detalle.
