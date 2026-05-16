# BBox, proyecciones y grillas

## La idea fundamental

La Tierra es una esfera (casi). Los mapas y satélites trabajan con **planos rectangulares**. Cualquier conversión entre los dos introduce **distorsión**. El proyecto necesita combinar 6 fuentes con grillas distintas — entender BBox y proyecciones es la diferencia entre que tus capas se alineen píxel-a-píxel o que tengan offsets aleatorios.

## Coordenadas geográficas: lat / lon

| Coordenada | Rango | Cali |
|---|---|---|
| **Latitud (φ)** | -90° (sur) a +90° (norte) | ~3.4° N |
| **Longitud (λ)** | -180° (oeste) a +180° (este) | ~-76.5° W |

Cali está cerca del **ecuador** (latitud baja) y al **oeste** del meridiano de Greenwich.

## BBox: definición

Un **bounding box** es un rectángulo definido por **4 valores**:

```
BBox = [min_lon, min_lat, max_lon, max_lat]
       [   W     S        E         N  ]
```

El BBox del proyecto:

```
BBox = [-76.65, 3.30, -76.30, 3.65]
       W=-76.65°  E=-76.30°
       S=3.30°    N=3.65°
```

Eso son:

- 0.35° de longitud × 0.35° de latitud
- ~38.9 km × 38.9 km a latitud 3.4° (cerca del ecuador 1° lat ≈ 111 km, 1° lon ≈ 111 × cos(3.4°) ≈ 110.8 km)
- ~1,514 km² (toda Cali + Yumbo + Acopi + cultivos del norte)

```
   N (3.65°) ┌───────────────────────────┐
             │                           │
             │   ▓▓▓▓ Yumbo + Acopi     │
             │   ▓▓▓▓ (refinerías)       │
             │                           │
             │   ░░░░ Cali centro        │
             │   ░░░░ (DAGMA)            │
             │                           │
             │   ▒▒▒▒ Sur Cali           │
             │   ▒▒▒▒ Farallones         │
             │                           │
   S (3.30°) └───────────────────────────┘
            W=-76.65°               E=-76.30°
```

## Proyecciones — por qué la Tierra no cabe en una hoja

Para representar una esfera en un plano, hay que **proyectarla**. Eso siempre distorsiona algo: forma, área, distancia, o ángulo. No hay proyección que conserve todo.

### Las 3 proyecciones que importan en el proyecto

| Proyección | Código EPSG | Usa | Distorsiona |
|---|---|---|---|
| **WGS84 geográfico** | EPSG:4326 | GEE catalogo, ERA5, S5P | Áreas hacia los polos |
| **UTM (Universal Transverse Mercator)** | EPSG:32618 (zona 18N) | Sentinel-2 raw | Mínima dentro de cada zona |
| **Web Mercator** | EPSG:3857 | OpenStreetMap, mapas web | Áreas hacia los polos (drásticamente) |

### EPSG:4326 — el sistema de "grados puros"

Cali en EPSG:4326: `(longitude=-76.5, latitude=3.4)`. Es lo que el ojo entiende: latitud y longitud directas. **No es una proyección plana de verdad** — es el sistema base sobre la elipse WGS84. Casi todo en GEE entrega coordenadas en EPSG:4326.

### EPSG:32618 — UTM zona 18N

Sentinel-2 raw entrega en UTM. Cali está en la **zona UTM 18N**. Coordenadas en metros desde un origen local:

```
WGS84 (3.4°N, -76.5°W)  →  UTM 18N  (≈ 167,000 East, 376,000 North) en metros
```

Ventaja: distancias y áreas en metros sin distorsión apreciable dentro de la zona (las zonas son franjas de 6° de ancho).

### Por qué unas fuentes vienen en UTM y otras en lat/lon

| Fuente | Proyección entregada | ¿Por qué? |
|---|---|---|
| Sentinel-2 L2A | UTM (por tile) | Resolución metro-precisa, baja distorsión |
| Sentinel-5P L3 | EPSG:4326 | Producto global ya regrillado |
| MODIS MAIAC | Sinusoidal MODIS | Diseño histórico NASA |
| ERA5 | EPSG:4326 | Grilla geográfica global |

GEE automáticamente reproyecta a EPSG:4326 cuando descargas con `getDownloadURL(crs='EPSG:4326')`. **El proyecto fuerza EPSG:4326 en todas las descargas** para que el panel combinado sea coherente.

## Grillas regulares vs grillas irregulares

### Grilla regular

Cada píxel tiene **el mismo tamaño** en coordenadas. Ejemplo: ERA5 a 0.25°.

```
Píxel (i, j):  lon = lon_min + j × 0.25
               lat = lat_min + i × 0.25

Todos los píxeles cubren exactamente 0.25° × 0.25°.
```

### Grilla irregular (Sentinel-5P L2 nativo)

TROPOMI escanea con un patrón de paralelogramos diagonales debido a la geometría de la órbita y el detector pushbroom. Píxeles vecinos tienen **distinto tamaño** según el ángulo del satélite.

```
   ╱─╱─╱─╱
  ╱─╱─╱─╱           ← Píxeles L2 nativos de TROPOMI
 ╱─╱─╱─╱              (paralelogramos, ~3.5×5.5 km)
╱─╱─╱─╱
```

**Por eso necesitamos L3**: reproyecta de paralelogramos a una grilla cartesiana regular (~1113 m). El producto GEE `COPERNICUS/S5P/OFFL/L3_*` ya hace esto con `harpconvert bin_spatial`.

## Por qué el BBox no encaja en la grilla — el caso ERA5

Cuando pides un BBox `[-76.65, 3.30, -76.30, 3.65]` a un dataset con grilla de 0.25° (ERA5), pasa algo importante:

```
                        Grilla ERA5 nativa
   3.75 ┤   ┌──────────┬──────────┐
        │   │ (0,0)    │ (0,1)    │
        │   │          │          │
   3.50 ┤   ├──────────┼──────────┤
        │   │ (1,0)    │ (1,1)    │
        │   │          │          │
   3.25 ┤   └──────────┴──────────┘
        ────────────────────────────
            −76.75    −76.50    −76.25
                  longitud (°)
```

Mi BBox `[−76.65, 3.30, −76.30, 3.65]` cae **a mitad de píxeles**. GEE no puede entregar fracciones de píxel, entonces entrega los **4 píxeles completos que tocan el BBox**:

```
BBox solicitado:       [-76.65, 3.30, -76.30, 3.65]   (0.35° × 0.35°)
BBox real entregado:   [-76.75, 3.25, -76.25, 3.75]   (0.5° × 0.5°)
Shape:                 (2, 2)                          (sobreestima por overshoot)
```

**Esto no es un bug** — es la realidad de la grilla. Aplica también a S5P pero menos visible porque su grilla es de 0.01° (1 km) y el BBox cabe en ~36 × 35 píxeles.

## La excepción de Sentinel-2 — tiles MGRS

Sentinel-2 no tiene una grilla global única. Está organizado en **tiles MGRS** (Military Grid Reference System): cuadrículas UTM de 100 × 100 km nombradas con un código.

El BBox del proyecto está cubierto por **3 tiles**:

| Tile | Ubicación |
|---|---|
| T18NUH | Oeste (parte) |
| T18NUJ | Centro (Cali) |
| T18NUK | Este (Yumbo + cultivos) |

Cuando descargas S2 sobre el BBox, GEE intersecta los tiles y mosaica. El conteo de 1,552 escenas surge de:

```
~516 escenas/tile × 3 tiles ≈ 1,548 (más algunas escenas mosaico) ≈ 1,552
```

## La proyección final del panel: EPSG:4326

Para que las 6 fuentes se alineen en el Zarr, el proyecto **reproyecta todo a EPSG:4326 a 10 m** (en el caso de S2) o **conserva resoluciones nativas** (en el caso de las demás). El BBox se aplica al final, recortando lo que sobra.

Las coordenadas del Zarr S2:

```
y ∈ [3.30005, 3.65003]   3,897 píxeles (~10 m c/u)
x ∈ [-76.65001, -76.30003]  3,897 píxeles (~10 m c/u)
```

Verificado bit-perfect contra los GeoTIFFs raw (ver [`JUSTIFICACIONES.md`](../JUSTIFICACIONES.md#coherencia-lossless-geotiff--zarr)).

## El truco de las coordenadas Y invertidas

Los GeoTIFFs (incluyendo los de GEE) siguen la convención **GDAL**: el origen del raster está arriba-izquierda, y `dy` es **negativo** (Y crece hacia el sur en notación array, hacia el norte en notación geográfica).

```python
y = np.arange(y_max, y_max + H * dy, dy)   # dy < 0
# Resultado: y[0] > y[-1]
# y[0] = 3.65003 (norte)
# y[-1] = 3.30005 (sur)
```

Xarray maneja esto transparentemente con `.sel(y=valor, method='nearest')`. Pero si trabajas con los arrays NumPy directos, recuerda que la primera fila es el **norte**, no el sur.

## EPSG:3857 (Web Mercator) — para visualización web del frontend de Situación 3

El frontend Leaflet del PDF usa Web Mercator (porque OpenStreetMap, Google Maps usan EPSG:3857). La conversión EPSG:4326 → EPSG:3857 introduce **distorsión hacia los polos**:

```
WebMercator(lat, lon) = (R · π/180 · lon, R · ln(tan(π/4 + lat/2 · π/180)))
```

donde `R = 6378137` (radio ecuatorial).

Pero esto **no afecta a Cali** apreciablemente porque está cerca del ecuador (la distorsión Mercator escala como `1/cos(lat)` ≈ 1.002 a 3.4°). Para visualizar mapas de NO₂ sobre Cali en Leaflet, no hay que preocuparse.

## Lecturas

- [EPSG.io — catálogo de proyecciones](https://epsg.io/) — busca 4326, 3857, 32618 para ver sus parámetros.
- [GDAL — Coordinate Reference Systems](https://gdal.org/tutorials/osr_api_tut.html) — guía técnica.
- [Earth Engine — Projections and Reprojection](https://developers.google.com/earth-engine/guides/projections) — cómo GEE maneja CRS.
- [S2 Products — SentiWiki Copernicus](https://sentiwiki.copernicus.eu/web/s2-products) — formato MGRS y productos de Sentinel-2.
- [Snyder, J. P. (1987). *Map Projections — A Working Manual*. USGS](https://pubs.usgs.gov/publication/pp1395) — clásico libre, todas las proyecciones explicadas.
- [Tissot's Indicatrix](https://en.wikipedia.org/wiki/Tissot%27s_indicatrix) — cómo visualizar la distorsión de una proyección.

## Próximos conceptos

- [`resolucion-espacial.md`](resolucion-espacial.md) — por qué ERA5 entrega 2×2 píxeles aunque pidas más.
- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — el paso L2→L3 que regulariza la grilla de S5P.
- [`resolucion-temporal-revisita.md`](resolucion-temporal-revisita.md) — la otra dimensión de la grilla.
