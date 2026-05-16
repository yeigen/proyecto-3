# Capa límite planetaria (BLH)

## La idea en una frase

La **BLH** (Boundary Layer Height) es la **altura del "techo invisible"** dentro del cual se mezcla el aire que respiramos. Todos los contaminantes urbanos están atrapados debajo de esa altura. Si la BLH baja a la mitad, la concentración de contaminantes se duplica con la misma emisión.

## La analogía

Imagina la atmósfera como un vaso con agua y aceite:

- **El vaso** es la troposfera.
- **El agua de abajo** (con todo lo disuelto) es la capa límite. Aquí están los contaminantes.
- **El aceite de arriba** es la "atmósfera libre" (free troposphere). Aislada, casi sin mezcla.
- **La interfase** entre los dos = **BLH**.

```
   ▓▓▓▓▓▓▓▓▓▓▓▓ Atmósfera libre (free troposphere) ▓▓▓▓▓▓▓▓▓▓
                            (poca turbulencia, lenta)
   ─── BLH ─── ↑ techo de la mezcla ───────────
       ↕
       ↕  Capa límite planetaria — turbulencia, mezcla, contaminantes
       ↕     (toda la actividad humana respirable)
   ════════════════════ SUPERFICIE (Cali, 1000 msnm) ════════════════════
```

## El ciclo diurno: por qué BLH varía tanto

**Es el factor #1 que determina si un día va a ser limpio o contaminado en Cali**, incluso con la misma cantidad de emisiones.

```
  Altura (m)
   2500 ┤        ╱╲
        │       ╱  ╲             BLH diurna típica Cali soleado
   2000 ┤      ╱    ╲             (mezcla profunda)
        │     ╱      ╲
   1500 ┤    ╱        ╲
        │   ╱          ╲
   1000 ┤  ╱            ╲
        │ ╱              ╲
    500 ┤╱                ╲___________
        │                    BLH nocturna estable (200-400 m)
      0 ┴────┬────┬────┬────┬────┬────┬────┬────
            06h  09h  12h  15h  18h  21h  00h  03h
```

### De día (10 AM a 4 PM)

- Sol calienta el suelo.
- Suelo calienta el aire en contacto.
- Aire caliente sube por convección.
- Se forma una capa mezclada de **1500–2500 m**.
- Los contaminantes se diluyen en esa caja grande.

### De noche (10 PM a 6 AM)

- Suelo se enfría por radiación infrarroja.
- Aire cerca del suelo más frío → más denso → no sube.
- Se forma una **inversión térmica**: aire frío estable abajo, aire más cálido arriba.
- BLH cae a **100–500 m** (a veces menos en valles).
- Los contaminantes nocturnos (camiones de carga, calderas industriales) quedan atrapados → **picos respiratorios al amanecer**.

## Cali es especial porque está en un valle

El Valle del Cauca tiene ~5 km de ancho con cordilleras de 2500–3500 m a ambos lados. Eso genera:

- **Mezcla atmosférica restringida lateralmente**: la BLH no se puede expandir horizontalmente, solo verticalmente.
- **Brisas de montaña-valle**: vientos descendentes nocturnos desde los Farallones aportan aire frío que **comprime aún más la BLH**.
- **Inversiones persistentes**: en mañanas frías de enero-febrero la BLH puede quedar bajo 200 m hasta las 9-10 AM. Esos son los días con peores índices de calidad del aire.

## Cómo lo entrega ERA5

```
boundary_layer_height   [m]   (banda obligatoria del proyecto)
```

ERA5 estima BLH usando el **número de Richardson bulk**:

$$
Ri_b(z) = \frac{g \cdot z}{\theta_v(z)} \cdot \frac{\theta_v(z) - \theta_v(0)}{u(z)^2 + v(z)^2}
$$

donde:
- `g` = gravedad (9.81 m/s²)
- `z` = altura
- `θ_v` = temperatura potencial virtual (corregida por humedad)
- `u, v` = componentes del viento

ERA5 declara `BLH = z` para el primer `z` donde `Ri_b(z) > 0.25` (criterio crítico de turbulencia). No es un sensor que mida BLH: es un diagnóstico del modelo de reanálisis.

> Por eso el proyecto usa ERA5 atmosférico y **no ERA5-Land**: ERA5-Land es un downscale solo de variables de superficie terrestre (suelo, vegetación, balance hídrico). No contiene BLH porque BLH es una variable atmosférica de la columna completa. Esa es la justificación técnica del cambio (ver [`JUSTIFICACIONES.md`](../JUSTIFICACIONES.md)).

## Por qué importa para el proyecto

La columna troposférica `C` que mide Sentinel-5P se relaciona con la concentración superficial `c` así (asumiendo distribución uniforme dentro de la capa límite):

$$
c_{\text{superficie}} \approx \frac{C}{\text{BLH}}
$$

(en unidades coherentes; ver derivación completa en [`contaminante-no2.md`](contaminante-no2.md)).

### Ejemplo lateral: dos días, misma columna

**Mismo NO₂ medido por TROPOMI, dos días distintos:**

| | Día A (soleado) | Día B (inversión) |
|---|---|---|
| C (TROPOMI) | 150 µmol/m² | 150 µmol/m² |
| BLH (ERA5) | 2000 m | 350 m |
| c superficie (∝ 1/BLH) | ~3.5 µg/m³ | ~20 µg/m³ |
| Sensación al respirar | Aire limpio | Garganta picando |

**El satélite ve lo mismo. La diferencia la sabes solo con BLH.** Por eso ningún modelo serio de calidad del aire en superficie puede prescindir de la BLH.

## Valores típicos en Cali (estimados con ERA5)

| Momento | BLH típica |
|---|---|
| Madrugada (3 AM, valle frío) | 100 – 300 m |
| Amanecer (6 AM) | 200 – 500 m |
| Media mañana (9 AM) | 500 – 1200 m |
| Mediodía (12 PM, día soleado) | 1500 – 2500 m |
| Tarde (3 PM) | 1500 – 2200 m |
| Atardecer (6 PM) | 500 – 1000 m |
| Noche estable (10 PM) | 150 – 400 m |

## Limitaciones de ERA5-BLH a 27.8 km

ERA5 da BLH sobre una grilla de 0.25° → un solo valor representa ~775 km² alrededor de Cali. Pero:

- BLH sobre el río Cauca puede ser distinta a BLH sobre la ladera de los Farallones.
- BLH urbana (efecto isla de calor) puede ser 30-50 % mayor que rural.
- ERA5 no resuelve estas heterogeneidades.

El modelo del proyecto **debería aprender** a corregir esa BLH gruesa usando las imágenes Sentinel-2 (que sí ven la diferencia urbana/rural a 10 m). Este es uno de los aportes que el approach CLIP+SAE puede dar respecto a métodos tradicionales.

## Lecturas

- Stull, R. (1988). *An Introduction to Boundary Layer Meteorology* — Springer. El libro de referencia.
- [Seidel et al. (2010) — Climatology of the planetary boundary layer](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2009JD013680) — climatología global.
- [ERA5 documentation — Boundary Layer Height](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation) — fórmula exacta usada por ECMWF.
- [Garratt (1992). *The Atmospheric Boundary Layer* — Internet Archive](https://archive.org/details/atmosphericbound0000garr) — Cambridge University Press, técnico.
- [Influence of atmospheric boundary-layer dynamics on air quality of Colombian cities (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S2352938526000078) — estudio reciente sobre BL urbana en valles colombianos.

## Próximos conceptos

- [`humedad-temperatura-viento.md`](humedad-temperatura-viento.md) — el resto de la meteorología que importa.
- [`contaminante-no2.md`](contaminante-no2.md) — donde se usa la fórmula `c = C/BLH`.
- [`reanalisis-era5.md`](reanalisis-era5.md) — qué es un reanálisis y por qué BLH es "diagnóstica" no observada.
