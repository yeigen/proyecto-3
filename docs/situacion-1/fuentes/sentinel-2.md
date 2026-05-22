# Sentinel-2 MSI

## Qué contiene

Sentinel-2 aporta la base visual multiespectral del proyecto. Se usa el producto Level-2A Surface Reflectance Harmonized con 13 bandas exportadas sobre una grilla común de 10 m.

## Uso en la situación 1

Es la fuente más pesada del panel y la entrada visual principal para etapas posteriores con CLIP. Permite observar superficie urbana, vegetación, suelo, humedad y nubosidad.

Bandas usadas:

- `B1`, `B2`, `B3`, `B4`, `B5`, `B6`, `B7`, `B8`, `B8A`, `B9`, `B11`, `B12`, `SCL`.

Hallazgos clave:

- 1,552 escenas entre 2021 y 2025.
- Solo 136 escenas pasan el umbral SCL > 30%.
- La nubosidad limita la cobertura útil.
- El tile `T18NUJ` aporta casi todo el material útil; `T18NUK` toca marginalmente el BBox.

## Evidencias relacionadas

- [Escena RGB Sentinel-2](../evidencias/eda/sentinel-2/s2_rgb_escena_138.png)
- [Distribución temporal Sentinel-2](../evidencias/eda/sit1_eda_s2_distribucion_temporal_captura.png)
- [Distribución NDVI](../evidencias/eda/sentinel-2/s2_ndvi_distribucion.png)
- [Distribución SCL mensual](../evidencias/eda/sentinel-2/s2_scl_distribucion_mensual.png)
- [Capturas Google Earth Sentinel-2](../evidencias/fuentes/google-earth/cali/sentinel2/)

## Referencias

- [Sentinel-2 MSI Level-2A en Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Sentinel-2 Mission Guide](https://sentiwiki.copernicus.eu/web/s2-mission)
- [Datasets del proyecto](../../DATASETS.md#1-sentinel-2-msi-l2a-surface-reflectance-harmonized)
- [Guía original de Situación 1](../GUIA_PROYECTO_SIT1.md)
