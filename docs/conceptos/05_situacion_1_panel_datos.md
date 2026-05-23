# 05. Situación 1: panel de datos, notebooks y auditoría

Este documento conecta la Situación 1 del PDF con lo que realmente hay en el proyecto: datos, notebooks, salidas, código, fórmulas y validaciones.

La idea es poder defender no solo “tenemos datos”, sino:

> qué datos hay, cómo se organizaron, qué salidas los prueban y qué cuidado matemático/estadístico hay detrás.

## 1. Qué pedía el PDF

La Situación 1 pedía construir un panel espacio-temporal de mínimo 50 GB con datos de Cali y su área metropolitana, incluyendo:

| Fuente pedida | Rol esperado |
|---|---|
| Sentinel-5P | columnas de NO₂, SO₂ y O₃ |
| Sentinel-2 | covariables ópticas de alta resolución |
| ERA5-Land / ERA5 | meteorología |
| MODIS MAIAC | AOD como proxy de aerosoles |
| DAGMA / SISAIRE | mediciones reales en estaciones |

También pedía:

- procesamiento distribuido o paralelizado;
- formato Zarr o Parquet particionado;
- almacenamiento en cloud;
- manifest con rutas, hashes, dimensiones, fechas, fuente y BBox;
- EDA con visualizaciones de cobertura, series y píxeles válidos.

## 2. Qué hizo el proyecto

El proyecto construyó un panel longitudinal multi-fuente para Cali + Yumbo + Acopi.

| Elemento | Resultado |
|---|---|
| BBox operativo | `[-76.65, 3.30, -76.30, 3.65]` |
| Periodo satelital | 2021-2025 |
| Ground truth DAGMA/CVC | 2020-2024 |
| Dataset Kaggle | 89.73 GB |
| Archivos Kaggle UI | 8,848 |
| Archivos manifest técnico | 8,847 |
| Fuentes principales | 6 paneles Zarr + DAGMA/CVC |

El BBox del proyecto es más grande que el del PDF porque incluye Yumbo, Acopi y parte de la zona cañera norte. Esta decisión es defendible porque Yumbo es clave para NO₂/SO₂ industrial y además es la única estación con NO₂ en el parquet principal.

## 3. Notebooks revisados

Para esta auditoría se revisaron salidas de estos notebooks:

| Notebook | Rol |
|---|---|
| `EDA.ipynb` | EDA general inicial, carga de fuentes desde Hugging Face, visualizaciones obligatorias. |
| `notebooks/eda/geovision-clip-eda-completo.ipynb` | EDA completo en Kaggle, revisión de S2, S5P, ERA5, MODIS, DAGMA y tiles. |
| `manifest/manifest.ipynb` | Generación del manifest técnico del dataset. |
| `notebooks/dagma/dagma-analisis-cruzado.ipynb` | Revisión cruzada entre parquet DAGMA/CVC y Excel complementario. |

No todos los notebooks cumplen el mismo rol. Algunos son de diagnóstico y otros producen evidencia final.

## 4. Estructura del panel Zarr

El panel usa Zarr porque las fuentes son arreglos multidimensionales.

Forma típica:

$$
(time, band, y, x)
$$

Donde:

| Dimensión | Significado |
|---|---|
| `time` | fecha o timestamp de la observación |
| `band` | variable o banda espectral |
| `y` | eje espacial vertical |
| `x` | eje espacial horizontal |

Zarr es apropiado porque permite guardar arrays grandes por chunks comprimidos. La documentación de Zarr confirma que está diseñado para arrays N-dimensionales comprimidos y particionados en chunks, con soporte para disco y almacenamiento cloud.

## 5. Shapes verificados por notebooks

Los notebooks reportan estas dimensiones:

| Fuente | Shape Zarr | Lectura |
|---|---:|---|
| Sentinel-2 | `(1552, 13, 3897, 3897)` | 1552 escenas, 13 bandas, grilla fina de ~10 m. |
| S5P NO₂ | `(25592, 3, 36, 36)` | muchas órbitas/escenas, 3 bandas. |
| S5P SO₂ | `(25829, 2, 36, 36)` | columna SO₂ + nubosidad. |
| S5P O₃ | `(25716, 2, 36, 36)` | columna total O₃ + nubosidad. |
| ERA5 | `(43824, 8, 2, 2)` | datos horarios, 8 variables, grilla gruesa. |
| MODIS MAIAC | `(1826, 4, 43, 43)` | diario, AOD/vapor de agua, ~1 km. |
| DAGMA/CVC | `(107291, 14)` | mediciones puntuales horarias. |

Estas salidas aparecen en `EDA.ipynb`, `geovision-clip-eda-completo.ipynb` y `manifest.ipynb`.

## 6. Sentinel-2: código, fórmula y salidas

### Qué se usa

Sentinel-2 aporta 13 bandas:

```text
B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12, SCL
```

La salida del notebook confirma:

```text
Dimensiones: {'time': 1552, 'band': 13, 'y': 3897, 'x': 3897}
```

### Fórmula revisada: NDVI

El código calcula NDVI usando rojo e infrarrojo cercano:

$$
NDVI = \frac{B8 - B4}{B8 + B4}
$$

El notebook `geovision-clip-eda-completo.ipynb` aplica filtro antes de interpretar NDVI:

```text
SCL ∈ {4,5,6,7} y B4 > 0 y B8 > 0
```

Auditoría:

- correcto: evita que NoData/nubes inflen el histograma;
- correcto: usa B8 como NIR y B4 como rojo;
- correcto: conecta con clases de Sit 2 (`vegetacion_densa`, `suelo_urbano`).

### Salidas importantes

| Salida | Resultado |
|---|---|
| escenas totales | 1552 |
| escenas con SCL ≥ 30% | 136 |
| tasa útil | 8.8% |
| NDVI | distribución bimodal: urbano bajo, vegetación alta |
| tile dominante | `T18NUJ` |

Evidencias:

- `docs/situacion-1/evidencias/eda/sentinel-2/s2_ndvi_distribucion.png`
- `docs/situacion-1/evidencias/eda/sentinel-2/s2_scl_distribucion_mensual.png`
- `docs/situacion-1/evidencias/eda/sentinel-2/s2_rgb_top12.png`

## 7. Sentinel-5P: código, bandas y unidades

### Qué se usa

| Contaminante | Banda principal | Unidad |
|---|---|---|
| NO₂ | `tropospheric_NO2_column_number_density` | `mol/m²` |
| SO₂ | `SO2_column_number_density` | `mol/m²` |
| O₃ | `O3_column_number_density` | `mol/m²` |
| Calidad | `cloud_fraction` | 0 a 1 |

La documentación de Earth Engine revisada vía Context7 confirma estas unidades para Sentinel-5P y `cloud_fraction` como fracción.

### Auditoría de código

En `EDA_HALLAZGOS.md` se documenta un bug importante:

```text
list(ds.data_vars)[0] tomaba el contenedor data sin seleccionar banda.
```

Eso mezclaba contaminante con `cloud_fraction` y podía producir distribuciones engañosas.

Fix correcto:

```text
usar .sel(band=...) con la banda explícita por contaminante
```

Auditoría:

- correcto: seleccionar banda explícita es necesario;
- correcto: evita confundir `cloud_fraction` con columna de gas;
- importante para defensa: las unidades `mol/m²` no son comparables directamente con `µg/m³` de DAGMA.

### Salidas importantes

| Fuente | Hallazgo |
|---|---|
| NO₂ | señales en Yumbo y Cali centro |
| SO₂ | más ruidoso y con valores negativos posibles por ajuste DOAS |
| O₃ | columna total casi uniforme, no ozono superficial |

Percentiles reportados:

| Gas | p50 | p90 | p99 | Unidad |
|---|---:|---:|---:|---|
| NO₂ | 2.64e-05 | 5.28e-05 | 8.87e-05 | mol/m² |
| SO₂ | 6.14e-05 | 3.87e-04 | 8.30e-04 | mol/m² |
| O₃ | 1.15e-01 | 1.23e-01 | 1.29e-01 | mol/m² |

Evidencias:

- `docs/situacion-1/evidencias/eda/s5p/s5p_mapas_promedio.png`
- `docs/situacion-1/evidencias/eda/s5p/s5p_distribucion_temporal.png`
- `docs/situacion-1/evidencias/eda/s5p/s5p_distribuciones_percentiles.png`

## 8. ERA5: código y variables meteorológicas

ERA5 se usa con 8 variables:

| Variable | Unidad | Rol |
|---|---|---|
| `temperature_2m` | K | temperatura |
| `dewpoint_temperature_2m` | K | punto de rocío |
| `u_component_of_wind_10m` | m/s | viento este-oeste |
| `v_component_of_wind_10m` | m/s | viento norte-sur |
| `boundary_layer_height` | m | mezcla vertical |
| `relative_humidity_850hPa` | % | humedad en altura |
| `surface_pressure` | Pa | presión |
| `total_precipitation` | m | lluvia |

### Fórmula revisada: velocidad del viento

$$
wind\_speed = \sqrt{u^2 + v^2}
$$

### Salidas importantes

| Hallazgo | Lectura |
|---|---|
| 43824 timestamps | cobertura horaria continua de 5 años |
| BLH 06:00 ≈ 66 m | poca mezcla, más acumulación posible |
| BLH 13:00 ≈ 607 m | mayor mezcla, más dilución |
| amplitud BLH | factor 9x |

Auditoría:

- correcto: ERA5 horario permite analizar ciclo diurno;
- correcto: BLH justifica incluir meteorología;
- decisión defendible: usar ERA5 atmosférico y no ERA5-Land si se necesitan `boundary_layer_height` y humedad en altura.

Evidencias:

- `docs/situacion-1/evidencias/eda/era5/era5_ciclo_diurno.png`
- `docs/situacion-1/evidencias/eda/era5/era5_correlacion_variables.png`
- `docs/situacion-1/evidencias/eda/era5/era5_distribuciones_variables.png`

## 9. MODIS MAIAC: escala, bug y corrección

MODIS aporta:

| Banda | Qué representa |
|---|---|
| `Optical_Depth_047` | AOD a 0.47 µm |
| `Optical_Depth_055` | AOD a 0.55 µm |
| `Column_WV` | vapor de agua |
| `AOD_QA` | calidad |

### Fórmula revisada: escala AOD

$$
AOD_{real} = AOD_{raw} \times 0.001
$$

El proyecto documenta que hubo versiones con problemas:

| Versión | Problema | Resultado |
|---|---|---|
| v1 | `_FillValue` no enmascarado | AOD negativo/no físico |
| v2 | escala aplicada pero gránulos no-Cali contaminaban | AOD diluido |
| v3 | máscara + escala + filtro `h10v08` | AOD físico |

Auditoría:

- correcto: aplicar escala `0.001`;
- correcto: enmascarar `_FillValue = -28672`;
- correcto: no vender AOD como PM2.5 directo;
- importante: MODIS tiene baja cobertura por nubosidad tropical.

Salidas reportadas:

| Variable | Cobertura | Mediana |
|---|---:|---:|
| `Optical_Depth_047` | 12.9% | 0.287 |
| `Optical_Depth_055` | 12.9% | 0.207 |
| `Column_WV` | 95.9% | 1.770 cm |

Evidencias:

- `docs/situacion-1/evidencias/eda/modis/v2/modis_raw_vs_escalado.png`
- `docs/situacion-1/evidencias/eda/modis/v2/modis_mapa_promedio.png`
- `docs/situacion-1/evidencias/eda/modis/v2/modis_cobertura_efectiva.png`

## 10. DAGMA/CVC: columnas, salidas y limitación clave

El parquet tiene:

```text
107291 filas × 14 columnas
```

Columnas principales:

```text
estacion_id, nombre_est, nombre_fgda, msfl_code,
med_concentracion_estandar, med_fecha_inicio, med_fecha_final,
nombre_unidad, sigla_unidad, latitud, longitud, altitud,
municipio, departamento
```

### Salidas de notebooks

`EDA.ipynb` y `dagma-analisis-cruzado.ipynb` confirman:

| Contaminante | Mediciones |
|---|---:|
| NO₂ | 6246 |
| O₃ | 60098 |
| SO₂ | 40947 |

Limitación crítica:

> NO₂ solo aparece en ESTACIÓN YUMBO dentro del parquet principal.

Auditoría:

- correcto: usar DAGMA/CVC como verdad observada principal;
- correcto: no mezclar automáticamente Excel Cristian con parquet;
- importante: NO₂ no permite LOO-CV espacial robusto en Situación 3.

El notebook `notebooks/dagma/dagma-analisis-cruzado.ipynb` muestra que el cruce parquet vs Excel tiene diferencias grandes para O₃/SO₂ y por eso el Excel queda como fuente complementaria, no como reemplazo.

## 11. Manifest: trazabilidad del dataset

El notebook `manifest/manifest.ipynb` genera el manifest técnico.

Salidas relevantes:

| Campo | Valor |
|---|---:|
| fuentes | 7 |
| peso total | 89.732 GB |
| archivos | 8847 |
| umbral ≥ 50 GB | True |
| hash manifest MD5 | `95fd112867f0d070a3294919f69...` |

Auditoría:

- correcto: el manifest prueba el umbral de peso;
- correcto: incluye fuentes Zarr + DAGMA;
- riesgo: en la celda de configuración del notebook aparece un token HF explícito; para entrega pública eso debe evitarse aunque el acceso a datos sea público.

Referencia:

- `manifest/manifest_output/manifest.json`

## 12. Fórmulas revisadas contra código

| Fórmula | Dónde aparece | Estado |
|---|---|---|
| NDVI = `(B8-B4)/(B8+B4)` | EDA Sentinel-2 | Correcta, con máscara SCL/B4/B8. |
| `AOD_real = raw × 0.001` | EDA MODIS | Correcta en versión final v3. |
| velocidad viento `sqrt(u²+v²)` | ERA5 / conceptos | Coherente con variables `u10`, `v10`. |
| columna S5P en `mol/m²` | EDA S5P | Correcta si se selecciona banda explícita. |
| concentración DAGMA en `ug/m3` | parquet DAGMA | Correcta para verdad observada superficial. |

## 13. Qué está bien defendible

- El dataset supera el umbral de 50 GB.
- El panel está organizado en Zarr, adecuado para arrays multidimensionales.
- Sentinel-2 domina el peso y aporta la señal visual fina.
- Sentinel-5P aporta gases en columna, con unidades correctas.
- ERA5 justifica meteorología y BLH.
- MODIS fue auditado y corregido para AOD físico.
- DAGMA/CVC está documentado con columnas y limitaciones.
- Hay manifest con trazabilidad.
- Las salidas EDA existen y se conectan con decisiones de muestreo y modelado.

## 14. Qué hay que cuidar en defensa

| Riesgo | Cómo explicarlo |
|---|---|
| BBox distinto al PDF | Se amplió para incluir Yumbo/Acopi y la zona industrial relevante. |
| NO₂ solo en Yumbo | Limitación real del ground truth; no prometer LOO-CV espacial para NO₂. |
| O₃ S5P es columna total | No equivale a ozono superficial; se usa con cuidado. |
| MODIS AOD no es PM2.5 | Es proxy óptico, no concentración directa. |
| Sentinel-2 tiene baja cobertura limpia | Es esperable en zona tropical nublada; se usa SCL para filtrar. |
| Excel Cristian no reemplaza parquet | Las diferencias con parquet no permiten mezclar sin sesgo. |
| Token en notebook manifest | Debe limpiarse antes de entrega pública. |

## 15. Referencias y documentación

### Internas

- [Datasets del proyecto](../DATASETS.md)
- [Hallazgos EDA](../EDA_HALLAZGOS.md)
- [Situación 1](../situacion-1/README.md)
- [Panel Zarr](../situacion-1/capas/panel-zarr.md)
- [Panel final](../situacion-1/resultados/panel.md)
- [EDA Situación 1](../situacion-1/resultados/eda.md)
- [Validaciones Situación 1](../situacion-1/resultados/validaciones.md)
- [Flujo de datos](../situacion-1/metodologia/flujo-datos.md)
- [Unidades de contaminantes](02_unidades_contaminantes.md)
- [Fórmulas del modelo](03_formulas_modelo.md)

### Notebooks revisados

- [`EDA.ipynb`](../../EDA.ipynb)
- [`notebooks/eda/geovision-clip-eda-completo.ipynb`](../../notebooks/eda/geovision-clip-eda-completo.ipynb)
- [`manifest/manifest.ipynb`](../../manifest/manifest.ipynb)
- [`notebooks/dagma/dagma-analisis-cruzado.ipynb`](../../notebooks/dagma/dagma-analisis-cruzado.ipynb)

### Externas

- [Earth Engine — Sentinel-2 SR Harmonized](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Earth Engine — Sentinel-5P NO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Earth Engine — Sentinel-5P SO₂](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Earth Engine — Sentinel-5P O₃](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [Earth Engine — ERA5 Hourly](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY)
- [Earth Engine — MODIS MAIAC MCD19A2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD19A2_GRANULES)
- [Zarr Python documentation](https://zarr.readthedocs.io/en/stable/)
- [Kaggle Dataset geovision-fuentes](https://www.kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)

### Nota de auditoría

Context7 se usó para confirmar documentación de Zarr como formato para arrays N-dimensionales comprimidos por chunks y para validar unidades/bandas principales del catálogo Earth Engine usadas por Sentinel-5P y Sentinel-2. Todas las referencias externas listadas tienen URL directa.
