# Sentinel-5P TROPOMI

## Qué contiene

Sentinel-5P/TROPOMI aporta columnas satelitales de gases atmosféricos: NO2, SO2 y O3. Estas variables no son mediciones directas a nivel de calle.

## Uso en la situación 1

Se usan como señales espaciales y temporales para caracterizar contaminantes regionales y apoyar pseudo-etiquetas en etapas posteriores.

Variables principales:

- NO2: `tropospheric_NO2_column_number_density`, `NO2_column_number_density`, `cloud_fraction`.
- SO2: `SO2_column_number_density`, `cloud_fraction`.
- O3: `O3_column_number_density`, `cloud_fraction`.

Lectura importante:

- NO2 muestra señales relevantes en Yumbo y Cali centro.
- SO2 es más ruidoso y esporádico.
- O3 es columna total, no ozono superficial.

## Evidencias relacionadas

- [Mapas promedio Sentinel-5P](../evidencias/eda/s5p/s5p_mapas_promedio.png)
- [Distribución temporal S5P](../evidencias/eda/s5p/s5p_distribucion_temporal.png)
- [Cobertura efectiva S5P](../evidencias/eda/s5p/s5p_cobertura_efectiva.png)
- [Capturas NO2](../evidencias/fuentes/google-earth/cali/s5p_no2/)
- [Capturas SO2](../evidencias/fuentes/google-earth/cali/s5p_so2/)
- [Capturas O3](../evidencias/fuentes/google-earth/cali/s5p_o3/)

## Referencias

- [Sentinel-5P OFFL NO2 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Sentinel-5P OFFL SO2 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Sentinel-5P OFFL O3 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
- [Sentinel-5P TROPOMI Mission Page](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-5p)
- [Datasets del proyecto](../../DATASETS.md#2-sentinel-5p-tropomi--dióxido-de-nitrógeno-no₂)
- [Guía original de Situación 1](../GUIA_PROYECTO_SIT1.md)
