# Resolución espacial — por qué unas imágenes se ven nítidas y otras pixeladas

## La idea fundamental

**La resolución espacial es el tamaño físico (en metros) que representa un solo píxel en la Tierra.**

Una imagen no es "alta o baja resolución" en abstracto. Es que cada píxel cubre 10 metros, o 1113 metros, o 27,830 metros. Si un píxel cubre mucho terreno, ves cuadrotes y no detalles. Si cubre poco, ves casas individuales.

```
1 píxel de Sentinel-2 = cuadrado de 10 m × 10 m del suelo
                         ────────────
                         tu auto cabe

1 píxel de Sentinel-5P L3 = cuadrado de 1113 m × 1113 m
                            ─────────────────
                            un barrio entero (40 manzanas)

1 píxel de ERA5 = cuadrado de 27,830 m × 27,830 m
                  ──────────────────────
                  toda Cali cabe adentro
```

## Comparación lado a lado de las 6 fuentes del proyecto

Tomamos el BBox **efectivo** del Zarr del proyecto (~39 × 39 km, declarado en `google-earth/config.py` y ampliado por buffer durante la descarga) y vemos cuántos píxeles caben. Las cifras de "píxeles que cubren Cali" se leyeron directamente de los `panel.zarr` cargados con `xarray`:

| Fuente | Resolución por píxel | Píxeles del Zarr | Cómo se ve |
|---|---|---:|---|
| **Sentinel-2** | 10 m | 3,897 × 3,897 = **15.2 M** | Nítido, casas individuales |
| **MODIS MAIAC** | ~1 km | ~40 × 40 ≈ 1,600 | Pixelado, barrios visibles |
| **Sentinel-5P L3** | 1,113 m | ~36 × 35 ≈ 1,260 | Pixelado, distritos visibles |
| **Sentinel-5P L2 nativo** | 3,500 × 5,500 m | ~11 × 7 ≈ 77 | Muy pixelado, ciudad como puñado de cuadros |
| **ERA5** | 27,830 m (0.25°) | 2 × 2 = 4 | Cali entera en un puñado de píxeles |

> Conteos exactos de cada fuente: ver bloque 2 del notebook `scripts/eda/eda_completo.py` (`inspeccionar_dataset(ds, ...)` imprime `dim {y, x}` por fuente).

> Pasar de Sentinel-2 a ERA5 es como pasar de Google Maps en zoom máximo a la silueta de Colombia en un mapa mundial. **No es peor calidad: es otra escala de fenómeno**.

## Por qué hay distintas resoluciones

No es que "los satélites caros tengan más resolución". Cada misión optimiza una variable distinta:

| Sensor | Optimizó para | Costo de optimizar | Resultado |
|---|---|---|---|
| Sentinel-2 (MSI) | Detalle espacial 10 m | Revisita lenta (5 días) | Casas sí, gas no |
| Sentinel-5P (TROPOMI) | Sensibilidad química (ver columnas de gases trazas) | Spectro grande → píxel grande | Gas sí, casas no |
| MODIS MAIAC | Cobertura global diaria | 1 km, polar orbit | Aerosoles globales diarios |
| ERA5 | Cobertura global horaria con asimilación de modelo | 0.25°, modelo físico | Meteorología consistente |

**Trade-off físico real**: para detectar una columna de NO₂ a través de un cielo nublado parcialmente, TROPOMI necesita capturar fotones de un área grande por un tiempo razonable. No es que el ingeniero haya querido píxeles grandes — el detector espectroscópico tendría señal-ruido inservible con píxeles de 10 m.

## El problema del re-grillado L3

Sentinel-5P nativo (L2) tiene píxeles de **3.5 × 5.5 km** en forma de **paralelogramos** (porque el satélite barre en diagonal). Difícil de combinar con datasets en grilla regular.

El producto **L3** que descargamos via GEE ya está **re-grillado a 0.01° (1113 m)** con `harpconvert bin_spatial`. Eso significa:

```
Asset GEE: COPERNICUS/S5P/OFFL/L3_NO2
Resolución entregada: 1113 m (interpolación de la L2 original de 3.5×5.5 km)
```

**El L3 no inventa información — la redistribuye en una grilla regular**. Si la pixel L2 era de 3.5×5.5 km, el L3 a 1 km vecino del centro hereda valores promediados. Por eso aparecen "manchas" de 4-5 píxeles L3 con el mismo valor: corresponden a un solo píxel L2 redistribuido.

> Esto es lo que el PDF llama "recorte HARP". Nosotros saltamos este paso porque GEE ya lo entrega hecho — ver `JUSTIFICACIONES.md` para la justificación.

## El caso especial de ERA5 — solo 2×2 píxeles sobre Cali

ERA5 entrega **0.25° × 0.25°** ≈ 27.8 km × 27.8 km. El BBox del proyecto pide `[-76.65, 3.30, -76.30, 3.65]` (0.35° × 0.35°). Eso debería ser ~1.4 × 1.4 píxeles ERA5 — pero **no puedes pedir fracciones de píxel**.

GEE entrega los píxeles **completos** que tocan el BBox, lo que resulta en una matriz **2 × 2 = 4 píxeles**, con cobertura efectiva `[-76.75, 3.25, -76.25, 3.75]` (0.5° × 0.5°). No es un error: es la grilla nativa.

```
                    ERA5 grilla nativa
   3.75 ┤   ┌──────────┬──────────┐
        │   │  px (0,0)│ px (0,1) │   ← 2 píxeles
   3.50 ┤   ├──────────┼──────────┤
        │   │  px (1,0)│ px (1,1) │
   3.25 ┤   └──────────┴──────────┘
        ────────────────────────────
            −76.75    −76.50    −76.25
                  longitud (°)
                  
   Tu BBox del proyecto:    Cali real:
   ────────────             ▓▓▓▓▓
   [-76.65, 3.30,           38×38 km
    -76.30, 3.65]           
```

Esos 4 píxeles sirven para todo Cali. **No es resolución insuficiente — es la realidad de ERA5**. Si quisieras 1 km de meteo necesitarías downscaling con modelo mesoescalar (WRF/HARMONIE), que no es el alcance del proyecto.

## Resampleo a 10 m de todas las bandas de Sentinel-2

Sentinel-2 tiene 3 resoluciones nativas:

- 10 m: B2, B3, B4, B8 (visible + NIR)
- 20 m: B5, B6, B7, B8A, B11, B12, SCL
- 60 m: B1, B9

Pero el proyecto las descarga **todas a 10 m**: `getDownloadURL(scale=10)`. GEE hace el resampleo **server-side** con interpolación bilineal.

### ¿Por qué? Porque ViT-B/32 lo necesita

El encoder visual de Situación 2 espera un tensor `(13, H, W)` con todas las bandas alineadas. Si dejas B9 a 60 m y B4 a 10 m, tendrías que hacer alineación manual (que termina siendo el mismo resampleo bilineal).

### ¿Qué pasa con B9 de 60 m "expandida" a 10 m?

No se inventa información. Lo que era 1 píxel de 60 m se convierte en una grilla **6×6 = 36 píxeles** con valores interpolados:

```
B9 original a 60 m:                B9 resampleado a 10 m:
                                   
┌──────────────┐                   ┌──┬──┬──┬──┬──┬──┐
│              │                   ├──┼──┼──┼──┼──┼──┤
│   pixel      │                   ├──┼──┼──┼──┼──┼──┤
│   (1 valor)  │       ────►       ├──┼──┼──┼──┼──┼──┤
│              │                   ├──┼──┼──┼──┼──┼──┤
│              │                   ├──┼──┼──┼──┼──┼──┤
└──────────────┘                   └──┴──┴──┴──┴──┴──┘
   60×60 m                            10×10 m (36 valores)
   1 valor real                       36 valores interpolados
                                      pero solo 1 dato físico
```

Es replicación inteligente, no creación de información. La práctica es estándar (RemoteCLIP, Prithvi, Satlas hacen lo mismo).

## La intuición visual final

Si tomas una foto de **toda Cali desde el espacio** y la imprimes en una hoja A4:

- **Con Sentinel-2** (10 m): cada manzana sería distinguible. Verías el río Cauca, la avenida Pasoancho.
- **Con MODIS MAIAC** (1 km): cada barrio sería un cuadro de color. Verías "Aguablanca + sur" como 4 cuadros homogéneos.
- **Con Sentinel-5P L3** (1 km): igual que MODIS.
- **Con ERA5** (28 km): toda Cali sería **un solo cuadro** o partido entre 2-4 cuadros. No distinguirías Aguablanca de Pance.

El proyecto **combina las 4 escalas** porque cada una mide un fenómeno distinto:
- Sentinel-2: morfología urbana, vegetación, sombras (escala calle).
- Sentinel-5P: columnas de gases (escala barrio).
- MODIS MAIAC: aerosoles (escala ciudad).
- ERA5: meteorología (escala valle).

## La pregunta inversa: ¿se puede mejorar resolución con software?

**Sí, pero no genera información nueva**. Se llama **downscaling estadístico** o **super-resolution**. La idea: si el modelo aprende patrones entre la información gruesa (S5P 1 km) y la fina (S2 10 m), puede predecir versiones a 10 m del campo grueso usando S2 como guía.

**Eso es exactamente lo que la Situación 2 + 3 del proyecto hacen**:

- CLIP aprende que ciertos patrones espaciales en S2 (autopistas, zonas industriales) se asocian a columnas altas de NO₂.
- ST-Kriging propaga la información puntual de DAGMA a una superficie continua.
- El producto final son mapas a **resolución efectiva ~100-500 m** validados contra ground truth.

Este es el aporte de valor del proyecto: pasar de píxeles de 1 km a estimaciones de barrio.

## Lecturas

- Jensen, J. R. (2015). *Introductory Digital Image Processing: A Remote Sensing Perspective*. — clásico sobre resolución espacial vs espectral vs temporal.
- [NASA Earthdata — Resolution (spatial, spectral, radiometric, temporal)](https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/remote-sensing-resolution) — explicación didáctica oficial.
- [Veefkind et al. (2012) — TROPOMI on the ESA Sentinel-5 Precursor](https://www.sciencedirect.com/science/article/pii/S0034425712000661) — por qué 3.5×5.5 km y no menos.
- [ESA Sentinel-2 User Handbook](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook) — diseño óptico de 10/20/60 m.
- [HARP toolset (S&T)](http://stcorp.github.io/harp/doc/html/index.html) — el reproyectador L2→L3.
- [Liu et al. (2024) — RemoteCLIP](https://ieeexplore.ieee.org/document/10504785) — práctica estándar de resampleo a banda común.

## Próximos conceptos

- [`resolucion-temporal-revisita.md`](resolucion-temporal-revisita.md) — la otra dimensión de "resolución" (tiempo).
- [`bandas-espectrales-ndvi.md`](bandas-espectrales-ndvi.md) — qué son las bandas que tienen distintas resoluciones nativas.
- [`bbox-proyecciones-grillas.md`](bbox-proyecciones-grillas.md) — cómo encajan grillas con BBox.
- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — el "L3" del re-grillado de S5P.
