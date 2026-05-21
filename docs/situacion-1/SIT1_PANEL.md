# Situacion 1 — Panel de datos satelital

## Resumen

Para una explicación narrativa del objetivo del proyecto y del alcance de esta fase, ver [`GUIA_PROYECTO_SIT1.md`](GUIA_PROYECTO_SIT1.md).

Panel analítico longitudinal multi-fuente sobre el área metropolitana de Santiago de Cali
incluyendo el corredor industrial Yumbo-Acopi. Periodo 2021-2026, ~90 GB en formato Zarr,
almacenado en Google Cloud Storage, HuggingFace Hub y Kaggle Datasets.

## BBox (bounding box)

El proyecto usa un area de estudio mayor a la solicitada originalmente por el PDF:

| | PDF | Proyecto | Diferencia |
|---|---|---|---|
| Lon oeste | -76.60 | -76.65 | 0.05 grados |
| Lon este | -76.40 | -76.30 | 0.10 grados |
| Lat sur | 3.30 | 3.30 | igual |
| Lat norte | 3.55 | 3.65 | 0.10 grados |
| Area | ~18 x 28 km | **~38 x 38 km** | **+35%** |

Razon del BBox ampliado (decision #1 documentada en JUSTIFICACIONES.md):
1. Capturar Yumbo (lat 3.58) — corredor industrial, unica estacion con NO2
2. Capturar Acopi — zona industrial satelite
3. Capturar cultivos de cana — quemas estacionales que afectan calidad del aire

![BBox comparacion](/docs/evidencias/situacion-1/panel/sit1_panel_bbox_pdf_vs_proyecto.png)

Vista satelital del area de estudio:

![Cali Google Earth](/docs/evidencias/situacion-1/panel/sit1_panel_cali_google_earth.png)

## Arquitectura cloud

Flujo de datos:
1. Google Earth Engine (GEE) → exportacion via `xee` o `getDownloadURL`
2. Google Cloud Storage (GCS) → almacenamiento raw en GeoTIFF + Zarr
3. HuggingFace Hub → datasets pequenos (S5P, ERA5, MODIS)
4. Kaggle Dataset → panel completo para consumo del equipo

## Fuentes de datos

| Fuente | Asset ID GEE | Bandas | Periodo | Shape Zarr | Peso |
|---|---|---|---|---|---|
| Sentinel-2 MSI L2A | COPERNICUS/S2_SR_HARMONIZED | 13 | 2021-2025 | (1552, 13, 3897, 3897) | 76.99 GB |
| S5P NO2 | COPERNICUS/S5P/OFFL/L3_NO2 | 3 | 2021-2025 | (25592, 3, 36, 36) | 0.04 GB |
| S5P SO2 | COPERNICUS/S5P/OFFL/L3_SO2 | 2 | 2021-2025 | (25829, 2, 36, 36) | 0.04 GB |
| S5P O3 | COPERNICUS/S5P/OFFL/L3_O3 | 2 | 2021-2025 | (25716, 2, 36, 36) | 0.06 GB |
| ERA5 Hourly | ECMWF/ERA5/HOURLY | 8 | 2021-2025 | (43824, 8, 2, 2) | 0.09 GB |
| MODIS MCD19A2 | MODIS/061/MCD19A2_GRANULES | 4 | 2021-2025 | (1826, 4, 43, 43) | 0.02 GB |

Justificacion de bandas en `/docs/DATASETS.md`.

## Almacenamiento

### Google Cloud Storage (source-of-truth)

Bucket: `gs://fuentes-proyecto-3`
Contenido: GeoTIFFs raw + paneles Zarr de las 6 fuentes.

![bucket-gcs](/docs/evidencias/situacion-1/panel/sit1_panel_bucket_gcs.png)

### HuggingFace Hub (backup publico)

Bucket: `yeigen/fuentes-proyecto-3`
Contenido: 5 paneles Zarr pequenos (S5P, ERA5, MODIS). S2 vive solo en GCS por peso.

![bucket-hf](/docs/evidencias/situacion-1/panel/sit1_panel_bucket_hugging_face.png)

### Kaggle Dataset (consumo del equipo)

Dataset: [`juanjoseorozcolopez/geovision-fuentes`](https://kaggle.com/datasets/juanjoseorozcolopez/geovision-fuentes)
Volumen: 89.73 GB · 8,848 archivos en Kaggle. El manifest técnico registra 8,847 archivos de datos; Kaggle cuenta además `dataset-metadata.json`.

![Kaggle dataset](/docs/evidencias/situacion-1/panel/sit1_panel_kaggle_dataset.png)

## EDA — Analisis Exploratorio

### Sentinel-2

**Distribucion temporal:** 1,552 escenas en total, cadencia 22-28 escenas/mes.
A partir de 2025-04 aumenta a 28-39 escenas/mes (entrada en operacion de Sentinel-2C).

![S2 temporal](/docs/evidencias/situacion-1/eda/sit1_eda_s2_distribucion_temporal_captura.png)

**Filtro SCL:** Solo 136 escenas (8.8%) pasan el umbral SCL > 30%.
La mediana de cobertura util por escena es 1.8% — la mayoria de escenas tienen menos de 2% de pixeles sin nubes.

| Umbral SCL | Escenas utiles | % del total |
|---|---|---|
| > 10% | 438 | 28.2% |
| > 30% | 136 | 8.8% |
| > 50% | 66 | 4.3% |
| > 70% | 17 | 1.1% |

![SCL distribucion](/docs/evidencias/situacion-1/eda/sentinel-2/s2_scl_distribucion_mensual.png)

**Tiles MGRS:** Solo 2 tiles cruzan el BBox. T18NUJ aporta 133 escenas utiles (97.8%), T18NUK solo 3 (2.2%). El modelo CLIP se entrena practicamente solo sobre T18NUJ.

**NDVI:** Distribucion bimodal con picos en ~0.15 (urbano) y ~0.75 (vegetacion).
Los umbrales del muestreo (NDVI < 0.3 urbano, > 0.6 vegetacion) caen exactamente en los valles del histograma.

![NDVI](/docs/evidencias/situacion-1/eda/sentinel-2/s2_ndvi_distribucion.png)

### Sentinel-5P (NO2, SO2, O3)

25,000+ escenas por contaminante, cadencia constante de 400-440 escenas/mes durante 5 anos.

![S5P temporal](/docs/evidencias/situacion-1/eda/s5p/s5p_distribucion_temporal.png)

**Cobertura efectiva** (pixeles que pasan control de calidad):

| Contaminante | Mediana cobertura | % escenas con >= 50% validos |
|---|---|---|
| NO2 | 0.0% | 16% |
| SO2 | 72.1% | 50% |
| O3 | 0.0% | 10% |

La baja cobertura de NO2 y O3 se debe a filtros `qa_value` aplicados por GEE upstream.
SO2 usa un umbral mas permisivo (50% vs 75% de NO2).

**Mapas promedio:** Dos hot-spots de NO2 claros: Yumbo (norte, lat ~3.5, corredor industrial) y Cali centro (lat ~3.4, trafico vehicular). SO2 muestra patron ruidoso (emision esporadica). O3 es casi uniforme (variabilidad espacial baja).

![S5P mapas](/docs/evidencias/situacion-1/eda/s5p/s5p_mapas_promedio.png)

**Percentiles S5P (full panel, usado para pseudo-labels del muestreo):**

| Gas | p50 | p90 | p99 | Unidad |
|---|---|---|---|---|
| NO2 | 2.64e-05 | 5.28e-05 | 8.87e-05 | mol/m2 |
| SO2 | 6.14e-05 | 3.87e-04 | 8.30e-04 | mol/m2 |
| O3 | 1.15e-01 | 1.23e-01 | 1.29e-01 | mol/m2 |

### ERA5 Hourly

43,824 timestamps horarios (5 anos continuos, 100% cobertura, sin gaps).
8 variables seleccionadas de 292 disponibles.

**Ciclo diurno BLH:**

| Hora | BLH |
|---|---|
| 06:00 (valle) | 66 m |
| 13:00 (pico) | 607 m |
| Amplitud | **factor 9x** |

BLH varía 9x entre noche y día. Esto justifica el uso de ERA5 horario sobre ERA5-Land
(que no contiene BLH). S5P TROPOMI pasa a las ~13:30, exactamente en el pico de mezcla atmosférica.

**Vientos predominantes:** v10 medio = -0.62 m/s (vientos del norte).
Esto confirma que los alisios del NE transportan contaminacion de Yumbo hacia Cali.
Justifica la decision #1 (BBox ampliado para capturar Yumbo).

**Correlaciones entre variables:** Solo 3 pares superan |r| > 0.5:
T2m-Td2m (0.71), T2m-BLH (0.64), Td2m-p_surf (0.61). Las 8 variables son complementarias.

![ERA5 ciclo](/docs/evidencias/situacion-1/eda/era5/era5_ciclo_diurno.png)

### MODIS MAIAC AOD

**Bug detectado y corregido en 3 iteraciones:**

| Version | Problema | Fix |
|---|---|---|
| v1 (original) | FillValue no enmascarado antes de promediar | Mediana AOD = -1.247 (invalido) |
| v2 | Escala aplicada, pero contaminado por granules no-Cali | AOD diluido 10x |
| v3 (final) | Filtro h10v08 + scale + mask correctos | AOD fisico: mediana 0.287 |

**Panel final (v3) sobre 500 escenas aleatorias:**

| Banda | Cobertura | Mediana | Rango fisico |
|---|---|---|---|
| Optical_Depth_047 | 12.9% pixeles | 0.287 | [0.000, 3.411] |
| Optical_Depth_055 | 12.9% | 0.207 | [0.000, 2.650] |
| Column_WV | 95.9% | 1.770 cm | [0.055, 5.785] |

Cobertura AOD baja (12.9%) es inherente al algoritmo MAIAC en zona tropical nublada.
WV mantiene 96% porque funciona bajo nubosidad parcial.

**Sobre los 5,000 tiles muestreados (contexto Sit 2):**

| Variable | Cobertura tiles | Media |
|---|---|---|
| modis_AOD_047 | 767 / 5,000 (15.3%) | 0.317 |
| modis_WV | 4,897 / 5,000 (97.9%) | 1.787 cm |

![MODIS v3](/docs/evidencias/situacion-1/eda/modis/v2/modis_mapa_promedio.png)

### DAGMA / SISAIRE

10 estaciones de monitoreo de calidad del aire, 107,291 mediciones horarias, periodo 2020-01-01 a 2024-12-31. Overlap util con el panel satelital: 4 anos (2021-2024).

**Listado completo de estaciones:**

| ID | Nombre | Operador | Latitud | Longitud | Altitud (m) | Municipio |
|---|---|---|---|---|---|---|
| 8285 | BASE AEREA | DAGMA | 3.457128 | -76.502303 | 956 | Santiago de Cali |
| 30109 | CANAVERALEJO | DAGMA | 3.416366 | -76.549613 | 975 | Santiago de Cali |
| 30110 | COMPARTIR | DAGMA | 3.428260 | -76.466584 | 952 | Santiago de Cali |
| 30004 | ERA OBRERO | DAGMA | 3.457317 | -76.506539 | 968 | Santiago de Cali |
| 8777 | ESTACION YUMBO | **CVC** | 3.579075 | -76.489558 | 950 | Yumbo |
| 30111 | LA ERMITA | DAGMA | 3.455514 | -76.530978 | 994 | Santiago de Cali |
| 8986 | LA FLORA | DAGMA | 3.488218 | -76.518058 | 959 | Santiago de Cali |
| 8288 | PANCE | DAGMA | 3.304517 | -76.531252 | 978 | Santiago de Cali |
| 26190 | TRANSITORIA-NAVARRO | DAGMA | 3.417183 | -76.494960 | 954 | Santiago de Cali |
| 8291 | UNIVERSIDAD DEL VALLE | DAGMA | 3.377911 | -76.533811 | 985 | Santiago de Cali |

**Mediciones por estacion y contaminante:**

| Estacion | NO2 | SO2 | O3 | Total | Cobertura temporal |
|---|---|---|---|---|---|
| YUMBO (CVC) | 6,246 | 12,035 | 16,091 | 34,372 | 80.9 % |
| BASE AEREA | 0 | 7,770 | 7,310 | 15,080 | 35.5 % |
| LA ERMITA | 0 | 8,627 | 0 | 8,627 | 20.3 % |
| LA FLORA | 0 | 4,165 | 5,902 | 10,067 | 23.7 % |
| COMPARTIR | 0 | 0 | 7,507 | 7,507 | 17.7 % |
| CANAVERALEJO | 0 | 5,053 | 0 | 5,053 | 11.9 % |
| UNIVERSIDAD DEL VALLE | 0 | 0 | 6,350 | 6,350 | 14.9 % |
| ERA OBRERO | 0 | 0 | 6,939 | 6,939 | 16.3 % |
| PANCE | 0 | 0 | 5,861 | 5,861 | 13.8 % |
| TRANSITORIA-NAVARRO | 0 | 3,297 | 4,138 | 7,435 | 17.5 % |

Total por contaminante: O3 = 60,098 (56%), SO2 = 40,947 (38%), NO2 = 6,246 (6%).

**Hallazgo critico:** NO2 solo se mide en 1 estacion (Yumbo CVC, 6,246 mediciones). Ninguna estacion DAGMA mide NO2. Esto hace imposible el LOO-CV para NO2 en Situacion 3 (penalizacion potencial: -60% del componente). Mitigacion: reportar validacion alternativa con concordancia espacial S5P y test KS.

SO2 se mide en 6 estaciones (Yumbo, Base Aerea, Ermita, Flora, Canaveralejo, Transitoria-Navarro).
O3 se mide en 8 estaciones (todas excepto Canaveralejo y Ermita).

**Distribucion por ano:**

| Ano | Mediciones |
|---|---|
| 2020 | 52,136 (48.6 %) |
| 2021 | 19,122 (17.8 %) |
| 2022 | 16,346 (15.2 %) |
| 2023 | 11,624 (10.8 %) |
| 2024 | 8,063 (7.5 %) |

La cobertura disminuye drasticamente a partir de 2021. Yumbo CVC es la unica estacion con datos consistentes en todo el periodo.

Cobertura temporal por estacion:

![DAGMA cobertura temporal](/docs/evidencias/situacion-3/dagma/figuras/dagma_cobertura_temporal.png)

Distribuciones por estacion y contaminante:

![DAGMA distribuciones](/docs/evidencias/situacion-3/dagma/figuras/dagma_distribuciones_por_estacion.png)

Ciclo diurno de contaminantes:

![DAGMA ciclo diurno](/docs/evidencias/situacion-3/dagma/figuras/dagma_ciclo_diurno.png)

### Excel SVCASC — fuente complementaria

Ademas del parquet SISAIRE, se descubrio un archivo Excel (`dagma/dagma-cristian.xlsx`)
con datos del sistema SVCASC que incluye variables no presentes en el parquet:

| Variable nueva | Mediciones | Estaciones |
|---|---|---|
| PM10 | 284,815 | 8 |
| PM25 | 140,646 | 8 |
| H2S | 79,773 | 3 |
| Temperatura | 165,475 | 9 |
| Humedad | 156,848 | 9 |
| Viento | ~139K | 6 |

**Cruce parquet vs Excel (35,184 registros coincidentes):**

| Variable | n | Correlacion r | Diferencia media |
|---|---|---|---|
| O3 | 20,449 | **0.387** | 20.88 ug/m3 |
| SO2 | 14,735 | **0.091** | 7.45 ug/m3 |

**Conclusion:** Las fuentes NO son consistentes para NO2/SO2/O3. El parquet (SISAIRE) se mantiene como ground truth oficial. El Excel se usa como fuente complementaria para PM2.5/PM10 y meteorologia.

## Lossless verification

Conversion GeoTIFF -> Zarr verificada bit-perfect:

| Fuente | Banda | diff_max | Resultado |
|---|---|---|---|
| Sentinel-2 | B1 | 0.000000 | bit-perfect |
| Sentinel-2 | B4 | 0.000000 | bit-perfect |
| Sentinel-2 | B8 | 0.000000 | bit-perfect |
| Sentinel-2 | SCL | 0.000000 | bit-perfect |
| S5P NO2 | tropospheric_NO2 | 2e-12 | ruido float64->float32 |
| ERA5 | temperature_2m | 0.000000 | bit-perfect |

## Manifest

Archivo: `/manifest/manifest_output/manifest.json`
8,847 archivos de datos, 89.732 GB total, hash MD5 por fuente. La UI de Kaggle muestra 8,848 archivos porque incluye `dataset-metadata.json`.

Nota: el campo global `spatial_extent.bbox` del manifest conserva el BBox original del PDF. Para la defensa usamos el BBox operativo del proyecto `[-76.65, 3.30, -76.30, 3.65]`, confirmado por `google-earth/config.py` y por los bounds reales de las fuentes.

## Costos cloud

El flujo se diseñó para mantener costos bajos usando cuotas académicas y almacenamiento público gratuito donde era viable.

| Servicio | Uso en el proyecto | Costo estimado |
|---|---|---|
| GEE | Consulta y exportación de imágenes satelitales | Gratuito con cuota académica |
| GCS | Almacenamiento intermedio de GeoTIFF + Zarr (~90 GB) | ~2-3 USD/mes |
| HuggingFace Hub | Backup público de paneles pequeños | Gratuito |
| Kaggle Dataset | Distribución del panel completo al equipo | Gratuito |
| Kaggle Notebooks | Entrenamiento con GPU T4 | Gratuito dentro de cuota semanal |

## Tiempo invertido

Basado en 120 ejecuciones registradas en logs (Droplet + local) desde el 6 de mayo al 19 de mayo de 2026.

| Actividad | Logs | Periodo | Tiempo estimado |
|---|---|---|---|
| EDA inicial + visualizacion Cali | 13 | 06-07 May | ~6 h |
| Exportaciones GEE a GCS | | | |
| - S5P NO2, SO2, O3 | 4 | 08 May | ~1 h |
| - ERA5 | 6 | 08 May | ~1 h |
| - MODIS | 1 | 08 May | ~30 min |
| - S2 (multiples intentos) | 10 | 09-10 May | ~8 h |
| Conversion GeoTIFF -> Zarr | | | |
| - S5P | 5 | 08-14 May | ~1 h |
| - ERA5 (6 intentos) | 10 | 08 May | ~1 h |
| - MODIS v1 | 4 | 09-10 May | ~2 h |
| - S2 (18 ejecuciones, debugging) | 24 | 08-10 May | ~8 h |
| Upload HF + Kaggle | | | |
| - Datasets pequenos | 14 | 10 May | ~1 h |
| - S2 (descarga GCS + upload) | 5 | 10-11 May | ~3 h |
| MODIS bug fixing (v2+v3) | 7 | 18-19 May | ~3 h |
| Analisis pesos y validacion | 6 | 06-07 May | ~1 h |
| Pruebas de subida | 3 | 07 May | ~30 min |
| Documentacion | varios | 07-19 May | ~6 h |
| **Total estimado** | **120** | **06-19 May 2026** | **~43 h** |

Distribucion por dia:
- 06 May: EDA inicial (~3 h)
- 07 May: EDA + primeras exportaciones (~4 h)
- 08 May: Exportaciones S5P, ERA5, MODIS + Zarrs (~6 h)
- 09 May: Exportacion S2 + Zarr S2 + MODIS (~6 h)
- 10 May: S2 debugging + Zarr + Uploads HF (~8 h)
- 11 May: Upload S2 a HF (~1 h)
- 14 May: Reproceso S5P NO2 (~1 h)
- 18-19 May: MODIS v2+v3 bug fixing (~3 h)
- Varios: Documentacion dispersa (~6 h)

## Referencias

- `/docs/DATASETS.md` — catalogo de fuentes
- `/docs/JUSTIFICACIONES.md` — decisiones tecnicas
- `/docs/EDA_HALLAZGOS.md` — hallazgos del EDA (1171 lineas)
- `/docs/REFERENCIAS.md` — indice de enlaces
- `docs/conceptos/` — 14 conceptos tecnicos
