# Bandas espectrales e índices (NDVI y otros)

## Por qué los satélites tienen "bandas"

La luz no es una sola cosa: es un **continuo de longitudes de onda** (frecuencias). Lo que llamamos "rojo", "azul", "infrarrojo" son rangos del espectro electromagnético.

```
       VISIBLE                             INFRARROJO
   ┌───────────────┐  ┌──────────────────────────────────────┐
   │ Azul Verde Rojo│  │  NIR cercano   │   SWIR (ondas cortas)│
   ────────────────────────────────────────────────────────────►
   400        700  nm                  1000           2500   nm
   
   ↑ ojo humano ↑    ↑ ojo humano NO ve ↑
```

Un **detector multispectral** divide la luz que recibe en **canales** o **bandas**, cada uno sensible a un rango específico. Cada banda revela algo distinto del paisaje:

- Rojo (~665 nm): la clorofila absorbe → vegetación viva se ve **oscura**.
- NIR (~833 nm): la clorofila refleja → vegetación viva se ve **brillante**.
- SWIR (~1610 nm): el agua absorbe → suelo seco vs húmedo distinguible.

Sentinel-2 tiene **13 bandas útiles** del azul al SWIR. Eso es lo que el proyecto extrae para cada escena (ver [`DATASETS.md`](../DATASETS.md#1-sentinel-2-msi-l2a-surface-reflectance-harmonized)).

## Las 13 bandas Sentinel-2 que usamos

| Banda | λ central | Resolución nativa | Para qué sirve |
|---|---|---|---|
| B1 | 443 nm | 60 m | Aerosol coastal — corrección atmosférica |
| B2 | 492 nm | 10 m | Azul — penetra agua, ciudades |
| B3 | 560 nm | 10 m | Verde — vegetación sana |
| B4 | 665 nm | 10 m | Rojo — clorofila |
| B5 | 704 nm | 20 m | Red Edge 1 |
| B6 | 740 nm | 20 m | Red Edge 2 — estrés vegetal |
| B7 | 783 nm | 20 m | Red Edge 3 |
| B8 | 833 nm | 10 m | NIR — vegetación, biomasa |
| B8A | 865 nm | 20 m | NIR estrecho |
| B9 | 945 nm | 60 m | Vapor de agua |
| B11 | 1610 nm | 20 m | SWIR 1 — humedad del suelo |
| B12 | 2190 nm | 20 m | SWIR 2 — minerales, agua |
| SCL | — | 20 m | Clasificación de escena (nubes, agua, vegetación) |

## El truco de las bandas Red Edge

Sentinel-2 tiene **3 bandas en el "borde rojo"** (B5, B6, B7), una característica única. ¿Por qué?

La clorofila tiene un salto brusco de absorción↔reflexión entre 700 y 760 nm:

```
Reflectancia
   0.5 ┤                     ╱──────  vegetación sana
       │                    ╱
   0.4 ┤                   ╱      
       │                  ╱        ← cambio enorme en 60 nm
   0.3 ┤                 ╱            (rojo → NIR)
       │                ╱       
   0.2 ┤               ╱        
       │              ╱        
   0.1 ┤  ─────────  ╱          
       │            
       └────┬────┬────┬────┬────
           600  700  800  900    λ (nm)
                B4   B5 B6 B7  B8
```

Las 3 bandas red edge **muestrean ese salto a distintas alturas**, lo que permite detectar:
- Estrés hídrico (la curva se aplana antes).
- Senescencia (la curva se desplaza).
- Tipos de cultivo (cada uno tiene una firma distinta).

Para el proyecto, esto es información de **uso de suelo** que el CLIP puede asociar a patrones de emisión: vegetación densa = no industrial; suelo desnudo = construcción/zona industrial.

## Índices espectrales: combinaciones útiles de bandas

Un **índice** es una operación aritmética entre 2 o más bandas que resalta una característica específica. El más famoso:

### NDVI — Normalized Difference Vegetation Index

$$
\text{NDVI} = \frac{\text{NIR} - \text{Rojo}}{\text{NIR} + \text{Rojo}} = \frac{B8 - B4}{B8 + B4}
$$

NDVI ∈ [-1, +1]. Interpretación:

| NDVI | Cobertura |
|---|---|
| -1 a 0 | Agua, nubes, sombras |
| 0 a 0.2 | Suelo desnudo, urbano denso |
| 0.2 a 0.4 | Pasto ralo, área construida con árboles |
| 0.4 a 0.6 | Cultivo, pasto sano |
| 0.6 a 0.85 | Bosque denso, caña de azúcar madura |
| > 0.85 | Selva tropical primaria |

### Ejemplo numérico con valores típicos del BBox del proyecto

Píxel sobre el bosque de los Farallones:

```
B4 = 0.04   (reflectancia roja, baja porque clorofila absorbe)
B8 = 0.55   (reflectancia NIR, alta porque clorofila refleja)

NDVI = (0.55 - 0.04) / (0.55 + 0.04)
     = 0.51 / 0.59
     ≈ 0.86         → vegetación primaria
```

Píxel sobre el centro de Cali (zona urbana densa):

```
B4 = 0.18   (concreto, asfalto reflejan más rojo)
B8 = 0.22   (poca clorofila → poca reflectancia NIR)

NDVI = (0.22 - 0.18) / (0.22 + 0.18)
     = 0.04 / 0.40
     = 0.10          → urbano denso
```

Píxel sobre el río Cauca:

```
B4 = 0.05   
B8 = 0.03   (agua absorbe NIR fuertemente)

NDVI = (0.03 - 0.05) / (0.03 + 0.05)
     = -0.02 / 0.08
     ≈ -0.25         → agua
```

Para el proyecto, NDVI sirve como **proxy del tipo de cobertura** que el modelo CLIP aprende a asociar con concentraciones de NO₂/SO₂/O₃. Zona urbana → más tráfico → más NO₂.

## Otros índices útiles para calidad del aire urbano

### NDBI — Normalized Difference Built-up Index

$$
\text{NDBI} = \frac{\text{SWIR}_1 - \text{NIR}}{\text{SWIR}_1 + \text{NIR}} = \frac{B11 - B8}{B11 + B8}
$$

Resalta áreas construidas (concreto, asfalto). NDBI alto → zona urbana → fuente de tráfico.

### NDWI — Normalized Difference Water Index

$$
\text{NDWI} = \frac{B3 - B8}{B3 + B8}
$$

Detecta cuerpos de agua (NDWI > 0). Útil para enmascarar el río Cauca y reservorios.

### BSI — Bare Soil Index

$$
\text{BSI} = \frac{(B11 + B4) - (B8 + B2)}{(B11 + B4) + (B8 + B2)}
$$

Resalta suelo desnudo (construcción, agricultura sin cosecha). Posible fuente de PM₁₀ por resuspensión.

## La banda SCL — Scene Classification Layer

SCL no es una banda espectral pura, es una **máscara categórica** entregada por el procesador L2A de ESA. Cada píxel tiene un código:

| Valor | Categoría |
|---|---|
| 0 | No data |
| 1 | Saturated/defective |
| 2 | Dark area pixels |
| 3 | Cloud shadows |
| 4 | Vegetation |
| 5 | Bare soils |
| 6 | Water |
| 7 | Unclassified |
| 8 | Cloud medium probability |
| 9 | Cloud high probability |
| 10 | Thin cirrus |
| 11 | Snow / ice |

Para el proyecto, SCL permite:

- Filtrar píxeles nublados (SCL ∈ {3, 8, 9, 10}) para entrenamiento.
- Construir máscaras de validación.
- Dar al modelo CLIP una **capa de contexto** que indique condiciones de captura.

## Cómo el modelo del proyecto usa las bandas

En la Situación 2, el encoder visual ViT-B/32 de RemoteCLIP recibe **un tensor 13×64×64**:

```
input ViT  = [B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12, SCL]
              ↓ embedding 512-dim
              ↓
        Sparse Autoencoder
              ↓ embedding 256-dim interpretable
              ↓
        Proyección al espacio contrastivo
```

El modelo aprende que combinaciones específicas de bandas predicen concentraciones. Por ejemplo: **NDVI bajo + NDBI alto + SCL = "Bare soils"** → patrón de zona industrial → asociado con columna alta de SO₂ por TROPOMI.

## Bandas vs imágenes RGB típicas

Una foto normal usa **3 bandas** (R, G, B) que aproximan lo que ve el ojo humano. Un satélite multiespectral usa **decenas de bandas** porque **el ojo se pierde mucha información**:

- Las plantas tienen colores que el ojo no ve (NIR, red edge).
- Los minerales tienen firmas SWIR únicas.
- El vapor de agua absorbe en bandas específicas.

**El proyecto no es procesamiento de imágenes normales — es análisis espectral. La "imagen" S2 es un tensor 13D, no RGB.**

## Lecturas

- [Sentinel-2 User Handbook (ESA)](https://sentinel.esa.int/documents/247904/685211/Sentinel-2_User_Handbook) — diseño de cada banda.
- [USGS Spectral Indices Guide](https://www.usgs.gov/landsat-missions/landsat-surface-reflectance-derived-spectral-indices) — fórmulas oficiales de NDVI, NDBI, NDWI, NDMI, etc.
- Rouse, J. W. et al. (1973). *Monitoring vegetation systems in the Great Plains with ERTS* — paper original de NDVI.
- [Sentinel-2 SCL documentation](https://sentiwiki.copernicus.eu/web/s2-mission#S2Mission-Scene-Classification) — la clasificación de escena.
- Roy, D. P. et al. (2016). *Characterization of Landsat-7 to Landsat-8 reflective wavelength and normalized difference vegetation index continuity* — RemSens of Env — cuidados al comparar NDVI entre sensores.
- [Liu et al. (2024) — RemoteCLIP](https://ieeexplore.ieee.org/document/10504785) — el modelo CLIP que el proyecto fine-tunea.

## Próximos conceptos

- [`resolucion-espacial.md`](resolucion-espacial.md) — por qué B1 está a 60 m y B4 a 10 m.
- [`material-particulado-aod.md`](material-particulado-aod.md) — bandas usadas por MODIS MAIAC.
- [`niveles-l1-l2-l3.md`](niveles-l1-l2-l3.md) — por qué descargamos L2A y no L1C.
