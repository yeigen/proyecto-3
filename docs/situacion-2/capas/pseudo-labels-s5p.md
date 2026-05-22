# Pseudo-labels Sentinel-5P

## Qué contiene

Pseudo-labels satelitales usados para guiar el muestreo de clases de contaminación.

## Uso en la situación 2

Se usan percentiles sobre Sentinel-5P:

| Clase | Fuente | Umbral usado |
|---|---|---:|
| `contaminacion_alta_NO2` | NO2 troposférico | p90 |
| `contaminacion_alta_SO2` | SO2 columna | p90 |
| `ozono_anomalo` | O3 columna total | p95 |

Estos pseudo-labels ayudan a construir pares imagen-texto. No deben interpretarse como medición directa a nivel de calle.

## Limitación principal

`ozono_anomalo` usa columna total de O3, no O3 superficial. La clase puede capturar régimen atmosférico o estacional más que contaminación local observada en superficie.

## Evidencias relacionadas

- [Distribución de pseudo-labels](../evidencias/muestreo/tiles/distribucion.seudolabel-modis-tiles.png)
- [Estacionalidad de ozono](../evidencias/muestreo/tiles/tiles_estacionalidad_ozono.png)

## Referencias

- [Sentinel-5P en Situación 1](../../situacion-1/fuentes/sentinel-5p.md)
- [Auditoría de sesgos](../metodologia/auditoria-sesgos.md)
- [Sentinel-5P NO2 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_NO2)
- [Sentinel-5P SO2 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_SO2)
- [Sentinel-5P O3 en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S5P_OFFL_L3_O3)
