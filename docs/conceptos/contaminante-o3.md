# Ozono (O₃) — troposférico vs estratosférico

## Lo más importante: hay dos ozonos

Esto confunde a todo el mundo. **El O₃ es el mismo gas** (tres átomos de oxígeno), pero su efecto en la salud y el clima depende **completamente de dónde esté**:

| Capa | Altura | Cómo se forma | Efecto |
|---|---|---|---|
| **Estratosfera** | 12–50 km | Fotólisis natural de O₂ por UV solar | **O₃ "bueno"**: nos protege del UV. Si no estuviera, habría melanoma masivo. Es la *capa de ozono* que el Protocolo de Montreal salvó. |
| **Troposfera** | 0–12 km | Reacción NOₓ + COVs + sol | **O₃ "malo"**: contaminante. Daña pulmones, oxida materiales, reduce cosechas. |

Por eso el proyecto trabaja con dos variables de O₃ de Sentinel-5P:

- `O3_column_number_density` — **columna total** (tropo + estrato). Lo que TROPOMI mide directo.
- (no se usa) Columnas separadas — más ruidosas, requieren procesamiento extra.

El asset GEE solo entrega la total. **Para Cali, casi toda la variabilidad de la columna total viene del estratosférico** (porque es la mayor parte del O₃), y eso es un problema. Por eso modelar O₃ urbano con TROPOMI es más difícil que NO₂ o SO₂.

## Cómo se forma el ozono troposférico (el "malo")

No se emite directamente. Se forma **en el aire** a partir de otros contaminantes (por eso se llama **contaminante secundario**):

```
                  luz UV solar
NO₂ + COVs ──────────────────►  O₃ + NO
   (precursores)                  
```

Los **COVs** (compuestos orgánicos volátiles) son cosas como benceno, tolueno, isopreno (de árboles), formaldehído. Sale de tubos de escape, solventes industriales, naturalmente de la vegetación.

La velocidad de formación depende de:
- **Luz solar** (UV-A). Por eso los picos de O₃ son al mediodía y la tarde, no en la noche.
- **Temperatura**. Reacciones más rápidas con calor → picos en días soleados de 30 °C+.
- **Razón NOₓ/COV**: zonas con mucho NOₓ y poco COV (centros urbanos) tienen O₃ más bajo del esperado; zonas con muchos COVs (bosques río abajo de la ciudad) tienen O₃ alto.

Cali es una "ciudad NOx-limitada" en el centro, pero las **laderas y el sur del municipio** pueden volverse COV-limitadas por el flujo de aire urbano que se mezcla con emisiones biogénicas de los Farallones. Esto es exactamente el tipo de patrón que el modelo del proyecto debe detectar.

## Por qué importa para la salud

| Promedio | Norma OMS 2021 | Norma Colombia (Res. 2254) |
|---|---|---|
| 8 horas (pico diurno) | 100 µg/m³ | 100 µg/m³ |
| Anual (temporada de pico) | 60 µg/m³ | — |

Efectos: **inflamación pulmonar aguda**, reducción de capacidad respiratoria, agravamiento de asma. A largo plazo se asocia con mortalidad cardiovascular. Es especialmente dañino para corredores, niños jugando en parques al mediodía.

## El problema del satélite

TROPOMI mide la columna **total** vertical de O₃:

```
O3_column_number_density   [mol/m²]
```

Valores típicos: **0.1 – 0.13 mol/m²** (es decir 100,000 – 130,000 µmol/m² — órdenes de magnitud más alto que NO₂ o SO₂ porque la columna estratosférica domina).

Las **variaciones troposféricas son ~1-2 % del total**: la señal "urbana" es muy pequeña sobre el fondo estratosférico. Por eso:

1. No se puede comparar directamente la columna O₃ del satélite con la estación DAGMA (que solo mide la troposférica, los primeros metros).
2. El modelo del proyecto debe **aprender la relación** entre la columna total + otras variables (NO₂, T2m, RH, hora del día) y la concentración superficial. Es donde el aprendizaje multimodal CLIP+SAE puede aportar valor.

## Estimación práctica desde el satélite

Para separar la componente troposférica se usa el **método de la diferencia** (no implementado en el dataset GEE pero útil de saber):

$$
\text{O}_{3,\text{tropo}} \approx C_{\text{total}} - C_{\text{estrato,clima}}
$$

donde `C_{estrato,clima}` es una climatología estratosférica (~0.105 mol/m² para latitudes tropicales). La diferencia es ruidosa pero capturable.

### Ejemplo numérico

```
C_total       = 0.118 mol/m²   (TROPOMI Cali, mediodía)
C_estrato     = 0.105 mol/m²   (climatología tropical)
C_tropo       = 0.013 mol/m²   = 13 µmol/m²

BLH           = 1800 m
M_O3          = 47.998 g/mol

c_superficie  ≈ (0.013 × 47.998 × 10⁶) / 1800
              ≈ 346.6 µg/m³
```

Eso es altísimo (3× sobre la norma). El número está sobreestimado porque la diferencia C_total − C_estrato no es exactamente lineal con la concentración superficial — la mayor parte del O₃ troposférico vive en los primeros 3 km, no en toda la columna troposférica. Por eso el proyecto **no usa la fórmula directa**, sino que entrena un modelo CLIP que aprende esta no-linealidad a partir de los pares satélite ↔ estación DAGMA.

## Por qué O₃ es el contaminante más difícil del proyecto

- Señal urbana = pequeña fracción de la columna total.
- Formación química no lineal (NOₓ vs COV-limitado).
- Depende fuerte de meteorología (T, UV, RH).
- Datos in-situ DAGMA escasos para entrenar.

Por eso el RMSE objetivo del PDF es **más permisivo para O₃** (12 µg/m³) que para NO₂ (8) o SO₂ (6). Ver KPIs Situación 3 en el PDF.

## Lecturas

- [Lefohn et al. (2018) — Tropospheric ozone assessment report (TOAR)](https://online.ucpress.edu/elementa/article/doi/10.1525/elementa.279/112779/Tropospheric-ozone-assessment-report-Global-ozone) — el compendio sobre O₃ troposférico.
- [S5P Documents — SentiWiki](https://sentiwiki.copernicus.eu/web/s5p-documents) — manuales del producto O₃ y algoritmo GODFIT.
- [Monks et al. (2015) — Tropospheric ozone and its precursors](https://acp.copernicus.org/articles/15/8889/2015/) — química troposférica de O₃.
- [Seinfeld & Pandis (2016)](https://www.wiley.com/en-us/Atmospheric+Chemistry+and+Physics%3A+From+Air+Pollution+to+Climate+Change%2C+3rd+Edition-p-9781118947401) — capítulos 5 y 6 sobre fotoquímica.

## Próximos conceptos

- [`contaminante-no2.md`](contaminante-no2.md) — precursor principal del O₃.
- [`humedad-temperatura-viento.md`](humedad-temperatura-viento.md) — las variables meteo que modulan la formación.
- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — algoritmo de TROPOMI.
