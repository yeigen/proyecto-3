# Columnas troposféricas y DOAS

## La pregunta de fondo

Sentinel-5P entrega valores en **mol/m²**. ¿Qué significa eso físicamente? ¿Cómo se mide algo así desde 800 km de altura?

## Qué es una "columna"

Una **columna** es la **cantidad total de moléculas de un gas integradas verticalmente sobre 1 m² de superficie**. Imagina una probeta de 1 m² extendida desde el suelo hasta el espacio:

```
                        ☼ Sol
                        │
                        │ (Luz que entra)
   ╔════════════════════│════════════════════╗
   ║                    │                    ║
   ║     ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕     ║   ← Estratosfera
   ║     ↕  moléculas NO₂  ↕  ↕  ↕  ↕  ↕     ║     (10-50 km)
   ║                                          ║
   ║                                          ║
   ║     ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕  ↕     ║   ← Troposfera
   ║     ↕  moléculas NO₂  ↕  ↕  ↕  ↕  ↕     ║     (0-12 km)
   ║                                          ║
   ╚════════════════════│════════════════════╝
                        │ (Luz reflejada)
                        ▼
                     [TROPOMI]
                     (detecta cuánta luz fue absorbida)
                     
   Columna troposférica = cuántas moléculas hay en la mitad inferior
   Unidad: mol/m² (cantidad de sustancia / área)
```

Si la columna es **150 µmol/m²** sobre Cali, significa que hay 150 micromoles de NO₂ encima de cada metro cuadrado, sumando todo el aire entre el suelo y la tropopausa.

### Conversión a número de moléculas

```
1 mol = 6.022 × 10²³ moléculas
150 µmol/m² = 1.5 × 10⁻⁴ mol/m² × 6.022 × 10²³ = 9 × 10¹⁹ moléculas/m²
```

Pero eso es la **columna entera**, no la concentración en superficie. La conversión a concentración respirable requiere BLH (ver [`contaminante-no2.md`](contaminante-no2.md)).

## Cómo TROPOMI mide la columna: DOAS

**DOAS** = Differential Optical Absorption Spectroscopy. La idea fundamental:

**Cada gas tiene una huella digital única de absorción en el espectro UV/visible.** Si conoces qué huellas estás viendo y qué tan profundas son, sabes cuánto gas hay.

### Paso a paso

#### 1. El satélite mira el sol reflejado por la Tierra

TROPOMI no mide emisión propia de la Tierra (no la hay en UV/visible). Mide **luz solar reflejada** por nubes y superficie, que pasó **dos veces** por la atmósfera:

```
Sol ──► entra ──► atmósfera ──► refleja en suelo ──► atmósfera ──► TROPOMI
        I₀                                                          I_obs
```

#### 2. Compara con un espectro de referencia

Si la atmósfera fuera completamente transparente, `I_obs` sería igual a `I₀` (modulo geometría). Pero los gases **absorben** en longitudes de onda específicas. La diferencia es lo que DOAS analiza:

$$
\ln\!\left(\frac{I_0(\lambda)}{I_{\text{obs}}(\lambda)}\right) = \sum_{i} \sigma_i(\lambda) \cdot N_i + P(\lambda)
$$

donde:
- `λ` = longitud de onda
- `σ_i(λ)` = sección eficaz de absorción del gas `i` (conocida en laboratorio)
- `N_i` = columna del gas `i` (lo que queremos saber)
- `P(λ)` = polinomio que absorbe efectos suaves (aerosoles, dispersión Rayleigh)

#### 3. Mira solo las "estructuras finas" del espectro

La idea brillante de DOAS: los **efectos atmosféricos suaves** (Rayleigh, aerosoles) varían lentamente con λ — los modelas con un polinomio bajo grado. Las **firmas moleculares** son rugosas, con picos finos a longitudes específicas. Las **diferencias** entre `I_obs` y el ajuste suave son la huella de los gases.

```
       Espectro observado vs ajuste polinomial
   
        ──────╲                ╱──────
              ╲╲     ↓        ╱╱       
                ╲╲╲╲     ╱╱╱╱╱           ← Si solo hubiera Rayleigh
                  ╲╲╲╲ ╱╱╱╱                (ajuste polinomial suave)
   ─ ─ ─ ─ ─╲╲   ╲ ╲╱╱╱   ╱╱╱╱╱╱─ ─ ─ ─ ─   ← Observación real
              ╲   ╲ │     │   ╱
               ╲  │ │ │ │ │  ╱             ← Picos de absorción
                ╲ │ │ │ │ │ ╱                 de NO₂ (la huella)
                 ╲│ │ │ │ │╱
                  └─┴─┴─┴─┴─┘
                     λ
```

#### 4. Ajusta las columnas que mejor explican el espectro

Un solver de mínimos cuadrados encuentra el vector `(N_NO₂, N_SO₂, N_O₃, ...)` que minimiza la diferencia entre el espectro observado y la suma de huellas modeladas.

## El paso clave: AMF (Air Mass Factor)

Lo que DOAS recupera primero es la **columna inclinada** (SCD = slant column density): la cantidad de gas a lo largo del camino real de la luz. Pero el camino depende del ángulo del sol y del satélite — no es vertical.

Para convertir SCD a **columna vertical** (VCD = lo que el proyecto usa):

$$
\text{VCD} = \frac{\text{SCD}}{\text{AMF}}
$$

donde AMF (Air Mass Factor) es un **factor geométrico** que depende de:

- Ángulo cenital solar (SZA).
- Ángulo cenital de visión del satélite (VZA).
- Albedo de superficie.
- Perfil vertical asumido del gas.
- Presencia de nubes (eleva el AMF efectivo).

```
AMF ≈ 1/cos(SZA) + 1/cos(VZA)     (aproximación para cielo claro)
```

El detalle: el AMF asume **un perfil vertical** del NO₂. Si en Cali la mezcla en BLH es distinta al perfil asumido por KNMI, el VCD tiene un sesgo. Esto es una **fuente conocida de incertidumbre** del producto S5P en ciudades de relieve complejo como Cali.

## Bandas auxiliares L2 que GEE entrega

Para cada producto S5P L3, además de la columna principal, viene `cloud_fraction`:

- `cloud_fraction` ∈ [0, 1]: fracción del píxel cubierta por nubes.
- Cuando `cloud_fraction > 0.3`, el AMF se vuelve poco confiable porque la nube oculta el NO₂ debajo.

El proyecto **no filtra automáticamente** por cloud_fraction — el modelo CLIP debe aprender a usar la banda como contexto. Pero si quisieras un cálculo limpio de VCD superficial, filtrarías por `cloud_fraction < 0.2`.

## Las unidades del proyecto: mol/m² vs Dobson

Hay dos formas comunes de reportar columnas:

| Unidad | Definición | Cuando se usa |
|---|---|---|
| **mol/m²** | SI estricto | Sentinel-5P, ERA5 |
| **DU (Dobson Unit)** | 1 DU = 2.69 × 10²⁰ moléculas/m² | Ozono total (climatología histórica) |
| **µmol/m²** | 10⁻⁶ mol/m² | Conversión cómoda para NO₂/SO₂ |
| **molec/cm²** | Multiplicar mol/m² por 6.022e19 | Literatura química clásica |

### Equivalencia para el proyecto

```
1.5 × 10⁻⁴ mol/m²  =  150 µmol/m²
                  =  9.0 × 10¹⁹ moléculas/m²
                  =  9.0 × 10¹⁵ moléculas/cm²

Para O₃ total típico:
0.115 mol/m²       ≈  258 DU       (banda ozono normal sobre Cali)
```

## Por qué DOAS no funciona para todos los gases

Funciona para gases que:

- Absorben en UV/visible (200-700 nm donde TROPOMI mide).
- Tienen huellas espectrales **estructuradas** (picos finos, no continuos).
- Tienen suficiente concentración para verse por encima del ruido.

DOAS **no funciona** para:

- CO₂ (absorbe en infrarrojo térmico, requiere otro instrumento como OCO-2).
- CH₄ (infrarrojo, requiere Sentinel-5P SWIR pero con técnica distinta).
- PM₂.₅ (no es un gas, es agregado de partículas — se mide vía AOD por dispersión).
- Vapor de agua en concentraciones tropicales (saturación de absorción).

Esa es la razón por la que el proyecto **combina 4 fuentes**:
- TROPOMI con DOAS: NO₂, SO₂, O₃.
- MODIS MAIAC con multi-ángulo: AOD.
- ERA5 con modelo: meteorología.
- Sentinel-2 multiespectral: contexto urbano.

## Lecturas

- Platt, U. & Stutz, J. (2008). *Differential Optical Absorption Spectroscopy: Principles and Applications*. Springer — el libro de referencia.
- [van Geffen et al. (2022) — TROPOMI NO₂ retrieval](https://amt.copernicus.org/articles/15/2037/2022/) — DOAS aplicado a NO₂ paso a paso.
- [Veefkind et al. (2012) — TROPOMI instrument](https://www.sciencedirect.com/science/article/pii/S0034425712000661) — diseño del espectrómetro.
- [TROPOMI — Documents and information](https://www.tropomi.eu/documents-and-information) — ATBDs oficiales de KNMI para cada gas.
- [DOAS tutorial — IUP Bremen](https://www.iup.uni-bremen.de/doas/) — material académico didáctico.
- Bovensmann, H. et al. (1999). *SCIAMACHY: Mission Objectives and Measurement Modes*. — paper antecesor de TROPOMI.

## Próximos conceptos

- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — DOAS produce productos L2.
- [`contaminante-no2.md`](contaminante-no2.md) — caso aplicado con fórmulas C/BLH.
- [`bandas-espectrales-ndvi.md`](bandas-espectrales-ndvi.md) — bandas espectrales para Sentinel-2.
