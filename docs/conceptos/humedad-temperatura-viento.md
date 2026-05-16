# Meteorología que mueve los contaminantes

Las 6 variables ERA5 restantes del proyecto (todas excepto BLH, que tiene su propio archivo). Cada una afecta cómo se forman, transportan o eliminan los contaminantes.

## Las 6 variables y su rol

| ERA5 banda | Símbolo | Unidad | Rol en calidad del aire |
|---|---|---|---|
| `temperature_2m` | T₂ₘ | K | Acelera fotoquímica del O₃; afecta densidad del aire |
| `dewpoint_temperature_2m` | T_d | K | Permite derivar RH a 2 m con fórmula de Magnus |
| `u_component_of_wind_10m` | u | m/s | Transporte horizontal este-oeste |
| `v_component_of_wind_10m` | v | m/s | Transporte horizontal norte-sur |
| `relative_humidity_850hPa` | RH | % | Formación de aerosoles secundarios; infla AOD |
| `surface_pressure` | P_s | Pa | Corrección de columnas mol/m² a ppb |
| `total_precipitation` | P | m | Lavado húmedo de contaminantes |

## 1. Temperatura a 2 metros (T₂ₘ)

Es la temperatura "del termómetro de la estación meteorológica" — medida 2 m sobre el suelo. ERA5 la entrega en **Kelvin**: para convertir a Celsius restas 273.15.

### Por qué importa para contaminación

- **Acelera reacciones fotoquímicas**: cada +10 °C duplica la velocidad de formación de O₃ troposférico (regla de van't Hoff).
- **Modula la BLH**: más calor → más convección → BLH más alta → mejor dispersión.
- **Volatiliza COVs**: árboles emiten más isopreno a > 28 °C; gasolineras también pierden más vapores.

### Valores típicos en Cali

| Momento | T₂ₘ típica |
|---|---|
| Amanecer | 18 – 21 °C |
| Mediodía | 27 – 32 °C |
| Tarde | 28 – 34 °C |
| Madrugada | 17 – 20 °C |

Cali tiene baja variación estacional (es clima ecuatorial), pero alta variación diurna (~10-12 °C entre noche y día).

## 2. Punto de rocío y humedad relativa

### Punto de rocío (T_d)

Es la temperatura a la que el aire actual **saturaría** si lo enfriaras sin cambiar la humedad. Si T_d = 22 °C, significa que a 22 °C habría nubes/rocío.

**Regla práctica**: T_d ≈ T₂ₘ → 100 % humedad (saturación, niebla). T_d << T₂ₘ → aire seco.

### Humedad relativa con Magnus

ERA5 entrega `T_d` y `T₂ₘ`, no RH a 2 m directamente. Para obtener RH se usa la **fórmula de Magnus** (aproximación de Tetens):

$$
e_s(T) = 6.112 \cdot \exp\!\left( \frac{17.625 \cdot T_{°C}}{T_{°C} + 243.04} \right)
$$

donde `e_s(T)` es la presión de vapor de saturación en hPa y `T_°C` es la temperatura en Celsius. Entonces:

$$
RH = \frac{e_s(T_d)}{e_s(T_{2m})} \times 100\%
$$

### Ejemplo numérico

```
T₂ₘ = 28 °C  (mediodía Cali)
T_d  = 22 °C  (típico día húmedo)

e_s(28) = 6.112 · exp(17.625 × 28 / (28 + 243.04))
        = 6.112 · exp(1.819)
        ≈ 37.80 hPa

e_s(22) = 6.112 · exp(17.625 × 22 / (22 + 243.04))
        ≈ 26.43 hPa

RH = 26.43 / 37.80 × 100 ≈ 69.9 %
```

### Por qué importa para contaminación

- **Aerosoles higroscópicos crecen con RH**: una partícula de sulfato a 30 % RH puede duplicar su diámetro a 90 % RH absorbiendo agua. AOD satelital se infla, pero **el PM seco no cambia**.
- **Lluvia ácida**: H₂SO₄ y HNO₃ disueltos en agua.
- **Limita la fotoquímica de O₃**: alta RH reduce el OH troposférico que cataliza la formación de O₃.

### Banda RH a 850 hPa

La banda `relative_humidity_850hPa` del ERA5 no es a 2 m, sino al nivel de presión de 850 hPa (~1500 m de altitud en Cali, dentro de la capa límite diurna). Eso es deliberado: la formación de aerosoles secundarios y el comportamiento de las gotas ocurre **dentro de la columna**, no solo en la superficie.

## 3. Viento (u, v a 10 m)

ERA5 entrega el viento como dos componentes:

- `u_component_of_wind_10m` = viento **hacia el este** (positivo) o oeste (negativo) [m/s]
- `v_component_of_wind_10m` = viento **hacia el norte** (positivo) o sur (negativo) [m/s]

```
Velocidad = √(u² + v²)
Dirección = atan2(v, u)        [matemática]
Dirección meteorológica = (270 − atan2(v, u) · 180/π) mod 360
```

> **Convención meteorológica**: la dirección es "de dónde viene" el viento, no "hacia dónde va". `Dirección = 270°` significa viento del oeste.

### Por qué importa

- **Transporta penachos**: la pluma de Yumbo se desplaza con el viento. Si u > 0 (oeste→este) y v > 0 (sur→norte), el SO₂ industrial llega al norte de Cali.
- **Diluye**: viento fuerte = más dispersión, menos acumulación.
- **Modula brisas de montaña-valle**: en Cali predominan vientos del **oeste-suroeste** durante el día (alisios + brisa del Pacífico) y del **este-noreste** durante la noche (descenso desde la cordillera Central).

### Ejemplo numérico

```
u = 2.8 m/s    (positivo, viento al este)
v = 1.5 m/s    (positivo, viento al norte)

Velocidad = √(2.8² + 1.5²) = √(7.84 + 2.25) = √10.09 ≈ 3.18 m/s

θ_mat = atan2(1.5, 2.8) ≈ 28.2°    (dirección hacia donde va)
θ_met = (270 − 28.2) mod 360 = 241.8°  (viene del WSW)
```

Esto es un viento del oeste-suroeste a ~3.2 m/s (11.5 km/h), brisa moderada.

## 4. Presión en superficie (P_s)

ERA5 la entrega en Pascales (Pa). Cali a 1000 msnm:

```
P_s típica ≈ 90,500 Pa = 905 hPa
P_s a nivel del mar ≈ 101,325 Pa = 1013 hPa
```

### Por qué importa

- **Convertir columnas (mol/m²) a concentraciones (ppb/µg/m³)** requiere la presión total para conocer cuántas moléculas hay en la columna.
- Cambios bruscos de P_s (paso de frente, baja presión) están correlacionados con cambios en la calidad del aire (lluvia → lavado, alta presión → estancamiento).

### Fórmula de conversión columna ↔ mixing ratio

$$
\text{VMR} \approx \frac{C \cdot R \cdot T}{P_s \cdot \text{BLH}}
$$

donde VMR es la fracción volumétrica (ppb si multiplicas por 10⁹), `R` la constante universal de los gases (8.314 J/(mol·K)), `T` la temperatura media de la capa.

## 5. Precipitación total (m)

ERA5 entrega precipitación **acumulada en una hora** en metros. Por ejemplo `total_precipitation = 0.005` = 5 mm/h (lluvia moderada).

### Por qué importa para calidad del aire

- **Lavado húmedo (wet deposition)**: las gotas de lluvia capturan aerosoles y gases solubles. SO₂ y NO₂ se solubilizan parcialmente; PM se "barre" en pocas horas.
- Tras una lluvia fuerte, las concentraciones suelen caer 40-70 %.
- Cali tiene clima bimodal con picos de lluvia en abril-mayo y octubre-noviembre.

### Eficiencia de lavado típica

| Contaminante | Lavado por 10 mm lluvia |
|---|---|
| PM₁₀ | 50 – 70 % |
| PM₂.₅ | 30 – 50 % |
| NO₂ | 10 – 25 % (poco soluble) |
| SO₂ | 30 – 60 % (más soluble) |
| O₃ | 5 – 15 % (poco soluble) |

## Resumen: qué hace cada variable en el modelo del proyecto

| Variable | Modela qué |
|---|---|
| T₂ₘ | Aceleración fotoquímica del O₃ |
| T_d → RH | Crecimiento higroscópico de PM, fotoquímica |
| u, v | Transporte horizontal de plumas Yumbo→Cali, mezcla |
| BLH | Volumen de mezcla (dilución vertical) |
| P_s | Conversión columna → concentración |
| RH 850 hPa | Aerosoles secundarios, lluvia |
| Precipitación | Lavado húmedo, episodios de mejora |

Las 8 bandas ERA5 del proyecto **no son redundantes**: cada una aporta un mecanismo físico distinto al modelo CLIP+SAE.

## Lecturas

- [American Meteorological Society Glossary](https://glossary.ametsoc.org/wiki/Welcome) — definiciones rigurosas.
- [WMO No. 8 — Guide to Instruments and Methods of Observation (CIMO Guide)](https://community.wmo.int/site/knowledge-hub/programmes-and-initiatives/instruments-and-methods-of-observation-programme-imop/guide-instruments-and-methods-of-observation-wmo-no-8) — cómo se miden estas variables.
- Alduchov & Eskridge (1996). *Improved Magnus Form Approximation of Saturation Vapor Pressure*. J. Applied Meteorology — fórmula Magnus moderna.
- [ERA5 hourly data documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation) — definiciones exactas usadas en el dataset.
- [Seinfeld & Pandis (2016)](https://www.wiley.com/en-us/Atmospheric+Chemistry+and+Physics%3A+From+Air+Pollution+to+Climate+Change%2C+3rd+Edition-p-9781118947401) — capítulos 16 (deposición húmeda) y 17 (transporte).

## Próximos conceptos

- [`capa-limite-blh.md`](capa-limite-blh.md) — la octava variable ERA5.
- [`reanalisis-era5.md`](reanalisis-era5.md) — cómo se producen estos datos.
- [`material-particulado-aod.md`](material-particulado-aod.md) — donde RH infla AOD.
