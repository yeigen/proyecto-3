# EDA

## Qué contiene

Hallazgos principales del análisis exploratorio de Situación 1, separados por fuente.

## Sentinel-2

- 1,552 escenas entre 2021 y 2025.
- Solo 136 escenas pasan SCL > 30%.
- NDVI bimodal: urbano cerca de 0.15 y vegetación cerca de 0.75.
- El tile `T18NUJ` domina el material útil.

Evidencias:

- [Distribución temporal Sentinel-2](../evidencias/eda/sit1_eda_s2_distribucion_temporal_captura.png)
- [NDVI Sentinel-2](../evidencias/eda/sentinel-2/s2_ndvi_distribucion.png)
- [SCL mensual](../evidencias/eda/sentinel-2/s2_scl_distribucion_mensual.png)

## Sentinel-5P

- NO2 muestra señales en Yumbo y Cali centro.
- SO2 es más ruidoso y esporádico.
- O3 es casi uniforme y representa columna total.

Evidencias:

- [Mapas promedio S5P](../evidencias/eda/s5p/s5p_mapas_promedio.png)
- [Distribución temporal S5P](../evidencias/eda/s5p/s5p_distribucion_temporal.png)
- [Percentiles S5P](../evidencias/eda/s5p/s5p_distribuciones_percentiles.png)

## ERA5

- Cobertura horaria continua.
- BLH varía fuertemente durante el día.
- El viento medio respalda incluir Yumbo en el BBox operativo.

Evidencias:

- [Ciclo diurno ERA5](../evidencias/eda/era5/era5_ciclo_diurno.png)
- [Correlación ERA5](../evidencias/eda/era5/era5_correlacion_variables.png)

## MODIS MAIAC

- La versión final confiable es `panel_v3.zarr`.
- AOD tiene cobertura baja por nubosidad.
- Vapor de agua conserva cobertura alta.

Evidencias:

- [Mapa promedio MODIS](../evidencias/eda/modis/v2/modis_mapa_promedio.png)
- [Cobertura MODIS](../evidencias/eda/modis/v2/modis_cobertura_efectiva.png)

## DAGMA/CVC

- 10 estaciones dentro del BBox.
- NO2 solo aparece en Yumbo.
- O3 y SO2 tienen mayor presencia espacial.

Evidencias:

- [Serie por contaminante](../evidencias/eda/dagma/dagma_serie_temporal_media_contaminantes.png)
- [Serie por estación](../evidencias/eda/dagma/dagma_serie_temporal_media_por_estacion.png)

## Referencias

- [Hallazgos EDA globales](../../EDA_HALLAZGOS.md)
- [Panel original de Situación 1](../SIT1_PANEL.md)
