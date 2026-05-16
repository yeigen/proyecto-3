# Niveles de procesamiento: L0, L1, L2, L3, L4

## La idea fundamental

Los datos satelitales no llegan "limpios" desde el satélite. Pasan por una **cadena de procesamiento** que la NASA estandarizó en **niveles numerados**. Cuanto más alto el número, más procesado (y más usable directamente).

| Nivel | Qué es | Ejemplo |
|---|---|---|
| **L0** | Bits crudos del telemetría descargada | Voltajes del detector, no usable |
| **L1A** | Convertido a unidades físicas, sin calibrar | Reconstrucción del raw |
| **L1B** | Calibrado radiométricamente | Radiancia en W/(m²·sr·nm) |
| **L1C** | Reproyectado y georreferenciado | Reflectancia en la **cima de la atmósfera** (TOA) |
| **L2** | Corregido atmosféricamente + variables geofísicas | NO₂ en mol/m², reflectancia de **superficie** |
| **L3** | Re-grillado a una grilla regular regular | NO₂ en grilla 0.01°×0.01° |
| **L4** | Análisis estadístico, modelado, fusión | Promedios mensuales, asimilación a modelos |

## Por qué importa entender los niveles

Cada nivel cambia **qué significa el número del píxel**:

- L1B de Sentinel-2: número de fotones que llegan al sensor.
- L1C: reflectancia en la cima de la atmósfera (afectada por aerosoles, vapor de agua).
- L2A: reflectancia **de la superficie** (los efectos atmosféricos ya están removidos).
- L3 promedio: media de varios L2A.

Para el proyecto, **L2 es el sweet spot** en la mayoría de fuentes: ya tiene variables físicas interpretables, pero conserva la resolución original.

## Niveles por fuente del proyecto

### Sentinel-2: usamos L2A

`COPERNICUS/S2_SR_HARMONIZED` = Sentinel-2 Surface Reflectance, Level 2A, harmonizado.

- **L1C**: reflectancia TOA (top-of-atmosphere). Veríamos las nubes y el vapor de agua "encima" del paisaje.
- **L2A**: reflectancia **de la superficie**, tras correr el procesador Sen2Cor que estima y remueve la dispersión por aerosoles, vapor de agua, y ozono. Esto es lo que queremos: la "verdadera" reflectancia del suelo.
- "Harmonized" significa: ESA cambió en 2022 el offset numérico de los datos crudos (de 0 a -1000); la versión harmonizada **re-suma 1000** para que series temporales pre-2022 y post-2022 sean comparables.

### Sentinel-5P: usamos L3, no L2

`COPERNICUS/S5P/OFFL/L3_NO2` (y SO₂, O₃)

- **L1B**: radiancias TOA crudas.
- **L2**: columnas geofísicas (mol/m²) recuperadas con DOAS, en grilla **irregular** de paralelogramos 3.5×5.5 km.
- **L3**: las L2 reproyectadas a una **grilla regular** de 0.01° (~1113 m) con `harpconvert bin_spatial`.

> El PDF pide que nosotros corramos HARP sobre L2. Pero GEE ya nos entrega el L3 pre-procesado, equivalente al output de HARP. Esto está justificado en [`JUSTIFICACIONES.md`](../JUSTIFICACIONES.md#decisiones-técnicas-adicionales).

### MODIS MAIAC: usamos L2G

`MODIS/061/MCD19A2_GRANULES`

- "MCD" significa "MODIS Combined" (Terra + Aqua).
- "MAIAC" es el algoritmo (Multi-Angle Implementation of Atmospheric Correction).
- "L2G" es L2 reproyectado a grilla, pero conservando la naturaleza de swath (no es L3 daily).
- "GRANULES" significa que **cada archivo es un swath individual**, no un mosaico diario.

### ERA5: no aplica niveles tradicionales

ERA5 no es un sensor — es un **reanálisis** (modelo + asimilación de observaciones). No hay L0/L1/L2 en el sentido satelital. Lo más cercano a L4. Ver [`reanalisis-era5.md`](reanalisis-era5.md).

## El procesamiento atmosférico de Sentinel-2 L2A

Esto es el corazón del paso de L1C → L2A. Es lo que Sen2Cor hace:

```
Reflectancia TOA (L1C)  = Reflectancia atmósfera + Reflectancia superficie  
                          ───────────  reemovida   ─────────────
                                 ↓ con AOD del propio S2 (cumming Eq)
                                 ↓ con vapor de agua (B9)
                                 ↓ con ozono climatológico
Reflectancia superficie (L2A)
```

### Bandas auxiliares para corrección atmosférica

Algunas bandas de S2 **no son para vegetación** — son para la corrección atmosférica:

- **B1 (443 nm, aerosol)**: detecta aerosoles ópticamente activos.
- **B9 (945 nm, vapor de agua)**: cuantifica vapor de agua para corregir su absorción.
- **B10 (1375 nm, cirrus)**: detecta cirrus de hielo, **B10 no existe en L2A** porque ya se usó para corregir y fue removida.

Por eso S2 L2A tiene **13 bandas** (no 14): B10 desaparece tras la corrección.

## OFFL vs NRTI en Sentinel-5P

Sentinel-5P entrega dos versiones del mismo producto L2:

| Suffix | Latencia | Calidad | Uso |
|---|---|---|---|
| **NRTI** | 3 horas | Provisional | Tiempo real (alertas) |
| **OFFL** | 5 días | Estándar | Investigación |
| **RPRO** | meses | Reprocesado | Series climáticas |

El proyecto usa **OFFL** (`COPERNICUS/S5P/OFFL/L3_*`). RPRO sería ideal para una análisis científico cerrado pero la latencia es prohibitiva. NRTI es para sistemas de respuesta rápida que no es nuestro caso.

## Por qué saltamos HARP

El PDF dice: *"Aplicar recorte HARP sobre los granules L2 de Sentinel-5P para reducir a la huella metropolitana de Cali (use harpconvert con bin_spatial sobre BBox −76.60, 3.30, −76.40, 3.55)."*

Lo que HARP hace:

1. Lee el granule L2 (~3 GB cada uno, paralelogramos 3.5×5.5 km).
2. Filtra por BBox.
3. Reproyecta a grilla regular.
4. Aplica filtros de calidad.

**El asset `COPERNICUS/S5P/OFFL/L3_NO2` de GEE ya es el resultado de hacer exactamente eso pero a escala global.** Nosotros descargamos solo los píxeles que caen en nuestro BBox.

> Equivalencia operativa: `harpconvert(L2, bbox=cali, bin_spatial=0.01)` ≈ filtrar L3 al BBox de Cali. La única ganancia de hacer HARP manual sería elegir filtros de calidad más estrictos (qa_value > 0.75) que GEE aplica por default.

## Niveles y la pirámide de datos

Una forma de pensarlo:

```
                    L4 (modelos, fusión)         ← análisis
                   ▲   ↑      
                   │   │ reduce variabilidad
                   │   │ 
                  L3 (grillas regulares)         ← lo que descargamos para S5P
                   ▲   ↑                            (~25K archivos pequeños)
                   │   │ reproyecta
                   │   │
                  L2 (variables físicas)         ← lo que descargamos para S2, MAIAC
                   ▲   ↑                            (lo más cercano a "verdad física")
                   │   │ corrige atmósfera
                   │   │
                  L1C (TOA georreferenciado)
                   ▲
                   │ calibra radiometría
                   │
                  L0 (telemetría cruda)          ← satélite
```

El proyecto opera en **L2/L3**, que es lo apropiado para análisis. Subir a L4 sería integrar datos en un modelo de transporte químico (CMAQ, WRF-Chem) — fuera del alcance.

## Lecturas

- [NASA Earthdata — Data Processing Levels](https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-information-policy/data-levels) — la definición oficial L0-L4.
- [Sen2Cor algorithm (ESA STEP)](https://step.esa.int/main/snap-supported-plugins/sen2cor/) — procesador L1C → L2A de Sentinel-2.
- [HARP documentation (S&T)](http://stcorp.github.io/harp/doc/html/index.html) — `harpconvert` y `bin_spatial`.
- [S5P Documents — SentiWiki](https://sentiwiki.copernicus.eu/web/s5p-documents) — diferencia OFFL/NRTI/RPRO y manuales por producto.
- [MODIS MAIAC ATBD (LP DAAC)](https://lpdaac.usgs.gov/documents/111/MCD19_ATBD.pdf) — niveles L2G del producto MCD19A2.

## Próximos conceptos

- [`columnas-troposfericas-doas.md`](columnas-troposfericas-doas.md) — qué hace exactamente DOAS para producir L2.
- [`reanalisis-era5.md`](reanalisis-era5.md) — el caso especial de ERA5.
- [`bandas-espectrales-ndvi.md`](bandas-espectrales-ndvi.md) — qué son las bandas a las que se aplica corrección atmosférica.
